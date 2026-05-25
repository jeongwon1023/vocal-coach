"""
강사 교재 RAG — coach_knowledge/ → 검색 → GPT 코칭 컨텍스트.

환경 변수:
    COACH_RAG_ENABLED=1          (기본 켜짐, 0이면 비활성)
    COACH_RAG_TOP_K=4            검색 상위 N개
    OPENAI_API_KEY               있으면 임베딩 검색, 없으면 키워드 검색
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_DIR = Path(__file__).resolve().parent
KNOWLEDGE_DIR = PROJECT_DIR / "coach_knowledge"
INDEX_DIR = PROJECT_DIR / ".cache" / "coach_rag"
INDEX_PATH = INDEX_DIR / "index.json"
INDEX_VERSION = 1
EMBED_MODEL = "text-embedding-3-small"
CHUNK_MAX_CHARS = 520
CHUNK_OVERLAP = 80
SUPPORTED_SUFFIXES = {".md", ".txt"}


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def rag_enabled() -> bool:
    return os.environ.get("COACH_RAG_ENABLED", "1").strip().lower() not in ("0", "false", "no", "off")


def top_k() -> int:
    try:
        return max(1, min(8, int(os.environ.get("COACH_RAG_TOP_K", "4"))))
    except ValueError:
        return 4


@dataclass
class KnowledgeChunk:
    id: str
    source: str
    title: str
    text: str
    embedding: list[float] = field(default_factory=list)


@dataclass
class RetrievedChunk:
    source: str
    title: str
    text: str
    score: float

    @property
    def label(self) -> str:
        base = Path(self.source).stem
        return self.title or base


@dataclass
class RagBundle:
    query: str
    chunks: list[RetrievedChunk]
    prompt_block: str
    source_labels: list[str]


def list_knowledge_files() -> list[Path]:
    if not KNOWLEDGE_DIR.exists():
        return []
    files: list[Path] = []
    for p in sorted(KNOWLEDGE_DIR.rglob("*")):
        if p.is_file() and p.suffix.lower() in SUPPORTED_SUFFIXES and p.name.upper() != "README.MD":
            files.append(p)
    return files


def _doc_title(path: Path, body: str) -> str:
    for line in body.splitlines():
        line = line.strip()
        if line.startswith("#"):
            return re.sub(r"^#+\s*", "", line).strip()
    return path.stem.replace("_", " ")


def _split_paragraphs(text: str) -> list[str]:
    parts = re.split(r"\n\s*\n+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def _chunk_text(text: str, source: str, title: str) -> list[KnowledgeChunk]:
    chunks: list[KnowledgeChunk] = []
    for para in _split_paragraphs(text):
        if len(para) <= CHUNK_MAX_CHARS:
            pieces = [para]
        else:
            pieces = []
            start = 0
            while start < len(para):
                end = min(len(para), start + CHUNK_MAX_CHARS)
                pieces.append(para[start:end].strip())
                if end >= len(para):
                    break
                start = max(start + 1, end - CHUNK_OVERLAP)
        for piece in pieces:
            if len(piece) < 40:
                continue
            cid = hashlib.md5(f"{source}:{piece[:120]}".encode()).hexdigest()[:12]
            chunks.append(KnowledgeChunk(id=cid, source=source, title=title, text=piece))
    return chunks


def _load_documents() -> list[KnowledgeChunk]:
    all_chunks: list[KnowledgeChunk] = []
    for path in list_knowledge_files():
        try:
            body = path.read_text(encoding="utf-8")
        except Exception:
            continue
        rel = str(path.relative_to(KNOWLEDGE_DIR)).replace("\\", "/")
        title = _doc_title(path, body)
        all_chunks.extend(_chunk_text(body, rel, title))
    return all_chunks


def _tokens(text: str) -> set[str]:
    text = text.lower()
    text = re.sub(r"[^\w\s가-힣]", " ", text)
    toks = {t for t in text.split() if len(t) >= 2}
    for m in re.finditer(r"[가-힣]{2,}", text):
        toks.add(m.group())
    return toks


def _keyword_score(query: str, chunk_text: str) -> float:
    q = _tokens(query)
    if not q:
        return 0.0
    c = _tokens(chunk_text)
    if not c:
        return 0.0
    overlap = len(q & c)
    if overlap == 0:
        return 0.0
    return overlap / math.sqrt(len(q))


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na <= 0 or nb <= 0:
        return 0.0
    return dot / (na * nb)


def _embed_texts(texts: list[str], api_key: str | None = None) -> list[list[float]]:
    key = api_key or os.environ.get("OPENAI_API_KEY")
    if not key or not texts:
        return [[] for _ in texts]
    try:
        from openai import OpenAI
    except ImportError:
        return [[] for _ in texts]
    client = OpenAI(api_key=key)
    resp = client.embeddings.create(model=EMBED_MODEL, input=texts)
    return [list(item.embedding) for item in resp.data]


def _index_fingerprint(chunks: list[KnowledgeChunk]) -> str:
    blob = "|".join(f"{c.source}:{c.id}" for c in chunks)
    return hashlib.md5(blob.encode()).hexdigest()


def build_index(*, force: bool = False, api_key: str | None = None) -> dict[str, Any]:
    """coach_knowledge → .cache/coach_rag/index.json"""
    chunks = _load_documents()
    fp = _index_fingerprint(chunks)
    if not force and INDEX_PATH.exists():
        try:
            cached = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
            if cached.get("fingerprint") == fp:
                return {"rebuilt": False, "chunks": len(cached.get("chunks", [])), "mode": cached.get("mode", "?")}
        except Exception:
            pass

    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    mode = "keyword"
    texts = [c.text for c in chunks]
    embeddings = _embed_texts(texts, api_key=api_key)
    if embeddings and embeddings[0]:
        mode = EMBED_MODEL
        for chunk, emb in zip(chunks, embeddings):
            chunk.embedding = emb
    else:
        for chunk in chunks:
            chunk.embedding = []

    payload = {
        "version": INDEX_VERSION,
        "built_at": _now_iso(),
        "fingerprint": fp,
        "mode": mode,
        "chunks": [
            {
                "id": c.id,
                "source": c.source,
                "title": c.title,
                "text": c.text,
                "embedding": c.embedding,
            }
            for c in chunks
        ],
    }
    INDEX_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"rebuilt": True, "chunks": len(chunks), "mode": mode}


def _load_index() -> dict[str, Any] | None:
    if not INDEX_PATH.exists():
        return None
    try:
        return json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    except Exception:
        return None


def _ensure_index() -> dict[str, Any]:
    idx = _load_index()
    chunks = _load_documents()
    fp = _index_fingerprint(chunks)
    if idx and idx.get("fingerprint") == fp and idx.get("chunks"):
        return idx
    build_index(force=True)
    return _load_index() or {"chunks": [], "mode": "keyword"}


def build_query_from_analysis(analysis_json: dict[str, Any] | None) -> str:
    """분석 JSON에서 약한 영역 키워드를 뽑아 검색 쿼리 생성."""
    if not analysis_json:
        return "보컬 연습 루틴 코칭"
    parts: list[str] = ["보컬 레슨"]
    stages = analysis_json.get("stage_scores") or {}
    if isinstance(stages, dict) and stages:
        labeled = []
        for key, val in stages.items():
            try:
                labeled.append((str(key), float(val)))
            except (TypeError, ValueError):
                continue
        if labeled:
            weakest = min(labeled, key=lambda x: x[1])
            stage_map = {"1": "음정", "2": "박자", "3": "호흡", "4": "종합"}
            parts.append(stage_map.get(weakest[0], "연습"))
    pitch = analysis_json.get("pitch") or {}
    devs = pitch.get("deviation_segments") or []
    if devs:
        parts.append("음정 틀린 구간 연습")
    breath = analysis_json.get("breath_issues") or []
    if breath:
        parts.append("호흡 지지")
    timbre = analysis_json.get("timbre_issues") or []
    if timbre:
        parts.append("음색 믹스보이스")
    song = analysis_json.get("song_title")
    if song and song != "미지정":
        parts.append(str(song))
    return " ".join(parts)


def retrieve(query: str, *, k: int | None = None) -> list[RetrievedChunk]:
    if not rag_enabled() or not query.strip():
        return []
    if not list_knowledge_files():
        return []

    idx = _ensure_index()
    raw_chunks = idx.get("chunks") or []
    if not raw_chunks:
        return []

    k = k or top_k()
    mode = idx.get("mode", "keyword")
    scored: list[RetrievedChunk] = []

    if mode == EMBED_MODEL and os.environ.get("OPENAI_API_KEY"):
        q_emb = _embed_texts([query.strip()])[0]
        if q_emb:
            for item in raw_chunks:
                emb = item.get("embedding") or []
                score = _cosine(q_emb, emb)
                if score > 0.05:
                    scored.append(
                        RetrievedChunk(
                            source=str(item.get("source", "")),
                            title=str(item.get("title", "")),
                            text=str(item.get("text", "")),
                            score=score,
                        )
                    )
        else:
            mode = "keyword"

    if mode != EMBED_MODEL or not scored:
        for item in raw_chunks:
            text = str(item.get("text", ""))
            score = _keyword_score(query, text)
            if score > 0:
                scored.append(
                    RetrievedChunk(
                        source=str(item.get("source", "")),
                        title=str(item.get("title", "")),
                        text=text,
                        score=score,
                    )
                )

    scored.sort(key=lambda c: c.score, reverse=True)
    return scored[:k]


def format_rag_prompt(chunks: list[RetrievedChunk]) -> str:
    if not chunks:
        return ""
    lines = [
        "아래는 학원·강사 교재에서 찾은 관련 내용입니다. "
        "학생에게 답할 때 이 내용을 우선 반영하되, 분석 JSON과 모순되면 JSON을 따르세요.",
        "",
    ]
    for i, ch in enumerate(chunks, 1):
        lines.append(f"--- 교재 {i}: {ch.label} ({ch.source}) ---")
        lines.append(ch.text.strip())
        lines.append("")
    return "\n".join(lines).strip()


def retrieve_for_coaching(
    query: str,
    analysis_json: dict[str, Any] | None = None,
    *,
    k: int | None = None,
) -> RagBundle:
    merged_query = query.strip()
    if analysis_json:
        ctx = build_query_from_analysis(analysis_json)
        merged_query = f"{merged_query} {ctx}".strip()
    chunks = retrieve(merged_query, k=k)
    labels = list(dict.fromkeys(c.label for c in chunks))
    return RagBundle(
        query=merged_query,
        chunks=chunks,
        prompt_block=format_rag_prompt(chunks),
        source_labels=labels,
    )


def rag_status() -> dict[str, Any]:
    files = list_knowledge_files()
    idx = _load_index()
    if not files:
        return {
            "enabled": rag_enabled(),
            "ready": False,
            "files": 0,
            "chunks": 0,
            "mode": "none",
            "message": "coach_knowledge/ 폴더에 .md·.txt 교재를 넣어 주세요.",
        }
    if not idx:
        build_index()
        idx = _load_index()
    chunk_n = len((idx or {}).get("chunks") or [])
    return {
        "enabled": rag_enabled(),
        "ready": chunk_n > 0,
        "files": len(files),
        "chunks": chunk_n,
        "mode": (idx or {}).get("mode", "?"),
        "built_at": (idx or {}).get("built_at", ""),
        "message": f"교재 {len(files)}개 · 조각 {chunk_n}개 ({(idx or {}).get('mode', '?')})",
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="강사 교재 RAG 인덱스 빌드")
    parser.add_argument("--force", action="store_true", help="캐시 무시하고 재빌드")
    args = parser.parse_args()
    stats = build_index(force=args.force)
    print(json.dumps({**stats, **rag_status()}, ensure_ascii=False, indent=2))

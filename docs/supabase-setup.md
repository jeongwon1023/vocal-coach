# Supabase 연동 (2단계)

로컬 `records/` JSON 대신 클라우드 DB에 사용자별 기록을 저장합니다.

## 1. Supabase 프로젝트 생성

1. [supabase.com](https://supabase.com) 가입
2. **New project** (무료 tier)
3. **SQL Editor** → `supabase/schema.sql` 내용 붙여넣기 → Run

## 2. API 키 설정

Project Settings → API:
- **Project URL** → `SUPABASE_URL`
- **anon public key** → `SUPABASE_KEY`

### 로컬 (.env)

```
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_KEY=eyJ...
```

### Streamlit Cloud (Secrets)

```toml
SUPABASE_URL = "https://xxxx.supabase.co"
SUPABASE_KEY = "eyJ..."
```

## 3. Python 패키지 (연동 활성화 시)

```powershell
.\venv\Scripts\python.exe -m pip install supabase
```

## 4. 동작 방식

`db_store.py`:
- `SUPABASE_URL` 없음 → 기존처럼 `records/*.json` (로컬)
- `SUPABASE_URL` 있음 → Supabase 저장 (로그인 연동 후 user_id 사용)

## 5. 동작 (베타)

- **로컬 JSON** — 항상 `records/users/{user_id}/` 에 저장 (Streamlit Cloud 재시작 대비)
- **Supabase** — Secrets 설정 시 **로컬 + 클라우드 동시 저장** (미러)
- `user_id` — 체험 계정(`demo_xxx`)·OAuth 공통 text

## 6. 다음 작업

- [ ] Supabase Auth와 RLS 정책 강화 (정식 런칭 전)
- [ ] 마이 페이지 Supabase 기록 우선 조회

/**
 * API 클라이언트 — FastAPI 서버(api_server.py) 연동
 *
 * 로컬 테스트: PC에서 run_api.bat 실행 후
 *   - Android 에뮬레이터: http://10.0.2.2:8000
 *   - 실제 기기 (같은 Wi-Fi): http://<PC_IP>:8000
 */

// TODO: 배포 후 실제 URL로 변경
export const API_BASE_URL = "http://localhost:8000";

export type RecordSummary = {
  id: string;
  recorded_at: string;
  song_title?: string;
  overall_score?: number;
  stage_scores?: Record<string, number>;
};

export type AnalyzeResult = {
  ok: boolean;
  overall_score: number;
  stage_scores?: Record<string, number>;
  record?: Record<string, unknown>;
  compare_text?: string;
  gpt_text?: string;
  gpt_error?: string;
  mr_message?: string;
};

export async function fetchRecords(limit = 20): Promise<RecordSummary[]> {
  const res = await fetch(`${API_BASE_URL}/records?limit=${limit}`);
  if (!res.ok) throw new Error("기록을 불러올 수 없습니다.");
  return res.json();
}

export async function analyzeAudio(
  uri: string,
  filename: string,
  options?: { songTitle?: string; useGpt?: boolean }
): Promise<AnalyzeResult> {
  const form = new FormData();
  form.append("file", {
    uri,
    name: filename,
    type: "audio/m4a",
  } as unknown as Blob);

  const params = new URLSearchParams();
  if (options?.songTitle) params.set("song_title", options.songTitle);
  if (options?.useGpt) params.set("use_gpt", "true");

  const url = `${API_BASE_URL}/analyze?${params.toString()}`;
  const res = await fetch(url, { method: "POST", body: form });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || "분석 실패");
  }
  return res.json();
}

export async function checkHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE_URL}/health`);
    return res.ok;
  } catch {
    return false;
  }
}

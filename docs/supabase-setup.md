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

## 5. 다음 작업 (아직 미구현)

- [ ] Streamlit 로그인 UI (Supabase Auth)
- [ ] 마이 페이지에서 Supabase 기록 조회
- [ ] user_id와 analysis_records 연결

지금은 **스키마 + 저장소 추상화**만 준비되어 있습니다.

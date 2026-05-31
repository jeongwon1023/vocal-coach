# 카카오 로그인 연동 체크리스트 (Vocal Coach)

Supabase + Kakao OAuth + Streamlit Cloud 기준입니다.

## 내 프로젝트 고정 URL

| 항목 | URL |
|------|-----|
| Streamlit 앱 | `https://vocal-coach-ld3wgkgpnqu3cvnoczuf6g.streamlit.app` |
| Supabase Auth 콜백 (카카오 Redirect URI) | `https://jwagmyyhjzjifirsglrd.supabase.co/auth/v1/callback` |
| 로컬 개발 | `http://localhost:8501` |

---

## ① Kakao Developers (developers.kakao.com)

1. **내 애플리케이션** → 앱 선택
2. **앱 설정 → 앱 키** → **REST API 키** 복사 (→ Supabase Client ID)
3. **제품 설정 → 카카오 로그인** → **활성화 ON**
4. **Redirect URI**에 아래 **한 줄** 추가 후 저장:
   ```
   https://jwagmyyhjzjifirsglrd.supabase.co/auth/v1/callback
   ```
5. **제품 설정 → 카카오 로그인 → 보안** → **Client Secret** 발급/확인 (→ Supabase Client Secret)
6. **동의 항목** → 닉네임·프로필 사진 등 최소 1개 필수 동의 설정

---

## ② Supabase Dashboard

1. [Supabase 프로젝트](https://supabase.com/dashboard/project/jwagmyyhjzjifirsglrd) → **Authentication** → **Providers** → **Kakao**
2. **Enable Kakao** ON
3. **Client ID** = Kakao **REST API 키**
4. **Client Secret** = Kakao **Client Secret**
5. **Authentication → URL Configuration**
   - **Site URL**: `https://vocal-coach-ld3wgkgpnqu3cvnoczuf6g.streamlit.app`
   - **Redirect URLs** (각 줄 추가):
     ```
     https://vocal-coach-ld3wgkgpnqu3cvnoczuf6g.streamlit.app
     http://localhost:8501
     ```

---

## ③ Streamlit Secrets (Cloud + 로컬)

[Streamlit Cloud Secrets](https://share.streamlit.io/) 또는 `.streamlit/secrets.toml`:

```toml
SUPABASE_URL = "https://jwagmyyhjzjifirsglrd.supabase.co"
SUPABASE_KEY = "본인_실제_키"   # anon(eyJ...) 또는 sb_publishable_...
STREAMLIT_URL = "https://vocal-coach-ld3wgkgpnqu3cvnoczuf6g.streamlit.app"
```

> Kakao REST API Key / Secret은 **Streamlit Secrets에 넣지 않습니다.** Supabase Dashboard에만 넣습니다.

---

## ④ 연동 확인

```powershell
cd vocal-coach
.\venv\Scripts\python.exe scripts\verify_kakao_setup.py
```

앱에서: 상단 **로그인** → **💬 카카오로 계속하기** → 카카오 화면으로 이동하면 성공.

---

## KOE205 오류 해결 (`잘못된 요청`)

카카오 화면에 **KOE205** / *vocal coach ai 서비스 설정 오류* 가 나오면 아래 순서로 수정하세요.

### 방법 A — 이메일 없이 로그인 (개인 개발자 · 추천)

**1. Supabase** → Authentication → Providers → **Kakao**

- **Allow users without an email** (이메일 없는 사용자 허용) → **ON** ✅

**2. Kakao Developers** → 제품 설정 → 카카오 로그인 → **동의항목**

| 항목 | 설정 |
|------|------|
| 닉네임 (profile_nickname) | **필수 동의** 또는 선택 동의 ON |
| 프로필 사진 (profile_image) | 선택 동의 ON |
| 카카오계정(이메일) (account_email) | **끄기** (개인 앱은 사용 불가) |

**3. Redirect URI** (다시 확인)

```
https://jwagmyyhjzjifirsglrd.supabase.co/auth/v1/callback
```

### 방법 B — 이메일도 받고 싶을 때

**Kakao Developers** → 앱 설정 → **비즈니스** → **개인 개발자 등록** (또는 사업자 정보 등록)

등록 후 **동의항목**에서 **account_email** 활성화 → Supabase Kakao에서 Allow users without an email **OFF** 가능

### Redirect URI / 플랫폼 추가 확인

- **앱 설정 → 플랫폼 → Web** 추가
  - 사이트 도메인: `https://jwagmyyhjzjifirsglrd.supabase.co`
- **REST API 키**를 Supabase Kakao **Client ID**에 사용 (JavaScript 키 ❌)

---

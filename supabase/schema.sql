-- Supabase schema for vocal-coach (Phase 2)
-- Run in Supabase SQL Editor: https://supabase.com/dashboard

create table if not exists analysis_records (
  id uuid primary key default gen_random_uuid(),
  user_id text not null,
  recorded_at timestamptz not null default now(),
  song_title text,
  user_recording text,
  overall_score numeric,
  stage_scores jsonb,
  payload jsonb not null,
  created_at timestamptz not null default now()
);

create index if not exists idx_records_user_date
  on analysis_records (user_id, recorded_at desc);

alter table analysis_records enable row level security;

-- 베타: anon key + 앱 user_id (체험·OAuth 공통). 정식 Auth 연동 시 정책 강화.
create policy "Allow insert for service"
  on analysis_records for insert
  with check (true);

create policy "Allow select by user_id"
  on analysis_records for select
  using (true);

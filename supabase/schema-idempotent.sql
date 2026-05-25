-- vocal-coach — Supabase (재실행해도 안전한 버전)
-- 이미 schema.sql 을 Run 했다면 이 파일은 필요 없습니다.
-- 정책 중복 오류(42710) 났을 때만 이 파일 전체 Run.

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

drop policy if exists "Allow insert for service" on analysis_records;
drop policy if exists "Allow select by user_id" on analysis_records;

create policy "Allow insert for service"
  on analysis_records for insert
  with check (true);

create policy "Allow select by user_id"
  on analysis_records for select
  using (true);

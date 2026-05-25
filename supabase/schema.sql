-- Supabase schema for vocal-coach (Phase 2)
-- Run in Supabase SQL Editor: https://supabase.com/dashboard

create table if not exists analysis_records (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) on delete cascade,
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

create policy "Users read own records"
  on analysis_records for select
  using (auth.uid() = user_id);

create policy "Users insert own records"
  on analysis_records for insert
  with check (auth.uid() = user_id);

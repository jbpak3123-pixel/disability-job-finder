-- ============================================================
-- disability-job-finder Supabase 스키마
-- Supabase > SQL Editor 에 전체 붙여넣고 Run 클릭
-- ============================================================

-- jobs 테이블 (채용공고)
create table if not exists jobs (
  id            uuid    default gen_random_uuid() primary key,
  source        text    not null,           -- '워크넷' | '광진구청' | 'KEAD' 등
  source_id     text    not null unique,    -- 원본 사이트 고유 ID (중복 방지)
  title         text    not null,           -- 공고 제목 (짧은 제목)
  post_title    text,                       -- 게시판에 올라온 원문 제목
  company       text,
  location      text,
  job_type      text,                       -- 'office'|'welfare'|'cafe'|'design'|'service'
  salary        text,
  deadline      date,
  employment    text,
  writing_dept  text,                       -- 작성부서 (게시판 표시 부서)
  contact_dept  text,                       -- 연락처 담당부서
  contact       text,
  qualification text,
  description   text,
  url           text,                       -- 게시글 직접 URL
  board_url     text,                       -- 게시판 목록 URL
  post_direct   boolean default false,      -- true = 게시글 직접링크
  rank          integer default 5,          -- 지역 우선순위 (1~5)
  region_name   text,
  region_class  text,                       -- 'r1'~'r5'
  match_type    text    default 'fair',     -- 'best'|'good'|'fair'
  match_label   text,
  score         integer default 50,
  reasons       text[], -- 매칭 근거 배열
  tags          text[], -- 직종·고용형태 태그
  tag_classes   text[], -- 태그 CSS 클래스
  posted_at     date,
  collected_at  timestamptz default now(),
  notified      boolean default false
);

-- 인덱스 (조회 성능)
create index if not exists idx_jobs_deadline   on jobs(deadline);
create index if not exists idx_jobs_rank       on jobs(rank);
create index if not exists idx_jobs_score      on jobs(score desc);
create index if not exists idx_jobs_collected  on jobs(collected_at desc);
create index if not exists idx_jobs_source_id  on jobs(source_id);

-- RLS: 웹페이지에서 anon key로 읽기 허용
alter table jobs enable row level security;

drop policy if exists "public read jobs" on jobs;
create policy "public read jobs" on jobs
  for select using (true);

-- 확인
select 'jobs 테이블 생성 완료' as status;

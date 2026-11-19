-- Schema for the books table used by supabase_books.py and catalogue.html.
-- Run this once in the Supabase SQL editor of your own project.

create table if not exists public.books (
  id           bigint generated always as identity primary key,
  title        text not null,
  price_gbp    numeric,
  rating       integer,
  availability text,
  url          text unique,
  scraped_at   timestamptz default now(),
  image_url    text
);

-- Row level security: nobody can read or write unless a policy allows it.
alter table public.books enable row level security;

-- Read-only access for the public catalogue page (publishable/anon key).
-- Writes happen only from supabase_books.py with the secret key, which bypasses RLS.
create policy "Anyone can read books" on public.books for select to anon using (true);

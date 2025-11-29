-- Migration: Initial schema for SmartBites (Supabase/Postgres)
-- Create core tables expected by the adapter and services

-- Note: Uses gen_random_uuid() (pgcrypto). If unavailable, replace with uuid_generate_v4().

-- Users table
create table if not exists public.users (
  id uuid primary key default gen_random_uuid(),
  username text unique,
  email text unique,
  full_name text,
  birth_date date,
  gender text,
  household_number integer,
  allergies jsonb,
  intolerances jsonb,
  restrictions jsonb,
  diet_type text,
  favorite_recipes jsonb,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- Receipts table
create table if not exists public.receipts (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references public.users(id) on delete cascade,
  store_name text,
  purchase_date date,
  purchase_time time,
  invoice_number text,
  items jsonb,
  subtotal numeric,
  discounts numeric,
  total numeric,
  payment_method text,
  raw_ocr_text text,
  parsed boolean default false,
  parsing_confidence numeric,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- Pantry items table
create table if not exists public.pantry_items (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references public.users(id) on delete cascade,
  name text,
  normalized_name text,
  quantity numeric,
  unit text,
  purchase_date date,
  source_receipt_id uuid references public.receipts(id),
  expiration_date date,
  category text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create index if not exists idx_pantry_user_normalized on public.pantry_items (user_id, normalized_name);

-- Shopping list items
create table if not exists public.shopping_list_items (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references public.users(id) on delete cascade,
  name text,
  normalized_name text,
  quantity numeric,
  unit text,
  section text,
  auto_added_by text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create index if not exists idx_shopping_user_normalized on public.shopping_list_items (user_id, normalized_name);

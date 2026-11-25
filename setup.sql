-- =====================================================================
-- GFB Machine Inspection Checklist (F52) - database setup
-- Lives in the same Supabase project as the GFB CMMS (shared sign-in), but
-- uses its own tables (all named mic_...). It does not change any CMMS table.
-- Safe to run more than once.
-- Every read and write goes through the functions below; the tables have
-- row level security switched on with no direct access for app users.
-- =====================================================================

create table if not exists public.mic_users (
  user_id    uuid primary key references auth.users(id) on delete cascade,
  name       text not null default '',
  login      text not null default '',
  role       text not null default 'operator' check (role in ('operator','checker','verifier','admin')),
  active     boolean not null default false,
  created_at timestamptz not null default now()
);

create table if not exists public.mic_templates (
  key          text primary key,
  sort         int  not null default 0,
  data         jsonb not null,
  updated_at   timestamptz not null default now(),
  updated_name text
);

create table if not exists public.mic_inspections (
  id          uuid primary key default gen_random_uuid(),
  machine     text not null references public.mic_templates(key),
  insp_date   date not null,
  template    jsonb not null,
  status      text not null default 'open' check (status in ('open','verified')),
  verify_by   uuid,
  verify_name text,
  verify_at   timestamptz,
  verify_note text,
  created_by  uuid,
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now(),
  unique (machine, insp_date)
);

create table if not exists public.mic_rounds (
  id            uuid primary key default gen_random_uuid(),
  inspection_id uuid not null references public.mic_inspections(id) on delete cascade,
  seq           int  not null,
  time_text     text not null default '',
  batch         text not null default '',
  refs          jsonb not null default '{}'::jsonb,
  items         jsonb not null default '{}'::jsonb,
  ng            int  not null default 0,
  status        text not null default 'draft' check (status in ('draft','submitted','checked')),
  done_by       uuid not null,
  done_name     text not null,
  submitted_at  timestamptz,
  check_by      uuid,
  check_name    text,
  check_at      timestamptz,
  note          text,
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now(),
  unique (inspection_id, seq)
);
create index if not exists mic_inspections_date_ix on public.mic_inspections (insp_date);

create table if not exists public.mic_log (
  id            bigserial primary key,
  at            timestamptz not null default now(),
  by            uuid,
  name          text,
  act           text not null,
  inspection_id uuid,
  round_id      uuid,
  detail        jsonb
);
create index if not exists mic_log_insp_ix on public.mic_log (inspection_id);

-- Running batch numbers for inspection rounds: one counter per month (YYYYMM-NNN).
create table if not exists public.mic_counters (
  ym text primary key,
  n  int  not null
);

-- ---------- functions a user may hold (tick boxes): fill = Done by, check = Check by, verify = Verify by, admin ----------
alter table public.mic_users add column if not exists funcs text[];
update public.mic_users set funcs = (case role when 'admin' then '{fill,check,verify,admin}' when 'verifier' then '{fill,check,verify}'
                                     when 'checker' then '{fill,check}' else '{fill}' end)::text[] where funcs is null;
alter table public.mic_users alter column funcs set default '{fill}'::text[];
alter table public.mic_users alter column funcs set not null;


alter table public.mic_users       enable row level security;
alter table public.mic_templates   enable row level security;
alter table public.mic_inspections enable row level security;
alter table public.mic_rounds      enable row level security;
alter table public.mic_log         enable row level security;
alter table public.mic_counters    enable row level security;
revoke all on public.mic_counters from anon, authenticated;
revoke all on public.mic_users, public.mic_templates, public.mic_inspections, public.mic_rounds, public.mic_log from anon, authenticated;
revoke all on sequence public.mic_log_id_seq from anon, authenticated;

-- ---------- helpers ----------
create or replace function public.mic_today() returns date
language sql stable set search_path = public as $$
  select (now() at time zone 'Asia/Kuala_Lumpur')::date
$$;

-- p_f: 'fill' | 'check' | 'verify' | 'admin', or 'any' (any active user), or 'review' (check, verify or admin)
create or replace function public.mic_can(p_f text) returns boolean
language sql stable security definer set search_path = public as $$
  select coalesce((select case p_f when 'any' then true when 'review' then funcs && '{check,verify,admin}'::text[] else p_f = any(funcs) end
                     from public.mic_users where user_id = auth.uid() and active), false)
$$;

create or replace function public.mic_must(p_f text) returns void
language plpgsql stable security definer set search_path = public as $$
begin
  if auth.uid() is null then raise exception 'Sila log masuk / Please sign in'; end if;
  if not public.mic_can(p_f) then
    raise exception 'Akaun anda tidak dibenarkan untuk tindakan ini / Your account is not allowed to do this';
  end if;
end $$;

create or replace function public.mic_name() returns text
language sql stable security definer set search_path = public as $$
  select coalesce((select name from public.mic_users where user_id = auth.uid()), '')
$$;

create or replace function public.mic_addlog(p_act text, p_insp uuid, p_round uuid, p_detail jsonb) returns void
language sql security definer set search_path = public as $$
  insert into public.mic_log (by, name, act, inspection_id, round_id, detail)
  values (auth.uid(), public.mic_name(), p_act, p_insp, p_round, p_detail)
$$;

-- ---------- sign-in / users ----------
-- Called after every sign-in. First call creates the person's row (waiting for
-- activation). An active CMMS admin becomes an active admin here automatically.
create or replace function public.mic_me(p_name text default null) returns jsonb
language plpgsql security definer set search_path = public as $$
declare uid uuid := auth.uid(); u record; r public.mic_users; is_adm boolean; nm text;
begin
  if uid is null then raise exception 'Sila log masuk / Please sign in'; end if;
  select * into r from public.mic_users where user_id = uid;
  if not found then
    select email, raw_user_meta_data into u from auth.users where id = uid;
    select exists (select 1 from public.profiles where id = uid and role = 'admin' and active) into is_adm;
    nm := coalesce(nullif(btrim(p_name), ''), nullif(u.raw_user_meta_data->>'name', ''),
                   (select nullif(name, '') from public.profiles where id = uid), split_part(u.email, '@', 1));
    insert into public.mic_users (user_id, name, login, role, active, funcs)
    values (uid, left(nm, 80), replace(coalesce(u.email, ''), '@mic.gfbfood.com', ''),
            case when is_adm then 'admin' else 'operator' end, is_adm, (case when is_adm then '{fill,check,verify,admin}' else '{fill}' end)::text[])
    on conflict (user_id) do nothing;
    select * into r from public.mic_users where user_id = uid;
    perform public.mic_addlog('register', null, null, jsonb_build_object('login', r.login));
  end if;
  return jsonb_build_object('id', r.user_id, 'name', r.name, 'login', r.login, 'role', r.role, 'funcs', to_jsonb(r.funcs), 'active', r.active,
                            'today', public.mic_today());
end $$;

create or replace function public.mic_users_list() returns jsonb
language plpgsql stable security definer set search_path = public as $$
begin
  perform public.mic_must('admin');
  return coalesce((select jsonb_agg(jsonb_build_object('id', m.user_id, 'name', m.name, 'login', m.login, 'role', m.role, 'funcs', to_jsonb(m.funcs),
                   'active', m.active, 'created_at', m.created_at,
                   'username', (select a.email like '%@mic.gfbfood.com' from auth.users a where a.id = m.user_id))
                   order by m.active, m.name) from public.mic_users m), '[]'::jsonb);
end $$;

-- Admin: change a user's name, functions and active state.
create or replace function public.mic_save_user(p_id uuid, p_name text, p_funcs text[], p_active boolean) returns void
language plpgsql security definer set search_path = public as $$
declare f text[];
begin
  perform public.mic_must('admin');
  select coalesce(array_agg(x order by array_position('{fill,check,verify,admin}'::text[], x)), '{}') into f
    from (select distinct unnest(coalesce(p_funcs, '{}')) as x) q where x in ('fill','check','verify','admin');
  if btrim(coalesce(p_name, '')) = '' then raise exception 'Nama diperlukan / Name is required'; end if;
  if p_active and cardinality(f) = 0 then raise exception 'Pilih sekurang-kurangnya satu fungsi / Choose at least one function'; end if;
  if not ('admin' = any(f) and p_active) and not exists
     (select 1 from public.mic_users where 'admin' = any(funcs) and active and user_id <> p_id) then
    raise exception 'Mesti ada sekurang-kurangnya seorang Admin aktif / There must be at least one active Admin';
  end if;
  update public.mic_users set name = left(btrim(p_name), 80), funcs = f, active = p_active,
         role = case when 'admin' = any(f) then 'admin' when 'verify' = any(f) then 'verifier' when 'check' = any(f) then 'checker' else 'operator' end
   where user_id = p_id;
  if not found then raise exception 'User not found'; end if;
  perform public.mic_addlog('user_update', null, null, jsonb_build_object('user', p_id, 'name', p_name, 'funcs', to_jsonb(f), 'active', p_active));
end $$;

-- Admin: add a person to this app. The sign-in account must already exist (a CMMS email account,
-- or a username account the Add user form has just created). Returns 'added', 'exists' or 'no_account'.
create or replace function public.mic_add_user(p_login text, p_name text, p_funcs text[], p_active boolean) returns text
language plpgsql security definer set search_path = public as $$
declare v_email text := lower(btrim(coalesce(p_login, ''))); v_id uuid;
begin
  perform public.mic_must('admin');
  if v_email = '' then raise exception 'Nama pengguna diperlukan / Username is required'; end if;
  if position('@' in v_email) = 0 then v_email := v_email || '@mic.gfbfood.com'; end if;
  select id into v_id from auth.users where lower(email) = v_email;
  if v_id is null then return 'no_account'; end if;
  if exists (select 1 from public.mic_users where user_id = v_id) then return 'exists'; end if;
  insert into public.mic_users (user_id, name, login, active)
  values (v_id, left(coalesce(nullif(btrim(p_name), ''), split_part(v_email, '@', 1)), 80), replace(v_email, '@mic.gfbfood.com', ''), false);
  perform public.mic_save_user(v_id, coalesce(nullif(btrim(p_name), ''), split_part(v_email, '@', 1)), p_funcs, p_active);
  perform public.mic_addlog('user_add', null, null, jsonb_build_object('user', v_id, 'login', replace(v_email, '@mic.gfbfood.com', '')));
  return 'added';
end $$;

-- Older copies of the page still call this; tell them to refresh.
create or replace function public.mic_set_user(p_id uuid, p_name text, p_role text, p_active boolean) returns void
language plpgsql security definer set search_path = public as $$
begin
  perform public.mic_must('admin');
  raise exception 'Sila muat semula halaman (Ctrl+Shift+R) / Please refresh the page (Ctrl+Shift+R)';
end $$;

-- Admin sets a new password for a username account (staff without email).
-- Accounts that sign in with a real email use "Forgot password" instead.
create or replace function public.mic_reset_password(p_id uuid, p_password text) returns void
language plpgsql security definer set search_path = public, extensions as $$
begin
  perform public.mic_must('admin');
  if length(coalesce(p_password, '')) < 8 then
    raise exception 'Kata laluan mesti sekurang-kurangnya 8 aksara / Password must be at least 8 characters';
  end if;
  if not exists (select 1 from public.mic_users where user_id = p_id) then raise exception 'User not found'; end if;
  update auth.users set encrypted_password = crypt(p_password, gen_salt('bf', 10)), updated_at = now()
   where id = p_id and email like '%@mic.gfbfood.com';
  if not found then
    raise exception 'Akaun ini log masuk dengan emel; guna "Lupa kata laluan" / This account signs in with an email; use "Forgot password"';
  end if;
  perform public.mic_addlog('password_reset', null, null, jsonb_build_object('user', p_id));
end $$;

-- ---------- checklist templates ----------
create or replace function public.mic_boot() returns jsonb
language plpgsql stable security definer set search_path = public as $$
begin
  perform public.mic_must('any');
  return jsonb_build_object('today', public.mic_today(),
    'templates', coalesce((select jsonb_agg(data order by sort, key) from public.mic_templates), '[]'::jsonb));
end $$;

create or replace function public.mic_save_template(p_key text, p_data jsonb) returns void
language plpgsql security definer set search_path = public as $$
declare n int;
begin
  perform public.mic_must('admin');
  if jsonb_typeof(p_data->'sections') is distinct from 'array' or coalesce(p_data->>'key', '') <> p_key then
    raise exception 'Invalid checklist data';
  end if;
  if coalesce(p_data->>'status', '') not in ('active','pending','not_in_use') then raise exception 'Invalid machine status'; end if;
  select count(*) into n from jsonb_array_elements(p_data->'sections') s, jsonb_array_elements(s->'items') i;
  if n = 0 then raise exception 'Senarai semak mesti ada sekurang-kurangnya satu bahagian / The checklist needs at least one part'; end if;
  if (select count(distinct i->>'id') from jsonb_array_elements(p_data->'sections') s, jsonb_array_elements(s->'items') i) <> n then
    raise exception 'Duplicate part id in checklist';
  end if;
  update public.mic_templates set data = p_data, updated_at = now(), updated_name = public.mic_name() where key = p_key;
  if not found then raise exception 'Machine not found'; end if;
  perform public.mic_addlog('template_update', null, null, jsonb_build_object('machine', p_key, 'formNo', p_data->>'formNo', 'rev', p_data->>'rev', 'eff', p_data->>'eff', 'parts', n));
end $$;

-- First run only: the Admin's browser loads the 8 standard F52 checklists (templates.json in the app)
-- and stores them here. Machines that already exist are left untouched, so Admin edits are never overwritten.
create or replace function public.mic_seed_templates(p_data jsonb) returns int
language plpgsql security definer set search_path = public as $$
declare t jsonb; n int := 0; k int := 0;
begin
  perform public.mic_must('admin');
  if jsonb_typeof(p_data) is distinct from 'array' then raise exception 'Invalid checklist data'; end if;
  for t in select * from jsonb_array_elements(p_data) loop
    k := k + 10;
    if coalesce(t->>'key', '') = '' or jsonb_typeof(t->'sections') is distinct from 'array' then raise exception 'Invalid checklist data'; end if;
    insert into public.mic_templates (key, sort, data, updated_name) values (t->>'key', k, t, public.mic_name()) on conflict (key) do nothing;
    if found then n := n + 1; end if;
  end loop;
  if n > 0 then perform public.mic_addlog('template_seed', null, null, jsonb_build_object('added', n)); end if;
  return n;
end $$;

-- ---------- reading ----------
create or replace function public.mic_round_json(r public.mic_rounds, p_full boolean) returns jsonb
language sql stable set search_path = public as $$
  select jsonb_build_object('id', r.id, 'seq', r.seq, 'time', r.time_text, 'batch', r.batch, 'status', r.status, 'ng', r.ng,
    'done_by', r.done_by, 'done_name', r.done_name, 'submitted_at', r.submitted_at,
    'check_by', r.check_by, 'check_name', r.check_name, 'check_at', r.check_at, 'note', r.note, 'updated_at', r.updated_at,
    'rv_pending', (select count(*) from jsonb_each(r.items) e where (e.value->>'c' = 'ng' or e.value->>'p' = 'n') and e.value->'rv' is null),
    'rv_hold', (select count(*) from jsonb_each(r.items) e where e.value->'rv'->>'d' = 'hold'))
    || case when p_full then jsonb_build_object('items', r.items, 'refs', r.refs) else '{}'::jsonb end
$$;

-- Summary of every checklist between two dates (no part-by-part detail).
create or replace function public.mic_range(p_from date, p_to date) returns jsonb
language plpgsql stable security definer set search_path = public as $$
begin
  perform public.mic_must('any');
  return coalesce((select jsonb_agg(jsonb_build_object('id', i.id, 'machine', i.machine, 'date', i.insp_date, 'status', i.status,
      'verify_name', i.verify_name, 'verify_at', i.verify_at, 'formNo', i.template->>'formNo', 'rev', i.template->>'rev',
      'name', i.template->>'name',
      'rounds', coalesce((select jsonb_agg(public.mic_round_json(r, false) order by r.seq) from public.mic_rounds r where r.inspection_id = i.id), '[]'::jsonb))
      order by i.insp_date desc, i.machine)
    from public.mic_inspections i where i.insp_date between p_from and p_to
      and exists (select 1 from public.mic_rounds r2 where r2.inspection_id = i.id)), '[]'::jsonb);
end $$;

-- One machine, one day: the full checklist with every round.
create or replace function public.mic_sheet(p_machine text, p_date date) returns jsonb
language plpgsql stable security definer set search_path = public as $$
declare i public.mic_inspections;
begin
  perform public.mic_must('any');
  select * into i from public.mic_inspections where machine = p_machine and insp_date = p_date;
  if not found then return null; end if;
  return jsonb_build_object('id', i.id, 'machine', i.machine, 'date', i.insp_date, 'status', i.status, 'template', i.template,
    'verify_by', i.verify_by, 'verify_name', i.verify_name, 'verify_at', i.verify_at, 'verify_note', i.verify_note,
    'rounds', coalesce((select jsonb_agg(public.mic_round_json(r, true) order by r.seq) from public.mic_rounds r where r.inspection_id = i.id), '[]'::jsonb),
    'log', case when public.mic_can('review') then coalesce((select jsonb_agg(jsonb_build_object('at', l.at, 'name', l.name, 'act', l.act, 'detail', l.detail) order by l.id)
              from public.mic_log l where l.inspection_id = i.id), '[]'::jsonb) else '[]'::jsonb end);
end $$;

-- Full detail for a date range (used by the Excel/CSV download), max 92 days.
create or replace function public.mic_export(p_from date, p_to date) returns jsonb
language plpgsql stable security definer set search_path = public as $$
begin
  perform public.mic_must('review');
  if p_to - p_from > 92 then raise exception 'Pilih tempoh 3 bulan atau kurang / Choose a period of 3 months or less'; end if;
  return coalesce((select jsonb_agg(public.mic_sheet(i.machine, i.insp_date) - 'log' order by i.insp_date, i.machine)
    from public.mic_inspections i where i.insp_date between p_from and p_to), '[]'::jsonb);
end $$;

-- ---------- inspection rounds (Done by) ----------
create or replace function public.mic_start_round(p_machine text, p_date date, p_time text, p_batch text) returns uuid
language plpgsql security definer set search_path = public as $$
declare uid uuid := auth.uid(); t jsonb; i public.mic_inspections; rid uuid; n int;
begin
  perform public.mic_must('fill');
  select data into t from public.mic_templates where key = p_machine;
  if t is null then raise exception 'Machine not found'; end if;
  if t->>'status' = 'not_in_use' then
    raise exception 'Mesin ini ditanda Tidak Digunakan / This machine is marked Not in use';
  end if;
  if not public.mic_can('admin') and (p_date > public.mic_today() or p_date < public.mic_today() - 1) then
    raise exception 'Pemeriksaan hanya boleh direkod untuk hari ini atau semalam / Inspections can only be recorded for today or yesterday';
  end if;
  insert into public.mic_inspections (machine, insp_date, template, created_by)
  values (p_machine, p_date, t, uid) on conflict (machine, insp_date) do nothing;
  select * into i from public.mic_inspections where machine = p_machine and insp_date = p_date for update;
  if i.status = 'verified' then
    raise exception 'Senarai semak ini telah disahkan / This checklist has already been verified';
  end if;
  select id into rid from public.mic_rounds where inspection_id = i.id and done_by = uid and status = 'draft' order by seq limit 1;
  if rid is not null then return rid; end if;
  select coalesce(max(seq), 0) + 1 into n from public.mic_rounds where inspection_id = i.id;
  insert into public.mic_rounds (inspection_id, seq, time_text, batch, done_by, done_name)
  values (i.id, n, left(coalesce(p_time, ''), 20), '', uid, public.mic_name())
  returning id into rid;
  perform public.mic_addlog('round_start', i.id, rid, jsonb_build_object('round', n));
  return rid;
end $$;

create or replace function public.mic_save_round(p_id uuid, p_time text, p_batch text, p_refs jsonb, p_items jsonb, p_submit boolean) returns jsonb
language plpgsql security definer set search_path = public as $$
declare uid uuid := auth.uid(); r public.mic_rounds; i public.mic_inspections; it record; a jsonb; c text; p text; rm text;
        v_clean jsonb := '{}'::jsonb; missing int := 0; bad int := 0; v_refs jsonb := '{}'::jsonb; s record; v_batch text := ''; v_ym text; v_n int;
begin
  perform public.mic_must('any');
  select * into r from public.mic_rounds where id = p_id for update;
  if not found then raise exception 'Pusingan tidak dijumpai / Round not found'; end if;
  if r.batch ~ '^[0-9]{6}-[0-9]+$' then v_batch := r.batch; end if;
  if r.done_by <> uid and not public.mic_can('admin') then
    raise exception 'Hanya orang yang memulakan pusingan ini boleh mengisinya / Only the person who started this round can fill it in';
  end if;
  if r.status <> 'draft' then
    raise exception 'Pusingan ini telah dihantar / This round has already been submitted';
  end if;
  select * into i from public.mic_inspections where id = r.inspection_id;
  if i.status = 'verified' then raise exception 'Senarai semak ini telah disahkan / This checklist has already been verified'; end if;
  for it in select x->>'id' as id from jsonb_array_elements(i.template->'sections') sec, jsonb_array_elements(sec->'items') x loop
    a := coalesce(p_items->it.id, '{}'::jsonb);
    c := a->>'c'; p := a->>'p'; rm := left(btrim(coalesce(a->>'r', '')), 300);
    if c in ('ok','ng','na') and (c = 'na' or p in ('y','n')) then
      if c = 'na' then p := ''; end if;
      if (c = 'ng' or p = 'n') then bad := bad + 1; end if;
      if (c = 'ng' or p = 'n') and rm = '' and p_submit then
        raise exception 'Sila tulis catatan untuk setiap bahagian yang Tidak OK atau tiada / Please write a remark for every part that is Not OK or missing';
      end if;
      v_clean := v_clean || jsonb_build_object(it.id, jsonb_build_object('c', c, 'p', p, 'r', rm));
    else
      missing := missing + 1;
    end if;
  end loop;
  for s in select sec->>'id' as id from jsonb_array_elements(i.template->'sections') sec where (sec->>'ref')::boolean loop
    if btrim(coalesce(p_refs->>s.id, '')) <> '' then v_refs := v_refs || jsonb_build_object(s.id, left(btrim(p_refs->>s.id), 30)); end if;
  end loop;
  if p_submit then
    if missing > 0 then
      raise exception '% bahagian belum diperiksa / % part(s) not yet inspected', missing, missing;
    end if;
    if btrim(coalesce(p_time, '')) = '' then
      raise exception 'Masa diperlukan / Time is required';
    end if;
    if v_batch = '' then   -- running batch number YYYYMM-NNN, given once when the round is first submitted
      v_ym := to_char(i.insp_date, 'YYYYMM');
      insert into public.mic_counters as c (ym, n) values (v_ym, 1) on conflict (ym) do update set n = c.n + 1 returning c.n into v_n;
      v_batch := v_ym || '-' || lpad(v_n::text, 3, '0');
    end if;
  end if;
  update public.mic_rounds set time_text = left(btrim(coalesce(p_time, '')), 20), batch = v_batch,
         refs = v_refs, items = v_clean, ng = bad, updated_at = now(),
         status = case when p_submit then 'submitted' else 'draft' end,
         submitted_at = case when p_submit then now() else null end,
         note = case when p_submit then null else note end
   where id = p_id;
  update public.mic_inspections set updated_at = now() where id = i.id;
  if p_submit then perform public.mic_addlog('round_submit', i.id, p_id, jsonb_build_object('round', r.seq, 'not_ok', bad)); end if;
  return jsonb_build_object('status', case when p_submit then 'submitted' else 'draft' end, 'ng', bad, 'missing', missing, 'batch', v_batch);
end $$;

create or replace function public.mic_delete_round(p_id uuid) returns void
language plpgsql security definer set search_path = public as $$
declare r public.mic_rounds;
begin
  perform public.mic_must('any');
  select * into r from public.mic_rounds where id = p_id for update;
  if not found then return; end if;
  if r.status <> 'draft' then raise exception 'Hanya draf boleh dipadam / Only a draft can be deleted'; end if;
  if r.done_by <> auth.uid() and not public.mic_can('admin') then
    raise exception 'Hanya orang yang memulakan pusingan ini boleh memadamnya / Only the person who started this round can delete it';
  end if;
  delete from public.mic_rounds where id = p_id;
  if not exists (select 1 from public.mic_rounds where inspection_id = r.inspection_id) then
    delete from public.mic_inspections where id = r.inspection_id and status = 'open';   -- nothing left on this checklist
  end if;
  perform public.mic_addlog('round_delete', r.inspection_id, p_id, jsonb_build_object('round', r.seq));
end $$;

-- ---------- Check by ----------
-- p_ok = true: sign as Check by.  p_ok = false: return the round to the operator for correction (note required).
create or replace function public.mic_check_round(p_id uuid, p_ok boolean, p_note text) returns void
language plpgsql security definer set search_path = public as $$
declare uid uuid := auth.uid(); r public.mic_rounds; i public.mic_inspections;
begin
  perform public.mic_must('check');
  select * into r from public.mic_rounds where id = p_id for update;
  if not found then raise exception 'Pusingan tidak dijumpai / Round not found'; end if;
  select * into i from public.mic_inspections where id = r.inspection_id;
  if i.status = 'verified' then raise exception 'Senarai semak ini telah disahkan / This checklist has already been verified'; end if;
  if p_ok then
    if r.status <> 'submitted' then raise exception 'Pusingan ini belum dihantar atau sudah disemak / This round is not waiting for a check'; end if;
    if r.done_by = uid then
      raise exception 'Anda tidak boleh menyemak pemeriksaan anda sendiri / You cannot check your own inspection';
    end if;
    if exists (select 1 from jsonb_each(r.items) e where (e.value->>'c' = 'ng' or e.value->>'p' = 'n') and e.value->'rv' is null) then
      raise exception 'Buat keputusan (Boleh teruskan / Tahan) untuk setiap bahagian Tidak OK dahulu / Decide Can proceed or Hold for every Not OK part first';
    end if;
    update public.mic_rounds set status = 'checked', check_by = uid, check_name = public.mic_name(), check_at = now(),
           note = nullif(left(btrim(coalesce(p_note, '')), 300), ''), updated_at = now() where id = p_id;
    perform public.mic_addlog('round_check', i.id, p_id, jsonb_build_object('round', r.seq, 'note', p_note));
  else
    if r.status = 'draft' then raise exception 'Pusingan ini masih draf / This round is still a draft'; end if;
    if r.status = 'checked' and r.check_by <> uid and not public.mic_can('admin') then
      raise exception 'Hanya penyemak asal atau Admin boleh memulangkan pusingan yang telah disemak / Only the original checker or an Admin can return a checked round';
    end if;
    if btrim(coalesce(p_note, '')) = '' then raise exception 'Sila nyatakan sebab / Please give a reason'; end if;
    update public.mic_rounds set status = 'draft', check_by = null, check_name = null, check_at = null, submitted_at = null,
           note = left(btrim(p_note), 300), updated_at = now() where id = p_id;
    perform public.mic_addlog('round_return', i.id, p_id, jsonb_build_object('round', r.seq, 'reason', p_note));
  end if;
  update public.mic_inspections set updated_at = now() where id = i.id;
end $$;

-- ---------- decision on a Not OK / missing part ----------
-- A person with Check by or Verify by classifies the issue (minor / major) and decides whether the
-- machine can proceed or must be held. A major issue is always Hold. Nobody decides on their own inspection.
create or replace function public.mic_review_item(p_round uuid, p_item text, p_sev text, p_dec text, p_note text) returns void
language plpgsql security definer set search_path = public as $$
declare uid uuid := auth.uid(); r public.mic_rounds; i public.mic_inspections; a jsonb; v_dec text;
        v_note text := left(btrim(coalesce(p_note, '')), 300);
begin
  perform public.mic_must('any');
  if not (public.mic_can('check') or public.mic_can('verify')) then
    raise exception 'Akaun anda tidak dibenarkan untuk tindakan ini / Your account is not allowed to do this';
  end if;
  select * into r from public.mic_rounds where id = p_round for update;
  if not found then raise exception 'Pemeriksaan tidak dijumpai / Inspection not found'; end if;
  select * into i from public.mic_inspections where id = r.inspection_id;
  if i.status = 'verified' then raise exception 'Senarai semak ini telah disahkan / This checklist has already been verified'; end if;
  if r.status = 'draft' then raise exception 'Pemeriksaan ini belum dihantar / This inspection has not been submitted yet'; end if;
  if r.done_by = uid then
    raise exception 'Anda tidak boleh membuat keputusan untuk pemeriksaan anda sendiri / You cannot decide on your own inspection';
  end if;
  a := r.items->p_item;
  if a is null or not (a->>'c' = 'ng' or a->>'p' = 'n') then
    raise exception 'Bahagian ini tidak ditanda Tidak OK / This part is not marked Not OK';
  end if;
  if p_sev not in ('minor','major') or p_dec not in ('go','hold') then raise exception 'Invalid decision'; end if;
  v_dec := case when p_sev = 'major' then 'hold' else p_dec end;
  if v_dec = 'go' and v_note = '' then
    raise exception 'Sila tulis sebab mesin boleh diteruskan / Please write why the machine can proceed';
  end if;
  update public.mic_rounds set items = jsonb_set(items, array[p_item, 'rv'],
           jsonb_build_object('s', p_sev, 'd', v_dec, 'r', v_note, 'by', uid, 'name', public.mic_name(), 'at', now())), updated_at = now()
   where id = p_round;
  update public.mic_inspections set updated_at = now() where id = i.id;
  perform public.mic_addlog('item_review', i.id, p_round, jsonb_build_object('round', r.seq, 'part', p_item, 'class', p_sev, 'decision', v_dec, 'note', v_note));
end $$;

-- ---------- Verify by ----------
create or replace function public.mic_verify(p_id uuid, p_note text) returns void
language plpgsql security definer set search_path = public as $$
declare uid uuid := auth.uid(); i public.mic_inspections;
begin
  perform public.mic_must('verify');
  select * into i from public.mic_inspections where id = p_id for update;
  if not found then raise exception 'Checklist not found'; end if;
  if i.status = 'verified' then raise exception 'Senarai semak ini telah disahkan / This checklist has already been verified'; end if;
  if not exists (select 1 from public.mic_rounds where inspection_id = p_id) then
    raise exception 'Tiada pusingan pemeriksaan untuk disahkan / There is no inspection round to verify';
  end if;
  if exists (select 1 from public.mic_rounds where inspection_id = p_id and status <> 'checked') then
    raise exception 'Semua pusingan mesti disemak (Check by) dahulu / Every round must be checked (Check by) first';
  end if;
  if exists (select 1 from public.mic_rounds where inspection_id = p_id and (done_by = uid or check_by = uid)) then
    raise exception 'Anda tidak boleh mengesahkan senarai semak yang anda sendiri isi atau semak / You cannot verify a checklist that you filled in or checked yourself';
  end if;
  update public.mic_inspections set status = 'verified', verify_by = uid, verify_name = public.mic_name(), verify_at = now(),
         verify_note = nullif(left(btrim(coalesce(p_note, '')), 300), ''), updated_at = now() where id = p_id;
  perform public.mic_addlog('verify', p_id, null, jsonb_build_object('note', p_note));
end $$;

create or replace function public.mic_reopen(p_id uuid, p_reason text) returns void
language plpgsql security definer set search_path = public as $$
begin
  perform public.mic_must('admin');
  if btrim(coalesce(p_reason, '')) = '' then raise exception 'Sila nyatakan sebab / Please give a reason'; end if;
  update public.mic_inspections set status = 'open', verify_by = null, verify_name = null, verify_at = null, verify_note = null, updated_at = now()
   where id = p_id and status = 'verified';
  if not found then raise exception 'Senarai semak ini belum disahkan / This checklist is not verified'; end if;
  perform public.mic_addlog('reopen', p_id, null, jsonb_build_object('reason', p_reason));
end $$;

-- ---------- Admin: delete a checklist record ----------
-- A reason is required and the deletion is written to the log (who, when, why, what was in it).
-- A verified checklist must be reopened first. Batch numbers of deleted inspections are not reused.
create or replace function public.mic_delete_inspection(p_id uuid, p_reason text) returns void
language plpgsql security definer set search_path = public as $$
declare i public.mic_inspections; v jsonb;
begin
  perform public.mic_must('admin');
  if btrim(coalesce(p_reason, '')) = '' then raise exception 'Sila nyatakan sebab / Please give a reason'; end if;
  select * into i from public.mic_inspections where id = p_id for update;
  if not found then raise exception 'Rekod tidak dijumpai / Record not found'; end if;
  if i.status = 'verified' then
    raise exception 'Senarai semak yang telah disahkan mesti dibuka semula dahulu / A verified checklist must be reopened first';
  end if;
  select coalesce(jsonb_agg(jsonb_build_object('no', seq, 'status', status, 'batch', batch, 'done_by', done_name, 'check_by', check_name, 'not_ok', ng) order by seq), '[]'::jsonb)
    into v from public.mic_rounds where inspection_id = p_id;
  delete from public.mic_inspections where id = p_id;
  perform public.mic_addlog('inspection_delete', p_id, null, jsonb_build_object('machine', i.machine, 'name', i.template->>'name',
          'date', i.insp_date, 'reason', left(btrim(p_reason), 300), 'inspections', v));
end $$;

create or replace function public.mic_deleted_log() returns jsonb
language plpgsql stable security definer set search_path = public as $$
begin
  perform public.mic_must('admin');
  return coalesce((select jsonb_agg(jsonb_build_object('at', l.at, 'by', l.name, 'detail', l.detail) order by l.id desc)
    from (select * from public.mic_log where act = 'inspection_delete' order by id desc limit 200) l), '[]'::jsonb);
end $$;

-- ---------- who may call what ----------
do $$
declare f record;
begin
  for f in select p.oid::regprocedure as sig, p.proname from pg_proc p join pg_namespace n on n.oid = p.pronamespace
            where n.nspname = 'public' and p.proname like 'mic\_%' loop
    execute format('revoke execute on function %s from public, anon', f.sig);
    if f.proname in ('mic_addlog', 'mic_need', 'mic_must', 'mic_rank', 'mic_round_json') then
      execute format('revoke execute on function %s from authenticated', f.sig);
    else
      execute format('grant execute on function %s to authenticated', f.sig);
    end if;
  end loop;
end $$;

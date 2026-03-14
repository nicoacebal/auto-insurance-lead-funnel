-- Esquema base inicial. Ajustar segun requisitos finales de negocio.

create extension if not exists pgcrypto;

create table if not exists leads (
  id uuid primary key default gen_random_uuid(),
  nombre text not null,
  email text not null,
  telefono text not null,
  marca text,
  modelo text,
  anio integer,
  version text,
  precio_cotizado numeric(12, 2),
  utm_source text,
  utm_medium text,
  utm_campaign text,
  referrer text,
  landing_page text,
  ip_address text,
  user_agent text,
  creado_en timestamptz not null default now()
);

-- Preparacion para bases existentes: agrega columnas nuevas solo si faltan.
alter table if exists leads add column if not exists marca text;
alter table if exists leads add column if not exists modelo text;
alter table if exists leads add column if not exists anio integer;
alter table if exists leads add column if not exists version text;
alter table if exists leads add column if not exists precio_cotizado numeric(12, 2);
alter table if exists leads add column if not exists utm_source text;
alter table if exists leads add column if not exists utm_medium text;
alter table if exists leads add column if not exists utm_campaign text;
alter table if exists leads add column if not exists referrer text;
alter table if exists leads add column if not exists landing_page text;
alter table if exists leads add column if not exists ip_address text;
alter table if exists leads add column if not exists user_agent text;

create table if not exists eventos_funnel (
  id bigint generated always as identity primary key,
  lead_id uuid,
  evento text not null,
  detalle jsonb,
  creado_en timestamptz not null default now()
);

create table if not exists vehiculos (
  id_vehiculo integer primary key,
  marca text not null,
  modelo text not null,
  version text,
  anio integer,
  tipo text,
  creado_en timestamptz not null default now()
);

alter table if exists vehiculos add column if not exists marca text;
alter table if exists vehiculos add column if not exists modelo text;
alter table if exists vehiculos add column if not exists version text;
alter table if exists vehiculos add column if not exists anio integer;
alter table if exists vehiculos add column if not exists tipo text;
alter table if exists vehiculos add column if not exists creado_en timestamptz not null default now();

create index if not exists idx_vehiculos_marca on vehiculos (marca);
create index if not exists idx_vehiculos_modelo on vehiculos (modelo);

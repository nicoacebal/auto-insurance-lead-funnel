-- Esquema base inicial. Ajustar segun requisitos finales de negocio.

create table if not exists leads (
  id uuid primary key,
  nombre text not null,
  email text not null,
  telefono text not null,
  creado_en timestamptz not null default now()
);

create table if not exists eventos_funnel (
  id bigint generated always as identity primary key,
  lead_id uuid,
  evento text not null,
  detalle jsonb,
  creado_en timestamptz not null default now()
);

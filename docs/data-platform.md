# Data Platform Foundation v1

## Purpose

This is the `foundation v1` stack for the project.

It adds a small analytics and automation base around the current application without trying to be the final production platform yet.

The goal of this version is to:

- keep local setup simple
- match the current repo state
- leave room for a later hardening pass

The stack includes:

- `backend`: FastAPI API that already exists in the repo and emits lead events.
- `n8n`: workflow runner for operational automations and ingestion jobs.
- `dw_postgres`: analytics warehouse database for reporting and transformations.
- `dbt`: future transformation layer for curated warehouse models.
- `superset`: BI layer for dashboards on top of `dw_postgres`.

## OLTP vs Analytics

`Supabase` remains the operational database for the product and is not part of `docker-compose`:

- lead capture
- quotation flow data
- current application tables

`dw_postgres` is separate and should only be used for analytics:

- replicated or transformed data from Supabase
- reporting-friendly tables
- dbt models
- Superset datasets and dashboards

The compose stack does not replace Supabase. It complements it with a separate analytics path.

## Planned Data Flow

The intended flow is:

`Supabase -> n8n -> dw_postgres -> dbt -> Superset`

In practice:

1. The backend stores operational data in Supabase.
2. The backend can already emit events to `N8N_WEBHOOK_URL`.
3. n8n will receive those events, or run scheduled syncs, and load analytics tables into `dw_postgres`.
4. dbt will transform raw warehouse tables into curated marts.
5. Superset will connect to `dw_postgres` for dashboards and exploration.

## Startup

1. Copy `.env.example` to `.env`.
2. Fill in the real Supabase, n8n, warehouse, and Superset values.
3. Start the stack:

```bash
docker compose up -d
```

4. Check the main endpoints:

- backend: `http://localhost:8000/salud`
- n8n: `http://localhost:5678`
- Superset: `http://localhost:8088`
- warehouse PostgreSQL: `localhost:5433`

## Why Superset Uses A Pinned Tag

In `foundation v1`, Superset is pinned to an explicit image tag instead of `latest` so the stack is more reproducible.

This stack uses the official `apache/superset:4.1.4-dev` image to keep first-time PostgreSQL connectivity practical without adding custom image work yet.

## Superset First-Time Bootstrap

The Superset container starts the web app and initializes metadata, but the admin account bootstrap is still a manual first-time step.

That manual step is expected in `foundation v1`.

Run:

```bash
docker compose run --rm superset /bin/sh -c 'superset fab create-admin \
  --username "$SUPERSET_ADMIN_USERNAME" \
  --firstname "$SUPERSET_ADMIN_FIRSTNAME" \
  --lastname "$SUPERSET_ADMIN_LASTNAME" \
  --email "$SUPERSET_ADMIN_EMAIL" \
  --password "$SUPERSET_ADMIN_PASSWORD"'
```

Then refresh or restart the service if needed:

```bash
docker compose restart superset
```

After logging in, add `dw_postgres` as a database in Superset with a connection similar to:

```text
postgresql+psycopg2://DW_POSTGRES_USER:DW_POSTGRES_PASSWORD@dw_postgres:5432/insurance_dw
```

Replace the placeholders with the values from `.env`.

## Current Status In This Repo

Already implemented:

- FastAPI backend under `backend/`
- Supabase integration for operational persistence
- backend webhook sender through `N8N_WEBHOOK_URL`
- compose foundation for local infrastructure

Pending:

- actual n8n workflows to extract/load analytics data
- warehouse schema and ingestion jobs inside `dw_postgres`
- dbt project, models, and profiles
- Superset datasource registration, charts, and dashboards
- backend Dockerfile for a more deployment-oriented image build

## Practical Notes

- The backend service currently runs from the repo source mounted into the container because the project does not yet include a dedicated Dockerfile.
- The backend still needs a dedicated Dockerfile later. For now, running it from mounted source is intentional.
- The Superset admin bootstrap remains a manual first-time action.
- The `dbt` service is only a placeholder for now, so the stack can reserve its place without inventing a dbt project too early.
- For a single Oracle VM deployment later, the same compose layout can be reused and tightened with a reverse proxy, a real backend image, and backups for persistent volumes.

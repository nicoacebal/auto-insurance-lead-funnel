# Architecture

## 1. System Purpose

`auto-insurance-lead-funnel` is an automated auto insurance quotation and lead capture system integrated with the Mercantil Andina API. Its main goal is to let a user select a vehicle, request a quotation, persist the result, and store the lead for commercial follow-up.

## 2. High-Level Architecture

The current high-level flow is:

User
-> Landing page
-> FastAPI backend
-> Supabase database
-> Mercantil API
-> n8n automation (future)

At a high level, the landing page collects vehicle and contact data, the FastAPI backend orchestrates the quotation flow, Supabase stores operational data, and the Mercantil API provides insurance quotation data. A future `n8n` layer can consume backend webhooks to trigger automated actions.

## 3. Backend Stack

The backend stack is:

- Python
- FastAPI

FastAPI exposes the HTTP API, coordinates the business flow, and connects the system with Supabase and Mercantil.

## 4. Database

The database layer uses Supabase on top of PostgreSQL.

Main tables:

- `vehicle_catalog`: normalized vehicle catalog used by the selector and quotation flow.
- `mercantil_vehicle_raw`: raw vehicle data imported from Mercantil sources for traceability and catalog processing.
- `cotizaciones_cache`: cached quotation results used to avoid repeating the same Mercantil request.
- `leads`: contact and quotation-related lead data captured from the funnel.

## 5. Backend Structure

The repository is organized around a production backend, integrations, infrastructure helpers, and operational scripts.

### `backend/api`

This folder contains the FastAPI route modules:

- `vehicles.py`: vehicle selection and catalog endpoints.
- `cotizaciones.py`: quotation-related endpoints in the current backend flow.
- `quotes.py`: quote endpoints exposed by the API.
- `leads.py`: lead creation endpoints.
- `main.py`: FastAPI application entrypoint and router registration.

### `backend/services`

This layer contains the business logic. It coordinates vehicle lookup, quotation orchestration, cache usage, and integration calls outside the API layer.

### `backend/integrations`

This folder contains the Mercantil API client and related authentication/integration code. It isolates external API communication from the rest of the backend.

### `infra`

- `supabase_client.py`: shared Supabase client configuration used by backend services and API modules.

### `scripts`

This folder contains crawling, catalog synchronization, discovery, debugging, and testing scripts used to support development and data ingestion.

## 6. Current System Flow

The current operational flow is:

vehicle selection
-> quotation request
-> Mercantil API call
-> cache quotation
-> create lead

In practice, the backend first resolves the selected vehicle, then requests a quotation from Mercantil, stores reusable results in `cotizaciones_cache`, and finally persists lead data in Supabase.

## 7. Future Automation

The planned automation path is:

FastAPI
-> webhook
-> n8n
-> automated notifications

This future flow would allow the backend to emit events after quotation or lead creation so that `n8n` can trigger automated notifications or downstream commercial processes.

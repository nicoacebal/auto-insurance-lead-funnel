# Auto Insurance Lead Funnel

Plataforma en construccion para captacion y cotizacion digital de seguros automotor, orientada a brokers que necesitan combinar conversion comercial, integracion con aseguradora y automatizacion operativa.

## Overview

El repositorio combina dos realidades:

- una implementacion operativa actual en `aplicacion/`, basada en FastAPI + Jinja2 + HTMX + Supabase,
- una estructura nueva de arquitectura objetivo para evolucionar a un sistema productivo por capas.

El foco del proyecto es:

- captar leads desde una landing optimizada,
- trabajar con catalogo vehicular asegurable real,
- integrar Mercantil Andina / Sigma,
- almacenar cotizaciones y leads en Supabase,
- disparar acciones operativas por WhatsApp,
- preparar validaciones asistidas por IA.

## Architecture Summary

Arquitectura objetivo:

- `frontend landing`
- `backend api`
- `quotation engine`
- `mercantil integrations`
- `database`
- `ai validation agent`
- `whatsapp messaging`

Estado actual:

- el prototipo funcional vive en `aplicacion/`,
- la estructura nueva vive en `backend/`, `agents/`, `messaging/`, `infra/` y `docs/`.

## Current Status

Ya existe soporte para:

- landing multi-paso con HTMX,
- persistencia de leads en Supabase,
- catalogo de vehiculos en Supabase,
- endpoints internos de catalogo (`marcas`, `modelos`, `anios`, `versiones`),
- scripts de scraping/catalogo Mercantil,
- scripts de discovery de endpoints,
- smoke tests de acceso a la API de catalogo.

## Repository Structure

```text
auto-insurance-lead-funnel/
├── README.md
├── docs/
├── data/
├── scripts/
│   ├── catalogo/
│   ├── discovery/
│   ├── tests/
│   └── legacy/
├── backend/
│   ├── api/
│   ├── services/
│   ├── models/
│   └── integrations/
├── agents/
├── messaging/
├── infra/
├── aplicacion/
└── requirements.txt
```

Notas:

- `aplicacion/` se conserva como implementacion funcional heredada.
- `docs/legacy/` preserva documentacion anterior para referencia.
- `data/` contiene outputs operativos como catalogos descargados.

## Getting Started

1. Crear entorno virtual.
2. Instalar dependencias.
3. Configurar variables de entorno.
4. Ejecutar el backend actual o los scripts necesarios.

```bash
python -m venv .venv
. .venv/Scripts/activate
pip install -r requirements.txt
```

### Variables de entorno minimas

```env
SUPABASE_URL=
SUPABASE_KEY=
MA_TOKEN=
MA_API_KEY=
```

### Ejecutar la app actual

```bash
uvicorn aplicacion.backend.main:app --reload
```

### Ejecutar scripts principales

```bash
python scripts/catalogo/importar_vehiculos_mercantil.py
python scripts/discovery/probar_endpoints_mercantil.py
python scripts/discovery/descubrir_endpoints_mercantil.py
python scripts/tests/test_catalogo.py
```

## Documentation

La documentacion principal vive en [docs](./docs):

- `00-resumen-ejecutivo.md`
- `01-estado-actual.md`
- `02-plan-maestro.md`
- `03-arquitectura.md`
- `04-modelo-de-datos.md`
- `05-integracion-mercantil.md`
- `06-roadmap.md`

## Migration Note

La siguiente etapa recomendada es migrar la logica hoy ubicada en `aplicacion/backend/` hacia los modulos nuevos de `backend/` sin interrumpir el flujo comercial ya operativo.

# Landing de Cotizacion de Seguros de Autos

Proyecto inicial para construir una landing page profesional de cotizacion de seguros de autos con enfoque en conversion, calidad tecnica y documentacion para portfolio.

## Objetivo

Implementar una base solida para evolucionar hacia un flujo de formulario paso a paso y cotizacion real, manteniendo separacion clara entre documentacion, backend, frontend y base de datos.

## Stack Tecnologico

- Python 3.12+
- FastAPI
- Jinja2
- HTMX
- Supabase (planificado para integracion posterior)

## Estructura del Repositorio

```text
auto-insurance-lead-funnel/
├─ docs/
│  ├─ producto-definicion.md
│  ├─ arquitectura-tecnica.md
│  └─ roadmap.md
├─ aplicacion/
│  ├─ backend/
│  │  └─ main.py
│  ├─ frontend/
│  │  ├─ plantillas/
│  │  │  └─ landing.html
│  │  ├─ componentes/
│  │  │  └─ .gitkeep
│  │  └─ estaticos/
│  │     ├─ css/
│  │     │  └─ estilos.css
│  │     └─ js/
│  │        └─ app.js
│  └─ base_datos/
│     └─ esquema.sql
├─ .env.example
└─ requirements.txt
```

## Puesta en Marcha

1. Crear entorno virtual.
2. Instalar dependencias.
3. Iniciar servidor de desarrollo.

```bash
python -m venv .venv
. .venv/Scripts/activate
pip install -r requirements.txt
uvicorn aplicacion.backend.main:app --reload
```

Abrir `http://127.0.0.1:8000` para ver la landing.

## Estado Actual

- Base del proyecto creada.
- Render inicial de plantilla con FastAPI + Jinja2.
- Estructura preparada para integrar HTMX y Supabase.
- Sin integracion real de cotizacion externa en esta etapa.

## Proximos Pasos

- Construir formulario paso a paso con validaciones.
- Persistir leads y eventos en Supabase.
- Integrar proveedor real de cotizacion y reglas de negocio.

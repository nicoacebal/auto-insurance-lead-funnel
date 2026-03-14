# Landing de Cotizacion de Seguros de Autos

Proyecto inicial para construir una landing page profesional de cotizacion de seguros de autos con enfoque en conversion, calidad tecnica y documentacion para portfolio.

## Objetivo

Implementar una base solida para evolucionar hacia un flujo de formulario paso a paso y cotizacion real, manteniendo separacion clara entre documentacion, backend, frontend y base de datos.

## Stack Tecnologico

- Python 3.12+
- FastAPI
- Jinja2
- HTMX
- Supabase

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

## Variables de Entorno

El proyecto utiliza un archivo `.env` en la raiz del repositorio. Ese archivo no debe versionarse.

Variables principales:

- `SUPABASE_URL`
- `SUPABASE_KEY`
- `MA_PORTAL_BASE_URL`
- `MA_TOKEN`
- `MA_API_KEY`
- `MA_CATALOGO_FABRICADO`
- `MA_CATALOGO_PAGE_SIZE`
- `MA_CATALOGO_TIPOS`
- `MA_CATALOGO_CON_VALOR`

Ejemplo orientativo:

```env
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_KEY=tu_clave

MA_PORTAL_BASE_URL=https://productos.mercantilandina.com.ar
MA_TOKEN=
MA_API_KEY=

MA_CATALOGO_FABRICADO=2026
MA_CATALOGO_PAGE_SIZE=5000
MA_CATALOGO_TIPOS=1;2;3;8;9;21;4;5;6;17
MA_CATALOGO_CON_VALOR=false
```

Notas de seguridad:

- `.env` esta ignorado en `.gitignore`.
- El archivo de catalogo descargado tambien se ignora para evitar publicar datos operativos innecesarios.
- El script de importacion no imprime secretos y utiliza `Authorization: Bearer <JWT>` junto con `ocp-apim-subscription-key`.

## Estado Actual

- Base del proyecto creada.
- Landing multi-paso con FastAPI + Jinja2 + HTMX.
- Persistencia de leads en Supabase con deduplicacion por `email + telefono`.
- API interna de catalogo asegurable (`marcas`, `modelos`, `anios`, `versiones`).
- Formulario de vehiculo conectado a selects dinamicos HTMX.
- Script de importacion para descargar y cargar el catalogo de Mercantil Andina en Supabase usando headers autenticados.

## Proximos Pasos

- Construir formulario paso a paso con validaciones.
- Ejecutar la importacion real del catalogo con `MA_TOKEN` y `MA_API_KEY` vigentes.
- Reemplazar la cotizacion simulada por una API real de aseguradora.
- Incorporar observabilidad y analitica operativa.

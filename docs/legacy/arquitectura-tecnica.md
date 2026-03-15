# Arquitectura Tecnica

## Objetivo Tecnico

Definir una base mantenible para una landing de captacion de leads con render server-side y comportamiento incremental en frontend.

## Componentes

### Backend

- Framework: FastAPI.
- Responsabilidades:
  - Exponer ruta principal de la landing.
  - Renderizar plantillas Jinja2.
  - Preparar endpoints para interacciones HTMX.

### Frontend

- Plantillas HTML en Jinja2.
- Estilos en CSS modular.
- JavaScript ligero para interacciones puntuales.
- HTMX para mejoras progresivas sin SPA completa.

### Base de Datos

- Supabase como backend de datos (futuro).
- Script SQL base para tablas de leads y eventos.

## Estructura de Carpetas

- `aplicacion/backend`: API y orquestacion del flujo.
- `aplicacion/frontend/plantillas`: vistas Jinja2.
- `aplicacion/frontend/componentes`: fragmentos reutilizables.
- `aplicacion/frontend/estaticos`: CSS y JS.
- `aplicacion/base_datos`: scripts SQL versionables.

## Decisiones Iniciales

- Render server-side para simplicidad y SEO.
- HTMX para interacciones graduales sin sobreingenieria.
- Separacion explicita por capas para facilitar crecimiento del proyecto.

## Consideraciones No Funcionales

- Mantenibilidad: nombres claros y documentacion activa.
- Observabilidad: preparar eventos de conversion.
- Seguridad: manejo de secretos en variables de entorno.

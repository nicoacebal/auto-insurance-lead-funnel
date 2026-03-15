# Arquitectura

## Vista general

La arquitectura objetivo del sistema es la siguiente:

Frontend landing
→ Backend API
→ Motor interno de cotizacion
→ APIs de Mercantil Andina
→ Base de datos
→ Agente de IA
→ Mensajeria WhatsApp

## Capas

### Frontend landing

Responsabilidad:

- captacion de trafico,
- render de experiencia comercial,
- navegacion incremental del embudo de cotizacion.

Tecnologia actual:

- Jinja2
- HTMX
- CSS/JS liviano

### Backend API

Responsabilidad:

- exponer endpoints internos,
- validar formularios,
- orquestar cotizacion, catalogo y persistencia,
- servir como frontera estable entre frontend e integraciones.

### Motor interno de cotizacion

Responsabilidad:

- centralizar reglas internas,
- ejecutar pre-cotizaciones,
- desacoplar el dominio de negocio de la API externa.

### Integraciones Mercantil

Responsabilidad:

- consultar catalogo vehicular,
- resolver usos, localidades, coberturas y productos tecnicos,
- encapsular dependencias con la aseguradora.

### Base de datos

Responsabilidad:

- almacenar leads,
- catalogo vehicular,
- futuras tablas maestras,
- cotizaciones y trazabilidad operativa.

Tecnologia actual:

- Supabase

### Agente de IA

Responsabilidad:

- prevalidar datos,
- detectar anomalías,
- clasificar calidad del lead,
- asistir decision operativa.

### Mensajeria WhatsApp

Responsabilidad:

- notificaciones internas,
- derivacion comercial,
- contacto asistido posterior a la cotizacion.

## Estrategia de migracion

La carpeta `aplicacion/` se mantiene como implementacion operativa actual. La nueva carpeta `backend/` y sus modulos asociados representan la arquitectura objetivo de produccion. La migracion recomendada es incremental, sin apagar el prototipo vigente hasta completar equivalencia funcional por modulo.

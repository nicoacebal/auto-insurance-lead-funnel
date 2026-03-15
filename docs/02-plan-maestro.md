# Plan Maestro

## Fases del sistema

### 1. Reverse engineering de APIs

Objetivo:

- identificar endpoints criticos,
- entender parametros obligatorios,
- validar headers, autenticacion y contratos de respuesta.

Entregables:

- scripts de discovery,
- endpoints confirmados,
- documentacion tecnica de integracion.

### 2. Ingesta del catalogo vehicular

Objetivo:

- descargar el catalogo asegurable completo,
- normalizar registros,
- deduplicar por identificador de vehiculo,
- almacenar el catalogo en Supabase.

Entregables:

- crawler operativo,
- pipeline de carga a base,
- tablas de catalogo consultables.

### 3. Motor interno de cotizacion

Objetivo:

- abstraer reglas internas de pre-cotizacion,
- desacoplar el frontend de la aseguradora,
- preparar el reemplazo de valores fijos por integracion real.

Entregables:

- servicio de cotizacion interno,
- contratos de entrada/salida,
- base para reglas de negocio y scoring.

### 4. Funnel de captura de leads

Objetivo:

- optimizar conversion de la landing,
- capturar trazabilidad de marketing,
- garantizar persistencia segura de leads.

Entregables:

- formulario multi-paso,
- tracking de origen,
- persistencia en Supabase,
- integracion con catalogo asegurable.

### 5. Notificaciones operativas por WhatsApp

Objetivo:

- enviar alertas a broker u operador,
- acelerar el seguimiento comercial,
- unificar salida operativa de cotizaciones y leads.

Entregables:

- dispatcher de WhatsApp,
- plantillas de mensajes,
- eventos de negocio conectados a mensajeria.

### 6. Agente de validacion con IA

Objetivo:

- prevalidar datos recibidos,
- detectar inconsistencias,
- asistir priorizacion comercial y control de calidad.

Entregables:

- agente de prevalidacion,
- reglas de consistencia,
- score o banderas operativas para cada lead/cotizacion.

# Integracion Mercantil

## Objetivo

Documentar los endpoints tecnicos relevantes para construir el flujo de cotizacion y el catalogo asegurable.

## Endpoints relevantes

### 1. `vehiculos/marca-modelo`

Estado:

- confirmado y utilizado en scripts actuales.

Uso:

- obtener catalogo de vehiculos asegurables.

Parametros observados:

- `descripcion`: termino de busqueda utilizado para segmentar consultas.
- `fabricado`: anio del vehiculo o universo de fabricacion.
- `page`: pagina de resultados.
- `size`: tamano de pagina.
- `tipo`: codigos de tipo de vehiculo permitidos.
- `conValor`: flag de comportamiento del endpoint.

Aplicacion en proceso de cotizacion:

- alimentar catalogo asegurable,
- poblar selects de marca/modelo/anio/version,
- restringir el funnel a vehiculos validos para la aseguradora.

### 2. `productos-tecnicos-suscripciones`

Estado:

- endpoint identificado como relevante para productos/coberturas tecnicas.
- pendiente validacion operacional final en el pipeline principal.

Uso esperado:

- resolver productos o suscripciones tecnicas disponibles segun parametros de cotizacion.

Aplicacion en proceso de cotizacion:

- mapear coberturas disponibles,
- seleccionar variantes de producto,
- construir inputs del motor interno de cotizacion.

### 3. `api_ramo/usos-vehiculos`

Estado:

- endpoint identificado para catalogo de usos del ramo.
- pendiente consolidacion en tablas maestras internas.

Uso esperado:

- obtener usos vehiculares validos para cotizacion.

Aplicacion en proceso de cotizacion:

- enriquecer motor de tarificacion,
- validar formularios,
- parametrizar requests a la aseguradora.

## Requisitos tecnicos observados

La integracion actual requiere:

- `MA_TOKEN`
- `MA_API_KEY`
- headers compatibles con browser/origin
- manejo explicito de respuestas `400`, `401` y `403`

## Estrategia recomendada

- encapsular toda llamada externa en `backend/integrations/mercantil_client.py`,
- guardar catalogos y tablas maestras en Supabase,
- no depender del frontend para llamadas directas a la aseguradora.

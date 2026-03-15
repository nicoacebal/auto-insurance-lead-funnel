# Modelo de Datos

## Entidades nucleares

### vehicles_model

Representa la definicion de modelo/version de vehiculo asegurable.

Campos sugeridos:

- id_modelo
- id_vehiculo_externo
- marca
- modelo
- version
- tipo
- activo

### vehicles_year

Relaciona un modelo con uno o mas anios asegurables.

Campos sugeridos:

- id
- id_modelo
- anio
- vigente

### usos

Tabla maestra de usos del ramo automotor.

Campos sugeridos:

- id_uso
- codigo
- descripcion
- ramo
- activo

### localidades

Tabla maestra de localidades utilizada para tarificacion y riesgo.

Campos sugeridos:

- id_localidad
- codigo_postal
- nombre
- provincia
- pais

### cotizaciones

Representa cada intento de cotizacion o pre-cotizacion.

Campos sugeridos:

- id_cotizacion
- id_lead
- id_modelo
- anio
- uso
- localidad
- precio_estimado
- precio_final
- proveedor
- estado
- payload_request
- payload_response
- creado_en

### leads

Representa la captura comercial del usuario final.

Campos ya presentes o previstos:

- id
- nombre
- telefono
- email
- marca
- modelo
- anio
- version
- precio_cotizado
- utm_source
- utm_medium
- utm_campaign
- referrer
- landing_page
- ip_address
- user_agent
- creado_en

## Consideraciones de modelado

- separar catalogo maestro de eventos transaccionales,
- evitar duplicacion entre `leads` y `cotizaciones` salvo snapshots de negocio,
- conservar payloads externos relevantes para auditoria e integracion.

# Estado Actual

## Componentes ya operativos

### Landing y flujo de leads

Existe una implementacion funcional en `aplicacion/` basada en:

- FastAPI
- Jinja2
- HTMX
- Supabase

El flujo actual soporta:

- seleccion de vehiculo,
- pre-cotizacion estimada,
- captura de contacto,
- persistencia del lead,
- resultado final con CTA a WhatsApp.

### Catalogo de vehiculos

Ya existe soporte para:

- scraping e ingesta de catalogo vehicular desde Mercantil Andina,
- deduplicacion por `id` de vehiculo,
- almacenamiento local del catalogo,
- carga posterior a Supabase,
- consulta del catalogo desde endpoints internos.

### Autenticacion contra Mercantil

Los scripts ya usan autenticacion por:

- `MA_TOKEN`
- `MA_API_KEY`

Los requests incorporan headers compatibles con el gateway protegido por Cloudflare y Azure API Management.

### Discovery de endpoints

El repositorio ya cuenta con tooling para:

- probar endpoints candidatos,
- descubrir rutas bajo prefijos comunes,
- guardar respuestas JSON validas,
- documentar endpoints tecnicos relevantes.

A la fecha se encuentra confirmado el uso de `vehiculos/marca-modelo` y se identificaron endpoints complementarios relacionados con coberturas tecnicas y usos del ramo.

### Supabase

La integracion actual ya cubre:

- persistencia de leads,
- deduplicacion por `email + telefono`,
- tabla `vehiculos` para catalogo asegurable,
- endpoints backend que consultan catalogo desde Supabase.

## Scripts existentes

El repositorio conserva scripts funcionales para:

- descarga de catalogo,
- carga de catalogo a Supabase,
- prueba de endpoints,
- descubrimiento de endpoints,
- smoke tests de acceso al catalogo.

## Estado de madurez

El proyecto ya supero la etapa de maqueta simple y cuenta con una base valida para reorganizarse hacia una arquitectura de produccion, manteniendo el prototipo operativo mientras se migra por capas.

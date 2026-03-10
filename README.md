# README — Landing de Captación para Cotización de Seguros de Auto

## 1. Propósito del proyecto

Este repositorio documenta la planificación, alcance, arquitectura, entregables, decisiones técnicas y roadmap de implementación de una **landing page orientada a conversión** para campañas de **Instagram Ads**, con foco en captación de leads para cotización de seguros de auto.

El objetivo no es solamente construir una página visualmente atractiva, sino diseñar un **funnel digital completo**, medible y escalable, que permita:

- recibir tráfico pago desde historias y anuncios de Instagram,
- guiar al usuario por un flujo breve y claro,
- capturar datos del vehículo y del prospecto,
- registrar correctamente el lead,
- preparar la integración posterior con automatizaciones comerciales.

Este documento está pensado como base profesional para:

- ordenar el proyecto desde cero,
- trabajar en equipo,
- justificar decisiones de producto y tecnología,
- servir como material de portfolio y experiencia profesional.

---

## 2. Contexto de negocio

La iniciativa responde a una necesidad concreta: construir una experiencia de cotización rápida para usuarios que llegan desde publicidad en Instagram.

El flujo deseado es:

1. El usuario visualiza una historia o anuncio.
2. Hace click en el CTA.
3. Ingresa a una landing mobile-first.
4. Completa en una primera etapa los datos de su vehículo:
   - marca,
   - modelo,
   - año,
   - versión.
5. En una segunda etapa completa sus datos de contacto:
   - nombre,
   - teléfono,
   - email.
6. El sistema registra el lead y deja preparado el proceso posterior de contacto, cotización o automatización.

La referencia funcional provista para entender el tipo de experiencia buscada es el cotizador de Segurate. ([cotizarauto.segurate.ar](https://cotizarauto.segurate.ar/))

---

## 3. Objetivo general

Diseñar e implementar un MVP profesional de landing page con foco en conversión, que pueda ser utilizado en campañas reales de performance marketing y que, al mismo tiempo, esté correctamente documentado y estructurado para futuras iteraciones.

### Objetivos específicos

- Diseñar una interfaz confiable, cálida y profesional.
- Minimizar fricción en la carga del formulario.
- Priorizar experiencia mobile.
- Capturar datos completos y útiles para gestión comercial.
- Medir el funnel con eventos y parámetros UTM.
- Dejar la arquitectura preparada para integraciones futuras.

---

## 4. Alcance del MVP

### Incluye

- Landing page mobile-first.
- Flujo de formulario en 2 pasos.
- Selectores dependientes para vehículo.
- Validación básica de campos.
- Persistencia del lead.
- Página o estado final de confirmación.
- Trazabilidad de campaña con UTM.
- Tracking de eventos clave.
- Documentación funcional y técnica.

### No incluye en la primera etapa

- Motor de cotización en tiempo real con aseguradoras.
- Login de usuarios.
- CRM completo.
- Automatizaciones complejas multi-canal.
- Panel administrativo.
- Integración productiva con WhatsApp API o email transaccional.

Estas piezas podrán incorporarse en una fase posterior.

---

## 5. Perfil del usuario objetivo

El usuario esperado llega desde un entorno de consumo rápido, generalmente en dispositivo móvil, con atención limitada y poca tolerancia a formularios extensos.

Por eso la experiencia debe priorizar:

- claridad inmediata,
- pocos pasos,
- lenguaje simple,
- sensación de rapidez,
- confianza,
- diseño limpio,
- CTA visibles.

---

## 6. Propuesta funcional del funnel

## Entrada del funnel

**Origen principal:** Instagram Stories / Instagram Ads.

### Supuestos de comportamiento

- El usuario llega desde un entorno visual y veloz.
- Probablemente navega desde el celular.
- Tiene una intención inicial, pero todavía débil.
- La landing debe convencer rápido y evitar deserción.

## Estructura funcional propuesta

### Paso 0 — Hero de conversión

La pantalla inicial debe resolver tres preguntas en segundos:

- qué se ofrece,
- cuánto tarda,
- qué debe hacer el usuario.

#### Mensaje sugerido

**Cotizá tu seguro en menos de 1 minuto**

#### Apoyos visuales sugeridos

- diseño limpio,
- sellos de confianza,
- breve texto de respaldo,
- CTA visible sin necesidad de scroll.

### Paso 1 — Datos del vehículo

Campos:

- Marca
- Modelo
- Año
- Versión

Decisión clave: estos selectores deben ser dependientes para evitar errores de ingreso y mejorar la calidad del dato.

### Paso 2 — Datos del prospecto

Campos:

- Nombre y apellido
- Teléfono
- Email

Decisión clave: pedir contacto recién después de que el usuario ya invirtió esfuerzo en cargar el vehículo. Esto suele mejorar la tasa de finalización.

### Paso 3 — Confirmación

Mensaje de cierre:

- confirmación de recepción,
- expectativa temporal,
- siguiente paso comercial.

Ejemplo:

> Recibimos tus datos. En breve te contactaremos para avanzar con tu cotización.

---

## 7. Decisiones de producto y UX

## 7.1. Formulario en dos etapas

### Por qué se elige

Separar el flujo en dos pasos reduce la sensación de complejidad inicial. Primero se pide información objetiva y fácil de responder; luego la información personal.

### Beneficios

- menor fricción inicial,
- mejor percepción de rapidez,
- posibilidad de medir abandono por etapa,
- mejor estructura para futuras automatizaciones.

## 7.2. Mobile first

### Por qué se elige

El tráfico principal provendrá de Instagram, por lo que el dispositivo dominante será el celular.

### Implicancias

- diseño vertical,
- campos grandes,
- CTA accesibles con el pulgar,
- tipografía legible,
- mínima carga visual,
- tiempos de carga bajos.

## 7.3. Tono visual: profesional + cálido

### Qué significa en práctica

- profesional: orden, claridad, confianza, consistencia.
- cálido: lenguaje cercano, estética amigable, sin frialdad corporativa excesiva.

### Qué evitar

- exceso de texto,
- interfaces densas,
- demasiados colores,
- formularios largos,
- lenguaje técnico.

## 7.4. Validaciones tempranas

Se validarán campos críticos para evitar leads pobres o imposibles de contactar.

Ejemplos:

- teléfono con formato válido,
- email válido,
- obligatoriedad de completar campos clave,
- bloqueo de avance si faltan datos.

---

## 8. Relevamiento inicial y fuente de datos de vehículos

Hay tres estrategias posibles para alimentar los selectores de vehículo.

### Opción A — JSON propio curado

Se arma un archivo estructurado con relaciones:

- marca → modelo → año → versión.

#### Ventajas

- implementación rápida,
- control total del contenido,
- evita depender de terceros,
- ideal para MVP.

#### Desventajas

- mantenimiento manual,
- cobertura inicial limitada.

### Opción B — Base de datos propia

Se modelan tablas normalizadas para marca, modelo, año y versión.

#### Ventajas

- escalabilidad,
- integridad de datos,
- mejor mantenimiento a mediano plazo.

#### Desventajas

- más tiempo de armado inicial.

### Opción C — Integración externa o scraping

Se consume o replica una fuente externa con catálogo vehicular.

#### Ventajas

- mayor cobertura potencial.

#### Desventajas

- mayor complejidad,
- dependencia de terceros,
- riesgo de cambios en la fuente,
- mayor probabilidad de errores.

### Decisión recomendada para este proyecto

**Comenzar con Opción A para el MVP**, pero diseñando la estructura del código para poder migrar luego a Opción B sin reescribir la interfaz.

---

## 9. Arquitectura propuesta

Se recomienda una arquitectura simple, moderna y mantenible.

### Frontend

- Next.js
- React
- TypeScript
- Tailwind CSS

### Backend

Dos caminos válidos:

- API routes en Next.js para un MVP simple, o
- backend separado en FastAPI / Node si luego habrá lógica más compleja.

### Base de datos

- PostgreSQL

### Hosting sugerido

- Vercel para frontend
- Supabase / Railway / Neon para base de datos y backend liviano

### Analítica y tracking

- Meta Pixel
- Google Tag Manager opcional
- parámetros UTM

---

## 10. Justificación del stack

## Next.js

Se elige porque permite:

- rapidez de desarrollo,
- excelente performance inicial,
- rutas simples,
- integración natural con formularios,
- despliegue ágil.

## TypeScript

Se elige para:

- reducir errores,
- mejorar mantenibilidad,
- documentar mejor contratos de datos.

## Tailwind CSS

Se elige para:

- velocidad en UI,
- consistencia visual,
- facilidad para iterar diseños mobile.

## PostgreSQL

Se elige porque:

- es robusto,
- escalable,
- conocido en entornos profesionales,
- sirve tanto para MVP como para crecimiento posterior.

---

## 11. Modelo de datos inicial

Tabla principal sugerida: `leads`

Campos mínimos:

- id
- marca
- modelo
- anio
- version
- nombre
- telefono
- email
- utm_source
- utm_medium
- utm_campaign
- utm_content
- created_at
- estado

### Observaciones

- `estado` permitirá luego marcar lead nuevo, contactado, cotizado, cerrado, etc.
- Los UTM son fundamentales para atribución de campañas.

---

## 12. Tracking y analítica

El proyecto debe nacer medible.

### Eventos mínimos a registrar

- `PageView`
- `FormStart`
- `VehicleStepCompleted`
- `LeadSubmitted`

### Qué permitirán responder estos eventos

- cuántas visitas llegaron,
- cuántos iniciaron el formulario,
- cuántos completaron el paso 1,
- cuántos terminaron el lead,
- dónde se produce abandono.

### Parámetros importantes

- UTM source
- UTM medium
- UTM campaign
- UTM content

---

## 13. Seguridad, calidad y buenas prácticas

Aunque sea un MVP, debe construirse con criterio profesional.

### Requisitos mínimos

- validación server-side,
- sanitización de inputs,
- rate limiting básico si se expone públicamente,
- manejo de errores amigable,
- protección de variables de entorno,
- logs de errores.

### Buenas prácticas de desarrollo

- ramas por feature,
- pull requests,
- commits claros,
- README actualizado,
- variables de entorno documentadas,
- separación entre config, UI y lógica.

---

## 14. Fases del proyecto

## Fase 1 — Descubrimiento y definición

Objetivo: alinear negocio, UX, datos, métricas y alcance.

### Entregables

- definición funcional,
- mapa del funnel,
- alcance MVP,
- criterios de éxito,
- riesgos y dependencias.

## Fase 2 — Diseño de experiencia

Objetivo: definir estructura, copy y flujo.

### Entregables

- wireframe mobile,
- textos base,
- estructura de formularios,
- mensajes de validación,
- mensajes de cierre.

## Fase 3 — Arquitectura técnica

Objetivo: preparar repositorio y estructura.

### Entregables

- repo inicial,
- stack configurado,
- estructura de carpetas,
- variables de entorno,
- modelo de datos inicial.

## Fase 4 — Desarrollo frontend

Objetivo: construir landing y formulario.

### Entregables

- hero,
- formulario paso 1,
- formulario paso 2,
- barra de progreso,
- estados visuales,
- pantalla de éxito.

## Fase 5 — Desarrollo backend

Objetivo: registrar leads y asegurar integridad.

### Entregables

- endpoint de alta,
- persistencia en base,
- validación server-side,
- logs básicos.

## Fase 6 — Tracking y QA

Objetivo: asegurar medición y funcionamiento real.

### Entregables

- eventos instalados,
- test mobile,
- test de envío,
- revisión visual,
- revisión de mensajes de error.

## Fase 7 — Preparación para marketing

Objetivo: dejar listo el uso con campañas.

### Entregables

- URL productiva,
- parámetros UTM documentados,
- definición de eventos,
- checklist de lanzamiento.

---

## 15. Cronograma estimado

Estimación realista para una primera versión bien hecha.

| Fase | Tarea | Estimación |
|---|---|---:|
| 1 | Descubrimiento y definición | 1 día |
| 2 | Wireframe, copy y UX | 1 a 2 días |
| 3 | Setup técnico y repositorio | 1 día |
| 4 | Desarrollo frontend | 2 a 3 días |
| 5 | Desarrollo backend y base | 1 a 2 días |
| 6 | Tracking + QA | 1 día |
| 7 | Ajustes finales y deploy | 1 día |

### Total estimado

**8 a 11 días hábiles** para un MVP profesional, ordenado y presentable.

### Escenario comprimido

Si se trabaja con foco, buen alcance y sin cambios grandes:

**5 a 6 días hábiles**.

### Escenario más realista

Si hay revisión, ajustes estéticos y validaciones:

**8 días hábiles**.

---

## 16. Riesgos del proyecto

### Riesgo 1 — Fuente de datos de vehículos insuficiente

Si no se define bien la fuente, el formulario puede quedar corto o inconsistente.

### Mitigación

Comenzar con un universo controlado de marcas/modelos y validar cobertura antes del lanzamiento.

### Riesgo 2 — Exceso de alcance

Intentar hacer cotización real + automatización + CRM desde el día 1 puede ralentizar todo.

### Mitigación

Separar MVP de futuras fases.

### Riesgo 3 — Mala medición de campañas

Sin UTMs y eventos, el funnel pierde valor analítico.

### Mitigación

Definir tracking desde el diseño inicial.

### Riesgo 4 — Mala conversión por UX

Un diseño pesado o confuso puede hacer caer la tasa de envío.

### Mitigación

Priorizar mobile, simplificar texto y validar rápido con usuarios reales.

---

## 17. Repositorio: estructura sugerida

```text
/landing-cotizador-autos
  /docs
    funnel.md
    tracking-plan.md
    decisiones-tecnicas.md
  /public
  /src
    /app
    /components
    /lib
    /data
    /types
  /db
  .env.example
  README.md
```

### Carpeta `docs`

Sirve para dejar trazabilidad profesional del proyecto.

Documentos sugeridos:

- `funnel.md`
- `tracking-plan.md`
- `decisiones-tecnicas.md`
- `roadmap.md`

---

## 18. Herramientas utilizadas o recomendadas

### Desarrollo

- VS Code
- Git
- GitHub
- Next.js
- Node.js
- TypeScript
- Tailwind CSS

### Backend y datos

- PostgreSQL
- Supabase / Neon / Railway

### Diseño y definición

- Figma
- Whimsical / Excalidraw para wireframes
- Notion u hoja de ruta simple para seguimiento

### Testing y lanzamiento

- Chrome DevTools
- Lighthouse
- Meta Events Manager
- Postman o cliente API equivalente

---

## 19. Entregables profesionales del proyecto

Al finalizar el MVP deberían existir, como mínimo, los siguientes entregables:

### Producto

- landing funcional,
- formulario 2 pasos,
- captura de lead,
- pantalla de confirmación.

### Técnica

- repositorio ordenado,
- README completo,
- variables de entorno documentadas,
- modelo de datos,
- endpoint funcional.

### Marketing

- definición de UTMs,
- eventos de tracking,
- checklist de publicación.

### Portfolio / carrera

- explicación de negocio,
- decisiones de UX,
- arquitectura,
- roadmap evolutivo,
- aprendizajes.

---

## 20. Roadmap posterior al MVP

Una vez estabilizada la primera versión, las siguientes mejoras naturales serían:

1. integración con WhatsApp API,
2. envío automático de email,
3. panel simple de leads,
4. catálogos de vehículos administrables,
5. scoring de leads,
6. cotización más automatizada,
7. A/B testing de copies y CTA,
8. integración con CRM.

---

## 21. Checklist de definición antes de comenzar el desarrollo

Antes de escribir código, conviene cerrar estas definiciones:

- nombre de marca o broker,
- identidad visual,
- texto principal de la propuesta de valor,
- universo de vehículos del MVP,
- qué se hará exactamente luego del envío,
- dónde se alojarán los leads,
- qué eventos se medirán,
- qué dominio o URL se usará,
- si habrá automatización inmediata o solo captura.

---

## 22. Próximo paso recomendado

Antes de pasar a implementación, se recomienda cerrar tres entregables de definición:

1. **brief funcional definitivo**,
2. **wireframe mobile del funnel**,
3. **decisión de stack final y fuente de datos vehiculares**.

Con eso aprobado, ya se puede redactar el prompt técnico para Codex y comenzar el desarrollo con bajo riesgo de retrabajo.

---

## 23. Estado actual del proyecto

### Situación actual

Proyecto en etapa de planificación y definición.

### Próximo hito

Transformar este README en un plan de ejecución accionable con:

- backlog inicial,
- estructura del repositorio,
- wireframe textual,
- prompt técnico para Codex,
- definición de base de datos,
- checklist de lanzamiento.

---

## 24. Conclusión

Este proyecto debe encararse como un **producto digital orientado a conversión**, no solo como una página linda. La calidad del resultado dependerá de cuatro factores:

- claridad del funnel,
- calidad del dato capturado,
- medición correcta,
- velocidad de implementación sin perder criterio técnico.

La estrategia recomendada es construir un **MVP simple, sólido y bien documentado**, que permita aprender rápido, lanzar antes y evolucionar con evidencia.


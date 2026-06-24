# Domain Events

## 1. Event Name

`lead.created`

## 2. Event Purpose

The `lead.created` event notifies external automation systems that a new lead was successfully captured by the platform. Its purpose is to provide a stable integration contract for downstream workflows that need to react to lead creation in near real time.

## 3. Event Producer

FastAPI backend.

## 4. Event Consumers

Automation systems such as `n8n`.

## 5. Event Delivery Mechanism

The event is delivered through an HTTP webhook triggered by the backend after the lead creation process completes successfully.

## 6. Event Payload Schema

The backend emits the event with the following payload structure:

```json
{
  "event_type": "lead.created",
  "event_version": "1",
  "event_id": "uuid",
  "occurred_at": "timestamp",
  "source": "auto-insurance-lead-funnel",
  "data": {
    "lead_id": "uuid",
    "nombre": "string",
    "telefono": "string",
    "email": "string",
    "vehiculo": {
      "id_vehiculo": "integer",
      "marca": "string",
      "modelo": "string",
      "version": "string",
      "anio": "integer"
    },
    "ubicacion": {
      "provincia": "string",
      "localidad": "string"
    }
  }
}
```

Field overview:

- `event_type`: identifies the domain event name.
- `event_version`: defines the schema version of the event contract.
- `event_id`: unique identifier for the emitted event instance.
- `occurred_at`: timestamp indicating when the event occurred.
- `source`: logical origin of the event.
- `data`: business payload associated with the created lead.
- `data.lead_id`: unique identifier of the created lead.
- `data.nombre`: lead full name.
- `data.telefono`: lead phone number.
- `data.email`: lead email address.
- `data.vehiculo`: vehicle information associated with the lead.
- `data.ubicacion`: location information associated with the lead.

## 7. Event Reliability Considerations

- Idempotency: consumers should use `event_id` to detect and ignore duplicate deliveries.
- Webhook retries: the backend should retry webhook delivery when the consumer endpoint is temporarily unavailable or returns a retryable failure.
- Payload validation: both producer and consumer should validate the payload schema to ensure contract consistency and prevent malformed event processing.

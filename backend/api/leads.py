"""Endpoints para registrar leads del cotizador."""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.events import LEAD_CREATED, emit_event
from infra.supabase_client import cliente_supabase

router = APIRouter(prefix="/leads", tags=["leads"])
logger = logging.getLogger(__name__)


class LeadRequest(BaseModel):
    nombre: str
    telefono: str
    email: Optional[str] = None

    marca: str
    modelo: str
    anio: str
    version: str

    precio_cotizado: float

    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None

    referrer: Optional[str] = None
    landing_page: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


@router.post("")
def crear_lead(payload: LeadRequest) -> dict[str, str]:
    if cliente_supabase is None:
        raise HTTPException(status_code=500, detail="Supabase client not configured")

    data = payload.model_dump()
    nombre = payload.nombre
    telefono = payload.telefono
    email = payload.email
    vehiculo_data = {
        "marca": payload.marca,
        "modelo": payload.modelo,
        "anio": payload.anio,
        "version": payload.version,
        "precio_cotizado": payload.precio_cotizado,
    }
    ubicacion_data = {}

    try:
        result = cliente_supabase.table("leads").insert(data).execute()
        print("SUPABASE RESULT:")
        print(result)

        if hasattr(result, "error") and result.error:
            print("SUPABASE ERROR:")
            print(result.error)

        registros = getattr(result, "data", None) or []
        if not isinstance(registros, list) or not registros:
            raise HTTPException(status_code=500, detail="Supabase did not return inserted lead")

        lead = registros[0]
        lead_id = lead.get("id") if isinstance(lead, dict) else None

        try:
            emit_event(
                LEAD_CREATED,
                {
                    "lead_id": lead_id,
                    "nombre": nombre,
                    "telefono": telefono,
                    "email": email,
                    "vehiculo": vehiculo_data,
                    "ubicacion": ubicacion_data,
                },
            )
        except Exception:  # noqa: BLE001
            logger.exception("Failed to emit lead.created event")

        return {
            "status": "ok",
            "lead_id": str(lead_id or ""),
        }
    except HTTPException:
        raise
    except Exception as error:  # noqa: BLE001
        import traceback

        print("ERROR INSERT LEAD")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(error)) from error

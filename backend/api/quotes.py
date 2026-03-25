"""Router de cotizacion interna contra Mercantil Andina."""

from __future__ import annotations

from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

from backend.services.cotizador_service import (
    cotizar_vehiculo as cotizar_vehiculo_service,
    simplificar_respuesta_cotizacion,
)

router = APIRouter(prefix="/api", tags=["Quotes"])


class CotizacionRequest(BaseModel):
    vehiculo_id: int = Field(..., gt=0)
    anio_modelo: int = Field(..., ge=1900)
    ubicacion: int = Field(..., ge=0)
    uso_vehiculo: str = Field(..., min_length=1)
    suma_asegurada: float = Field(..., gt=0)
    comision: float = Field(..., ge=0)
    bonificacion: float = Field(..., ge=0)
    recargo: float = Field(..., ge=0)


class CotizacionResponse(BaseModel):
    producto: str
    precio: float
    prima_tecnica: float
    cuota: float


@router.post("/cotizar", response_model=CotizacionResponse)
async def cotizar_vehiculo(payload: CotizacionRequest) -> CotizacionResponse:
    try:
        respuesta = await cotizar_vehiculo_service(
            payload.vehiculo_id,
            anio_modelo=payload.anio_modelo,
            ubicacion=payload.ubicacion,
            suma_asegurada=payload.suma_asegurada,
            uso_vehiculo=payload.uso_vehiculo,
            bonificacion=payload.bonificacion,
            recargo=payload.recargo,
            comision=payload.comision,
        )
        simplificada = simplificar_respuesta_cotizacion(respuesta)
        return CotizacionResponse(
            producto=simplificada["producto"],
            precio=simplificada["precio"],
            prima_tecnica=simplificada["prima_tecnica"],
            cuota=simplificada["cuota"],
        )
    except RuntimeError as error:
        mensaje = str(error)
        status_code = 404 if "no encontrado" in mensaje.lower() else 502
        raise HTTPException(status_code=status_code, detail=mensaje) from error
    except Exception as error:  # noqa: BLE001
        raise HTTPException(status_code=502, detail="No se pudo obtener la cotizacion de Mercantil.") from error

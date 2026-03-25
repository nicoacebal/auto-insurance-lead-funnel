"""Endpoint de cotizacion automotor contra Mercantil Andina."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.services.cotizador_service import cotizar_vehiculo

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Cotizaciones"])


class CotizacionRequest(BaseModel):
    vehiculo_id: int
    anio_modelo: int
    ubicacion: int
    suma_asegurada: float
    uso_vehiculo: str = "14"
    bonificacion: float = 0
    recargo: float = 25
    comision: float = 20


class Cobertura(BaseModel):
    codigo: str
    nombre: str
    descripcion: str
    prima_tecnica: float
    precio: float


class CotizacionResponse(BaseModel):
    cotizacion_id: str
    numero: int
    coberturas: list[Cobertura]


@router.post("/cotizar-auto", response_model=CotizacionResponse)
async def cotizar_auto(request: CotizacionRequest) -> CotizacionResponse:
    try:
        resultado = await cotizar_vehiculo(
            request.vehiculo_id,
            anio_modelo=request.anio_modelo,
            ubicacion=request.ubicacion,
            suma_asegurada=request.suma_asegurada,
            uso_vehiculo=request.uso_vehiculo,
            bonificacion=request.bonificacion,
            recargo=request.recargo,
            comision=request.comision,
        )
    except RuntimeError as error:
        mensaje = str(error)
        logger.error("Error en cotizacion Mercantil: %s", mensaje)
        if "no encontrado" in mensaje.lower():
            raise HTTPException(status_code=404, detail=mensaje) from error
        raise HTTPException(status_code=502, detail="Error en cotizacion de Mercantil") from error
    except Exception as error:  # noqa: BLE001
        logger.exception("Error no controlado en cotizacion Mercantil")
        raise HTTPException(status_code=502, detail="Error en cotizacion de Mercantil") from error

    coberturas = resultado.get("coberturas", [])
    if not isinstance(coberturas, list) or not coberturas:
        raise HTTPException(status_code=404, detail="No se encontraron coberturas")

    return CotizacionResponse(
        cotizacion_id=str(resultado.get("cotizacion_id") or ""),
        numero=int(resultado.get("numero") or 0),
        coberturas=[
            Cobertura(
                codigo=str(cobertura.get("codigo") or ""),
                nombre=str(cobertura.get("nombre") or ""),
                descripcion=str(cobertura.get("descripcion") or ""),
                prima_tecnica=float(cobertura.get("prima_tecnica") or 0.0),
                precio=float(cobertura.get("precio") or 0.0),
            )
            for cobertura in coberturas
            if isinstance(cobertura, dict)
        ],
    )

"""Router del selector profesional de vehiculos."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from backend.services.vehiculos_service import (
    obtener_anios,
    obtener_marcas,
    obtener_modelos,
    obtener_versiones,
)

router = APIRouter(prefix="/vehicles", tags=["Vehicles"])


@router.get("/marcas", response_model=list[str])
def listar_marcas() -> list[str]:
    try:
        return obtener_marcas()
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.get("/modelos", response_model=list[str])
def listar_modelos(marca: str = Query(..., min_length=1)) -> list[str]:
    try:
        return obtener_modelos(marca)
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.get("/versiones", response_model=list[str])
def listar_versiones(
    marca: str = Query(..., min_length=1),
    modelo: str = Query(..., min_length=1),
) -> list[str]:
    try:
        return obtener_versiones(marca, modelo)
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.get("/anios", response_model=list[int])
def listar_anios(
    marca: str = Query(..., min_length=1),
    modelo: str = Query(..., min_length=1),
    version: str = Query(..., min_length=1),
) -> list[int]:
    try:
        return obtener_anios(marca, modelo, version)
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error

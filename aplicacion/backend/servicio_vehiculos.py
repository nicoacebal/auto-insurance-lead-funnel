"""Servicio para consultar el catalogo de vehiculos en Supabase."""

from __future__ import annotations

from typing import Any

from .servicios.cliente_supabase import cliente_supabase

TAMANO_LOTE = 1000


def _asegurar_cliente() -> Any:
    if cliente_supabase is None:
        raise RuntimeError("Supabase no esta configurado para consultar vehiculos.")
    return cliente_supabase


def _obtener_registros(columnas: str, filtros: dict[str, Any]) -> list[dict[str, Any]]:
    """Consulta todos los registros necesarios en lotes para evitar limites por pagina."""
    cliente = _asegurar_cliente()
    registros: list[dict[str, Any]] = []
    inicio = 0

    while True:
        consulta = cliente.table("vehiculos").select(columnas).range(inicio, inicio + TAMANO_LOTE - 1)
        for campo, valor in filtros.items():
            consulta = consulta.eq(campo, valor)

        respuesta = consulta.execute()
        lote = getattr(respuesta, "data", None) or []
        if not lote:
            break

        registros.extend(lote)
        if len(lote) < TAMANO_LOTE:
            break

        inicio += TAMANO_LOTE

    return registros


def obtener_marcas() -> list[str]:
    registros = _obtener_registros("marca", {})
    return sorted({registro["marca"] for registro in registros if registro.get("marca")})


def obtener_modelos(marca: str) -> list[str]:
    registros = _obtener_registros("modelo", {"marca": marca})
    return sorted({registro["modelo"] for registro in registros if registro.get("modelo")})


def obtener_anios(marca: str, modelo: str) -> list[int]:
    registros = _obtener_registros("anio", {"marca": marca, "modelo": modelo})
    return sorted({registro["anio"] for registro in registros if isinstance(registro.get("anio"), int)})


def obtener_versiones(marca: str, modelo: str, anio: int) -> list[str]:
    registros = _obtener_registros("version", {"marca": marca, "modelo": modelo, "anio": anio})
    return sorted({registro["version"] for registro in registros if registro.get("version")})

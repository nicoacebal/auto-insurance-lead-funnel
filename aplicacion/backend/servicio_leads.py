"""Servicio para persistir leads en Supabase."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from .servicios.cliente_supabase import cliente_supabase

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ResultadoGuardadoLead:
    """Representa el resultado de intentar guardar un lead."""

    exito: bool
    mensaje: str | None = None


def guardar_lead(
    *,
    nombre: str,
    telefono: str,
    email: str,
    marca: str,
    modelo: str,
    anio: int | str,
    version: str,
    precio_cotizado: int | float,
) -> ResultadoGuardadoLead:
    """Inserta un lead en la tabla `leads` de Supabase."""
    if cliente_supabase is None:
        return ResultadoGuardadoLead(
            exito=False,
            mensaje="No pudimos registrar tus datos en este momento.",
        )

    payload_lead = {
        "nombre": nombre,
        "telefono": telefono,
        "email": email,
        "marca": marca,
        "modelo": modelo,
        "anio": anio,
        "version": version,
        "precio_cotizado": precio_cotizado,
    }

    try:
        cliente_supabase.table("leads").insert(payload_lead).execute()
        return ResultadoGuardadoLead(exito=True)
    except Exception:
        # El error se registra y se devuelve un estado controlado para no romper el flujo.
        logger.exception("Error al insertar lead en Supabase.")
        return ResultadoGuardadoLead(
            exito=False,
            mensaje="Recibimos tu solicitud, pero hubo un inconveniente al guardarla.",
        )

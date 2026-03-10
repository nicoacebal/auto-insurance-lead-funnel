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


def _actualizar_por_email_y_telefono(email: str, telefono: str, payload: dict) -> None:
    (
        cliente_supabase.table("leads")
        .update(payload)
        .eq("email", email)
        .eq("telefono", telefono)
        .execute()
    )


def _insertar_lead(payload: dict) -> None:
    cliente_supabase.table("leads").insert(payload).execute()


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
    utm_source: str | None = None,
    utm_medium: str | None = None,
    utm_campaign: str | None = None,
    referrer: str | None = None,
    landing_page: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> ResultadoGuardadoLead:
    """Guarda un lead en Supabase evitando duplicados por email + telefono."""
    if cliente_supabase is None:
        return ResultadoGuardadoLead(
            exito=False,
            mensaje="No pudimos registrar tus datos en este momento.",
        )

    payload_actualizacion_base = {
        "marca": marca,
        "modelo": modelo,
        "anio": anio,
        "version": version,
        "precio_cotizado": precio_cotizado,
    }
    payload_opcional = {
        "utm_source": utm_source,
        "utm_medium": utm_medium,
        "utm_campaign": utm_campaign,
        "referrer": referrer,
        "landing_page": landing_page,
        "ip_address": ip_address,
        "user_agent": user_agent,
    }

    payload_actualizacion_extendido = {**payload_actualizacion_base, **payload_opcional}
    payload_nuevo_base = {
        "nombre": nombre,
        "telefono": telefono,
        "email": email,
        **payload_actualizacion_base,
    }
    payload_nuevo_extendido = {**payload_nuevo_base, **payload_opcional}

    try:
        # Primero se consulta si ya existe un lead con el mismo email y telefono.
        respuesta_busqueda = (
            cliente_supabase.table("leads")
            .select("id")
            .eq("email", email)
            .eq("telefono", telefono)
            .limit(1)
            .execute()
        )
        registros_existentes = getattr(respuesta_busqueda, "data", None) or []

        if registros_existentes:
            # Se intenta actualizar incluyendo campos nuevos de tracking y dispositivo.
            try:
                _actualizar_por_email_y_telefono(email, telefono, payload_actualizacion_extendido)
            except Exception:
                logger.warning(
                    "No se pudieron guardar campos opcionales en update; se reintenta con campos base.",
                    exc_info=True,
                )
                _actualizar_por_email_y_telefono(email, telefono, payload_actualizacion_base)
        else:
            # Si no existe, se intenta insertar el lead con todos los campos disponibles.
            try:
                _insertar_lead(payload_nuevo_extendido)
            except Exception:
                logger.warning(
                    "No se pudieron guardar campos opcionales en insert; se reintenta con campos base.",
                    exc_info=True,
                )
                _insertar_lead(payload_nuevo_base)

        return ResultadoGuardadoLead(exito=True)
    except Exception:
        # El error se registra y se devuelve un estado controlado para no romper el flujo HTMX.
        logger.exception("Error al guardar lead en Supabase.")
        return ResultadoGuardadoLead(
            exito=False,
            mensaje="Recibimos tu solicitud, pero hubo un inconveniente al guardarla.",
        )

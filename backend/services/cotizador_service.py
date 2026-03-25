"""Servicios de cotizacion Mercantil para el backend productivo."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any

from backend.integrations.mercantil_client import MercantilClient
from backend.services.productos_service import obtener_productos_tecnicos
from backend.services.vehiculos_service import obtener_vehiculo_por_id

logger = logging.getLogger(__name__)

PRODUCTOR_DEFAULT = 51262
CATEGORIA_IVA_DEFAULT = "1"
AJUSTE_SUMA_DEFAULT = "0"
CANAL_COTIZACION_DEFAULT = "DELTA"
CUOTA_DEFAULT = 1
PERIODO_DEFAULT = 1
MONEDA_DEFAULT = 1
TIPO_PAGO_DEFAULT = "C"


def get_vehicle(vehicle_id: int) -> dict[str, Any]:
    """Obtiene un vehiculo desde `vehicle_catalog` por id."""
    vehiculo = obtener_vehiculo_por_id(vehicle_id)
    if vehiculo is None:
        raise RuntimeError("Vehiculo no encontrado en vehicle_catalog.")
    return vehiculo


def build_payload(
    vehicle: dict[str, Any],
    ubicacion: int,
    uso_vehiculo: str,
    suma_asegurada: int | float,
    *,
    anio_modelo: int,
    comision: int | float,
    bonificacion: int | float,
    recargo: int | float,
    productos_tecnicos: list[str] | None = None,
) -> dict[str, Any]:
    """Construye el payload base esperado por Mercantil para cotizar."""
    vehiculo_id = vehicle.get("id")
    if not isinstance(vehiculo_id, int):
        raise RuntimeError("El vehiculo seleccionado no tiene un id valido para cotizar.")

    return {
        "productor": PRODUCTOR_DEFAULT,
        "bonificacion": bonificacion,
        "recargo": recargo,
        "comision": comision,
        "categoria_iva": CATEGORIA_IVA_DEFAULT,
        "ajuste_suma": AJUSTE_SUMA_DEFAULT,
        "canal_cotizacion": CANAL_COTIZACION_DEFAULT,
        "cuota": CUOTA_DEFAULT,
        "periodo": PERIODO_DEFAULT,
        "moneda": MONEDA_DEFAULT,
        "tipo_pago": TIPO_PAGO_DEFAULT,
        "desde": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "item": {
            "vehiculo_id": vehiculo_id,
            "anio_modelo": anio_modelo,
            "ubicacion": ubicacion,
            "suma_asegurada": suma_asegurada,
            "uso_vehiculo": uso_vehiculo,
            "es_0km": False,
            "gnc": False,
            "franquicia": "0",
            "productos_tecnicos": list(productos_tecnicos or []),
            "rastreo": 0,
            "adicionales": [],
            "accesorios": [],
        },
    }


def cotizar(payload: dict[str, Any]) -> Any:
    """Llama al endpoint de cotizacion de Mercantil."""
    cliente = MercantilClient()
    return cliente.crear_cotizacion(payload)


def _a_numero(valor: Any) -> float | None:
    if isinstance(valor, (int, float)):
        return float(valor)
    if isinstance(valor, str):
        normalizado = valor.strip().replace(".", "").replace(",", ".")
        try:
            return float(normalizado)
        except ValueError:
            return None
    return None


def parse_cotizacion_mercantil(response_json: dict[str, Any]) -> dict[str, Any]:
    """Normaliza la respuesta de Mercantil y extrae todas las coberturas disponibles."""
    cotizacion = response_json.get("cotizacion")
    item = response_json.get("item")

    if not isinstance(cotizacion, dict):
        cotizacion = {}
    if not isinstance(item, dict):
        item = {}

    productos_tecnicos = item.get("productos_tecnicos", [])
    if not isinstance(productos_tecnicos, list):
        productos_tecnicos = []

    coberturas: list[dict[str, Any]] = []
    for producto in productos_tecnicos:
        if not isinstance(producto, dict):
            continue

        premio = _a_numero(
            (
                producto.get("producto_tecnico_premio_calculado", {})
                .get("cuota", {})
                .get("premio")
            )
        )

        coberturas.append(
            {
                "codigo": str(producto.get("codigo") or ""),
                "nombre": str(producto.get("nombre") or "").strip(),
                "descripcion": str(producto.get("descripcion") or "").strip(),
                "prima_tecnica": _a_numero(producto.get("prima_tecnica")) or 0.0,
                "precio": premio or 0.0,
            }
        )

    return {
        "cotizacion_id": str(cotizacion.get("id") or ""),
        "numero": int(cotizacion.get("numero") or 0),
        "coberturas": coberturas,
    }


def simplificar_respuesta_cotizacion(respuesta: Any) -> dict[str, Any]:
    """Mantiene compatibilidad con el endpoint legacy `/api/cotizar`."""
    if isinstance(respuesta, dict):
        cotizacion_parseada = respuesta if "coberturas" in respuesta else parse_cotizacion_mercantil(respuesta)
    else:
        cotizacion_parseada = {"cotizacion_id": "", "numero": 0, "coberturas": []}

    coberturas = cotizacion_parseada.get("coberturas", [])
    primera = coberturas[0] if isinstance(coberturas, list) and coberturas else {}
    if not isinstance(primera, dict):
        primera = {}

    precio = _a_numero(primera.get("precio")) or 0.0
    prima_tecnica = _a_numero(primera.get("prima_tecnica")) or 0.0
    return {
        "cotizacion_id": cotizacion_parseada.get("cotizacion_id", ""),
        "numero": cotizacion_parseada.get("numero", 0),
        "coberturas": coberturas,
        "producto": str(primera.get("nombre") or ""),
        "precio": precio,
        "prima_tecnica": prima_tecnica,
        "cuota": 1.0 if coberturas else 0.0,
        "cobertura": str(primera.get("descripcion") or ""),
    }


async def cotizar_vehiculo(
    vehiculo_id: int,
    *,
    anio_modelo: int,
    ubicacion: int,
    suma_asegurada: float,
    uso_vehiculo: str = "14",
    bonificacion: float = 0,
    recargo: float = 25,
    comision: float = 20,
) -> dict[str, Any]:
    """Orquesta la cotizacion completa y devuelve coberturas normalizadas."""
    vehiculo = get_vehicle(vehiculo_id)
    productos = await obtener_productos_tecnicos(
        vehiculo_id,
        anio_modelo,
        ubicacion,
        suma_asegurada,
        uso_vehiculo,
    )
    payload = build_payload(
        vehiculo,
        ubicacion,
        uso_vehiculo,
        suma_asegurada,
        anio_modelo=anio_modelo,
        comision=comision,
        bonificacion=bonificacion,
        recargo=recargo,
        productos_tecnicos=productos,
    )
    respuesta = await asyncio.to_thread(cotizar, payload)
    if not isinstance(respuesta, dict):
        raise RuntimeError("Respuesta invalida de Mercantil.")

    resultado = parse_cotizacion_mercantil(respuesta)
    logger.info("Mercantil cotizacion generada")
    logger.info("Cotizacion numero: %s", resultado.get("numero"))
    return resultado

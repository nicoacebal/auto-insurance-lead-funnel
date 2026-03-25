"""Servicio para resolver productos tecnicos disponibles antes de cotizar."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any

from backend.integrations.mercantil_client import MercantilClient
from backend.services.vehiculos_service import obtener_vehiculo_por_id
from infra.supabase_client import cliente_supabase

logger = logging.getLogger(__name__)

PRODUCTOR_ID_DEFAULT = 51262
RAMO_CODIGO_DEFAULT = "05"
NO_RODAMIENTO_DEFAULT = "0"


def _buscar_productos_tecnicos(payload: Any) -> list[str]:
    """Extrae codigos de productos tecnicos desde una respuesta arbitraria."""
    productos: list[str] = []

    def recorrer(valor: Any) -> None:
        if isinstance(valor, list):
            if valor and all(isinstance(item, (str, int, float)) for item in valor):
                for item in valor:
                    codigo = str(item).strip()
                    if codigo and codigo not in productos:
                        productos.append(codigo)
                return

            for item in valor:
                recorrer(item)
            return

        if isinstance(valor, dict):
            for clave, contenido in valor.items():
                clave_normalizada = clave.lower()
                if clave_normalizada in {"productos_tecnicos", "productostecnicos"} and isinstance(contenido, list):
                    recorrer(contenido)
                    continue
                if clave_normalizada == "codigo" and isinstance(contenido, (str, int, float)):
                    codigo = str(contenido).strip()
                    if codigo and codigo not in productos:
                        productos.append(codigo)
                    continue
                recorrer(contenido)

    recorrer(payload)
    return productos


def _resolver_localidad_codigo(ubicacion: int) -> str:
    """Mapea la ubicacion usada por cotizacion al localidad_codigo requerido por coberturas."""
    if cliente_supabase is None:
        raise RuntimeError("Supabase no esta configurado para consultar ubicaciones.")

    try:
        respuesta = (
            cliente_supabase.table("ubicaciones")
            .select("localidad_codigo, codigo_postal, localidad_nombre")
            .eq("ubicacion", ubicacion)
            .limit(1)
            .execute()
        )
    except Exception as error:  # noqa: BLE001
        raise RuntimeError("No se pudo resolver localidad_codigo desde ubicaciones.") from error

    registros = getattr(respuesta, "data", None) or []
    if not isinstance(registros, list) or not registros:
        raise ValueError("No se encontro localidad_codigo para la ubicacion indicada.")

    registro = registros[0]
    localidad_codigo = registro.get("localidad_codigo") if isinstance(registro, dict) else None
    codigo_postal = registro.get("codigo_postal") if isinstance(registro, dict) else None
    localidad_nombre = registro.get("localidad_nombre") if isinstance(registro, dict) else None

    if not isinstance(localidad_codigo, str) or not localidad_codigo.strip():
        raise ValueError("No se encontro localidad_codigo para la ubicacion indicada.")

    logger.info(
        "localidad_codigo_resuelto",
        extra={
            "ubicacion": ubicacion,
            "codigo_postal": codigo_postal,
            "localidad_codigo": localidad_codigo,
            "localidad_nombre": localidad_nombre,
        },
    )
    return localidad_codigo.strip()


def _resolver_suma_asegurada(vehiculo: dict[str, Any], suma_asegurada: float) -> int:
    """Usa la suma del catalogo cuando existe; si no, usa la recibida en el request."""
    for clave in ("suma", "suma_asegurada", "valor"):
        valor = vehiculo.get(clave)
        if isinstance(valor, (int, float)) and valor > 0:
            return int(valor)
        if isinstance(valor, str):
            normalizado = valor.strip().replace(".", "").replace(",", ".")
            try:
                numero = float(normalizado)
            except ValueError:
                numero = 0
            if numero > 0:
                return int(numero)
    return int(suma_asegurada)


def _construir_parametros_productos(
    vehiculo: dict[str, Any],
    anio_modelo: int,
    ubicacion: int,
    suma_asegurada: float,
    uso_vehiculo: str,
) -> dict[str, Any]:
    """Arma los parametros requeridos por el endpoint de productos tecnicos."""
    tipo_vehiculo = vehiculo.get("tipo_vehiculo_codigo")
    categoria_tipo = vehiculo.get("categoria_tipo_codigo")
    carroceria_tipo = vehiculo.get("carroceria_tipo_codigo")

    faltantes = [
        nombre
        for nombre, valor in (
            ("tipo_vehiculo_codigo", tipo_vehiculo),
            ("categoria_tipo_codigo", categoria_tipo),
            ("carroceria_tipo_codigo", carroceria_tipo),
        )
        if valor in (None, "")
    ]
    if faltantes:
        raise ValueError(
            "El vehiculo no tiene datos suficientes para consultar productos tecnicos: "
            + ", ".join(faltantes)
        )

    parametros = {
        "antiguedad": max(0, datetime.now().year - int(anio_modelo)),
        "carroceria_tipo": str(carroceria_tipo),
        "categoria_tipo": str(categoria_tipo),
        "vehiculo_tipo": str(tipo_vehiculo),
        "uso_tipo": str(uso_vehiculo),
        "suma_asegurada": _resolver_suma_asegurada(vehiculo, suma_asegurada),
        "no_rodamiento": NO_RODAMIENTO_DEFAULT,
        "productor_id": PRODUCTOR_ID_DEFAULT,
        "ramo_codigo": RAMO_CODIGO_DEFAULT,
        "fecha": datetime.utcnow().isoformat(timespec="milliseconds") + "Z",
        "localidad_codigo": _resolver_localidad_codigo(ubicacion),
    }
    return parametros


def _obtener_productos_tecnicos_sync(
    vehiculo_id: int,
    anio_modelo: int,
    ubicacion: int,
    suma_asegurada: float,
    uso_vehiculo: str,
) -> list[str]:
    vehiculo = obtener_vehiculo_por_id(vehiculo_id)
    if vehiculo is None:
        raise ValueError("Vehiculo no encontrado para consultar productos tecnicos.")

    parametros = _construir_parametros_productos(
        vehiculo,
        anio_modelo,
        ubicacion,
        suma_asegurada,
        uso_vehiculo,
    )

    logger.info("productos_tecnicos_request_params", extra={"params": parametros})

    cliente = MercantilClient()
    respuesta = cliente.obtener_coberturas(parametros)
    productos = _buscar_productos_tecnicos(respuesta)
    if not productos:
        raise ValueError("No se encontraron productos tecnicos para el vehiculo")

    logger.info("productos_tecnicos_obtenidos", extra={"productos": productos})
    return productos


async def obtener_productos_tecnicos(
    vehiculo_id: int,
    anio_modelo: int,
    ubicacion: int,
    suma_asegurada: float,
    uso_vehiculo: str,
) -> list[str]:
    """Consulta y devuelve los codigos de productos tecnicos disponibles."""
    return await asyncio.to_thread(
        _obtener_productos_tecnicos_sync,
        vehiculo_id,
        anio_modelo,
        ubicacion,
        suma_asegurada,
        uso_vehiculo,
    )
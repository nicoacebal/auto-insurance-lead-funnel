"""Servicio de lectura del selector profesional de vehiculos."""

from __future__ import annotations

from typing import Any

from supabase import Client

from infra.supabase_client import cliente_supabase


def _asegurar_cliente() -> Client:
    if cliente_supabase is None:
        raise RuntimeError("Supabase no esta configurado para consultar vehicle_catalog.")
    return cliente_supabase


def _normalizar_texto(valor: str) -> str:
    return " ".join(valor.strip().upper().split())


def _ejecutar_rpc(nombre_funcion: str, parametros: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    cliente = _asegurar_cliente()

    try:
        respuesta = cliente.rpc(nombre_funcion, parametros or {}).execute()
    except Exception as error:  # noqa: BLE001
        raise RuntimeError(f"No se pudo ejecutar la consulta de vehiculos ({nombre_funcion}).") from error

    datos = getattr(respuesta, "data", None)
    if not isinstance(datos, list):
        return []

    return [fila for fila in datos if isinstance(fila, dict)]


def obtener_marcas() -> list[str]:
    filas = _ejecutar_rpc("get_vehicle_brands")
    return [fila["marca"] for fila in filas if isinstance(fila.get("marca"), str) and fila["marca"].strip()]


def obtener_modelos(marca: str) -> list[str]:
    filas = _ejecutar_rpc("get_vehicle_models", {"p_marca": _normalizar_texto(marca)})
    return [fila["modelo"] for fila in filas if isinstance(fila.get("modelo"), str) and fila["modelo"].strip()]


def obtener_versiones(marca: str, modelo: str) -> list[str]:
    filas = _ejecutar_rpc(
        "get_vehicle_versions",
        {
            "p_marca": _normalizar_texto(marca),
            "p_modelo": _normalizar_texto(modelo),
        },
    )
    return [fila["version"] for fila in filas if isinstance(fila.get("version"), str) and fila["version"].strip()]


def obtener_anios(marca: str, modelo: str, version: str) -> list[int]:
    filas = _ejecutar_rpc(
        "get_vehicle_years",
        {
            "p_marca": _normalizar_texto(marca),
            "p_modelo": _normalizar_texto(modelo),
            "p_version": _normalizar_texto(version),
        },
    )
    return [fila["anio"] for fila in filas if isinstance(fila.get("anio"), int)]


def obtener_vehiculo_por_id(vehicle_id: int) -> dict[str, Any] | None:
    cliente = _asegurar_cliente()

    try:
        respuesta = (
            cliente.table("vehicle_catalog")
            .select("*")
            .eq("id", vehicle_id)
            .limit(1)
            .execute()
        )
    except Exception as error:  # noqa: BLE001
        print("\n==============================")
        print("ERROR CONSULTANDO vehicle_catalog")
        print(f"vehicle_id: {vehicle_id}")
        print(str(error))
        print("==============================\n")
        raise RuntimeError("No se pudo consultar vehicle_catalog por id.") from error

    datos = getattr(respuesta, "data", None)
    if not isinstance(datos, list) or not datos:
        return None

    vehiculo = datos[0]
    return vehiculo if isinstance(vehiculo, dict) else None

"""Sincroniza el catalogo de ubicaciones de Mercantil Andina hacia Supabase."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv
from supabase import Client, create_client

RUTA_RAIZ = Path(__file__).resolve().parents[2]
RUTA_ENV = RUTA_RAIZ / ".env"
BASE_URL = "https://productos.mercantilandina.com.ar/api_tarifa_mapeo/ubicaciones/zona-riesgo"
TOKEN_URL_DEFAULT = "https://idm.mercantilandina.com.ar/auth/realms/meran/protocol/openid-connect/token"
CLIENT_ID_DEFAULT = "sigma"
PREFIJO_INICIAL = 1000
PREFIJO_FINAL = 9999
TAMANO_LOTE = 500
INTERVALO_FLUSH_PREFIJOS = 500
TIMEOUT = 30
MAX_MUESTRAS_ERROR = 5

logger = logging.getLogger(__name__)


def cargar_dotenv_repositorio() -> None:
    """Carga variables de entorno desde la raiz del repositorio si existe `.env`."""
    if RUTA_ENV.exists():
        load_dotenv(dotenv_path=RUTA_ENV)
    else:
        load_dotenv()


def crear_cliente_supabase() -> Client:
    """Crea un cliente de Supabase usando credenciales de entorno."""
    cargar_dotenv_repositorio()

    supabase_url = (os.getenv("SUPABASE_URL") or "").strip()
    service_role_key = (os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY") or "").strip()

    if not supabase_url:
        raise RuntimeError("SUPABASE_URL not defined in environment variables")
    if not service_role_key:
        raise RuntimeError("SUPABASE_SERVICE_ROLE_KEY or SUPABASE_KEY not defined in environment variables")

    return create_client(supabase_url, service_role_key)


def crear_contexto_autenticacion_mercantil() -> dict[str, str | None]:
    """Carga configuracion de autenticacion Mercantil desde entorno."""
    cargar_dotenv_repositorio()

    return {
        "token": (os.getenv("MA_TOKEN") or "").strip() or None,
        "api_key": (os.getenv("MA_API_KEY") or "").strip() or None,
        "refresh_token": (os.getenv("MA_REFRESH_TOKEN") or "").strip() or None,
        "token_url": (os.getenv("MA_TOKEN_URL") or TOKEN_URL_DEFAULT).strip(),
        "client_id": (os.getenv("MA_CLIENT_ID") or CLIENT_ID_DEFAULT).strip(),
        "client_secret": (os.getenv("MA_CLIENT_SECRET") or "").strip() or None,
        "username": (os.getenv("MA_USERNAME") or "").strip() or None,
        "password": (os.getenv("MA_PASSWORD") or "").strip() or None,
    }


def iniciar_sesion_con_credenciales(contexto_auth: dict[str, str | None]) -> bool:
    """Obtiene access token usando usuario y password si no hay token previo."""
    username = contexto_auth.get("username")
    password = contexto_auth.get("password")
    token_url = contexto_auth.get("token_url")
    client_id = contexto_auth.get("client_id")

    if not username or not password or not token_url or not client_id:
        return False

    payload = {
        "grant_type": "password",
        "client_id": client_id,
        "username": username,
        "password": password,
    }
    if contexto_auth.get("client_secret"):
        payload["client_secret"] = contexto_auth["client_secret"]

    try:
        respuesta = requests.post(
            token_url,
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=TIMEOUT,
        )
    except requests.RequestException as error:
        print(f"No se pudo iniciar sesion en Mercantil: {error}")
        return False

    if respuesta.status_code != 200:
        print(f"No se pudo iniciar sesion en Mercantil. HTTP {respuesta.status_code}")
        print(f"Preview login: {vista_previa_respuesta(respuesta)}")
        return False

    try:
        payload_respuesta = respuesta.json()
    except ValueError:
        print("La respuesta de login no devolvio JSON valido.")
        return False

    nuevo_access_token = payload_respuesta.get("access_token")
    nuevo_refresh_token = payload_respuesta.get("refresh_token")

    if not isinstance(nuevo_access_token, str) or not nuevo_access_token.strip():
        print("La respuesta de login no devolvio access_token.")
        return False

    contexto_auth["token"] = nuevo_access_token.strip()
    if isinstance(nuevo_refresh_token, str) and nuevo_refresh_token.strip():
        contexto_auth["refresh_token"] = nuevo_refresh_token.strip()

    os.environ["MA_TOKEN"] = contexto_auth["token"] or ""
    if contexto_auth.get("refresh_token"):
        os.environ["MA_REFRESH_TOKEN"] = contexto_auth["refresh_token"] or ""

    print("Access token de Mercantil obtenido por login correctamente.")
    return True


def refrescar_access_token(contexto_auth: dict[str, str | None]) -> bool:
    """Intenta renovar el access token usando refresh token si esta disponible."""
    refresh_token = contexto_auth.get("refresh_token")
    token_url = contexto_auth.get("token_url")
    client_id = contexto_auth.get("client_id")

    if not refresh_token or not token_url or not client_id:
        return False

    payload = {
        "grant_type": "refresh_token",
        "client_id": client_id,
        "refresh_token": refresh_token,
    }
    if contexto_auth.get("client_secret"):
        payload["client_secret"] = contexto_auth["client_secret"]

    try:
        respuesta = requests.post(
            token_url,
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=TIMEOUT,
        )
    except requests.RequestException as error:
        print(f"No se pudo refrescar el token de Mercantil: {error}")
        return False

    if respuesta.status_code != 200:
        print(f"No se pudo refrescar el token de Mercantil. HTTP {respuesta.status_code}")
        print(f"Preview refresh: {vista_previa_respuesta(respuesta)}")
        return False

    try:
        payload_respuesta = respuesta.json()
    except ValueError:
        print("La respuesta de refresh token no devolvio JSON valido.")
        return False

    nuevo_access_token = payload_respuesta.get("access_token")
    nuevo_refresh_token = payload_respuesta.get("refresh_token")

    if not isinstance(nuevo_access_token, str) or not nuevo_access_token.strip():
        print("La respuesta de refresh token no devolvio access_token.")
        return False

    contexto_auth["token"] = nuevo_access_token.strip()
    if isinstance(nuevo_refresh_token, str) and nuevo_refresh_token.strip():
        contexto_auth["refresh_token"] = nuevo_refresh_token.strip()

    os.environ["MA_TOKEN"] = contexto_auth["token"] or ""
    if contexto_auth.get("refresh_token"):
        os.environ["MA_REFRESH_TOKEN"] = contexto_auth["refresh_token"] or ""

    print("Access token de Mercantil renovado correctamente.")
    return True


def crear_headers_desde_contexto(contexto_auth: dict[str, str | None]) -> dict[str, str]:
    """Construye headers autenticados a partir de un contexto de auth ya resuelto."""
    token = (contexto_auth.get("token") or "").strip()
    api_key = (contexto_auth.get("api_key") or "").strip()

    if not token:
        raise RuntimeError("MA_TOKEN not defined in environment variables")
    if not api_key:
        raise RuntimeError("MA_API_KEY not defined in environment variables")

    return {
        "Authorization": f"Bearer {token}",
        "Ocp-Apim-Subscription-Key": api_key,
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://servicios.mercantilandina.com.ar",
        "Referer": "https://servicios.mercantilandina.com.ar/",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/146.0.0.0 Safari/537.36"
        ),
        "x-requested-with": "XMLHttpRequest",
    }


def vista_previa_respuesta(respuesta: requests.Response) -> str:
    """Devuelve una vista previa compacta del body para diagnostico."""
    texto = respuesta.text.strip().replace("\n", " ")
    if not texto:
        return "<sin contenido>"
    return texto[:220]


def consultar_ubicaciones(
    prefix: int,
    *,
    headers: dict[str, str],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Consulta ubicaciones por prefijo postal y devuelve lista + metadatos."""
    try:
        respuesta = requests.get(
            BASE_URL,
            params={"ubicacion": str(prefix)},
            headers=headers,
            timeout=TIMEOUT,
        )
    except requests.RequestException as error:
        return [], {
            "prefix": prefix,
            "status_code": None,
            "content_type": None,
            "total_registros": 0,
            "error": f"request_error: {error}",
            "preview": None,
        }

    content_type = respuesta.headers.get("content-type", "<sin content-type>")

    if respuesta.status_code != 200:
        return [], {
            "prefix": prefix,
            "status_code": respuesta.status_code,
            "content_type": content_type,
            "total_registros": 0,
            "error": "http_error",
            "preview": vista_previa_respuesta(respuesta),
        }

    try:
        payload = respuesta.json()
    except ValueError:
        return [], {
            "prefix": prefix,
            "status_code": 200,
            "content_type": content_type,
            "total_registros": 0,
            "error": "invalid_json",
            "preview": vista_previa_respuesta(respuesta),
        }

    ubicaciones = payload.get("listaUbicacionZonaRiesgo", [])
    if not isinstance(ubicaciones, list):
        return [], {
            "prefix": prefix,
            "status_code": 200,
            "content_type": content_type,
            "total_registros": payload.get("totalRegistros", 0),
            "error": "invalid_list",
            "preview": vista_previa_respuesta(respuesta),
        }

    return [item for item in ubicaciones if isinstance(item, dict)], {
        "prefix": prefix,
        "status_code": 200,
        "content_type": content_type,
        "total_registros": payload.get("totalRegistros", 0),
        "error": None,
        "preview": None,
    }


def normalizar_ubicacion(item: dict[str, Any]) -> dict[str, Any] | None:
    """Transforma la respuesta de Mercantil al esquema esperado por Supabase."""
    localidad_codigo = item.get("localidadCodigo")
    if not localidad_codigo:
        return None

    inder = item.get("inder")
    ubicacion = int(inder) if isinstance(inder, int) or (isinstance(inder, str) and inder.isdigit()) else None
    localidad_codigo_str = str(localidad_codigo)

    return {
        "codigo_postal": item.get("codigoPostal"),
        "localidad_codigo": localidad_codigo_str,
        "ubicacion": ubicacion,
        "localidad_nombre": item.get("localidadNombre"),
        "provincia_codigo": item.get("provinciaCodigo"),
        "provincia_nombre": item.get("provinciaNombre"),
    }


def dividir_en_lotes(registros: list[dict[str, Any]], tamano_lote: int) -> list[list[dict[str, Any]]]:
    """Divide una lista de registros en lotes para upsert mas eficiente."""
    return [registros[indice : indice + tamano_lote] for indice in range(0, len(registros), tamano_lote)]


def upsert_ubicaciones(cliente: Client, ubicaciones: list[dict[str, Any]]) -> int:
    """Realiza upsert logico por `localidad_codigo` sin depender de constraints SQL."""
    if not ubicaciones:
        return 0

    total_upsert = 0
    for lote in dividir_en_lotes(ubicaciones, TAMANO_LOTE):
        codigos = [item["localidad_codigo"] for item in lote if item.get("localidad_codigo")]
        respuesta_existentes = (
            cliente.table("ubicaciones")
            .select("localidad_codigo")
            .in_("localidad_codigo", codigos)
            .execute()
        )
        existentes = {
            item["localidad_codigo"]
            for item in (getattr(respuesta_existentes, "data", None) or [])
            if isinstance(item, dict) and item.get("localidad_codigo")
        }

        nuevos = [item for item in lote if item.get("localidad_codigo") not in existentes]
        actualizaciones = [item for item in lote if item.get("localidad_codigo") in existentes]

        if nuevos:
            cliente.table("ubicaciones").insert(nuevos).execute()
            total_upsert += len(nuevos)

        for item in actualizaciones:
            localidad_codigo = item.get("localidad_codigo")
            payload_actualizacion = dict(item)
            cliente.table("ubicaciones").update(payload_actualizacion).eq("localidad_codigo", localidad_codigo).execute()
            total_upsert += 1

    return total_upsert


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    cliente = crear_cliente_supabase()
    contexto_auth = crear_contexto_autenticacion_mercantil()
    if not contexto_auth.get("token"):
        iniciar_sesion_con_credenciales(contexto_auth)
    if contexto_auth.get("refresh_token"):
        refrescar_access_token(contexto_auth)
    headers_mercantil = crear_headers_desde_contexto(contexto_auth)

    ubicaciones_unicas: dict[str, dict[str, Any]] = {}
    procesados = 0
    resumen_estados: dict[str, int] = {}
    respuestas_exitosas = 0
    total_registros_reportados = 0
    muestras_error = 0
    total_flush_insertado = 0

    print("Sincronizacion de ubicaciones Mercantil iniciada.")
    print("Token cargado:", bool(contexto_auth.get("token")))
    print("Refresh token cargado:", bool(contexto_auth.get("refresh_token")))
    print("API key cargada:", bool(contexto_auth.get("api_key")))
    print("Se imprimira un resumen cada 100 prefijos y hasta 5 muestras de error.")
    print(f"Flush incremental configurado cada {INTERVALO_FLUSH_PREFIJOS} prefijos.")

    for prefix in range(PREFIJO_INICIAL, PREFIJO_FINAL + 1):
        resultados, meta = consultar_ubicaciones(prefix, headers=headers_mercantil)
        if meta["status_code"] == 401 and contexto_auth.get("refresh_token"):
            print(f"401 detectado en prefix {prefix}. Intentando renovar token y reintentar una vez.")
            if refrescar_access_token(contexto_auth):
                headers_mercantil = crear_headers_desde_contexto(contexto_auth)
                resultados, meta = consultar_ubicaciones(prefix, headers=headers_mercantil)

        estado = str(meta["status_code"]) if meta["status_code"] is not None else meta["error"] or "desconocido"
        resumen_estados[estado] = resumen_estados.get(estado, 0) + 1

        if meta["status_code"] == 200 and meta["error"] is None:
            respuestas_exitosas += 1
            total_registros_reportados += int(meta["total_registros"] or 0)
        elif muestras_error < MAX_MUESTRAS_ERROR:
            print(
                f"Muestra error {muestras_error + 1}: prefix={prefix} "
                f"status={meta['status_code']} error={meta['error']} "
                f"content_type={meta['content_type']}"
            )
            if meta["preview"]:
                print(f"Preview: {meta['preview']}")
            muestras_error += 1

        for item in resultados:
            ubicacion_normalizada = normalizar_ubicacion(item)
            if ubicacion_normalizada is None:
                continue
            ubicaciones_unicas[ubicacion_normalizada["localidad_codigo"]] = ubicacion_normalizada

        procesados += 1
        if procesados % 100 == 0:
            estados_ordenados = ", ".join(
                f"{clave}={valor}" for clave, valor in sorted(resumen_estados.items(), key=lambda item: item[0])
            )
            print(f"Processed prefix {prefix}")
            print(f"HTTP/status summary: {estados_ordenados}")
            print(f"Successful responses: {respuestas_exitosas}")
            print(f"Total registros reported by API: {total_registros_reportados}")
            print(f"Total locations collected: {len(ubicaciones_unicas)}")
            print(f"Total upserted so far: {total_flush_insertado}")

        if procesados % INTERVALO_FLUSH_PREFIJOS == 0 and ubicaciones_unicas:
            insertadas = upsert_ubicaciones(cliente, list(ubicaciones_unicas.values()))
            total_flush_insertado += insertadas
            print(
                f"Flush parcial ejecutado en prefix {prefix}. "
                f"Registros enviados en este flush: {insertadas}"
            )
            ubicaciones_unicas.clear()

    registros = list(ubicaciones_unicas.values())
    total_insertadas = upsert_ubicaciones(cliente, registros)
    total_flush_insertado += total_insertadas

    estados_ordenados = ", ".join(
        f"{clave}={valor}" for clave, valor in sorted(resumen_estados.items(), key=lambda item: item[0])
    )
    print(f"Final status summary: {estados_ordenados}")
    print(f"Registros enviados en flush final: {total_insertadas}")
    print(f"Total unique localidades inserted: {total_flush_insertado}")
    logger.info("ubicaciones_sync", extra={"registros_insertados": total_flush_insertado})


if __name__ == "__main__":
    main()

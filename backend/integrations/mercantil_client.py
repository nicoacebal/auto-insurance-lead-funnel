"""Mercantil API client.

Responsible for interacting with Mercantil Andina APIs including:

* vehicle catalog lookup
* usos catalog
* coverage availability
"""

from __future__ import annotations

import logging
import os
from typing import Any
from urllib.parse import urljoin

from .auth.mercantil_auth import MercantilAuthManager

logger = logging.getLogger(__name__)

BASE_URL_DEFAULT = "https://productos.mercantilandina.com.ar"
MA_API_BASE_URL = "https://api.mercantilandina.com.ar"
TIMEOUT_DEFAULT = 30
PRODUCTOS_TECNICOS_ENDPOINT = "/productos-coberturas-api/v1/productos-tecnicos-suscripciones"


class MercantilClient:
    """Cliente HTTP para consumir endpoints tecnicos de Mercantil Andina."""

    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout: int = TIMEOUT_DEFAULT,
    ) -> None:
        self.timeout = timeout
        self.auth = MercantilAuthManager(timeout=timeout)
        self.base_url = (base_url or os.getenv("MA_PORTAL_BASE_URL") or BASE_URL_DEFAULT).rstrip("/")

    def _request_json(
        self,
        endpoint: str,
        *,
        method: str = "GET",
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
        empty_on_400: Any | None = None,
        base_url: str | None = None,
    ) -> Any:
        """Ejecuta una llamada HTTP autenticada y devuelve su contenido JSON."""
        request_base_url = (base_url or self.base_url).rstrip("/")
        url = urljoin(f"{request_base_url}/", endpoint.lstrip("/"))
        logger.info(
            "mercantil_request_started",
            extra={
                "endpoint": endpoint,
                "method": method,
                "params": params or {},
                "has_json_body": bool(json_body),
                "base_url": request_base_url,
            },
        )

        try:
            respuesta = self.auth.handle_request(method, url, params=params, json_body=json_body)
        except Exception:
            logger.exception(
                "mercantil_request_failed",
                extra={"endpoint": endpoint, "params": params or {}, "base_url": request_base_url},
            )
            raise

        logger.info(
            "mercantil_request_finished",
            extra={
                "endpoint": endpoint,
                "status_code": respuesta.status_code,
                "content_type": respuesta.headers.get("content-type"),
                "base_url": request_base_url,
            },
        )

        if respuesta.status_code in (401, 403):
            raise RuntimeError("Mercantil API returned 401/403. Token may be invalid or expired.")

        if respuesta.status_code == 400 and empty_on_400 is not None:
            return empty_on_400

        respuesta.raise_for_status()
        try:
            return respuesta.json()
        except ValueError:
            return None

    def crear_cotizacion(self, payload: dict[str, Any]) -> Any:
        """Ejecuta una cotizacion vehicular contra el endpoint principal de Mercantil."""
        return self._request_json(
            "/api_vehiculo_cotizador/v2/cotizaciones",
            method="POST",
            json_body=payload,
        )

    @staticmethod
    def _normalizar_vehiculo(item: dict[str, Any]) -> dict[str, Any]:
        """Normaliza un vehiculo del catalogo a un contrato interno minimo."""
        marca = item.get("marca") if isinstance(item.get("marca"), dict) else {}
        modelo = item.get("modelo") if isinstance(item.get("modelo"), dict) else {}
        version = item.get("version") if isinstance(item.get("version"), dict) else {}
        tipo = item.get("tipo") if isinstance(item.get("tipo"), dict) else {}

        return {
            "id": item.get("id"),
            "marca": marca.get("descripcion") or item.get("marca"),
            "modelo": modelo.get("descripcion") or item.get("modelo"),
            "version": version.get("descripcion") or item.get("version"),
            "anio": (
                item.get("anio")
                or item.get("fabricado")
                or item.get("anio_modelo")
                or item.get("ano")
            ),
            "tipo": tipo.get("descripcion") or item.get("tipo"),
            "payload": item,
        }

    @staticmethod
    def _normalizar_uso(item: dict[str, Any]) -> dict[str, Any]:
        """Normaliza un registro de uso a una estructura minima consistente."""
        return {
            "id": item.get("id") or item.get("codigo") or item.get("idUso"),
            "codigo": item.get("codigo") or item.get("id") or item.get("idUso"),
            "descripcion": (
                item.get("descripcion")
                or item.get("nombre")
                or item.get("detalle")
                or item.get("desc")
            ),
            "payload": item,
        }

    def buscar_vehiculos(self, descripcion: str, anio: int | str) -> list[dict[str, Any]]:
        """Consulta el catalogo vehicular asegurables por descripcion y anio."""
        payload = self._request_json(
            "/api_integracion_productos/vehiculos/marca-modelo",
            params={
                "descripcion": descripcion,
                "fabricado": str(anio),
                "page": 0,
                "size": 5000,
                "tipo": "1;2;3;8;9;21;4;5;6;17",
                "conValor": "false",
            },
            empty_on_400={"vehiculos": []},
        )
        vehiculos = payload.get("vehiculos", [])
        if not isinstance(vehiculos, list):
            raise RuntimeError("Mercantil vehicle catalog response does not include a valid 'vehiculos' list.")
        return [self._normalizar_vehiculo(item) for item in vehiculos if isinstance(item, dict)]

    def obtener_usos(self) -> list[dict[str, Any]]:
        """Obtiene y normaliza el catalogo de usos de vehiculos."""
        payload = self._request_json("/api_ramo/usos-vehiculos")

        if isinstance(payload, list):
            registros = payload
        elif isinstance(payload, dict):
            registros = payload.get("usos") or payload.get("data") or payload.get("items") or []
        else:
            registros = []

        if not isinstance(registros, list):
            raise RuntimeError("Mercantil usos response does not contain a valid list.")

        return [self._normalizar_uso(item) for item in registros if isinstance(item, dict)]

    def obtener_coberturas(self, params: dict[str, Any]) -> Any:
        """Consulta coberturas tecnicas segun los parametros del vehiculo y operacion."""
        params_requeridos = [
            "antiguedad",
            "carroceria_tipo",
            "categoria_tipo",
            "vehiculo_tipo",
            "uso_tipo",
            "suma_asegurada",
            "no_rodamiento",
            "productor_id",
            "ramo_codigo",
            "fecha",
            "localidad_codigo",
        ]
        faltantes = [campo for campo in params_requeridos if campo not in params]
        if faltantes:
            raise RuntimeError(
                "Missing required Mercantil coverage params: " + ", ".join(sorted(faltantes))
            )

        return self._request_json(
            PRODUCTOS_TECNICOS_ENDPOINT,
            params=params,
            base_url=MA_API_BASE_URL,
        )


__all__ = ["MercantilClient"]

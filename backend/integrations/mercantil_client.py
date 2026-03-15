"""Mercantil API client.

Responsible for interacting with Mercantil Andina APIs including:

* vehicle catalog lookup
* usos catalog
* coverage availability
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import requests
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

RUTA_RAIZ = Path(__file__).resolve().parents[2]
RUTA_ENV = RUTA_RAIZ / ".env"
BASE_URL_DEFAULT = "https://productos.mercantilandina.com.ar"
TIMEOUT_DEFAULT = 30


def _cargar_dotenv() -> None:
    """Carga variables de entorno desde el repositorio si el archivo existe."""
    if RUTA_ENV.exists():
        load_dotenv(dotenv_path=RUTA_ENV)
    else:
        load_dotenv()


class MercantilClient:
    """Cliente HTTP para consumir endpoints tecnicos de Mercantil Andina."""

    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout: int = TIMEOUT_DEFAULT,
    ) -> None:
        _cargar_dotenv()

        self.base_url = (base_url or os.getenv("MA_PORTAL_BASE_URL") or BASE_URL_DEFAULT).rstrip("/")
        self.timeout = timeout
        self.token = (os.getenv("MA_TOKEN") or "").strip()
        self.api_key = (os.getenv("MA_API_KEY") or "").strip()

        if not self.token:
            raise RuntimeError("MA_TOKEN not defined in environment variables")
        if not self.api_key:
            raise RuntimeError("MA_API_KEY not defined in environment variables")

        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.token}",
                "ocp-apim-subscription-key": self.api_key,
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
        )

    def _request_json(
        self,
        endpoint: str,
        *,
        params: dict[str, Any] | None = None,
        empty_on_400: Any | None = None,
    ) -> Any:
        """Ejecuta una llamada GET y devuelve su contenido JSON."""
        url = urljoin(f"{self.base_url}/", endpoint.lstrip("/"))
        logger.info("mercantil_request_started %s", {"endpoint": endpoint, "params": params or {}})

        try:
            respuesta = self.session.get(url, params=params, timeout=self.timeout)
        except requests.RequestException:
            logger.exception("mercantil_request_failed %s", {"endpoint": endpoint, "params": params or {}})
            raise

        logger.info(
            "mercantil_request_finished %s",
            {
                "endpoint": endpoint,
                "status_code": respuesta.status_code,
                "content_type": respuesta.headers.get("content-type"),
            },
        )

        if respuesta.status_code in (401, 403):
            raise RuntimeError("Mercantil API returned 401/403. Token may be invalid or expired.")

        if respuesta.status_code == 400 and empty_on_400 is not None:
            return empty_on_400

        respuesta.raise_for_status()

        try:
            return respuesta.json()
        except ValueError as error:
            logger.exception("mercantil_invalid_json %s", {"endpoint": endpoint})
            raise RuntimeError(f"Mercantil API returned non-JSON response for {endpoint}") from error

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
        return vehiculos

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
            "/productos-coberturas-api/v1/productos-tecnicos-suscripciones",
            params=params,
        )


__all__ = ["MercantilClient"]

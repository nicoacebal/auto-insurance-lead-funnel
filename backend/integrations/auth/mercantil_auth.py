"""Mercantil authentication lifecycle manager based on Keycloak OAuth2."""

from __future__ import annotations

import logging
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

RUTA_RAIZ = Path(__file__).resolve().parents[3]
RUTA_ENV = RUTA_RAIZ / ".env"
TOKEN_URL = "https://idm.mercantilandina.com.ar/auth/realms/meran/protocol/openid-connect/token"
TIMEOUT_DEFAULT = 30


def _cargar_dotenv() -> None:
    """Carga variables de entorno desde la raiz del repositorio."""
    if RUTA_ENV.exists():
        load_dotenv(dotenv_path=RUTA_ENV)
    else:
        load_dotenv()


class MercantilAuthManager:
    """Administra autenticacion, refresh y headers autorizados de Mercantil."""

    def __init__(self, *, timeout: int = TIMEOUT_DEFAULT) -> None:
        _cargar_dotenv()

        self.timeout = timeout
        self.access_token = (os.getenv("MA_TOKEN") or "").strip()
        self.api_key = (os.getenv("MA_API_KEY") or "").strip()
        self.refresh_token = (os.getenv("MA_REFRESH_TOKEN") or "").strip()
        self.client_id = (os.getenv("MA_CLIENT_ID") or "").strip()
        self.username = (os.getenv("MA_USERNAME") or "").strip()
        self.password = (os.getenv("MA_PASSWORD") or "").strip()
        self.expires_in: int | None = None

        if not self.api_key:
            raise RuntimeError("MA_API_KEY not defined in environment variables")
        if (self.refresh_token or self.username or self.password) and not self.client_id:
            raise RuntimeError("MA_CLIENT_ID not defined in environment variables")
        if not self.access_token and not (self.username and self.password):
            raise RuntimeError("MA_TOKEN not defined in environment variables")
        if not self.refresh_token:
            logger.warning("Token refresh not configured. Manual token renewal required.")

    def _almacenar_tokens(self, data: dict) -> bool:
        """Actualiza tokens en memoria a partir de una respuesta Keycloak."""
        nuevo_access_token = data.get("access_token")
        nuevo_refresh_token = data.get("refresh_token")
        expires_in = data.get("expires_in")

        if not isinstance(nuevo_access_token, str) or not nuevo_access_token.strip():
            return False

        self.access_token = nuevo_access_token.strip()
        if isinstance(nuevo_refresh_token, str) and nuevo_refresh_token.strip():
            self.refresh_token = nuevo_refresh_token.strip()
        if isinstance(expires_in, int):
            self.expires_in = expires_in
        return True

    def login(self) -> bool:
        """Obtiene nuevos tokens usando password grant."""
        if not self.username or not self.password or not self.client_id:
            logger.error("auth failure")
            return False

        payload = {
            "grant_type": "password",
            "client_id": self.client_id,
            "username": self.username,
            "password": self.password,
        }

        try:
            respuesta = requests.post(
                TOKEN_URL,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data=payload,
                timeout=self.timeout,
            )
        except requests.RequestException:
            logger.exception("auth failure")
            return False

        if respuesta.status_code != 200:
            logger.error("auth failure")
            return False

        try:
            data = respuesta.json()
        except ValueError:
            logger.exception("auth failure")
            return False

        if not self._almacenar_tokens(data):
            logger.error("auth failure")
            return False

        logger.info("login success")
        return True

    def refresh_access_token(self) -> bool:
        """Renueva access token usando refresh token si esta disponible."""
        if not self.refresh_token:
            logger.error("refresh failed")
            return False

        payload = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "refresh_token": self.refresh_token,
        }

        try:
            respuesta = requests.post(
                TOKEN_URL,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data=payload,
                timeout=self.timeout,
            )
        except requests.RequestException:
            logger.exception("refresh failed")
            return False

        if respuesta.status_code != 200:
            logger.error("refresh failed")
            return False

        try:
            data = respuesta.json()
        except ValueError:
            logger.exception("refresh failed")
            return False

        if not self._almacenar_tokens(data):
            logger.error("refresh failed")
            return False

        logger.info("token refreshed")
        return True

    def get_access_token(self) -> str:
        """Devuelve un access token util, intentando login si falta."""
        if self.access_token:
            return self.access_token
        if self.login():
            return self.access_token
        raise RuntimeError("auth failure")

    def authorized_headers(self) -> dict[str, str]:
        """Devuelve headers autorizados para requests a Mercantil."""
        return {
            "Authorization": f"Bearer {self.get_access_token()}",
            "Ocp-Apim-Subscription-Key": self.api_key,
            "Accept": "application/json",
            "Origin": "https://servicios.mercantilandina.com.ar",
            "Referer": "https://servicios.mercantilandina.com.ar/",
            "User-Agent": "Mozilla/5.0",
        }

    def handle_request(
        self,
        method: str,
        url: str,
        params: dict | None = None,
        json_body: dict | None = None,
        data: dict | None = None,
    ) -> requests.Response:
        """Ejecuta request autorizada y reintenta una vez ante 401 con refresh."""
        respuesta = requests.request(
            method=method,
            url=url,
            params=params,
            json=json_body,
            data=data,
            headers=self.authorized_headers(),
            timeout=self.timeout,
        )

        if respuesta.status_code == 401:
            logger.warning("401 detected")
            reautenticado = False
            if self.refresh_token:
                reautenticado = self.refresh_access_token()
            if not reautenticado:
                reautenticado = self.login()
            if reautenticado:
                respuesta = requests.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json_body,
                    data=data,
                    headers=self.authorized_headers(),
                    timeout=self.timeout,
                )
            else:
                logger.error("auth failure")

        return respuesta


__all__ = ["MercantilAuthManager"]

"""Cliente central de Supabase para el backend."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from supabase import Client, create_client

logger = logging.getLogger(__name__)

# Carga variables de entorno desde .env en la raiz del repositorio.
RUTA_RAIZ = Path(__file__).resolve().parents[3]
RUTA_ENV = RUTA_RAIZ / ".env"
if RUTA_ENV.exists():
    load_dotenv(dotenv_path=RUTA_ENV)
else:
    load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()


def _crear_cliente_supabase() -> Client | None:
    """Crea el cliente oficial de Supabase si la configuracion esta completa."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.warning("Supabase no esta configurado: faltan SUPABASE_URL o SUPABASE_KEY.")
        return None

    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception:
        logger.exception("No se pudo crear el cliente de Supabase.")
        return None


# Cliente compartido para reutilizar en los servicios de backend.
cliente_supabase = _crear_cliente_supabase()

__all__ = ["cliente_supabase", "SUPABASE_URL", "SUPABASE_KEY"]

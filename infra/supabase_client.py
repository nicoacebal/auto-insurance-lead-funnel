"""Shared Supabase client for the production backend."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from supabase import Client, create_client

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = REPO_ROOT / ".env"

if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()


def _crear_cliente_supabase() -> Client | None:
    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.warning("Supabase no esta configurado: faltan SUPABASE_URL o SUPABASE_KEY.")
        return None

    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception:  # noqa: BLE001
        logger.exception("No se pudo crear el cliente de Supabase.")
        return None


cliente_supabase = _crear_cliente_supabase()

__all__ = ["cliente_supabase", "SUPABASE_URL", "SUPABASE_KEY"]

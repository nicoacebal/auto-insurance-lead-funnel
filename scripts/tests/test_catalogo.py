"""Smoke test para el endpoint de catalogo de Mercantil Andina."""

from __future__ import annotations

import os

import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("MA_TOKEN")
API_KEY = os.getenv("MA_API_KEY")

if not TOKEN:
    raise RuntimeError("MA_TOKEN not defined in environment variables")

if not API_KEY:
    raise RuntimeError("MA_API_KEY not defined in environment variables")

URL = "https://productos.mercantilandina.com.ar/api_integracion_productos/vehiculos/marca-modelo"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Ocp-Apim-Subscription-Key": API_KEY,
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://servicios.mercantilandina.com.ar",
    "Referer": "https://servicios.mercantilandina.com.ar/",
    "User-Agent": "Mozilla/5.0",
}

PARAMS = {
    "descripcion": "VOL",
    "fabricado": "2025",
    "page": 0,
    "size": 5000,
    "tipo": "1;2;3;8;9;21;4;5;6;17",
    "conValor": "false",
}

respuesta = requests.get(URL, headers=HEADERS, params=PARAMS, timeout=30)

print("STATUS:", respuesta.status_code)
print(respuesta.text[:500])

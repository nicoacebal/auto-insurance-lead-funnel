"""Descubre endpoints potenciales del catalogo de Mercantil Andina.

El script genera combinaciones de rutas comunes bajo:
- vehiculos/*
- catalogo/*
- productos/*

Para cada combinacion:
- envia GET,
- imprime status y preview,
- guarda respuestas JSON validas a disco,
- resume endpoints que respondieron 200 con JSON.

Admite headers opcionales por variables de entorno:
- MA_TOKEN
- MA_API_KEY
"""

from __future__ import annotations

import itertools
import json
import os
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

BASE_URL = "https://productos.mercantilandina.com.ar/api_integracion_productos/"
DIRECTORIO_SALIDA = Path("scripts") / "salidas_api_mercantil" / "descubrimiento"
TIMEOUT = 15

PREFIJOS = ["vehiculos", "catalogo", "productos"]
SEGMENTOS = [
    "marcas",
    "marca",
    "modelos",
    "modelo",
    "tipos",
    "tipo",
    "tipo-vehiculo",
    "usos",
    "uso",
    "usos-vehiculos",
    "subusos",
    "subusos-vehiculos",
    "catalogo",
    "listado",
    "lista",
]


def cargar_headers() -> dict[str, str]:
    """Construye headers base y agrega autenticacion opcional si existe."""
    load_dotenv()

    headers = {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0",
    }

    token = os.getenv("MA_TOKEN", "").strip()
    api_key = os.getenv("MA_API_KEY", "").strip()

    if token:
        headers["Authorization"] = f"Bearer {token}"
    if api_key:
        headers["ocp-apim-subscription-key"] = api_key

    return headers


def construir_endpoints() -> list[str]:
    """Genera rutas candidatas unicas usando combinaciones simples."""
    endpoints = set()

    for prefijo in PREFIJOS:
        for segmento in SEGMENTOS:
            endpoints.add(f"{prefijo}/{segmento}")

        for segmento_1, segmento_2 in itertools.product(SEGMENTOS, repeat=2):
            if segmento_1 == segmento_2:
                continue
            endpoints.add(f"{prefijo}/{segmento_1}/{segmento_2}")

    return sorted(endpoints)


def vista_previa_respuesta(respuesta: requests.Response) -> str:
    """Devuelve una vista previa corta y segura del cuerpo."""
    texto = respuesta.text.strip().replace("\n", " ")
    if not texto:
        return "<sin contenido>"
    return texto[:220]


def guardar_json(endpoint: str, data: Any) -> Path:
    """Guarda una respuesta JSON valida en disco."""
    DIRECTORIO_SALIDA.mkdir(parents=True, exist_ok=True)
    ruta = DIRECTORIO_SALIDA / f"{endpoint.replace('/', '_')}.json"
    ruta.write_text(json.dumps(data, ensure_ascii=True, indent=2), encoding="utf-8")
    return ruta


def probar_endpoint(session: requests.Session, endpoint: str) -> tuple[int | None, bool]:
    """Prueba un endpoint y guarda su JSON si responde correctamente."""
    url = f"{BASE_URL}{endpoint}"
    try:
        respuesta = session.get(url, timeout=TIMEOUT)
    except requests.RequestException as error:
        print(f"{endpoint:<40} ERROR {error}")
        return None, False

    print(f"{endpoint:<40} {respuesta.status_code} {vista_previa_respuesta(respuesta)}")

    if respuesta.status_code != 200:
        return respuesta.status_code, False

    try:
        data = respuesta.json()
    except ValueError:
        return respuesta.status_code, False

    ruta = guardar_json(endpoint, data)
    print(f"  -> JSON detectado y guardado en {ruta}")
    return respuesta.status_code, True


def main() -> None:
    headers = cargar_headers()
    session = requests.Session()
    session.headers.update(headers)

    endpoints = construir_endpoints()
    endpoints_json: list[str] = []

    print("=== Descubrimiento de endpoints ===")
    print(f"Base URL: {BASE_URL}")
    print(f"Candidatos generados: {len(endpoints)}")
    print(f"Salida JSON: {DIRECTORIO_SALIDA}")
    print()

    for endpoint in endpoints:
        _, tiene_json = probar_endpoint(session, endpoint)
        if tiene_json:
            endpoints_json.append(endpoint)

    print("\n=== Endpoints con JSON 200 ===")
    if endpoints_json:
        for endpoint in endpoints_json:
            print(f"- {endpoint}")
    else:
        print("No se detectaron endpoints JSON 200 en esta corrida.")


if __name__ == "__main__":
    main()

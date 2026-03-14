"""Prueba endpoints candidatos del catalogo vehicular de Mercantil Andina.

El script:
- recorre una lista de endpoints conocidos o sospechados,
- envia requests GET,
- imprime estado HTTP y una vista previa de la respuesta,
- guarda en disco las respuestas JSON validas.

Admite headers opcionales por variables de entorno si la API los requiere:
- MA_TOKEN
- MA_API_KEY
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

BASE_URL = "https://productos.mercantilandina.com.ar/api_integracion_productos/"
DIRECTORIO_SALIDA = Path("scripts") / "salidas_api_mercantil"
TIMEOUT = 10

load_dotenv()

API_KEY = os.getenv("MA_API_KEY", "8cb15b592fe74272bb73ac1cd5cc3d2e")
TOKEN = os.getenv("MA_TOKEN")

headers = {
    "accept": "application/json, text/plain, */*",
    "user-agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36"
    ),
    "origin": "https://servicios.mercantilandina.com.ar",
    "referer": "https://servicios.mercantilandina.com.ar/",
    "x-requested-with": "XMLHttpRequest",
    "Ocp-Apim-Subscription-Key": API_KEY,
}

if TOKEN:
    headers["Authorization"] = f"Bearer {TOKEN}"

ENDPOINTS_CANDIDATOS = [
    "vehiculos/marcas",
    "vehiculos/marca",
    "vehiculos/modelos",
    "vehiculos/tipos",
    "vehiculos/catalogo",
    "vehiculos/listado",
    "vehiculos/tipo-vehiculo",
    "vehiculos/usos-vehiculos",
    "vehiculos/subusos-vehiculos",
]

def vista_previa_respuesta(respuesta: requests.Response) -> str:
    """Devuelve una vista previa corta y segura del cuerpo."""
    texto = respuesta.text.strip().replace("\n", " ")
    if not texto:
        return "<sin contenido>"
    return texto[:220]


def guardar_json(endpoint: str, data: Any) -> Path:
    """Guarda una respuesta JSON a disco usando un nombre de archivo estable."""
    DIRECTORIO_SALIDA.mkdir(parents=True, exist_ok=True)
    ruta = DIRECTORIO_SALIDA / f"{endpoint.replace('/', '_')}.json"
    ruta.write_text(json.dumps(data, ensure_ascii=True, indent=2), encoding="utf-8")
    return ruta


def probar_endpoint(endpoint: str) -> tuple[int | None, bool]:
    """Prueba un endpoint candidato y guarda JSON si corresponde."""
    url = f"{BASE_URL}{endpoint}"
    try:
        respuesta = requests.get(url, headers=headers, timeout=TIMEOUT)
    except requests.RequestException as error:
        print(f"{endpoint:<32} ERROR {error}")
        return None, False

    content_type = respuesta.headers.get("content-type", "<sin content-type>")
    print(f"{endpoint:<32} {respuesta.status_code:<6} {content_type}")
    print(f"  -> Preview: {vista_previa_respuesta(respuesta)}")

    if respuesta.status_code != 200:
        return respuesta.status_code, False

    try:
        data = respuesta.json()
    except ValueError:
        print("  -> Respuesta 200, pero no es JSON valido.")
        return respuesta.status_code, False

    ruta = guardar_json(endpoint, data)
    print(f"  -> JSON detectado y guardado en {ruta}")
    return respuesta.status_code, True


def main() -> None:
    print("=== Exploracion de endpoints candidatos ===")
    print(f"Base URL: {BASE_URL}")
    print(f"Salida JSON: {DIRECTORIO_SALIDA}")
    print("Using API key:", API_KEY[:6] + "...")
    print("Token loaded:", bool(TOKEN))
    print("Headers configured for Mercantil API gateway")
    print()

    endpoints_json: list[str] = []
    for endpoint in ENDPOINTS_CANDIDATOS:
        _, tiene_json = probar_endpoint(endpoint)
        if tiene_json:
            endpoints_json.append(endpoint)

    print("\n=== Resumen ===")
    if endpoints_json:
        for endpoint in endpoints_json:
            print(f"- {endpoint}")
    else:
        print("No se detectaron endpoints con respuesta JSON 200 en esta corrida.")


if __name__ == "__main__":
    main()

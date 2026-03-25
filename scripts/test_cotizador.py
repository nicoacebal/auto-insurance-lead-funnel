"""Prueba manual del endpoint local de cotizacion automotor."""

from __future__ import annotations

import json

import requests

API_URL = "http://localhost:8000/cotizar-auto"
TIMEOUT = 60


def main() -> None:
    payload = {
        "vehiculo_id": 138603,
        "anio_modelo": 2025,
        "ubicacion": 363,
        "suma_asegurada": 15000000,
    }

    try:
        respuesta = requests.post(API_URL, json=payload, timeout=TIMEOUT)
    except requests.RequestException as error:
        print("error request")
        print(str(error))
        raise SystemExit(1) from error

    print("Request payload:")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print()

    if respuesta.status_code >= 400:
        print(f"error {respuesta.status_code}")
        print(respuesta.text)
        raise SystemExit(1)

    try:
        data = respuesta.json()
    except ValueError:
        print("error invalid_json")
        print(respuesta.text)
        raise SystemExit(1)

    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

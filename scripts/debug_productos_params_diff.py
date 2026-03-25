"""Compara parametros de productos-tecnicos-suscripciones entre backend y navegador.

Archivos admitidos:
- productos_params_browser.json
- productos_params_browser.txt
- productos_params_backend.json

Si no existe `productos_params_backend.json`, intenta extraer el bloque
`PARAMETROS PRODUCTOS TECNICOS` desde `tmp_uvicorn_log.txt`.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs


REPO_ROOT = Path(__file__).resolve().parents[1]
FIELDS_OF_INTEREST = [
    "marca_tipo",
    "modelo_tipo",
    "version_tipo",
    "carroceria_tipo",
    "categoria_tipo",
    "vehiculo_tipo",
    "no_rodamiento",
    "localidad_codigo",
]


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(_read_text(path))
    if not isinstance(payload, dict):
        raise ValueError(f"{path.name} no contiene un objeto JSON.")
    return payload


def _load_querystring_text(path: Path) -> dict[str, Any]:
    raw = _read_text(path)
    if raw.startswith("?"):
        raw = raw[1:]
    if "&" not in raw and "\n" in raw:
        pairs: dict[str, Any] = {}
        for line in raw.splitlines():
            stripped = line.strip()
            if not stripped or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            pairs[key.strip()] = value.strip()
        if pairs:
            return pairs
    parsed = parse_qs(raw, keep_blank_values=True)
    return {key: values[0] if len(values) == 1 else values for key, values in parsed.items()}


def _extract_backend_from_log(path: Path) -> dict[str, Any]:
    lines = path.read_text(encoding="utf-8").splitlines()
    marker = "PARAMETROS PRODUCTOS TECNICOS"

    for index, line in enumerate(lines):
        if marker not in line:
            continue

        json_lines: list[str] = []
        opened = False
        balance = 0

        for next_line in lines[index + 1 :]:
            stripped = next_line.strip()
            if not stripped:
                continue
            if stripped.startswith("=============================="):
                if opened and balance <= 0:
                    break
                continue
            if stripped.startswith("QUERYSTRING PRODUCTOS TECNICOS"):
                break

            json_lines.append(next_line)
            balance += next_line.count("{") - next_line.count("}")
            if "{" in next_line:
                opened = True
            if opened and balance <= 0:
                break

        if json_lines:
            payload = json.loads("\n".join(json_lines))
            if isinstance(payload, dict):
                return payload

    raise FileNotFoundError("No se pudo extraer PARAMETROS PRODUCTOS TECNICOS desde tmp_uvicorn_log.txt")


def load_backend_params() -> dict[str, Any]:
    backend_json = REPO_ROOT / "productos_params_backend.json"
    if backend_json.exists():
        return _load_json(backend_json)

    uvicorn_log = REPO_ROOT / "tmp_uvicorn_log.txt"
    if uvicorn_log.exists():
        return _extract_backend_from_log(uvicorn_log)

    raise FileNotFoundError(
        "No se encontro productos_params_backend.json ni tmp_uvicorn_log.txt con el bloque de parametros."
    )


def load_browser_params() -> dict[str, Any]:
    browser_json = REPO_ROOT / "productos_params_browser.json"
    if browser_json.exists():
        return _load_json(browser_json)

    browser_txt = REPO_ROOT / "productos_params_browser.txt"
    if browser_txt.exists():
        return _load_querystring_text(browser_txt)

    raise FileNotFoundError(
        "No se encontro productos_params_browser.json ni productos_params_browser.txt en la raiz del repo."
    )


def describe_match(backend_value: Any, browser_value: Any) -> str:
    if backend_value == browser_value:
        return "OK"
    return "DIFF"


def main() -> None:
    backend_params = load_backend_params()
    browser_params = load_browser_params()

    print("COMPARACION PARAMETROS PRODUCTOS")
    print("================================\n")

    for field in FIELDS_OF_INTEREST:
        backend_value = backend_params.get(field, "<missing>")
        browser_value = browser_params.get(field, "<missing>")
        status = describe_match(backend_value, browser_value)

        print(field)
        print(f"backend   : {backend_value}")
        print(f"navegador : {browser_value}")
        print(f"estado    : {status}")
        print()

    extras_browser = sorted(set(browser_params) - set(backend_params))
    extras_backend = sorted(set(backend_params) - set(browser_params))

    print("CAMPOS EXTRA EN NAVEGADOR")
    print("=========================")
    print(extras_browser if extras_browser else "ninguno")
    print()

    print("CAMPOS EXTRA EN BACKEND")
    print("=======================")
    print(extras_backend if extras_backend else "ninguno")


if __name__ == "__main__":
    main()

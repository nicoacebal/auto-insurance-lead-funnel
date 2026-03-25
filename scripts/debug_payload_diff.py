"""Herramienta de diagnostico para comparar payloads backend vs navegador.

Uso esperado:
    python scripts/debug_payload_diff.py

Archivos buscados por defecto:
    - payload_backend.json
    - payload_browser.json

Se pueden ubicar en:
    - el directorio actual
    - la raiz del repositorio
    - el directorio scripts/
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from pprint import pprint
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SEARCH_PATHS = [
    Path.cwd(),
    REPO_ROOT,
    Path(__file__).resolve().parent,
]


def ensure_deepdiff():
    """Importa deepdiff o intenta instalarlo automaticamente."""
    try:
        from deepdiff import DeepDiff  # type: ignore
    except ImportError:
        print("deepdiff no esta instalado. Intentando instalarlo...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "deepdiff"])
        from deepdiff import DeepDiff  # type: ignore
    return DeepDiff


def find_file(filename: str) -> Path:
    """Busca un archivo en ubicaciones comunes del proyecto."""
    for base_path in SEARCH_PATHS:
        candidate = base_path / filename
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        f"No se encontro {filename}. Colocalo en el directorio actual, en la raiz del repo o en scripts/."
    )


def load_json(filename: str) -> Any:
    path = find_file(filename)
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def describe_type(value: Any) -> str:
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, list):
        return "array"
    if isinstance(value, str):
        return "string"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "float"
    if value is None:
        return "null"
    return type(value).__name__


def format_path(path_parts: list[str]) -> str:
    return ".".join(path_parts) if path_parts else "<root>"


def add_issue(issues: list[dict[str, Any]], category: str, path: str, backend: Any, browser: Any) -> None:
    issues.append(
        {
            "category": category,
            "path": path,
            "backend": backend,
            "browser": browser,
        }
    )


def compare_nodes(backend: Any, browser: Any, path_parts: list[str], issues: list[dict[str, Any]]) -> None:
    path = format_path(path_parts)
    backend_type = describe_type(backend)
    browser_type = describe_type(browser)

    if backend_type != browser_type:
        category = "TYPE MISMATCH"
        if backend_type in {"object", "array"} or browser_type in {"object", "array"}:
            category = "NIVEL DE NESTING INCORRECTO"
        add_issue(issues, category, path, backend_type, browser_type)
        return

    if isinstance(browser, dict):
        browser_keys = set(browser.keys())
        backend_keys = set(backend.keys())

        for missing_key in sorted(browser_keys - backend_keys):
            add_issue(
                issues,
                "MISSING FIELD IN BACKEND",
                format_path(path_parts + [missing_key]),
                "<missing>",
                browser[missing_key],
            )

        for extra_key in sorted(backend_keys - browser_keys):
            add_issue(
                issues,
                "EXTRA FIELD IN BACKEND",
                format_path(path_parts + [extra_key]),
                backend[extra_key],
                "<missing>",
            )

        for common_key in sorted(browser_keys & backend_keys):
            compare_nodes(backend[common_key], browser[common_key], path_parts + [common_key], issues)
        return

    if isinstance(browser, list):
        if not browser and backend:
            add_issue(issues, "EXTRA ITEMS IN BACKEND", path, backend, browser)
            return

        if browser and not backend:
            add_issue(issues, "VALOR REQUERIDO NO ENVIADO", path, backend, browser)
            return

        if browser and backend:
            compare_nodes(backend[0], browser[0], path_parts + ["[0]"], issues)
        return

    if backend is None and browser is not None:
        add_issue(issues, "VALOR REQUERIDO NO ENVIADO", path, backend, browser)


def print_issue(issue: dict[str, Any]) -> None:
    print(issue["category"])
    print(issue["path"])
    print(f"backend: {issue['backend']}")
    print(f"browser: {issue['browser']}")
    print()


def main() -> None:
    backend_payload = load_json("payload_backend.json")
    browser_payload = load_json("payload_browser.json")

    issues: list[dict[str, Any]] = []
    compare_nodes(backend_payload, browser_payload, [], issues)

    print("DIFFERENCES FOUND")
    print("=================\n")

    if not issues:
        print("No se encontraron diferencias estructurales en la comparacion recursiva.\n")
    else:
        for issue in issues:
            print_issue(issue)

    DeepDiff = ensure_deepdiff()
    diff = DeepDiff(browser_payload, backend_payload, ignore_order=True, verbose_level=2)

    print("DEEPDIFF SUMMARY")
    print("================")
    if diff:
        pprint(diff)
    else:
        print("Sin diferencias detectadas por DeepDiff.")


if __name__ == "__main__":
    main()

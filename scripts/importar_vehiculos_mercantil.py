"""FASE 2 y FASE 4: descarga de catalogo Mercantil Andina y carga en Supabase.

La autenticacion contra la API se realiza mediante headers:
- Authorization: Bearer <JWT>
- ocp-apim-subscription-key: <API_KEY>
"""

from __future__ import annotations
from datetime import datetime
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import requests
from dotenv import load_dotenv
from supabase import Client, create_client

API_CATALOGO_PATH = "/api_integracion_productos/vehiculos/marca-modelo"
SALIDA_CATALOGO_PATH = Path("data") / "catalogo_vehiculos_mercantil.json"
TABLA_VEHICULOS = "vehiculos"
LOTE_INSERCION = 500
RUTA_RAIZ = Path(__file__).resolve().parents[1]
RUTA_ENV = RUTA_RAIZ / ".env"
ANIO_INICIO_CATALOGO = 1997
COMBUSTIBLES_BUSQUEDA = ["nafta", "diesel", "gnc", "hibrido", "electrico"]


@dataclass
class ConfigMercantil:
    portal_base_url: str
    token: str
    api_key: str


@dataclass(frozen=True)
class ConfigCatalogo:
    fabricado: int
    page_size: int
    tipos: str
    con_valor: bool


@dataclass(frozen=True)
class ConfigSupabase:
    url: str
    key: str


def cargar_dotenv_repositorio() -> None:
    """Carga variables de entorno desde el .env del repositorio, si existe."""
    if RUTA_ENV.exists():
        load_dotenv(dotenv_path=RUTA_ENV)
    else:
        load_dotenv()


def cargar_configuracion() -> ConfigMercantil:
    cargar_dotenv_repositorio()

    portal_base_url = os.getenv("MA_PORTAL_BASE_URL", "https://productos.mercantilandina.com.ar").strip()
    token = os.getenv("MA_TOKEN", "").strip()
    api_key = os.getenv("MA_API_KEY", "").strip()

    return ConfigMercantil(
        portal_base_url=portal_base_url,
        token=token,
        api_key=api_key,
    )


def cargar_configuracion_catalogo() -> ConfigCatalogo:
    cargar_dotenv_repositorio()

    fabricado = int(os.getenv("MA_CATALOGO_FABRICADO", str(datetime.now().year)).strip())
    page_size = int(os.getenv("MA_CATALOGO_PAGE_SIZE", "5000").strip())
    tipos = os.getenv("MA_CATALOGO_TIPOS", "1;2;3;8;9;21;4;5;6;17").strip()
    con_valor = os.getenv("MA_CATALOGO_CON_VALOR", "false").strip().lower() == "true"

    return ConfigCatalogo(
        fabricado=fabricado,
        page_size=page_size,
        tipos=tipos,
        con_valor=con_valor,
    )


def cargar_configuracion_supabase() -> ConfigSupabase | None:
    cargar_dotenv_repositorio()

    url = os.getenv("SUPABASE_URL", "").strip()
    key = os.getenv("SUPABASE_KEY", "").strip()

    if not url or not key:
        return None

    return ConfigSupabase(url=url, key=key)


def crear_sesion(config: ConfigMercantil) -> requests.Session:
    if not config.token or not config.api_key:
        raise RuntimeError(
            "Faltan MA_TOKEN o MA_API_KEY en variables de entorno. "
            "Configuralos en el archivo .env antes de ejecutar el script."
        )

    sesion = requests.Session()
    sesion.headers.update(
        {
            "Authorization": f"Bearer {config.token}",
            "ocp-apim-subscription-key": config.api_key,
            "Accept": "application/json",
            "Origin": "https://servicios.mercantilandina.com.ar",
            "Referer": "https://servicios.mercantilandina.com.ar/",
            "User-Agent": "Mozilla/5.0",
        }
    )
    return sesion


def verificar_sesion_api(sesion: requests.Session, portal_base_url: str) -> bool:
    url = urljoin(portal_base_url.rstrip("/") + "/", API_CATALOGO_PATH.lstrip("/"))
    params = {
        "descripcion": "VOL",
        "fabricado": str(datetime.now().year),
        "page": 0,
        "size": 1,
        "tipo": "1;2;3;8;9;21;4;5;6;17",
        "conValor": "false",
    }

    try:
        respuesta = sesion.get(url, params=params, timeout=30)
    except requests.RequestException as error:
        print(f"No se pudo verificar sesion contra API: {error}")
        return False

    if respuesta.status_code in (401, 403):
        print("La API respondio 401/403. El token es invalido o expiro.")
        return False

    if respuesta.status_code != 200:
        print(f"Respuesta inesperada al verificar sesion: HTTP {respuesta.status_code}")
        return False

    try:
        payload: dict[str, Any] = respuesta.json()
    except ValueError:
        print("La API respondio algo no JSON al verificar sesion.")
        return False

    if "vehiculos" not in payload:
        print("La API no devolvio el campo 'vehiculos'.")
        return False

    return True

def consultar_vehiculos(
    sesion: requests.Session,
    portal_base_url: str,
    *,
    descripcion: str,
    page: int,
    config_catalogo: ConfigCatalogo,
) -> dict[str, Any]:
    url = urljoin(portal_base_url.rstrip("/") + "/", API_CATALOGO_PATH.lstrip("/"))
    params = {
        "descripcion": descripcion,
        "fabricado": str(config_catalogo.fabricado),
        "page": page,
        "size": config_catalogo.page_size,
        "tipo": config_catalogo.tipos,
        "conValor": str(config_catalogo.con_valor).lower(),
    }

    respuesta = sesion.get(url, params=params, timeout=60)
    if respuesta.status_code in (401, 403):
        raise RuntimeError("La API respondio 401/403 durante la descarga. El token es invalido o expiro.")
    if respuesta.status_code == 200:
        payload: dict[str, Any] = respuesta.json()
        if "vehiculos" not in payload:
            raise ValueError("La respuesta de la API no contiene el campo 'vehiculos'.")
        return payload
    if respuesta.status_code == 400:
        return {"vehiculos": []}
    respuesta.raise_for_status()
    return {"vehiculos": []}


def extraer_texto(objeto: Any, clave: str = "descripcion") -> str | None:
    if isinstance(objeto, dict):
        valor = objeto.get(clave)
        if isinstance(valor, str):
            return valor.strip() or None
    if isinstance(objeto, str):
        return objeto.strip() or None
    return None


def extraer_entero_desde_campos(vehiculo: dict[str, Any], *claves: str) -> int | None:
    for clave in claves:
        valor = vehiculo.get(clave)
        if isinstance(valor, int):
            return valor
        if isinstance(valor, str) and valor.isdigit():
            return int(valor)
    return None


def normalizar_vehiculo(vehiculo: dict[str, Any]) -> dict[str, Any] | None:
    id_vehiculo = vehiculo.get("id")
    if not isinstance(id_vehiculo, int):
        return None

    return {
        "id": id_vehiculo,
        "marca": extraer_texto(vehiculo.get("marca")),
        "modelo": extraer_texto(vehiculo.get("modelo")),
        "version": extraer_texto(vehiculo.get("version")),
        "anio": extraer_entero_desde_campos(
            vehiculo,
            "anio",
            "fabricado",
            "anio_modelo",
            "ano",
        ),
        "tipo": extraer_texto(vehiculo.get("tipo")),
    }


def descargar_catalogo_completo(
    sesion: requests.Session,
    portal_base_url: str,
    config_catalogo: ConfigCatalogo,
) -> list[dict[str, Any]]:
    vehiculos_descargados: list[dict[str, Any]] = []
    anio_actual = datetime.now().year

    print("\n=== FASE 2 - Descarga del catalogo ===")
    print(
        f"Recorriendo catalogo por anio ({ANIO_INICIO_CATALOGO}-{anio_actual}) "
        "y descripcion por combustible..."
    )

    for anio in range(ANIO_INICIO_CATALOGO, anio_actual + 1):
        for combustible in COMBUSTIBLES_BUSQUEDA:
            payload = consultar_vehiculos(
                sesion,
                portal_base_url,
                descripcion=combustible,
                page=0,
                config_catalogo=ConfigCatalogo(
                    fabricado=anio,
                    page_size=config_catalogo.page_size,
                    tipos=config_catalogo.tipos,
                    con_valor=config_catalogo.con_valor,
                ),
            )

            vehiculos = payload.get("vehiculos", [])
            if not isinstance(vehiculos, list):
                raise ValueError("El campo 'vehiculos' no es una lista.")

            print(f"{anio} {combustible}: {len(vehiculos)} registros")

            for vehiculo in vehiculos:
                if not isinstance(vehiculo, dict):
                    continue
                vehiculo_normalizado = normalizar_vehiculo(vehiculo)
                if vehiculo_normalizado is None:
                    continue
                vehiculos_descargados.append(vehiculo_normalizado)

    vehiculos_unicos: dict[int, dict[str, Any]] = {}
    for vehiculo in vehiculos_descargados:
        id_vehiculo = vehiculo["id"]
        if id_vehiculo not in vehiculos_unicos:
            vehiculos_unicos[id_vehiculo] = vehiculo

    vehiculos_finales = sorted(
        vehiculos_unicos.values(),
        key=lambda item: (
            item.get("marca") or "",
            item.get("modelo") or "",
            item.get("anio") or 0,
            item["id"],
        ),
    )

    print(f"\nTotal de vehiculos unicos: {len(vehiculos_finales)}")

    return vehiculos_finales


def guardar_catalogo_local(vehiculos: list[dict[str, Any]], ruta_salida: Path) -> None:
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    contenido = {
        "total_vehiculos": len(vehiculos),
        "generado_en": datetime.now().isoformat(),
        "vehiculos": vehiculos,
    }
    ruta_salida.write_text(
        json.dumps(contenido, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )


def cargar_catalogo_local(ruta_entrada: Path) -> list[dict[str, Any]]:
    if not ruta_entrada.exists():
        raise FileNotFoundError(f"No existe el archivo de catalogo: {ruta_entrada}")

    contenido = json.loads(ruta_entrada.read_text(encoding="utf-8"))
    vehiculos = contenido.get("vehiculos", [])
    if not isinstance(vehiculos, list):
        raise ValueError("El archivo de catalogo no contiene una lista valida en 'vehiculos'.")
    return [vehiculo for vehiculo in vehiculos if isinstance(vehiculo, dict)]


def crear_cliente_supabase(config_supabase: ConfigSupabase) -> Client:
    return create_client(config_supabase.url, config_supabase.key)


def dividir_en_lotes(elementos: list[Any], tamano_lote: int) -> list[list[Any]]:
    return [elementos[indice : indice + tamano_lote] for indice in range(0, len(elementos), tamano_lote)]


def obtener_ids_existentes(cliente: Client, ids_vehiculos: list[int]) -> set[int]:
    ids_existentes: set[int] = set()

    for lote_ids in dividir_en_lotes(ids_vehiculos, LOTE_INSERCION):
        respuesta = (
            cliente.table(TABLA_VEHICULOS)
            .select("id_vehiculo")
            .in_("id_vehiculo", lote_ids)
            .execute()
        )
        registros = getattr(respuesta, "data", None) or []
        for registro in registros:
            id_vehiculo = registro.get("id_vehiculo")
            if isinstance(id_vehiculo, int):
                ids_existentes.add(id_vehiculo)

    return ids_existentes


def insertar_vehiculos_nuevos(cliente: Client, vehiculos: list[dict[str, Any]]) -> int:
    total_insertados = 0

    for lote in dividir_en_lotes(vehiculos, LOTE_INSERCION):
        cliente.table(TABLA_VEHICULOS).insert(lote).execute()
        total_insertados += len(lote)
        print(f"  Insertados {len(lote)} vehiculos en este lote. Total acumulado: {total_insertados}")

    return total_insertados


def cargar_catalogo_en_supabase(ruta_catalogo: Path) -> None:
    config_supabase = cargar_configuracion_supabase()
    if config_supabase is None:
        raise RuntimeError("Faltan SUPABASE_URL o SUPABASE_KEY en variables de entorno.")

    vehiculos = cargar_catalogo_local(ruta_catalogo)
    if not vehiculos:
        print("El catalogo local esta vacio. No hay registros para insertar.")
        return

    cliente = crear_cliente_supabase(config_supabase)
    ids_catalogo = [vehiculo["id"] for vehiculo in vehiculos if isinstance(vehiculo.get("id"), int)]
    ids_existentes = obtener_ids_existentes(cliente, ids_catalogo)

    vehiculos_nuevos = []
    for vehiculo in vehiculos:
        id_vehiculo = vehiculo.get("id")
        if not isinstance(id_vehiculo, int) or id_vehiculo in ids_existentes:
            continue

        vehiculos_nuevos.append(
            {
                "id_vehiculo": id_vehiculo,
                "marca": vehiculo.get("marca"),
                "modelo": vehiculo.get("modelo"),
                "version": vehiculo.get("version"),
                "anio": vehiculo.get("anio"),
                "tipo": vehiculo.get("tipo"),
            }
        )

    print("\n=== FASE 4 - Carga en Supabase ===")
    print(f"Vehiculos en catalogo local: {len(vehiculos)}")
    print(f"Vehiculos ya existentes en Supabase: {len(ids_existentes)}")
    print(f"Vehiculos nuevos a insertar: {len(vehiculos_nuevos)}")

    if not vehiculos_nuevos:
        print("No hay vehiculos nuevos para insertar.")
        return

    total_insertados = insertar_vehiculos_nuevos(cliente, vehiculos_nuevos)
    print(f"FASE 4 completada. Vehiculos insertados: {total_insertados}")


def main() -> None:
    print("=== FASE 2 y FASE 4 - Mercantil Andina ===")
    print("La autenticacion se realiza con headers cargados desde .env.")

    config = cargar_configuracion()
    config_catalogo = cargar_configuracion_catalogo()
    try:
        sesion = crear_sesion(config)
    except RuntimeError as error:
        print(error)
        raise SystemExit(1)

    if not verificar_sesion_api(sesion, config.portal_base_url):
        print("\nNo se pudo validar acceso a la API. Revisa MA_TOKEN y MA_API_KEY.")
        raise SystemExit(1)

    print("\nAcceso validado correctamente contra la API de catalogo.")

    continuar_fase_2 = input("\nDeseas iniciar la FASE 2 y descargar el catalogo completo? [s/N]: ").strip().lower()
    if continuar_fase_2 not in {"s", "si", "y", "yes"}:
        print("FASE 2 cancelada por el usuario.")
    else:
        catalogo = descargar_catalogo_completo(sesion, config.portal_base_url, config_catalogo)
        guardar_catalogo_local(catalogo, SALIDA_CATALOGO_PATH)

        print(f"\nFASE 2 completada. Vehiculos unicos descargados: {len(catalogo)}")
        print(f"Catalogo guardado en: {SALIDA_CATALOGO_PATH}")

    continuar_fase_4 = input(
        "\nDeseas iniciar la FASE 4 y cargar el catalogo local en Supabase? [s/N]: "
    ).strip().lower()
    if continuar_fase_4 not in {"s", "si", "y", "yes"}:
        print("FASE 4 cancelada por el usuario.")
        print("\nSiguiente paso sugerido: FASE 5 (API interna de vehiculos en FastAPI).")
        return

    try:
        cargar_catalogo_en_supabase(SALIDA_CATALOGO_PATH)
    except Exception as error:
        print(f"No se pudo completar la FASE 4: {error}")
        raise SystemExit(1)

    print("\nSiguiente paso sugerido: FASE 5 (API interna de vehiculos en FastAPI).")


if __name__ == "__main__":
    main()

"""Sync Mercantil crawler v2 output to Supabase.

Consumes:
    data/mercantil_catalog_v2/raw/vehicles_raw.jsonl

Loads data into:
    - mercantil_vehicle_raw
    - vehicle_catalog

Behavior:
    - uses the existing shared Supabase client
    - creates tables if missing when a direct DB connection is available
    - upserts by `id`
    - logs totals for processed, inserted, updated and errors
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.append(str(REPO_ROOT))

logger = logging.getLogger("sync_catalog_to_supabase")

DEFAULT_INPUT_PATH = REPO_ROOT / "data" / "mercantil_catalog_v2" / "raw" / "vehicles_raw.jsonl"
RAW_TABLE = "mercantil_vehicle_raw"
CATALOG_TABLE = "vehicle_catalog"
DEFAULT_BATCH_SIZE = 500


@dataclass
class SyncStats:
    total_records: int = 0
    inserted: int = 0
    updated: int = 0
    errors: int = 0


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def load_repo_dotenv() -> None:
    env_path = REPO_ROOT / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
    else:
        load_dotenv()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            payload = line.strip()
            if not payload:
                continue
            try:
                data = json.loads(payload)
            except json.JSONDecodeError as error:
                raise ValueError(f"Invalid JSONL at line {line_number}: {error}") from error
            if isinstance(data, dict):
                records.append(data)
    return records


def chunked(items: list[Any], chunk_size: int) -> list[list[Any]]:
    return [items[index : index + chunk_size] for index in range(0, len(items), chunk_size)]


def get_supabase_client() -> Any:
    from aplicacion.backend.servicios.cliente_supabase import cliente_supabase

    if cliente_supabase is None:
        raise RuntimeError(
            "Supabase client is not configured. Check SUPABASE_URL and SUPABASE_KEY/SERVICE_ROLE."
        )
    return cliente_supabase


def probe_table_exists(client: Any, table_name: str) -> bool:
    try:
        client.table(table_name).select("id").limit(1).execute()
        return True
    except Exception as error:  # noqa: BLE001
        message = str(error).lower()
        missing_markers = [
            "does not exist",
            "relation",
            "could not find the table",
            "not found",
            "404",
        ]
        if any(marker in message for marker in missing_markers):
            return False
        raise


def build_tables_sql() -> str:
    return """
create table if not exists public.mercantil_vehicle_raw (
  id bigint primary key,
  run_id text,
  captured_at timestamptz,
  query jsonb,
  job jsonb,
  payload jsonb not null,
  updated_at timestamptz not null default now()
);

create table if not exists public.vehicle_catalog (
  id bigint primary key,
  marca_descripcion text,
  marca_codigo text,
  modelo_descripcion text,
  modelo_codigo text,
  fabricado integer,
  propulsion_descripcion text,
  origen_descripcion text,
  tipo_vehiculo_codigo text,
  categoria_tipo_codigo text,
  carroceria_tipo_codigo text,
  suma numeric,
  updated_at timestamptz not null default now()
);

create index if not exists idx_vehicle_catalog_marca_descripcion on public.vehicle_catalog (marca_descripcion);
create index if not exists idx_vehicle_catalog_modelo_descripcion on public.vehicle_catalog (modelo_descripcion);
create index if not exists idx_vehicle_catalog_fabricado on public.vehicle_catalog (fabricado);
create index if not exists idx_vehicle_catalog_tipo_vehiculo_codigo on public.vehicle_catalog (tipo_vehiculo_codigo);
"""


def ensure_tables_exist(client: Any) -> None:
    missing_tables = [name for name in (RAW_TABLE, CATALOG_TABLE) if not probe_table_exists(client, name)]
    if not missing_tables:
        return

    db_url = (
        os.getenv("SUPABASE_DB_URL")
        or os.getenv("DATABASE_URL")
        or os.getenv("POSTGRES_URL")
        or os.getenv("SUPABASE_DATABASE_URL")
    )
    psql_path = shutil.which("psql")

    if not db_url or not psql_path:
        raise RuntimeError(
            "Missing tables detected but no direct SQL transport is available. "
            "Set SUPABASE_DB_URL (or DATABASE_URL) and ensure `psql` is installed, "
            "or create the tables manually before running the sync."
        )

    logger.info("creating_missing_tables tables=%s", ",".join(missing_tables))
    subprocess.run(
        [psql_path, db_url, "-v", "ON_ERROR_STOP=1", "-c", build_tables_sql()],
        check=True,
        capture_output=True,
        text=True,
    )

    still_missing = [name for name in (RAW_TABLE, CATALOG_TABLE) if not probe_table_exists(client, name)]
    if still_missing:
        raise RuntimeError(f"Failed to create required tables: {', '.join(still_missing)}")


def nested_value(payload: dict[str, Any], *path: str) -> Any:
    current: Any = payload
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def extract_text(value: Any) -> str | None:
    if isinstance(value, str):
        value = value.strip()
        return value or None
    if isinstance(value, (int, float)):
        return str(value)
    return None


def extract_int(value: Any) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        value = value.strip()
        if value.isdigit():
            return int(value)
    return None


def extract_number(value: Any) -> float | int | None:
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        cleaned = value.strip().replace(",", ".")
        if not cleaned:
            return None
        try:
            number = float(cleaned)
        except ValueError:
            return None
        if number.is_integer():
            return int(number)
        return number
    return None


def extract_first(payload: dict[str, Any], *paths: tuple[str, ...]) -> Any:
    for path in paths:
        value = nested_value(payload, *path)
        if value is not None:
            return value
    return None


def extract_fabricado(payload: dict[str, Any]) -> int | None:
    return extract_int(
        extract_first(
            payload,
            ("fabricado",),
            ("anio",),
            ("anio_modelo",),
            ("ano",),
        )
    )


def transform_raw_record(source: dict[str, Any]) -> dict[str, Any]:
    payload = source.get("payload")
    if not isinstance(payload, dict):
        raise ValueError("Source record does not include a valid payload object")

    vehicle_id = extract_int(source.get("vehicle_id")) or extract_int(payload.get("id"))
    if vehicle_id is None:
        raise ValueError("Source record does not include a valid vehicle id")

    return {
        "id": vehicle_id,
        "run_id": extract_text(source.get("run_id")),
        "captured_at": extract_text(source.get("captured_at")),
        "query": source.get("query") if isinstance(source.get("query"), dict) else {},
        "job": source.get("job") if isinstance(source.get("job"), dict) else {},
        "payload": payload,
        "updated_at": "now()",
    }


def transform_catalog_record(source: dict[str, Any]) -> dict[str, Any]:
    payload = source.get("payload")
    if not isinstance(payload, dict):
        raise ValueError("Source record does not include a valid payload object")

    vehicle_id = extract_int(source.get("vehicle_id")) or extract_int(payload.get("id"))
    if vehicle_id is None:
        raise ValueError("Source record does not include a valid vehicle id")

    return {
        "id": vehicle_id,
        "marca_descripcion": extract_text(extract_first(payload, ("marca", "descripcion"), ("marca",))),
        "marca_codigo": extract_text(extract_first(payload, ("marca", "codigo"), ("marca", "id"))),
        "modelo_descripcion": extract_text(extract_first(payload, ("modelo", "descripcion"), ("modelo",))),
        "modelo_codigo": extract_text(extract_first(payload, ("modelo", "codigo"), ("modelo", "id"))),
        "fabricado": extract_fabricado(payload),
        "propulsion_descripcion": extract_text(
            extract_first(payload, ("propulsion", "descripcion"), ("propulsion",))
        ),
        "origen_descripcion": extract_text(extract_first(payload, ("origen", "descripcion"), ("origen",))),
        "tipo_vehiculo_codigo": extract_text(
            extract_first(
                payload,
                ("tipo_vehiculo", "codigo"),
                ("tipoVehiculo", "codigo"),
                ("tipo", "codigo"),
                ("tipo", "id"),
                ("tipo_vehiculo_codigo",),
                ("vehiculo_tipo",),
            )
        ),
        "categoria_tipo_codigo": extract_text(
            extract_first(
                payload,
                ("categoria_tipo", "codigo"),
                ("categoriaTipo", "codigo"),
                ("categoria_tipo_codigo",),
            )
        ),
        "carroceria_tipo_codigo": extract_text(
            extract_first(
                payload,
                ("carroceria_tipo", "codigo"),
                ("carroceriaTipo", "codigo"),
                ("carroceria_tipo_codigo",),
            )
        ),
        "suma": extract_number(
            extract_first(
                payload,
                ("suma",),
                ("suma_asegurada",),
                ("sumaAsegurada",),
                ("valor",),
            )
        ),
        "updated_at": "now()",
    }


def fetch_existing_ids(client: Any, table_name: str, ids: list[int], batch_size: int) -> set[int]:
    existing_ids: set[int] = set()
    for batch in chunked(ids, batch_size):
        response = client.table(table_name).select("id").in_("id", batch).execute()
        records = getattr(response, "data", None) or []
        for record in records:
            if not isinstance(record, dict):
                continue
            record_id = extract_int(record.get("id"))
            if record_id is not None:
                existing_ids.add(record_id)
    return existing_ids


def upsert_batches(client: Any, table_name: str, rows: list[dict[str, Any]], batch_size: int) -> None:
    for batch in chunked(rows, batch_size):
        payload = []
        for row in batch:
            db_row = dict(row)
            if db_row.get("updated_at") == "now()":
                db_row.pop("updated_at", None)
            payload.append(db_row)
        client.table(table_name).upsert(payload, on_conflict="id").execute()


def build_sync_payloads(source_records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int]:
    raw_rows: list[dict[str, Any]] = []
    catalog_rows: list[dict[str, Any]] = []
    errors = 0

    for source in source_records:
        try:
            raw_rows.append(transform_raw_record(source))
            catalog_rows.append(transform_catalog_record(source))
        except Exception as error:  # noqa: BLE001
            errors += 1
            logger.exception("transform_failed error=%s", error)

    return raw_rows, catalog_rows, errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync Mercantil crawler v2 dataset to Supabase.")
    parser.add_argument(
        "--input",
        default=str(DEFAULT_INPUT_PATH),
        help="Path to vehicles_raw.jsonl generated by crawler_mercantil_catalog_v2.py",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help="Number of rows per upsert batch.",
    )
    return parser.parse_args()


def main() -> None:
    configure_logging()
    load_repo_dotenv()
    args = parse_args()

    input_path = Path(args.input)
    if args.batch_size <= 0:
        raise ValueError("--batch-size must be greater than zero")

    source_records = read_jsonl(input_path)
    raw_rows, catalog_rows, transform_errors = build_sync_payloads(source_records)
    if not raw_rows or not catalog_rows:
        raise RuntimeError("No valid records were loaded from the crawler output")

    client = get_supabase_client()
    ensure_tables_exist(client)

    ids = sorted({row["id"] for row in catalog_rows if isinstance(row.get("id"), int)})
    existing_ids = fetch_existing_ids(client, RAW_TABLE, ids, args.batch_size)
    existing_ids.update(fetch_existing_ids(client, CATALOG_TABLE, ids, args.batch_size))

    stats = SyncStats(
        total_records=len(ids),
        inserted=len([record_id for record_id in ids if record_id not in existing_ids]),
        updated=len([record_id for record_id in ids if record_id in existing_ids]),
        errors=transform_errors,
    )

    try:
        upsert_batches(client, RAW_TABLE, raw_rows, args.batch_size)
        upsert_batches(client, CATALOG_TABLE, catalog_rows, args.batch_size)
    except Exception as error:  # noqa: BLE001
        stats.errors += len(ids)
        logger.exception("sync_failed error=%s", error)
        raise

    logger.info("sync_completed total_records=%s inserted=%s updated=%s errors=%s", stats.total_records, stats.inserted, stats.updated, stats.errors)


if __name__ == "__main__":
    main()

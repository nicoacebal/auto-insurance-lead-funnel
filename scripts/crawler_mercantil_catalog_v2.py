"""Mercantil Catalog Crawler v2.

Robust catalog crawler for the Mercantil search endpoint:
`/api_integracion_productos/vehiculos/marca-modelo`.

Features:
- seed generator
- pagination engine
- persistent deduplication by external `id`
- raw payload storage
- normalized dataset storage
- resumable interrupted runs
- clear structured logging
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.append(str(REPO_ROOT))

from backend.integrations.auth.mercantil_auth import (  # noqa: E402
    MercantilAuthManager,
)

logger = logging.getLogger("mercantil_catalog_crawler_v2")

API_PATH = "/api_integracion_productos/vehiculos/marca-modelo"
BASE_URL_DEFAULT = "https://productos.mercantilandina.com.ar"
DEFAULT_TYPES = ["1", "2", "3", "8", "9", "21", "4", "5", "6", "17"]
DEFAULT_OUTPUT_DIR = REPO_ROOT / "data" / "mercantil_catalog_v2"
DEFAULT_PAGE_SIZE = 5000
DEFAULT_TIMEOUT = 30
DEFAULT_MAX_PAGES_PER_QUERY = 200
DEFAULT_SLEEP_SECONDS = 0.0
INITIAL_YEAR = 1997


def build_default_seeds() -> list[str]:
    return [
        "VOLKSWAGEN",
        "FORD",
        "CHEVROLET",
        "RENAULT",
        "FIAT",
        "PEUGEOT",
        "TOYOTA",
        "CITROEN",
        "NISSAN",
        "HONDA",
        "BMW",
        "AUDI",
        "MERCEDES",
        "JEEP",
        "HYUNDAI",
        "KIA",
        "CHERY",
        "IVECO",
        "SCANIA",
        "VOLVO",
    ]


def load_repo_dotenv() -> None:
    env_path = REPO_ROOT / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
    else:
        load_dotenv()


def utc_now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    ensure_parent_dir(path)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=True) + "\n")


def append_text_line(path: Path, line: str) -> None:
    ensure_parent_dir(path)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"{line}\n")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []

    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            payload = line.strip()
            if not payload:
                continue
            data = json.loads(payload)
            if isinstance(data, dict):
                records.append(data)
    return records


def read_seen_ids(path: Path) -> set[int]:
    if not path.exists():
        return set()

    ids: set[int] = set()
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            value = line.strip()
            if value.isdigit():
                ids.add(int(value))
    return ids


def normalize_text(value: Any, key: str = "descripcion") -> str | None:
    if isinstance(value, dict):
        nested = value.get(key)
        if isinstance(nested, str):
            nested = nested.strip()
            return nested or None
    if isinstance(value, str):
        value = value.strip()
        return value or None
    return None


def normalize_vehicle(item: dict[str, Any]) -> dict[str, Any] | None:
    vehicle_id = item.get("id")
    if not isinstance(vehicle_id, int):
        return None

    return {
        "id": vehicle_id,
        "marca": normalize_text(item.get("marca")),
        "modelo": normalize_text(item.get("modelo")),
        "version": normalize_text(item.get("version")),
        "anio": extract_year(item),
        "tipo": normalize_text(item.get("tipo")),
    }


def extract_year(item: dict[str, Any]) -> int | None:
    for key in ("anio", "fabricado", "anio_modelo", "ano"):
        value = item.get(key)
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.isdigit():
            return int(value)
    return None


def extract_vehicle_type_code(item: dict[str, Any]) -> str | None:
    tipo = item.get("tipo")
    if isinstance(tipo, dict):
        for key in ("codigo", "id", "idTipo", "tipoCodigo", "codigoTipo"):
            value = tipo.get(key)
            if isinstance(value, int):
                return str(value)
            if isinstance(value, str):
                value = value.strip()
                if value:
                    return value
    return None


def format_file_size(path: Path) -> str:
    if not path.exists():
        return "0 B"

    size_bytes = path.stat().st_size
    units = ["B", "KB", "MB", "GB"]
    size = float(size_bytes)
    unit = units[0]
    for current_unit in units:
        unit = current_unit
        if size < 1024 or current_unit == units[-1]:
            break
        size /= 1024
    if unit == "B":
        return f"{size_bytes} B"
    return f"{size:.2f} {unit} ({size_bytes} B)"


@dataclass(frozen=True)
class CrawlJob:
    descripcion: str
    fabricado: int
    tipo: str


@dataclass
class CrawlStats:
    requests: int = 0
    pages: int = 0
    raw_pages_saved: int = 0
    raw_records_saved: int = 0
    normalized_records_saved: int = 0
    new_ids: int = 0
    duplicates: int = 0
    errors: int = 0


@dataclass
class CrawlState:
    run_id: str
    started_at: str
    updated_at: str
    job_index: int = 0
    page: int = 0
    completed: bool = False
    config: dict[str, Any] = field(default_factory=dict)
    stats: CrawlStats = field(default_factory=CrawlStats)


@dataclass(frozen=True)
class CrawlConfig:
    output_dir: Path
    base_url: str
    timeout: int
    page_size: int
    max_pages_per_query: int
    sleep_seconds: float
    years: list[int]
    types: list[str]
    seeds: list[str]

    def serializable(self) -> dict[str, Any]:
        return {
            "output_dir": str(self.output_dir),
            "base_url": self.base_url,
            "timeout": self.timeout,
            "page_size": self.page_size,
            "max_pages_per_query": self.max_pages_per_query,
            "sleep_seconds": self.sleep_seconds,
            "years": self.years,
            "types": self.types,
            "seeds": self.seeds,
        }


class MercantilCatalogCrawlerV2:
    def __init__(self, config: CrawlConfig, reset: bool = False) -> None:
        self.config = config
        self.jobs = self._build_jobs()
        self.paths = self._build_paths(config.output_dir)

        if reset:
            self._reset_state_files()

        self.seen_ids = read_seen_ids(self.paths["seen_ids"])
        self.state = self._load_or_create_state()
        self._validate_resume_config()

        self.auth = MercantilAuthManager(timeout=config.timeout)
        self.base_url = config.base_url.rstrip("/")

    def _build_jobs(self) -> list[CrawlJob]:
        return [
            CrawlJob(descripcion=seed, fabricado=year, tipo=type_code)
            for year in self.config.years
            for type_code in self.config.types
            for seed in self.config.seeds
        ]

    @staticmethod
    def _build_paths(output_dir: Path) -> dict[str, Path]:
        return {
            "output_dir": output_dir,
            "state": output_dir / "state.json",
            "seen_ids": output_dir / "state" / "seen_ids.txt",
            "raw_pages": output_dir / "raw" / "raw_pages.jsonl",
            "raw_records": output_dir / "raw" / "vehicles_raw.jsonl",
            "normalized_records": output_dir / "normalized" / "vehicles_normalized.jsonl",
            "errors": output_dir / "logs" / "errors.jsonl",
        }

    def _reset_state_files(self) -> None:
        output_dir = self.paths["output_dir"]
        if output_dir.exists():
            for path in sorted(output_dir.rglob("*"), reverse=True):
                if path.is_file():
                    path.unlink()
            for path in sorted(output_dir.rglob("*"), reverse=True):
                if path.is_dir():
                    path.rmdir()

    def _load_or_create_state(self) -> CrawlState:
        state_path = self.paths["state"]
        if state_path.exists():
            payload = json.loads(state_path.read_text(encoding="utf-8"))
            return CrawlState(
                run_id=payload["run_id"],
                started_at=payload["started_at"],
                updated_at=payload["updated_at"],
                job_index=payload["job_index"],
                page=payload["page"],
                completed=payload.get("completed", False),
                config=payload.get("config", {}),
                stats=CrawlStats(**payload.get("stats", {})),
            )

        state = CrawlState(
            run_id=datetime.utcnow().strftime("run-%Y%m%d-%H%M%S"),
            started_at=utc_now_iso(),
            updated_at=utc_now_iso(),
            config=self.config.serializable(),
        )
        self._save_state(state)
        return state

    def _validate_resume_config(self) -> None:
        saved_config = self.state.config or {}
        current_config = self.config.serializable()
        if saved_config and saved_config != current_config:
            raise RuntimeError(
                "Existing crawl state was created with a different configuration. "
                "Use --reset to start a fresh run or keep the same args."
            )

    def _save_state(self, state: CrawlState | None = None) -> None:
        state = state or self.state
        state.updated_at = utc_now_iso()
        ensure_parent_dir(self.paths["state"])
        payload = asdict(state)
        payload["stats"] = asdict(state.stats)
        self.paths["state"].write_text(
            json.dumps(payload, ensure_ascii=True, indent=2),
            encoding="utf-8",
        )

    def run(self) -> None:
        total_jobs = len(self.jobs)
        logger.info(
            "crawl_started run_id=%s jobs=%s seen_ids=%s output_dir=%s",
            self.state.run_id,
            total_jobs,
            len(self.seen_ids),
            self.paths["output_dir"],
        )

        while self.state.job_index < total_jobs:
            job = self.jobs[self.state.job_index]
            self._crawl_job(job)

        self.state.completed = True
        self._save_state()
        logger.info(
            "crawl_completed run_id=%s requests=%s new_ids=%s duplicates=%s errors=%s",
            self.state.run_id,
            self.state.stats.requests,
            self.state.stats.new_ids,
            self.state.stats.duplicates,
            self.state.stats.errors,
        )
        self._log_dataset_summary()

    def _crawl_job(self, job: CrawlJob) -> None:
        while self.state.page < self.config.max_pages_per_query:
            query = {
                "descripcion": job.descripcion,
                "fabricado": str(job.fabricado),
                "tipo": job.tipo,
                "page": self.state.page,
                "size": self.config.page_size,
                "conValor": "false",
            }
            self._save_state()

            try:
                payload, status_code = self._request_page(query)
            except Exception as error:
                self._handle_request_error(job, query, error)
                self.state.job_index += 1
                self.state.page = 0
                self._save_state()
                return

            records = payload.get("vehiculos", [])
            if not isinstance(records, list):
                self._handle_request_error(job, query, RuntimeError("Invalid 'vehiculos' list"))
                self.state.job_index += 1
                self.state.page = 0
                self._save_state()
                return

            self.state.stats.requests += 1
            self.state.stats.pages += 1
            self._store_raw_page(job, query, status_code, payload)

            new_ids, duplicates = self._process_records(job, query, records)
            logger.info(
                "page_processed run_id=%s job=%s/%s seed=%s year=%s tipo=%s page=%s status=%s results=%s new_ids=%s duplicates=%s",
                self.state.run_id,
                self.state.job_index + 1,
                len(self.jobs),
                job.descripcion,
                job.fabricado,
                job.tipo,
                self.state.page,
                status_code,
                len(records),
                new_ids,
                duplicates,
            )

            should_continue = len(records) >= self.config.page_size
            if not records or not should_continue:
                self.state.job_index += 1
                self.state.page = 0
                self._save_state()
                if self.config.sleep_seconds > 0:
                    time.sleep(self.config.sleep_seconds)
                return

            self.state.page += 1
            self._save_state()
            if self.config.sleep_seconds > 0:
                time.sleep(self.config.sleep_seconds)

        logger.warning(
            "max_pages_reached run_id=%s seed=%s year=%s tipo=%s max_pages=%s",
            self.state.run_id,
            job.descripcion,
            job.fabricado,
            job.tipo,
            self.config.max_pages_per_query,
        )
        self.state.job_index += 1
        self.state.page = 0
        self._save_state()

    def _request_page(self, query: dict[str, Any]) -> tuple[dict[str, Any], int]:
        url = urljoin(f"{self.base_url}/", API_PATH.lstrip("/"))
        response = self.auth.handle_request("GET", url, params=query)

        if response.status_code in (401, 403):
            raise RuntimeError(f"Unauthorized status from Mercantil API: {response.status_code}")

        if response.status_code == 400:
            return {"vehiculos": []}, 400

        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise RuntimeError("Mercantil API did not return a JSON object")
        return payload, response.status_code

    def _store_raw_page(
        self,
        job: CrawlJob,
        query: dict[str, Any],
        status_code: int,
        payload: dict[str, Any],
    ) -> None:
        append_jsonl(
            self.paths["raw_pages"],
            {
                "run_id": self.state.run_id,
                "captured_at": utc_now_iso(),
                "query": query,
                "job": asdict(job),
                "status_code": status_code,
                "response": payload,
            },
        )
        self.state.stats.raw_pages_saved += 1

    def _process_records(
        self,
        job: CrawlJob,
        query: dict[str, Any],
        records: list[dict[str, Any]],
    ) -> tuple[int, int]:
        new_ids = 0
        duplicates = 0

        for item in records:
            if not isinstance(item, dict):
                continue

            vehicle_id = item.get("id")
            if not isinstance(vehicle_id, int):
                duplicates += 1
                self.state.stats.duplicates += 1
                continue

            if vehicle_id in self.seen_ids:
                duplicates += 1
                self.state.stats.duplicates += 1
                continue

            normalized = normalize_vehicle(item)
            if normalized is None:
                duplicates += 1
                self.state.stats.duplicates += 1
                continue

            self.seen_ids.add(vehicle_id)
            append_text_line(self.paths["seen_ids"], str(vehicle_id))

            append_jsonl(
                self.paths["raw_records"],
                {
                    "run_id": self.state.run_id,
                    "captured_at": utc_now_iso(),
                    "query": query,
                    "job": asdict(job),
                    "vehicle_id": vehicle_id,
                    "payload": item,
                },
            )
            append_jsonl(
                self.paths["normalized_records"],
                {
                    "run_id": self.state.run_id,
                    "captured_at": utc_now_iso(),
                    "query": query,
                    "job": asdict(job),
                    **normalized,
                },
            )

            new_ids += 1
            self.state.stats.new_ids += 1
            self.state.stats.raw_records_saved += 1
            self.state.stats.normalized_records_saved += 1

        return new_ids, duplicates

    def _handle_request_error(
        self,
        job: CrawlJob,
        query: dict[str, Any],
        error: Exception,
    ) -> None:
        self.state.stats.errors += 1
        logger.exception(
            "page_failed run_id=%s seed=%s year=%s tipo=%s page=%s",
            self.state.run_id,
            job.descripcion,
            job.fabricado,
            job.tipo,
            query["page"],
        )
        append_jsonl(
            self.paths["errors"],
            {
                "run_id": self.state.run_id,
                "captured_at": utc_now_iso(),
                "query": query,
                "job": asdict(job),
                "error": str(error),
                "error_type": type(error).__name__,
            },
        )

    def _log_dataset_summary(self) -> None:
        normalized_records = read_jsonl(self.paths["normalized_records"])
        raw_records = read_jsonl(self.paths["raw_records"])

        brand_counter: Counter[str] = Counter()
        year_counter: Counter[str] = Counter()
        vehicle_type_counter: Counter[str] = Counter()

        for record in normalized_records:
            brand = record.get("marca") or "<sin_marca>"
            brand_counter[str(brand)] += 1

            year = record.get("anio")
            year_label = str(year) if year is not None else "<sin_anio>"
            year_counter[year_label] += 1

        for record in raw_records:
            payload = record.get("payload")
            type_code = None
            if isinstance(payload, dict):
                type_code = extract_vehicle_type_code(payload)
            if not type_code:
                query = record.get("query")
                if isinstance(query, dict):
                    fallback_type = query.get("tipo")
                    if isinstance(fallback_type, str) and fallback_type.strip():
                        type_code = fallback_type.strip()
            vehicle_type_counter[type_code or "<sin_tipo_codigo>"] += 1

        sample_records = normalized_records[:10]

        logger.info("dataset_summary total_unique_vehicles=%s", len(normalized_records))

        logger.info("dataset_summary top_15_marcas_begin")
        for brand, count in brand_counter.most_common(15):
            logger.info("dataset_summary marca=%s count=%s", brand, count)
        logger.info("dataset_summary top_15_marcas_end")

        logger.info("dataset_summary distribucion_anio_begin")
        for year, count in sorted(year_counter.items(), key=lambda item: item[0]):
            logger.info("dataset_summary anio=%s count=%s", year, count)
        logger.info("dataset_summary distribucion_anio_end")

        logger.info("dataset_summary distribucion_tipo_vehiculo_codigo_begin")
        for type_code, count in sorted(vehicle_type_counter.items(), key=lambda item: item[0]):
            logger.info("dataset_summary tipo_vehiculo_codigo=%s count=%s", type_code, count)
        logger.info("dataset_summary distribucion_tipo_vehiculo_codigo_end")

        logger.info("dataset_summary ejemplo_10_registros_normalizados_begin")
        for index, record in enumerate(sample_records, start=1):
            logger.info(
                "dataset_summary ejemplo_index=%s record=%s",
                index,
                json.dumps(record, ensure_ascii=True),
            )
        logger.info("dataset_summary ejemplo_10_registros_normalizados_end")

        logger.info(
            "dataset_summary file=%s size=%s",
            self.paths["raw_pages"].name,
            format_file_size(self.paths["raw_pages"]),
        )
        logger.info(
            "dataset_summary file=%s size=%s",
            self.paths["raw_records"].name,
            format_file_size(self.paths["raw_records"]),
        )
        logger.info(
            "dataset_summary file=%s size=%s",
            self.paths["normalized_records"].name,
            format_file_size(self.paths["normalized_records"]),
        )


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def parse_args() -> argparse.Namespace:
    current_year = datetime.now().year

    parser = argparse.ArgumentParser(
        description="Mercantil catalog crawler v2 with pagination, raw storage and resume support.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directory where state, raw payloads and normalized datasets are stored.",
    )
    parser.add_argument(
        "--base-url",
        default=os.getenv("MA_PORTAL_BASE_URL", BASE_URL_DEFAULT),
        help="Mercantil portal base URL.",
    )
    parser.add_argument(
        "--start-year",
        type=int,
        default=INITIAL_YEAR,
        help="Start year for crawling.",
    )
    parser.add_argument(
        "--end-year",
        type=int,
        default=current_year,
        help="End year for crawling.",
    )
    parser.add_argument(
        "--page-size",
        type=int,
        default=DEFAULT_PAGE_SIZE,
        help="Requested page size for the search endpoint.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help="HTTP timeout in seconds.",
    )
    parser.add_argument(
        "--max-pages-per-query",
        type=int,
        default=DEFAULT_MAX_PAGES_PER_QUERY,
        help="Safety cap to avoid infinite pagination loops.",
    )
    parser.add_argument(
        "--sleep-seconds",
        type=float,
        default=DEFAULT_SLEEP_SECONDS,
        help="Optional sleep between requests.",
    )
    parser.add_argument(
        "--types",
        nargs="+",
        default=DEFAULT_TYPES,
        help="Vehicle type codes to send in the `tipo` parameter.",
    )
    parser.add_argument(
        "--seeds",
        nargs="+",
        default=build_default_seeds(),
        help="Seed list for the `descripcion` parameter.",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete any previous crawler state/output in the target directory before starting.",
    )
    return parser.parse_args()


def build_config(args: argparse.Namespace) -> CrawlConfig:
    if args.start_year > args.end_year:
        raise ValueError("--start-year cannot be greater than --end-year")
    if args.page_size <= 0:
        raise ValueError("--page-size must be greater than zero")
    if args.max_pages_per_query <= 0:
        raise ValueError("--max-pages-per-query must be greater than zero")

    years = list(range(args.start_year, args.end_year + 1))
    types = [type_code.strip() for type_code in args.types if type_code.strip()]
    seeds = []
    seen = set()
    for seed in args.seeds:
        clean_seed = seed.strip().upper()
        if clean_seed and clean_seed not in seen:
            seeds.append(clean_seed)
            seen.add(clean_seed)

    if not types:
        raise ValueError("At least one vehicle type code is required")
    if not seeds:
        raise ValueError("At least one search seed is required")

    return CrawlConfig(
        output_dir=Path(args.output_dir),
        base_url=args.base_url,
        timeout=args.timeout,
        page_size=args.page_size,
        max_pages_per_query=args.max_pages_per_query,
        sleep_seconds=args.sleep_seconds,
        years=years,
        types=types,
        seeds=seeds,
    )


def main() -> None:
    configure_logging()
    load_repo_dotenv()
    args = parse_args()
    config = build_config(args)

    crawler = MercantilCatalogCrawlerV2(config=config, reset=args.reset)
    crawler.run()


if __name__ == "__main__":
    main()

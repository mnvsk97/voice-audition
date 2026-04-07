from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from audition import CATALOG_DIR


CATALOG_DB_FILENAME = "voice_catalog.db"
RUNTIME_DB_FILENAME = "runtime.db"
LEGACY_DB_FILENAME = "voice_audition.db"
SKIP_CATALOGS = {"providers", "hosting"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_state_dir() -> Path:
    env_dir = os.environ.get("VOICE_AUDITION_STATE_DIR")
    if env_dir:
        return Path(env_dir)
    return Path.cwd() / ".voice-audition"


def get_catalog_db_path(catalog_db_path: str | Path | None = None) -> Path:
    if catalog_db_path:
        return Path(catalog_db_path)
    env_path = os.environ.get("VOICE_AUDITION_CATALOG_DB_PATH")
    if env_path:
        return Path(env_path)
    return CATALOG_DIR / CATALOG_DB_FILENAME


def get_runtime_db_path(runtime_db_path: str | Path | None = None) -> Path:
    if runtime_db_path:
        return Path(runtime_db_path)
    env_path = os.environ.get("VOICE_AUDITION_RUNTIME_DB_PATH")
    if env_path:
        return Path(env_path)
    return get_state_dir() / RUNTIME_DB_FILENAME


@contextmanager
def connect_catalog(catalog_db_path: str | Path | None = None) -> Iterator[sqlite3.Connection]:
    path = get_catalog_db_path(catalog_db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


@contextmanager
def connect_runtime(runtime_db_path: str | Path | None = None) -> Iterator[sqlite3.Connection]:
    path = get_runtime_db_path(runtime_db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_catalog_db(catalog_db_path: str | Path | None = None) -> Path:
    path = get_catalog_db_path(catalog_db_path)
    with connect_catalog(path) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS catalog_meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS providers (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                estimated_cost_per_min_usd REAL,
                latency_tier TEXT,
                quality_elo INTEGER,
                pricing_updated TEXT,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS hosting_models (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                estimated_cost_per_min_self_hosted REAL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS voices (
                id TEXT PRIMARY KEY,
                provider TEXT NOT NULL,
                provider_voice_id TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                gender TEXT,
                age_group TEXT,
                accent TEXT,
                language TEXT,
                provider_model TEXT,
                effective_cost_per_min_usd REAL,
                effective_latency_tier TEXT,
                effective_quality_elo INTEGER,
                payload_json TEXT NOT NULL,
                status TEXT,
                metadata_source TEXT,
                enrichment_status TEXT,
                enrichment_attempts INTEGER DEFAULT 0,
                first_seen TEXT,
                last_seen TEXT,
                last_synced TEXT,
                last_verified TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_voices_provider ON voices(provider);
            CREATE INDEX IF NOT EXISTS idx_voices_enrichment_status ON voices(enrichment_status);

            CREATE TABLE IF NOT EXISTS voice_acoustic_features (
                voice_id TEXT PRIMARY KEY,
                f0_mean_hz REAL,
                f0_std_hz REAL,
                speech_rate_syl_per_sec REAL,
                hnr_db REAL,
                spectral_centroid_hz REAL,
                utmos_score REAL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (voice_id) REFERENCES voices(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS voice_embeddings (
                voice_id TEXT NOT NULL,
                embedding_kind TEXT NOT NULL,
                vector_json TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (voice_id, embedding_kind),
                FOREIGN KEY (voice_id) REFERENCES voices(id) ON DELETE CASCADE
            );
            """
        )
        _set_meta(conn, "catalog_version", _get_meta(conn, "catalog_version") or "1")
    return path


def init_runtime_db(runtime_db_path: str | Path | None = None) -> Path:
    path = get_runtime_db_path(runtime_db_path)
    with connect_runtime(path) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS pipeline_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stage TEXT NOT NULL,
                provider TEXT,
                voice_id TEXT,
                status TEXT NOT NULL,
                details_json TEXT,
                started_at TEXT NOT NULL,
                finished_at TEXT
            );

            CREATE TABLE IF NOT EXISTS provider_sync_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider TEXT NOT NULL,
                status TEXT NOT NULL,
                added_count INTEGER DEFAULT 0,
                updated_count INTEGER DEFAULT 0,
                removed_count INTEGER DEFAULT 0,
                total_count INTEGER DEFAULT 0,
                error TEXT,
                started_at TEXT NOT NULL,
                finished_at TEXT
            );

            CREATE TABLE IF NOT EXISTS analysis_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                brief TEXT NOT NULL,
                use_case TEXT NOT NULL,
                status TEXT NOT NULL,
                cache_hit INTEGER DEFAULT 0,
                result_json TEXT,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS audition_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                audition_kind TEXT NOT NULL,
                mode TEXT NOT NULL,
                brief TEXT NOT NULL,
                use_case TEXT NOT NULL,
                status TEXT NOT NULL,
                output_dir TEXT,
                result_json TEXT,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS audition_clips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                audition_run_id INTEGER NOT NULL,
                voice_id TEXT NOT NULL,
                script_name TEXT NOT NULL,
                script_text TEXT NOT NULL,
                file_path TEXT,
                provider TEXT,
                status TEXT NOT NULL,
                error TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (audition_run_id) REFERENCES audition_runs(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS query_cache (
                cache_key TEXT PRIMARY KEY,
                kind TEXT NOT NULL,
                catalog_version INTEGER NOT NULL,
                result_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                last_accessed_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_query_cache_kind ON query_cache(kind);
            """
        )
    return path


def init_databases(catalog_db_path: str | Path | None = None, runtime_db_path: str | Path | None = None) -> tuple[Path, Path]:
    return init_catalog_db(catalog_db_path), init_runtime_db(runtime_db_path)


def _get_meta(conn: sqlite3.Connection, key: str) -> str | None:
    row = conn.execute("SELECT value FROM catalog_meta WHERE key = ?", (key,)).fetchone()
    return None if row is None else row["value"]


def _set_meta(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        """
        INSERT INTO catalog_meta (key, value, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(key) DO UPDATE SET
            value=excluded.value,
            updated_at=excluded.updated_at
        """,
        (key, value, _now()),
    )


def get_catalog_version(catalog_db_path: str | Path | None = None) -> int:
    init_catalog_db(catalog_db_path)
    with connect_catalog(catalog_db_path) as conn:
        value = _get_meta(conn, "catalog_version") or "1"
    try:
        return int(value)
    except ValueError:
        return 1


def _bump_catalog_version(conn: sqlite3.Connection) -> int:
    current = _get_meta(conn, "catalog_version") or "1"
    try:
        next_version = int(current) + 1
    except ValueError:
        next_version = 2
    _set_meta(conn, "catalog_version", str(next_version))
    return next_version


def make_cache_key(kind: str, payload: dict[str, Any]) -> str:
    normalized = json.dumps({"kind": kind, **payload}, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def get_cached_query(cache_key: str, kind: str, runtime_db_path: str | Path | None = None,
                     catalog_db_path: str | Path | None = None) -> Any | None:
    init_runtime_db(runtime_db_path)
    version = get_catalog_version(catalog_db_path)
    with connect_runtime(runtime_db_path) as conn:
        row = conn.execute(
            """
            SELECT result_json FROM query_cache
            WHERE cache_key = ? AND kind = ? AND catalog_version = ?
            """,
            (cache_key, kind, version),
        ).fetchone()
        if row is None:
            return None
        conn.execute(
            "UPDATE query_cache SET last_accessed_at = ? WHERE cache_key = ?",
            (_now(), cache_key),
        )
    return json.loads(row["result_json"])


def cache_query_result(cache_key: str, kind: str, result: Any,
                       runtime_db_path: str | Path | None = None,
                       catalog_db_path: str | Path | None = None) -> None:
    init_runtime_db(runtime_db_path)
    version = get_catalog_version(catalog_db_path)
    with connect_runtime(runtime_db_path) as conn:
        now = _now()
        conn.execute(
            """
            INSERT INTO query_cache (
                cache_key, kind, catalog_version, result_json, created_at, last_accessed_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(cache_key) DO UPDATE SET
                kind=excluded.kind,
                catalog_version=excluded.catalog_version,
                result_json=excluded.result_json,
                last_accessed_at=excluded.last_accessed_at
            """,
            (cache_key, kind, version, json.dumps(result, ensure_ascii=False), now, now),
        )


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text())


def import_provider_catalog(path: str | Path | None = None, catalog_db_path: str | Path | None = None) -> int:
    src = Path(path) if path else CATALOG_DIR / "providers.json"
    if not src.exists():
        return 0
    data = _read_json(src)
    providers = data.get("providers", {}) if isinstance(data, dict) else {}
    if not isinstance(providers, dict):
        return 0
    init_catalog_db(catalog_db_path)
    rows = []
    now = _now()
    for provider_id, payload in providers.items():
        pricing = payload.get("pricing", {}) if isinstance(payload, dict) else {}
        technical = payload.get("technical", {}) if isinstance(payload, dict) else {}
        quality = payload.get("quality", {}) if isinstance(payload, dict) else {}
        rows.append(
            (
                provider_id,
                payload.get("name", provider_id.title()),
                json.dumps(payload, ensure_ascii=False),
                pricing.get("estimated_cost_per_minute"),
                technical.get("latency_tier"),
                quality.get("arena_elo") or _DEFAULT_PROVIDER_ELO.get(provider_id),
                pricing.get("pricing_updated"),
                now,
            )
        )
    with connect_catalog(catalog_db_path) as conn:
        conn.executemany(
            """
            INSERT INTO providers (
                id, name, payload_json, estimated_cost_per_min_usd, latency_tier,
                quality_elo, pricing_updated, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name,
                payload_json=excluded.payload_json,
                estimated_cost_per_min_usd=excluded.estimated_cost_per_min_usd,
                latency_tier=excluded.latency_tier,
                quality_elo=COALESCE(excluded.quality_elo, providers.quality_elo),
                pricing_updated=excluded.pricing_updated,
                updated_at=excluded.updated_at
            """,
            rows,
        )
        if rows:
            _bump_catalog_version(conn)
    return len(rows)


def import_hosting_catalog(path: str | Path | None = None, catalog_db_path: str | Path | None = None) -> int:
    src = Path(path) if path else CATALOG_DIR / "hosting.json"
    if not src.exists():
        return 0
    data = _read_json(src)
    models = data.get("open_source_models", {}) if isinstance(data, dict) else {}
    if not isinstance(models, dict):
        return 0
    init_catalog_db(catalog_db_path)
    rows = []
    now = _now()
    for model_id, payload in models.items():
        rows.append(
            (
                model_id,
                payload.get("name", model_id.title()),
                json.dumps(payload, ensure_ascii=False),
                payload.get("estimated_cost_per_min_self_hosted"),
                now,
            )
        )
    with connect_catalog(catalog_db_path) as conn:
        conn.executemany(
            """
            INSERT INTO hosting_models (
                id, name, payload_json, estimated_cost_per_min_self_hosted, updated_at
            ) VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name,
                payload_json=excluded.payload_json,
                estimated_cost_per_min_self_hosted=excluded.estimated_cost_per_min_self_hosted,
                updated_at=excluded.updated_at
            """,
            rows,
        )
        if rows:
            _bump_catalog_version(conn)
    return len(rows)


def import_catalog_json(catalog_dir: str | Path | None = None,
                        catalog_db_path: str | Path | None = None,
                        force: bool = False) -> int:
    src_dir = Path(catalog_dir) if catalog_dir else CATALOG_DIR
    if not src_dir.exists():
        return 0
    imported = 0
    import_provider_catalog(src_dir / "providers.json", catalog_db_path=catalog_db_path)
    import_hosting_catalog(src_dir / "hosting.json", catalog_db_path=catalog_db_path)
    for path in sorted(src_dir.glob("*.json")):
        if path.stem in SKIP_CATALOGS:
            continue
        try:
            data = _read_json(path)
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(data, list):
            continue
        imported += upsert_voices(data, catalog_db_path=catalog_db_path, force_version_bump=force)
    return imported


def import_legacy_db(legacy_db_path: str | Path,
                     catalog_db_path: str | Path | None = None) -> int:
    src = Path(legacy_db_path)
    if not src.exists():
        return 0
    conn = sqlite3.connect(src)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute("SELECT payload_json FROM voices").fetchall()
    finally:
        conn.close()
    voices = [json.loads(row["payload_json"]) for row in rows]
    return upsert_voices(voices, catalog_db_path=catalog_db_path)


def ensure_catalog_seeded(catalog_db_path: str | Path | None = None,
                          legacy_catalog_dir: str | Path | None = None,
                          legacy_db_path: str | Path | None = None) -> Path:
    path = init_catalog_db(catalog_db_path)
    with connect_catalog(path) as conn:
        row = conn.execute("SELECT COUNT(*) AS count FROM voices").fetchone()
    if row["count"] > 0:
        return path
    if legacy_db_path:
        import_legacy_db(legacy_db_path, catalog_db_path=path)
    legacy_dir = Path(legacy_catalog_dir) if legacy_catalog_dir else CATALOG_DIR
    if legacy_dir.exists():
        import_catalog_json(catalog_dir=legacy_dir, catalog_db_path=path)
    return path


def _provider_defaults(provider: str, conn: sqlite3.Connection) -> dict[str, Any]:
    row = conn.execute(
        """
        SELECT payload_json, estimated_cost_per_min_usd, latency_tier, quality_elo
        FROM providers WHERE id = ?
        """,
        (provider,),
    ).fetchone()
    if row is None:
        return {}
    payload = json.loads(row["payload_json"])
    payload["estimated_cost_per_min_usd"] = row["estimated_cost_per_min_usd"]
    payload["latency_tier"] = row["latency_tier"]
    payload["quality_elo"] = row["quality_elo"]
    return payload


def normalize_voice(voice: dict, conn: sqlite3.Connection | None = None,
                    catalog_db_path: str | Path | None = None) -> dict:
    normalized = {**voice}
    local_conn: sqlite3.Connection | None = None
    if conn is None:
        init_catalog_db(catalog_db_path)
        local_conn = sqlite3.connect(get_catalog_db_path(catalog_db_path))
        local_conn.row_factory = sqlite3.Row
        conn = local_conn
    try:
        defaults = _provider_defaults(normalized.get("provider", ""), conn)
        normalized["cost_per_min_usd"] = normalized.get("cost_per_min_usd")
        normalized["latency_tier"] = normalized.get("latency_tier")
        if normalized.get("cost_per_min_usd") is None:
            normalized["cost_per_min_usd"] = defaults.get("estimated_cost_per_min_usd")
        if normalized.get("latency_tier") is None:
            normalized["latency_tier"] = defaults.get("latency_tier")
        normalized["effective_cost_per_min_usd"] = normalized.get("cost_per_min_usd")
        normalized["effective_latency_tier"] = normalized.get("latency_tier")
        normalized["effective_quality_elo"] = defaults.get("quality_elo")
        return normalized
    finally:
        if local_conn is not None:
            local_conn.close()


def _serialize_voice(voice: dict, conn: sqlite3.Connection) -> tuple[Any, ...]:
    voice = normalize_voice(voice, conn=conn)
    now = _now()
    payload = json.dumps(voice, ensure_ascii=False)
    return (
        voice["id"],
        voice["provider"],
        voice.get("provider_voice_id", ""),
        voice.get("name", ""),
        voice.get("description"),
        voice.get("gender"),
        voice.get("age_group"),
        voice.get("accent"),
        voice.get("language"),
        voice.get("provider_model"),
        voice.get("effective_cost_per_min_usd"),
        voice.get("effective_latency_tier"),
        voice.get("effective_quality_elo"),
        payload,
        voice.get("status", "active"),
        voice.get("metadata_source"),
        voice.get("enrichment_status"),
        int(voice.get("enrichment_attempts", 0) or 0),
        voice.get("first_seen"),
        voice.get("last_seen"),
        voice.get("last_synced"),
        voice.get("last_verified"),
        now,
        now,
    )


def upsert_voices(voices: list[dict], catalog_db_path: str | Path | None = None,
                  force_version_bump: bool = True) -> int:
    if not voices:
        return 0
    init_catalog_db(catalog_db_path)
    with connect_catalog(catalog_db_path) as conn:
        rows = [_serialize_voice(voice, conn) for voice in voices]
        conn.executemany(
            """
            INSERT INTO voices (
                id, provider, provider_voice_id, name, description, gender, age_group,
                accent, language, provider_model, effective_cost_per_min_usd,
                effective_latency_tier, effective_quality_elo, payload_json, status,
                metadata_source, enrichment_status, enrichment_attempts, first_seen,
                last_seen, last_synced, last_verified, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                provider=excluded.provider,
                provider_voice_id=excluded.provider_voice_id,
                name=excluded.name,
                description=excluded.description,
                gender=excluded.gender,
                age_group=excluded.age_group,
                accent=excluded.accent,
                language=excluded.language,
                provider_model=excluded.provider_model,
                effective_cost_per_min_usd=excluded.effective_cost_per_min_usd,
                effective_latency_tier=excluded.effective_latency_tier,
                effective_quality_elo=excluded.effective_quality_elo,
                payload_json=excluded.payload_json,
                status=excluded.status,
                metadata_source=excluded.metadata_source,
                enrichment_status=excluded.enrichment_status,
                enrichment_attempts=excluded.enrichment_attempts,
                first_seen=COALESCE(voices.first_seen, excluded.first_seen),
                last_seen=excluded.last_seen,
                last_synced=excluded.last_synced,
                last_verified=excluded.last_verified,
                updated_at=excluded.updated_at
            """,
            rows,
        )
        if force_version_bump:
            _bump_catalog_version(conn)
    return len(rows)


def load_voices(provider: str | None = None,
                catalog_db_path: str | Path | None = None,
                legacy_catalog_dir: str | Path | None = None,
                include_deprecated: bool = False) -> list[dict]:
    ensure_catalog_seeded(catalog_db_path=catalog_db_path, legacy_catalog_dir=legacy_catalog_dir)
    clauses: list[str] = []
    params: list[Any] = []
    if provider:
        clauses.append("provider = ?")
        params.append(provider)
    if not include_deprecated:
        clauses.append("(status IS NULL OR status != 'deprecated')")
    query = "SELECT payload_json FROM voices"
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    query += " ORDER BY provider, name"
    with connect_catalog(catalog_db_path) as conn:
        rows = conn.execute(query, tuple(params)).fetchall()
    return [json.loads(row["payload_json"]) for row in rows]


def list_providers(catalog_db_path: str | Path | None = None,
                   legacy_catalog_dir: str | Path | None = None) -> list[str]:
    ensure_catalog_seeded(catalog_db_path=catalog_db_path, legacy_catalog_dir=legacy_catalog_dir)
    with connect_catalog(catalog_db_path) as conn:
        rows = conn.execute("SELECT DISTINCT provider FROM voices ORDER BY provider").fetchall()
    return [row["provider"] for row in rows]


def get_voice(voice_id: str, catalog_db_path: str | Path | None = None) -> dict | None:
    ensure_catalog_seeded(catalog_db_path=catalog_db_path)
    with connect_catalog(catalog_db_path) as conn:
        row = conn.execute("SELECT payload_json FROM voices WHERE id = ?", (voice_id,)).fetchone()
    return None if row is None else json.loads(row["payload_json"])


def list_provider_costs(catalog_db_path: str | Path | None = None) -> list[dict]:
    ensure_catalog_seeded(catalog_db_path=catalog_db_path)
    with connect_catalog(catalog_db_path) as conn:
        rows = conn.execute(
            """
            SELECT id, name, estimated_cost_per_min_usd, pricing_updated, payload_json
            FROM providers
            WHERE estimated_cost_per_min_usd IS NOT NULL
            ORDER BY estimated_cost_per_min_usd, id
            """
        ).fetchall()
    out = []
    for row in rows:
        payload = json.loads(row["payload_json"])
        pricing = payload.get("pricing", {})
        out.append(
            {
                "provider": row["id"],
                "name": row["name"],
                "cost_per_min_usd": row["estimated_cost_per_min_usd"],
                "pricing_updated": row["pricing_updated"],
                "notes": pricing.get("notes"),
                "cost_tier": pricing.get("cost_tier"),
            }
        )
    return out


def get_provider_record(provider: str, catalog_db_path: str | Path | None = None) -> dict | None:
    ensure_catalog_seeded(catalog_db_path=catalog_db_path)
    with connect_catalog(catalog_db_path) as conn:
        row = conn.execute("SELECT payload_json FROM providers WHERE id = ?", (provider,)).fetchone()
    return None if row is None else json.loads(row["payload_json"])


def save_provider_record(provider: str, payload: dict, catalog_db_path: str | Path | None = None) -> None:
    ensure_catalog_seeded(catalog_db_path=catalog_db_path)
    pricing = payload.get("pricing", {}) if isinstance(payload, dict) else {}
    technical = payload.get("technical", {}) if isinstance(payload, dict) else {}
    quality = payload.get("quality", {}) if isinstance(payload, dict) else {}
    with connect_catalog(catalog_db_path) as conn:
        conn.execute(
            """
            INSERT INTO providers (
                id, name, payload_json, estimated_cost_per_min_usd, latency_tier,
                quality_elo, pricing_updated, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name,
                payload_json=excluded.payload_json,
                estimated_cost_per_min_usd=excluded.estimated_cost_per_min_usd,
                latency_tier=excluded.latency_tier,
                quality_elo=COALESCE(excluded.quality_elo, providers.quality_elo),
                pricing_updated=excluded.pricing_updated,
                updated_at=excluded.updated_at
            """,
            (
                provider,
                payload.get("name", provider.title()),
                json.dumps(payload, ensure_ascii=False),
                pricing.get("estimated_cost_per_minute"),
                technical.get("latency_tier"),
                quality.get("arena_elo") or _DEFAULT_PROVIDER_ELO.get(provider),
                pricing.get("pricing_updated"),
                _now(),
            ),
        )
        _bump_catalog_version(conn)


def list_hosting_costs(catalog_db_path: str | Path | None = None) -> list[dict]:
    ensure_catalog_seeded(catalog_db_path=catalog_db_path)
    with connect_catalog(catalog_db_path) as conn:
        rows = conn.execute(
            """
            SELECT id, name, estimated_cost_per_min_self_hosted, payload_json
            FROM hosting_models
            WHERE estimated_cost_per_min_self_hosted IS NOT NULL
            ORDER BY estimated_cost_per_min_self_hosted, id
            """
        ).fetchall()
    out = []
    for row in rows:
        payload = json.loads(row["payload_json"])
        out.append(
            {
                "model": row["id"],
                "name": row["name"],
                "cost_per_min_usd": row["estimated_cost_per_min_self_hosted"],
                "hardware": payload.get("hardware"),
                "quality_tier": payload.get("quality_tier"),
                "notes": payload.get("notes"),
            }
        )
    return out


def get_cost_notes(catalog_db_path: str | Path | None = None) -> dict:
    record = get_provider_record("hosting_notes", catalog_db_path=catalog_db_path)
    if record:
        return record
    return {}


def create_analysis_run(brief: str, use_case: str, status: str, result: dict | None = None,
                        cache_hit: bool = False, runtime_db_path: str | Path | None = None) -> int:
    init_runtime_db(runtime_db_path)
    with connect_runtime(runtime_db_path) as conn:
        cursor = conn.execute(
            """
            INSERT INTO analysis_runs (brief, use_case, status, cache_hit, result_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (brief, use_case, status, int(cache_hit), json.dumps(result or {}, ensure_ascii=False), _now()),
        )
        return int(cursor.lastrowid)


def create_audition_run(audition_kind: str, mode: str, brief: str, use_case: str,
                        status: str, output_dir: str | None = None, result: dict | None = None,
                        runtime_db_path: str | Path | None = None) -> int:
    init_runtime_db(runtime_db_path)
    with connect_runtime(runtime_db_path) as conn:
        cursor = conn.execute(
            """
            INSERT INTO audition_runs (
                audition_kind, mode, brief, use_case, status, output_dir, result_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (audition_kind, mode, brief, use_case, status, output_dir, json.dumps(result or {}, ensure_ascii=False), _now()),
        )
        return int(cursor.lastrowid)


def update_audition_run(audition_run_id: int, *, status: str | None = None,
                        output_dir: str | None = None, result: dict | None = None,
                        runtime_db_path: str | Path | None = None) -> None:
    init_runtime_db(runtime_db_path)
    with connect_runtime(runtime_db_path) as conn:
        current = conn.execute(
            "SELECT status, output_dir, result_json FROM audition_runs WHERE id = ?",
            (audition_run_id,),
        ).fetchone()
        if current is None:
            return
        conn.execute(
            """
            UPDATE audition_runs
            SET status = ?, output_dir = ?, result_json = ?
            WHERE id = ?
            """,
            (
                status or current["status"],
                output_dir if output_dir is not None else current["output_dir"],
                json.dumps(result or json.loads(current["result_json"] or "{}"), ensure_ascii=False),
                audition_run_id,
            ),
        )


def add_audition_clip(audition_run_id: int, voice_id: str, script_name: str, script_text: str,
                      file_path: str | None, provider: str | None, status: str,
                      error: str | None = None, runtime_db_path: str | Path | None = None) -> int:
    init_runtime_db(runtime_db_path)
    with connect_runtime(runtime_db_path) as conn:
        cursor = conn.execute(
            """
            INSERT INTO audition_clips (
                audition_run_id, voice_id, script_name, script_text, file_path,
                provider, status, error, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (audition_run_id, voice_id, script_name, script_text, file_path, provider, status, error, _now()),
        )
        return int(cursor.lastrowid)


def record_pipeline_run(stage: str, status: str, *, provider: str | None = None,
                        voice_id: str | None = None, details: dict | None = None,
                        started_at: str | None = None, finished_at: str | None = None,
                        runtime_db_path: str | Path | None = None) -> int:
    init_runtime_db(runtime_db_path)
    with connect_runtime(runtime_db_path) as conn:
        cursor = conn.execute(
            """
            INSERT INTO pipeline_runs (
                stage, provider, voice_id, status, details_json, started_at, finished_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                stage,
                provider,
                voice_id,
                status,
                json.dumps(details or {}, ensure_ascii=False),
                started_at or _now(),
                finished_at,
            ),
        )
        return int(cursor.lastrowid)


def record_provider_sync_run(provider: str, status: str, *, added_count: int = 0,
                             updated_count: int = 0, removed_count: int = 0,
                             total_count: int = 0, error: str | None = None,
                             started_at: str | None = None, finished_at: str | None = None,
                             runtime_db_path: str | Path | None = None) -> int:
    init_runtime_db(runtime_db_path)
    with connect_runtime(runtime_db_path) as conn:
        cursor = conn.execute(
            """
            INSERT INTO provider_sync_runs (
                provider, status, added_count, updated_count, removed_count,
                total_count, error, started_at, finished_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                provider,
                status,
                added_count,
                updated_count,
                removed_count,
                total_count,
                error,
                started_at or _now(),
                finished_at,
            ),
        )
        return int(cursor.lastrowid)


def save_acoustic_features(voice_id: str, features: dict[str, float | None],
                           catalog_db_path: str | Path | None = None) -> None:
    init_catalog_db(catalog_db_path)
    with connect_catalog(catalog_db_path) as conn:
        conn.execute(
            """
            INSERT INTO voice_acoustic_features (
                voice_id, f0_mean_hz, f0_std_hz, speech_rate_syl_per_sec,
                hnr_db, spectral_centroid_hz, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(voice_id) DO UPDATE SET
                f0_mean_hz=excluded.f0_mean_hz,
                f0_std_hz=excluded.f0_std_hz,
                speech_rate_syl_per_sec=excluded.speech_rate_syl_per_sec,
                hnr_db=excluded.hnr_db,
                spectral_centroid_hz=excluded.spectral_centroid_hz,
                updated_at=excluded.updated_at
            """,
            (
                voice_id,
                features.get("f0_mean_hz"),
                features.get("f0_std_hz"),
                features.get("speech_rate_syl_per_sec"),
                features.get("hnr_db"),
                features.get("spectral_centroid_hz"),
                _now(),
            ),
        )
        _bump_catalog_version(conn)


def get_acoustic_features(voice_id: str, catalog_db_path: str | Path | None = None) -> dict | None:
    init_catalog_db(catalog_db_path)
    with connect_catalog(catalog_db_path) as conn:
        row = conn.execute(
            """
            SELECT f0_mean_hz, f0_std_hz, speech_rate_syl_per_sec, hnr_db, spectral_centroid_hz, utmos_score, updated_at
            FROM voice_acoustic_features WHERE voice_id = ?
            """,
            (voice_id,),
        ).fetchone()
    return dict(row) if row else None


def save_utmos_score(voice_id: str, utmos_score: float,
                     catalog_db_path: str | Path | None = None) -> None:
    """Save or update the UTMOS quality score for a voice."""
    init_catalog_db(catalog_db_path)
    with connect_catalog(catalog_db_path) as conn:
        conn.execute(
            """
            INSERT INTO voice_acoustic_features (voice_id, utmos_score, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(voice_id) DO UPDATE SET
                utmos_score=excluded.utmos_score,
                updated_at=excluded.updated_at
            """,
            (voice_id, utmos_score, _now()),
        )
        _bump_catalog_version(conn)


# Artificial Analysis TTS Arena ELO scores (April 2026)
_DEFAULT_PROVIDER_ELO: dict[str, int] = {
    "elevenlabs": 1177,
    "openai": 1135,
    "cartesia": 1090,
    "playht": 1080,
    "wellsaid": 1060,
    "deepgram": 1050,
    "rime": 1020,
}


def seed_provider_elo(catalog_db_path: str | Path | None = None) -> int:
    """Seed provider quality ELO scores from Artificial Analysis TTS Arena."""
    init_catalog_db(catalog_db_path)
    updated = 0
    with connect_catalog(catalog_db_path) as conn:
        for provider_id, elo in _DEFAULT_PROVIDER_ELO.items():
            result = conn.execute(
                """
                UPDATE providers SET quality_elo = ?, updated_at = ?
                WHERE id = ? AND (quality_elo IS NULL OR quality_elo != ?)
                """,
                (elo, _now(), provider_id, elo),
            )
            if result.rowcount > 0:
                updated += 1
        if updated:
            _bump_catalog_version(conn)
    return updated


def save_embedding(voice_id: str, embedding_kind: str, vector: list[float],
                   catalog_db_path: str | Path | None = None) -> None:
    init_catalog_db(catalog_db_path)
    with connect_catalog(catalog_db_path) as conn:
        conn.execute(
            """
            INSERT INTO voice_embeddings (voice_id, embedding_kind, vector_json, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(voice_id, embedding_kind) DO UPDATE SET
                vector_json=excluded.vector_json,
                updated_at=excluded.updated_at
            """,
            (voice_id, embedding_kind, json.dumps(vector), _now()),
        )
        _bump_catalog_version(conn)


def get_embedding(voice_id: str, embedding_kind: str = "clap",
                  catalog_db_path: str | Path | None = None) -> list[float] | None:
    init_catalog_db(catalog_db_path)
    with connect_catalog(catalog_db_path) as conn:
        row = conn.execute(
            "SELECT vector_json FROM voice_embeddings WHERE voice_id = ? AND embedding_kind = ?",
            (voice_id, embedding_kind),
        ).fetchone()
    return json.loads(row["vector_json"]) if row else None


def get_embedding_rows(embedding_kind: str = "clap",
                       catalog_db_path: str | Path | None = None) -> list[tuple[str, list[float]]]:
    init_catalog_db(catalog_db_path)
    with connect_catalog(catalog_db_path) as conn:
        rows = conn.execute(
            "SELECT voice_id, vector_json FROM voice_embeddings WHERE embedding_kind = ?",
            (embedding_kind,),
        ).fetchall()
    return [(row["voice_id"], json.loads(row["vector_json"])) for row in rows]

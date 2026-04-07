import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest import mock
import sys
import types

if "moss" not in sys.modules:
    moss = types.ModuleType("moss")

    class _Dummy:
        def __init__(self, *args, **kwargs):
            pass

    moss.DocumentInfo = _Dummy
    moss.MossClient = _Dummy
    moss.MutationOptions = _Dummy
    moss.QueryOptions = _Dummy
    sys.modules["moss"] = moss


class SearchFallbackTests(unittest.TestCase):
    def test_load_all_voices_reads_from_sqlite(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "voice_catalog.db"
            conn = sqlite3.connect(db_path)
            conn.execute(
                """
                CREATE TABLE voices (
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
                    payload_json TEXT NOT NULL,
                    status TEXT,
                    metadata_source TEXT,
                    enrichment_status TEXT,
                    enrichment_attempts INTEGER DEFAULT 0,
                    first_seen TEXT,
                    last_seen TEXT,
                    last_synced TEXT,
                    last_verified TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
                """
            )
            conn.execute(
                """
                INSERT INTO voices (
                    id, provider, provider_voice_id, name, description, gender, age_group,
                    accent, language, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "openai:alloy",
                    "openai",
                    "alloy",
                    "Alloy",
                    "Warm and clear support voice.",
                    "neutral",
                    "middle",
                    "american",
                    "en",
                    '{"id":"openai:alloy","provider":"openai","provider_voice_id":"alloy","name":"Alloy","description":"Warm and clear support voice.","gender":"neutral","age_group":"middle","accent":"american","language":"en","additional_languages":[],"traits":{},"use_cases":["customer_support"],"personality_tags":[],"style_tags":[],"provider_metadata":{}}',
                ),
            )
            conn.execute("CREATE TABLE catalog_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL, updated_at TEXT NOT NULL)")
            conn.execute("INSERT INTO catalog_meta (key, value, updated_at) VALUES ('catalog_version', '1', 'now')")
            conn.execute("CREATE TABLE providers (id TEXT PRIMARY KEY, name TEXT NOT NULL, payload_json TEXT NOT NULL, estimated_cost_per_min_usd REAL, latency_tier TEXT, pricing_updated TEXT, updated_at TEXT NOT NULL)")
            conn.commit()
            conn.close()

            with mock.patch.dict("os.environ", {"VOICE_AUDITION_CATALOG_DB_PATH": str(db_path)}):
                from audition.search import load_all_voices

                voices = load_all_voices()

            self.assertEqual(len(voices), 1)
            self.assertEqual(voices[0]["id"], "openai:alloy")
            self.assertEqual(voices[0]["provider"], "openai")

    def test_search_results_are_cached_in_runtime_db(self):
        with tempfile.TemporaryDirectory() as tmp:
            catalog_db = Path(tmp) / "voice_catalog.db"
            runtime_db = Path(tmp) / "runtime.db"
            conn = sqlite3.connect(catalog_db)
            conn.execute("CREATE TABLE catalog_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL, updated_at TEXT NOT NULL)")
            conn.execute("INSERT INTO catalog_meta (key, value, updated_at) VALUES ('catalog_version', '1', 'now')")
            conn.execute("CREATE TABLE providers (id TEXT PRIMARY KEY, name TEXT NOT NULL, payload_json TEXT NOT NULL, estimated_cost_per_min_usd REAL, latency_tier TEXT, pricing_updated TEXT, updated_at TEXT NOT NULL)")
            conn.execute(
                """
                CREATE TABLE voices (
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
                    payload_json TEXT NOT NULL,
                    status TEXT,
                    metadata_source TEXT,
                    enrichment_status TEXT,
                    enrichment_attempts INTEGER DEFAULT 0,
                    first_seen TEXT,
                    last_seen TEXT,
                    last_synced TEXT,
                    last_verified TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
                """
            )
            conn.execute(
                """
                INSERT INTO voices (
                    id, provider, provider_voice_id, name, description, gender, age_group, accent,
                    language, provider_model, effective_cost_per_min_usd, effective_latency_tier, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "openai:alloy",
                    "openai",
                    "alloy",
                    "Alloy",
                    "Warm and clear support voice.",
                    "neutral",
                    "middle",
                    "american",
                    "en",
                    "gpt-4o-mini-tts",
                    0.015,
                    "fast",
                    '{"id":"openai:alloy","provider":"openai","provider_voice_id":"alloy","name":"Alloy","description":"Warm and clear support voice.","gender":"neutral","age_group":"middle","accent":"american","language":"en","additional_languages":[],"traits":{},"use_cases":["customer_support"],"personality_tags":[],"style_tags":[],"provider_metadata":{},"effective_cost_per_min_usd":0.015,"effective_latency_tier":"fast"}',
                ),
            )
            conn.commit()
            conn.close()

            with mock.patch.dict(
                "os.environ",
                {
                    "VOICE_AUDITION_CATALOG_DB_PATH": str(catalog_db),
                    "VOICE_AUDITION_RUNTIME_DB_PATH": str(runtime_db),
                },
            ):
                from audition.index import search_voices

                with mock.patch("audition.index.keyword_search", wraps=search_voices.__globals__["keyword_search"]) as keyword_mock:
                    first = search_voices("warm support", top_k=5)
                    second = search_voices("warm support", top_k=5)

                self.assertFalse(first["cache_hit"])
                self.assertTrue(second["cache_hit"])
                self.assertEqual(keyword_mock.call_count, 1)

from __future__ import annotations

import json
import tempfile
import unittest
import sys
import types
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

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

if "enrichment.graph" not in sys.modules:
    graph = types.ModuleType("enrichment.graph")
    graph.init_llm = lambda: None
    graph.enrich_voice_graph = lambda voice: {
        "status": "completed",
        "scores": {"warmth": 0.9},
        "description": "warm",
        "attempt": 1,
    }
    graph._judge_provider = "test-provider"
    graph._judge_config = {"model": "mock"}
    sys.modules["enrichment.graph"] = graph

from audition.audition import detect_use_case, get_profile
from cli.main import main as cli_main
from enrichment import pipeline


class EnrichAuditionTests(unittest.TestCase):
    def _write_catalog(self, root: Path, provider: str, voices: list[dict]) -> None:
        root.mkdir(parents=True, exist_ok=True)
        (root / f"{provider}.json").write_text(json.dumps(voices, indent=2))

    def _rime_voice(self, voice_id: str, status: str | None = None) -> dict:
        voice = {
            "id": f"rime:{voice_id}",
            "provider": "rime",
            "provider_voice_id": voice_id,
            "provider_model": "mist",
            "provider_metadata": {"original_lang_code": "eng"},
            "name": voice_id.title(),
            "gender": "unknown",
            "age_group": "unknown",
            "accent": None,
            "description": None,
            "traits": {
                "warmth": None,
                "energy": None,
                "clarity": None,
                "authority": None,
                "friendliness": None,
                "confidence": None,
            },
            "texture": None,
            "pitch": None,
            "use_cases": [],
            "personality_tags": [],
            "style_tags": [],
            "metadata_source": "provider_api",
            "enrichment": {},
        }
        if status:
            voice["enrichment_status"] = status
        return voice

    def test_preview_estimates_rime_cost_and_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_catalog(root, "rime", [
                self._rime_voice("one"),
                self._rime_voice("two"),
                self._rime_voice("three"),
            ])
            (root / "providers.json").write_text(json.dumps({
                "providers": {
                    "rime": {
                        "name": "Rime",
                        "pricing": {
                            "estimated_cost_per_minute": 0.03,
                            "pricing_updated": "2026-04-06",
                        },
                        "technical": {"latency_tier": "fast"},
                    }
                }
            }))

            with patch.dict("os.environ", {"VOICE_AUDITION_CATALOG_DB_PATH": str(root / "voice_catalog.db")}):
                from audition import db

                db.import_catalog_json(catalog_dir=root, catalog_db_path=root / "voice_catalog.db")
                preview = pipeline.preview_enrich_targets(["rime"], limit=2, retry=False)

        self.assertEqual(preview["rime"]["eligible_count"], 2)
        self.assertAlmostEqual(preview["rime"]["estimated_cost_usd"], 0.06)

    def test_run_enrich_respects_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_catalog(root, "rime", [
                self._rime_voice("one"),
                self._rime_voice("two"),
                self._rime_voice("three"),
            ])
            with patch.dict("os.environ", {"VOICE_AUDITION_CATALOG_DB_PATH": str(root / "voice_catalog.db")}):
                from audition import db
                db.import_catalog_json(catalog_dir=root, catalog_db_path=root / "voice_catalog.db")

            calls: list[str] = []

            def fake_enrich_voice_graph(voice):
                calls.append(voice["id"])
                return {
                    "status": "completed",
                    "scores": {"warmth": 0.9},
                    "description": "warm",
                    "attempt": 1,
                }

            with patch.dict("os.environ", {"VOICE_AUDITION_CATALOG_DB_PATH": str(root / "voice_catalog.db")}), \
                 patch("enrichment.graph.init_llm"), \
                 patch("enrichment.graph.enrich_voice_graph", side_effect=fake_enrich_voice_graph), \
                 patch("enrichment.graph._judge_provider", "test-provider"), \
                 patch("enrichment.graph._judge_config", {"model": "mock"}), \
                 patch("audition.index.run_index"):
                result = pipeline.run_enrich(["rime"], retry=False, limit=1)

        self.assertEqual(calls, ["rime:one"])
        self.assertEqual(result["enriched"], 1)

    def test_cli_yes_skips_confirmation(self):
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_catalog(root, "rime", [self._rime_voice("one")])
            with patch.dict("os.environ", {"VOICE_AUDITION_CATALOG_DB_PATH": str(root / "voice_catalog.db")}):
                from audition import db
                db.import_catalog_json(catalog_dir=root, catalog_db_path=root / "voice_catalog.db")

            def fake_run_enrich(*args, **kwargs):
                return {"enriched": 0, "failed": 0, "pending": 0, "completed": 0}

            with patch.dict("os.environ", {"VOICE_AUDITION_CATALOG_DB_PATH": str(root / "voice_catalog.db")}), \
                 patch("cli.main.click.confirm") as confirm_mock, \
                 patch("enrichment.pipeline.run_enrich", side_effect=fake_run_enrich):
                result = runner.invoke(cli_main, ["enrich", "rime", "--limit", "1", "--yes"])

        self.assertEqual(result.exit_code, 0, result.output)
        confirm_mock.assert_not_called()

    def test_education_use_case_has_phrase_bank(self):
        self.assertEqual(detect_use_case("I need voice text for a classroom lesson"), "education")
        profile = get_profile("education")
        self.assertIn("Let's work through this together.", profile["scripts"][0]["text"])


if __name__ == "__main__":
    unittest.main()

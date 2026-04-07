import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest import mock


class VoiceDatabaseTests(unittest.TestCase):
    def test_import_catalog_json_populates_database(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            catalog_dir = base / "catalog"
            catalog_dir.mkdir()
            (catalog_dir / "rime.json").write_text(json.dumps([
                {
                    "id": "rime:mist:test_voice",
                    "provider": "rime",
                    "provider_voice_id": "mist:test_voice",
                    "name": "Test Voice",
                    "gender": "unknown",
                    "age_group": "unknown",
                    "language": "en",
                    "additional_languages": [],
                    "traits": {},
                    "use_cases": [],
                    "personality_tags": [],
                    "style_tags": [],
                    "provider_metadata": {},
                }
            ]))

            catalog_db_path = base / "voice_catalog.db"
            with mock.patch.dict("os.environ", {"VOICE_AUDITION_CATALOG_DB_PATH": str(catalog_db_path)}):
                from audition import db

                db.init_catalog_db(catalog_db_path=catalog_db_path)
                imported = db.import_catalog_json(catalog_dir=catalog_dir, catalog_db_path=catalog_db_path)
                self.assertEqual(imported, 1)

                conn = sqlite3.connect(catalog_db_path)
                row = conn.execute("SELECT id, provider, name FROM voices").fetchone()
                conn.close()

                self.assertEqual(row, ("rime:mist:test_voice", "rime", "Test Voice"))

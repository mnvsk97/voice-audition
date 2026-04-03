"""
Run all provider sync scripts and print a summary.
Usage: python scripts/sync_all.py
"""

import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent
SYNC_SCRIPTS = [
    "sync_elevenlabs.py",
    "sync_rime.py",
    "sync_openai.py",
    "sync_deepgram.py",
    # Add new providers here:
    # "sync_cartesia.py",  # requires API key
    # "sync_playht.py",    # requires API key
    # "sync_azure.py",     # requires API key
]


def main():
    results = {}
    for script in SYNC_SCRIPTS:
        path = SCRIPTS_DIR / script
        if not path.exists():
            print(f"SKIP {script} (not found)")
            continue
        print(f"\n{'='*60}")
        print(f"Running {script}...")
        print(f"{'='*60}")
        result = subprocess.run(
            [sys.executable, str(path)],
            capture_output=False,
        )
        results[script] = "OK" if result.returncode == 0 else f"FAILED (exit {result.returncode})"

    print(f"\n{'='*60}")
    print("SYNC SUMMARY")
    print(f"{'='*60}")
    for script, status in results.items():
        print(f"  {script}: {status}")

    # Count total voices
    catalog_dir = SCRIPTS_DIR.parent / "catalog"
    total = 0
    for f in catalog_dir.glob("*.json"):
        import json
        voices = json.loads(f.read_text())
        count = len(voices)
        total += count
        print(f"  {f.name}: {count} voices")
    print(f"  TOTAL: {total} voices")


if __name__ == "__main__":
    main()

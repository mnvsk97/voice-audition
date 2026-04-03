"""Run all provider syncs."""

import sys
import traceback


def main():
    providers = [
        ("elevenlabs", "sync_elevenlabs"),
        ("rime", "sync_rime"),
        ("deepgram", "sync_deepgram"),
        ("openai", "sync_openai"),
    ]

    results = {}

    for name, module_name in providers:
        try:
            print(f"\n{'='*60}")
            print(f"Syncing {name}...")
            print(f"{'='*60}")
            mod = __import__(module_name)
            mod.sync()
            results[name] = "ok"
        except Exception as e:
            print(f"[{name}] FAILED: {e}")
            traceback.print_exc()
            results[name] = f"failed: {e}"

    print(f"\n{'='*60}")
    print("Sync complete:")
    for name, status in results.items():
        print(f"  {name}: {status}")

    if any("failed" in str(v) for v in results.values()):
        sys.exit(1)


if __name__ == "__main__":
    main()

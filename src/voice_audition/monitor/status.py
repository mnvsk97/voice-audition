import json
from datetime import datetime, timezone
from pathlib import Path

import httpx

CATALOG_DIR = Path(__file__).resolve().parent.parent.parent.parent / "catalog"
PROVIDERS_FILE = CATALOG_DIR / "providers.json"

STATUS_PAGES = {
    "elevenlabs": "https://status.elevenlabs.io/api/v2/summary.json",
    "openai": "https://status.openai.com/api/v2/summary.json",
    "deepgram": "https://status.deepgram.com/api/v2/summary.json",
    "cartesia": None,
    "rime": None,
    "playht": None,
}

INCIDENT_URLS = {
    "elevenlabs": "https://status.elevenlabs.io/api/v2/incidents.json",
    "openai": "https://status.openai.com/api/v2/incidents.json",
    "deepgram": "https://status.deepgram.com/api/v2/incidents.json",
}

_TIMEOUT = 15


def fetch_status(provider: str) -> dict | None:
    url = STATUS_PAGES.get(provider)
    if url is None:
        return None
    try:
        resp = httpx.get(url, timeout=_TIMEOUT, follow_redirects=True)
        resp.raise_for_status()
        return resp.json()
    except (httpx.HTTPError, json.JSONDecodeError):
        return None


def fetch_incidents(provider: str, days: int = 90) -> list[dict]:
    url = INCIDENT_URLS.get(provider)
    if url is None:
        return []
    try:
        resp = httpx.get(url, timeout=_TIMEOUT, follow_redirects=True)
        resp.raise_for_status()
        data = resp.json()
    except (httpx.HTTPError, json.JSONDecodeError):
        return []

    cutoff = datetime.now(timezone.utc).timestamp() - days * 86400
    incidents = []
    for inc in data.get("incidents", []):
        created = inc.get("created_at", "")
        try:
            created_dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            continue
        if created_dt.timestamp() < cutoff:
            continue

        resolved = inc.get("resolved_at")
        duration_min = None
        if resolved:
            try:
                resolved_dt = datetime.fromisoformat(resolved.replace("Z", "+00:00"))
                duration_min = (resolved_dt - created_dt).total_seconds() / 60
            except (ValueError, AttributeError):
                pass

        incidents.append({
            "name": inc.get("name"),
            "impact": inc.get("impact", "none"),
            "created_at": created,
            "resolved_at": resolved,
            "duration_min": duration_min,
            "components": [c.get("name") for c in inc.get("components", [])],
        })
    return incidents


def compute_reliability(provider: str) -> dict:
    now = datetime.now(timezone.utc).isoformat()

    if STATUS_PAGES.get(provider) is None:
        return {
            "score": None,
            "status": "unknown",
            "incidents_90d": None,
            "status_page_url": None,
            "last_checked": now,
        }

    summary = fetch_status(provider)
    incidents = fetch_incidents(provider, days=90)

    if summary:
        indicator = summary.get("status", {}).get("indicator", "none")
        page_url = summary.get("page", {}).get("url")
    else:
        indicator = "none"
        page_url = None

    status_map = {"none": "operational", "minor": "degraded", "major": "outage", "critical": "outage"}
    status_label = status_map.get(indicator, "unknown")

    # Scoring: current status (40%), incident count (30%), severity (20%), MTTR (10%)
    status_points = {"none": 40, "minor": 25, "major": 10, "critical": 0}
    s_current = status_points.get(indicator, 0)

    n = len(incidents)
    if n == 0:
        s_count = 30
    elif n <= 2:
        s_count = 24
    elif n <= 5:
        s_count = 18
    elif n <= 10:
        s_count = 12
    else:
        s_count = 6

    if n == 0:
        s_severity = 20
    else:
        impacts = [inc["impact"] for inc in incidents]
        if any(i == "critical" for i in impacts):
            s_severity = 4
        elif all(i in ("none", "minor") for i in impacts):
            s_severity = 20
        else:
            s_severity = 12

    durations = [inc["duration_min"] for inc in incidents if inc["duration_min"] is not None]
    if not durations:
        s_mttr = 10  # no resolved incidents = assume good
    else:
        avg_min = sum(durations) / len(durations)
        if avg_min < 30:
            s_mttr = 10
        elif avg_min < 60:
            s_mttr = 8
        elif avg_min < 240:
            s_mttr = 5
        else:
            s_mttr = 2

    score = s_current + s_count + s_severity + s_mttr

    return {
        "score": score,
        "status": status_label,
        "incidents_90d": n,
        "status_page_url": page_url,
        "last_checked": now,
    }


def run_monitor():
    if not PROVIDERS_FILE.exists():
        print(f"providers.json not found at {PROVIDERS_FILE}")
        return

    data = json.loads(PROVIDERS_FILE.read_text())
    providers = data.get("providers", {})

    results = {}
    for name in STATUS_PAGES:
        rel = compute_reliability(name)
        results[name] = rel
        if name in providers:
            providers[name]["reliability"] = rel

    PROVIDERS_FILE.write_text(json.dumps(data, indent=2) + "\n")

    # Print summary table
    print(f"{'Provider':<14}{'Status':<14}{'Score':>5}  {'Incidents(90d)':>14}")
    for name in sorted(results):
        r = results[name]
        score_str = str(r["score"]) if r["score"] is not None else "-"
        inc_str = str(r["incidents_90d"]) if r["incidents_90d"] is not None else "-"
        print(f"{name:<14}{r['status']:<14}{score_str:>5}  {inc_str:>14}")


if __name__ == "__main__":
    run_monitor()

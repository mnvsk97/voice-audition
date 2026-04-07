from datetime import datetime, timezone

import httpx

from audition.db import get_provider_record, save_provider_record

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


def fetch_status(provider: str) -> dict | None:
    url = STATUS_PAGES.get(provider)
    if not url:
        return None
    try:
        resp = httpx.get(url, timeout=15, follow_redirects=True)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None


def fetch_incidents(provider: str, days: int = 90) -> list[dict]:
    url = INCIDENT_URLS.get(provider)
    if not url:
        return []
    try:
        resp = httpx.get(url, timeout=15, follow_redirects=True)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return []

    cutoff = datetime.now(timezone.utc).timestamp() - days * 86400
    incidents = []
    for inc in data.get("incidents", []):
        try:
            created_dt = datetime.fromisoformat(inc["created_at"].replace("Z", "+00:00"))
        except (ValueError, KeyError):
            continue
        if created_dt.timestamp() < cutoff:
            continue
        duration = None
        if inc.get("resolved_at"):
            try:
                resolved_dt = datetime.fromisoformat(inc["resolved_at"].replace("Z", "+00:00"))
                duration = (resolved_dt - created_dt).total_seconds() / 60
            except ValueError:
                pass
        incidents.append(
            {
                "name": inc.get("name"),
                "impact": inc.get("impact", "none"),
                "created_at": inc["created_at"],
                "duration_min": duration,
            }
        )
    return incidents


def compute_reliability(provider: str) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    if not STATUS_PAGES.get(provider):
        return {"score": None, "status": "unknown", "incidents_90d": None, "last_checked": now}

    summary = fetch_status(provider)
    incidents = fetch_incidents(provider, days=90)
    indicator = (summary or {}).get("status", {}).get("indicator", "none")

    status_map = {"none": "operational", "minor": "degraded", "major": "outage", "critical": "outage"}
    score_parts = [
        {"none": 40, "minor": 25, "major": 10, "critical": 0}.get(indicator, 0),
        30 if len(incidents) == 0 else 24 if len(incidents) <= 2 else 18 if len(incidents) <= 5 else 12 if len(incidents) <= 10 else 6,
        20 if not incidents else (4 if any(i["impact"] == "critical" for i in incidents) else 20 if all(i["impact"] in ("none", "minor") for i in incidents) else 12),
    ]
    durations = [i["duration_min"] for i in incidents if i["duration_min"] is not None]
    avg = sum(durations) / len(durations) if durations else 0
    score_parts.append(10 if not durations else 10 if avg < 30 else 8 if avg < 60 else 5 if avg < 240 else 2)

    return {
        "score": sum(score_parts),
        "status": status_map.get(indicator, "unknown"),
        "incidents_90d": len(incidents),
        "last_checked": now,
    }


def run_monitor():
    results = {}
    for name in STATUS_PAGES:
        reliability = compute_reliability(name)
        results[name] = reliability
        record = get_provider_record(name)
        if record:
            record["reliability"] = reliability
            save_provider_record(name, record)

    print(f"{'Provider':<14}{'Status':<14}{'Score':>5}  {'Incidents':>9}")
    for name in sorted(results):
        reliability = results[name]
        print(f"{name:<14}{reliability['status']:<14}{reliability['score'] or '-':>5}  {reliability['incidents_90d'] or '-':>9}")

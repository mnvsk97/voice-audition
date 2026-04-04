import json
from pathlib import Path

CATALOG_DIR = Path(__file__).resolve().parent.parent.parent / "catalog"


def _load_api_costs() -> dict[str, float]:
    path = CATALOG_DIR / "providers.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text())
    providers = data.get("providers", {})
    return {
        name: info.get("pricing", {}).get("estimated_cost_per_minute", 0)
        for name, info in providers.items()
        if info.get("pricing", {}).get("estimated_cost_per_minute")
    }


def _load_self_hosted() -> dict[str, dict]:
    path = CATALOG_DIR / "hosting.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text())
    models = data.get("open_source_models", {})
    result = {}
    for key, info in models.items():
        cost = info.get("estimated_cost_per_min_self_hosted", 0)
        latency = info.get("latency_ms", "?")
        quality = info.get("quality_tier", "?")
        hardware = info.get("hardware", "?")
        name = info.get("name", key)
        # Create fixed-cost entry for CPU models, per-min for GPU
        if hardware == "CPU":
            result[f"{key}_cpu"] = {
                "name": f"{name} (CPU VM)",
                "monthly_cost": 50 if "piper" not in key else 20,
                "latency_ms": latency,
                "quality": quality,
            }
        else:
            result[f"{key}_gpu"] = {
                "name": f"{name} (GPU)",
                "cost_per_min": cost,
                "latency_ms": latency,
                "quality": quality,
            }
    return result


def calculate_costs(minutes_per_month: int) -> dict:
    api_costs = _load_api_costs()
    self_hosted = _load_self_hosted()

    results = {"volume_minutes_per_month": minutes_per_month, "api": {}, "self_hosted": {}}

    for provider, cost_per_min in api_costs.items():
        monthly = minutes_per_month * cost_per_min
        results["api"][provider] = {
            "cost_per_min": cost_per_min,
            "monthly_cost": round(monthly, 2),
        }

    for key, info in self_hosted.items():
        if "cost_per_min" in info:
            monthly = minutes_per_month * info["cost_per_min"]
        else:
            monthly = info.get("monthly_cost", 0)
        results["self_hosted"][key] = {
            "name": info["name"],
            "monthly_cost": round(monthly, 2),
            "latency_ms": info.get("latency_ms", "?"),
            "quality": info.get("quality", "?"),
        }

    if results["api"]:
        cheapest_api = min(results["api"].items(), key=lambda x: x[1]["monthly_cost"])
    else:
        cheapest_api = ("none", {"cost_per_min": 0, "monthly_cost": 0})

    if results["self_hosted"]:
        cheapest_self = min(results["self_hosted"].items(), key=lambda x: x[1]["monthly_cost"])
    else:
        cheapest_self = ("none", {"name": "none", "monthly_cost": 0})

    results["recommendation"] = {
        "cheapest_api": {"provider": cheapest_api[0], **cheapest_api[1]},
        "cheapest_self_hosted": {"option": cheapest_self[0], **cheapest_self[1]},
        "savings_vs_cheapest_api": round(cheapest_api[1]["monthly_cost"] - cheapest_self[1]["monthly_cost"], 2),
    }

    return results


def format_cost_table(results: dict) -> str:
    lines = []
    vol = results["volume_minutes_per_month"]
    lines.append(f"Cost comparison at {vol:,} minutes/month")
    lines.append("")

    lines.append("  API Providers:")
    lines.append(f"  {'Provider':<20} {'$/min':>8} {'Monthly':>12}")
    lines.append(f"  {'-'*42}")
    for provider, data in sorted(results["api"].items(), key=lambda x: x[1]["monthly_cost"]):
        lines.append(f"  {provider:<20} ${data['cost_per_min']:.3f}   ${data['monthly_cost']:>10,.2f}")

    lines.append("")
    lines.append("  Self-Hosted:")
    lines.append(f"  {'Option':<28} {'Monthly':>12} {'Latency':>10} {'Quality':>10}")
    lines.append(f"  {'-'*62}")
    for key, data in sorted(results["self_hosted"].items(), key=lambda x: x[1]["monthly_cost"]):
        lat = f"{data['latency_ms']}ms" if data.get('latency_ms') != '?' else '?'
        lines.append(f"  {data['name']:<28} ${data['monthly_cost']:>10,.2f} {lat:>10} {data.get('quality', '?'):>10}")

    rec = results["recommendation"]
    lines.append("")
    savings = rec["savings_vs_cheapest_api"]
    if savings > 0:
        lines.append(f"  Self-hosting saves ${savings:,.2f}/month vs cheapest API ({rec['cheapest_api']['provider']})")
    else:
        lines.append(f"  API is cheaper at this volume. Use {rec['cheapest_api']['provider']} (${rec['cheapest_api']['monthly_cost']:,.2f}/mo)")

    return "\n".join(lines)


def run_costs(minutes: int):
    results = calculate_costs(minutes)
    print(format_cost_table(results))

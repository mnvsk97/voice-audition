"""Voice cost calculator — compare API providers vs self-hosted at any volume."""

# Provider costs per minute (USD) — keep in sync with providers.json
API_COSTS = {
    "elevenlabs": 0.030,
    "cartesia": 0.015,
    "openai": 0.020,
    "deepgram": 0.010,
    "rime": 0.008,
    "playht": 0.020,
}

# Self-hosted costs (estimated monthly for always-on)
SELF_HOSTED = {
    "kokoro_cpu": {
        "name": "Kokoro (CPU VM)",
        "monthly_cost": 50,
        "max_concurrent": 5,
        "latency_ms": 100,
        "quality": "very_good",
    },
    "kokoro_replicate": {
        "name": "Kokoro (Replicate)",
        "cost_per_min": 0.002,
        "latency_ms": 100,
        "quality": "very_good",
    },
    "orpheus_gpu": {
        "name": "Orpheus (H100 MIG)",
        "monthly_cost": 2800,
        "max_concurrent": 20,
        "latency_ms": 150,
        "quality": "excellent",
    },
    "orpheus_replicate": {
        "name": "Orpheus (Replicate)",
        "cost_per_min": 0.005,
        "latency_ms": 150,
        "quality": "excellent",
    },
    "piper_cpu": {
        "name": "Piper (CPU VM)",
        "monthly_cost": 20,
        "max_concurrent": 10,
        "latency_ms": 50,
        "quality": "good",
    },
}


def calculate_costs(minutes_per_month: int) -> dict:
    """Calculate costs for all options at a given volume."""
    results = {"volume_minutes_per_month": minutes_per_month, "api": {}, "self_hosted": {}}

    for provider, cost_per_min in API_COSTS.items():
        monthly = minutes_per_month * cost_per_min
        results["api"][provider] = {
            "cost_per_min": cost_per_min,
            "monthly_cost": round(monthly, 2),
        }

    for key, info in SELF_HOSTED.items():
        if "cost_per_min" in info:
            monthly = minutes_per_month * info["cost_per_min"]
        else:
            monthly = info["monthly_cost"]
        results["self_hosted"][key] = {
            "name": info["name"],
            "monthly_cost": round(monthly, 2),
            "latency_ms": info["latency_ms"],
            "quality": info["quality"],
        }

    # Find cheapest API and cheapest self-hosted
    cheapest_api = min(results["api"].items(), key=lambda x: x[1]["monthly_cost"])
    cheapest_self = min(results["self_hosted"].items(), key=lambda x: x[1]["monthly_cost"])

    results["recommendation"] = {
        "cheapest_api": {"provider": cheapest_api[0], **cheapest_api[1]},
        "cheapest_self_hosted": {"option": cheapest_self[0], **cheapest_self[1]},
        "savings_vs_cheapest_api": round(cheapest_api[1]["monthly_cost"] - cheapest_self[1]["monthly_cost"], 2),
    }

    return results


def format_cost_table(results: dict) -> str:
    """Format cost comparison as a readable table."""
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
        lines.append(f"  {data['name']:<28} ${data['monthly_cost']:>10,.2f} {data['latency_ms']:>8}ms {data['quality']:>10}")

    rec = results["recommendation"]
    lines.append("")
    savings = rec["savings_vs_cheapest_api"]
    if savings > 0:
        lines.append(f"  Self-hosting saves ${savings:,.2f}/month vs cheapest API ({rec['cheapest_api']['provider']})")
    else:
        lines.append(f"  API is cheaper at this volume. Use {rec['cheapest_api']['provider']} (${rec['cheapest_api']['monthly_cost']:,.2f}/mo)")

    return "\n".join(lines)


def run_costs(minutes: int):
    """CLI entry point."""
    results = calculate_costs(minutes)
    print(format_cost_table(results))

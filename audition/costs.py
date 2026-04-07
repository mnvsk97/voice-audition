from __future__ import annotations

from audition.db import list_hosting_costs, list_provider_costs


def _format_money(value: float) -> str:
    return f"${value:,.2f}"


def _monthly_cost(rate_per_minute: float, minutes_per_month: int) -> float:
    return round(rate_per_minute * minutes_per_month, 2)


def calculate_voice_costs(minutes_per_month: int) -> dict:
    if minutes_per_month < 0:
        raise ValueError("minutes_per_month must be non-negative")

    api_providers = []
    for row in list_provider_costs():
        api_providers.append(
            {
                **row,
                "monthly_cost_usd": _monthly_cost(row["cost_per_min_usd"], minutes_per_month),
            }
        )

    self_hosted_models = []
    for row in list_hosting_costs():
        self_hosted_models.append(
            {
                **row,
                "monthly_cost_usd": _monthly_cost(row["cost_per_min_usd"], minutes_per_month),
            }
        )

    cheapest_api = api_providers[0] if api_providers else None
    cheapest_self_hosted = self_hosted_models[0] if self_hosted_models else None

    return {
        "minutes_per_month": minutes_per_month,
        "api_providers": api_providers,
        "self_hosted_models": self_hosted_models,
        "cheapest_api": cheapest_api,
        "cheapest_self_hosted": cheapest_self_hosted,
        "notes": {},
    }


def render_voice_costs(result: dict) -> str:
    lines = [f"Monthly volume: {result['minutes_per_month']:,} minutes"]

    api = result.get("api_providers", [])
    if api:
        lines.append("")
        lines.append("API providers")
        for row in api:
            lines.append(
                f"  {row['name']:<12} {_format_money(row['cost_per_min_usd'])}/min"
                f"  {_format_money(row['monthly_cost_usd'])}/mo"
            )

    self_hosted = result.get("self_hosted_models", [])
    if self_hosted:
        lines.append("")
        lines.append("Self-hosted models")
        for row in self_hosted:
            lines.append(
                f"  {row['name']:<12} {_format_money(row['cost_per_min_usd'])}/min"
                f"  {_format_money(row['monthly_cost_usd'])}/mo"
            )

    cheapest_api = result.get("cheapest_api")
    if cheapest_api:
        lines.append("")
        lines.append(
            "Cheapest API: "
            f"{cheapest_api['name']} at {_format_money(cheapest_api['monthly_cost_usd'])}/mo"
        )

    cheapest_self_hosted = result.get("cheapest_self_hosted")
    if cheapest_self_hosted:
        lines.append(
            "Cheapest self-hosted: "
            f"{cheapest_self_hosted['name']} at {_format_money(cheapest_self_hosted['monthly_cost_usd'])}/mo"
        )

    return "\n".join(lines)

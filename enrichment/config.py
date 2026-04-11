from __future__ import annotations

import os
import re
from pathlib import Path

import yaml

CONFIG_FILENAME = "enrichment.yaml"
_ENV_VAR_RE = re.compile(r"\$\{([^}]+)\}")


def _resolve_env(value):
    """Recursively resolve ${ENV_VAR} references in config values."""
    if isinstance(value, str):
        def replacer(m):
            return os.environ.get(m.group(1), "")
        return _ENV_VAR_RE.sub(replacer, value)
    if isinstance(value, dict):
        return {k: _resolve_env(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_resolve_env(v) for v in value]
    return value


def find_config() -> Path | None:
    """Look for enrichment.yaml — check cwd first, then walk up from module."""
    # Check cwd first (pip-installed users)
    cwd = Path.cwd() / CONFIG_FILENAME
    if cwd.exists():
        return cwd
    # Walk up from this file (dev installs)
    current = Path(__file__).resolve().parent
    for _ in range(5):
        candidate = current / CONFIG_FILENAME
        if candidate.exists():
            return candidate
        current = current.parent
    return None


def load_config() -> dict:
    """Load and resolve enrichment config."""
    path = find_config()
    if path is None:
        raise FileNotFoundError(
            f"No {CONFIG_FILENAME} found. Create one in the project root.\n"
            f"See: https://github.com/mnvsk97/voice-audition#enrichment-config"
        )
    raw = yaml.safe_load(path.read_text())
    config = _resolve_env(raw.get("enrichment", {}))
    return config


def get_provider_config(config: dict) -> tuple[str, dict]:
    """Get the active provider name and its config section."""
    provider = config.get("provider", "mlx")
    provider_config = config.get(provider, {})
    if not provider_config:
        raise ValueError(
            f"Provider '{provider}' selected but no config section found in {CONFIG_FILENAME}.\n"
            f"Add an '{provider}:' section with the required credentials."
        )
    return provider, provider_config


# --- Per-Provider Credential Validation ---

_PROVIDER_REQUIREMENTS = {
    "openai": {
        "required": ["api_key"],
        "optional": ["base_url", "model"],
        "help": "Set OPENAI_API_KEY env var or add api_key to the openai section.",
    },
    "gemini": {
        "required_one_of": ["api_key", "credentials_file"],
        "optional": ["model"],
        "help": "Set GEMINI_API_KEY env var, or provide a credentials_file path.",
    },
    "anthropic": {
        "required": ["api_key"],
        "optional": ["model"],
        "help": "Set ANTHROPIC_API_KEY env var or add api_key to the anthropic section.",
    },
    "bedrock": {
        "required": ["region", "access_key_id", "secret_access_key"],
        "optional": ["session_token", "model"],
        "help": "Set AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and configure region.",
    },
    "ollama": {
        "required": ["base_url"],
        "optional": ["model"],
        "help": "Ensure Ollama is running. Default: http://localhost:11434",
    },
    "mlx": {
        "required": [],
        "optional": ["model_id"],
        "help": "Requires Apple Silicon and pip install 'voice-audition[enrich]'.",
    },
}


def validate_credentials(provider: str, provider_config: dict) -> None:
    """Validate that required credentials are present for the provider. Raises on failure."""
    reqs = _PROVIDER_REQUIREMENTS.get(provider)
    if reqs is None:
        raise ValueError(f"Unknown provider: '{provider}'. Choose from: {', '.join(_PROVIDER_REQUIREMENTS)}")

    missing = []

    # Check required fields
    for field in reqs.get("required", []):
        val = provider_config.get(field)
        if not val or val == f"${{{field.upper()}}}":
            missing.append(field)

    # Check required_one_of (at least one must be set)
    one_of = reqs.get("required_one_of", [])
    if one_of:
        has_any = any(
            provider_config.get(f) and provider_config.get(f) != f"${{{f.upper()}}}"
            for f in one_of
        )
        if not has_any:
            missing.append(f"one of: {', '.join(one_of)}")

    if missing:
        raise ValueError(
            f"Missing credentials for provider '{provider}':\n"
            f"  Missing: {', '.join(missing)}\n"
            f"  {reqs['help']}"
        )

    # Provider-specific checks
    if provider == "ollama":
        _check_ollama(provider_config)
    if provider == "mlx":
        _check_mlx()
    if provider == "gemini" and provider_config.get("credentials_file"):
        _check_file_exists(provider_config["credentials_file"], "credentials_file")


def _check_ollama(config: dict) -> None:
    """Check if Ollama is reachable."""
    import httpx
    base_url = config.get("base_url", "http://localhost:11434")
    try:
        resp = httpx.get(f"{base_url}/api/tags", timeout=5)
        resp.raise_for_status()
    except Exception:
        raise ConnectionError(
            f"Cannot reach Ollama at {base_url}.\n"
            f"Start it with: ollama serve"
        )


def _check_mlx() -> None:
    """Check if mlx-audio is importable."""
    try:
        import mlx_audio  # noqa: F401
    except ImportError:
        raise ImportError(
            "mlx-audio not installed. Install with: pip install 'voice-audition[enrich]'\n"
            "Requires Apple Silicon Mac."
        )


def _check_file_exists(path: str, name: str) -> None:
    expanded = Path(path).expanduser()
    if not expanded.exists():
        raise FileNotFoundError(f"{name} not found: {expanded}")

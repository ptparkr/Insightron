import tomllib
import logging
from pathlib import Path
from typing import Any, Optional
from functools import cache

logger = logging.getLogger(__name__)

CONFIG_DIR = Path(__file__).resolve().parent.parent.parent.parent
CONFIG_FILE = CONFIG_DIR / "config.toml"


@cache
def _load_config() -> dict[str, Any]:
    """Load and cache config file - O(1) access after initial load."""
    if not CONFIG_FILE.exists():
        logger.warning("Config file not found at %s; using defaults.", CONFIG_FILE)
        return {}

    with open(CONFIG_FILE, "rb") as f:
        return tomllib.load(f)


def get_config(path: str, default: Any = None) -> Any:
    """Get config value by dot-notation path. O(1) after load."""
    config = _load_config()
    keys = path.split(".")

    value = config
    for key in keys:
        if isinstance(value, dict):
            value = value.get(key)
        else:
            return default

        if value is None:
            return default

    return value


def get_all_config() -> dict[str, Any]:
    """Get entire config as dict."""
    return _load_config()


def reload_config() -> None:
    """Reload config file (for hot-reload support)."""
    _load_config.cache_clear()

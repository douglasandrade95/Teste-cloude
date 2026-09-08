"""
Non-secret user preferences (which provider/model is active).

Kept in a plain JSON file next to the vault — no secrets here, only the
provider id and model id the user picked in the Integrações screen.
"""

import json
import logging
import os
from pathlib import Path
from threading import Lock
from typing import Dict, Optional

from app.services.vault import get_vault

logger = logging.getLogger(__name__)

_lock = Lock()

DEFAULT_PREFERENCES: Dict[str, Optional[str]] = {
    "active_provider": None,
    "active_model": None,
}


def _preferences_path() -> Path:
    return get_vault().vault_dir / "preferences.json"


def load_preferences() -> Dict[str, Optional[str]]:
    path = _preferences_path()
    if not path.exists():
        return dict(DEFAULT_PREFERENCES)

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Could not read preferences (%s); using defaults.", exc)
        return dict(DEFAULT_PREFERENCES)

    merged = dict(DEFAULT_PREFERENCES)
    if isinstance(data, dict):
        merged.update({k: data.get(k, v) for k, v in DEFAULT_PREFERENCES.items()})
    return merged


def save_preferences(**updates) -> Dict[str, Optional[str]]:
    with _lock:
        current = load_preferences()
        current.update({k: v for k, v in updates.items() if k in DEFAULT_PREFERENCES})

        path = _preferences_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = path.with_suffix(".json.tmp")
        tmp_path.write_text(json.dumps(current, indent=2), encoding="utf-8")
        os.replace(tmp_path, path)

    return current

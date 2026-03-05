import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter

router = APIRouter(prefix="/api/realms", tags=["realms"])

_REALMS_PATH = Path(__file__).resolve().parents[3] / "shared" / "tbc_data" / "realms.json"
_realms_cache: list[dict[str, Any]] | None = None


def _load_realms() -> list[dict[str, Any]]:
    global _realms_cache
    if _realms_cache is None:
        with open(_REALMS_PATH) as f:
            data: list[dict[str, Any]] = json.load(f)
            _realms_cache = data
    return _realms_cache or []


@router.get("")
async def list_realms() -> list[dict[str, Any]]:
    """Return static list of TBC Classic realms."""
    return _load_realms()

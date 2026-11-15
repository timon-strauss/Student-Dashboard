import os

from dotenv import load_dotenv

load_dotenv()

DEFAULT_CONSOLIDATED_FALLBACK_DAYS = 21.0
DEFAULT_CONSOLIDATED_RETRIEVABILITY = 0.9


def _float_from_env(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    try:
        return float(raw)
    except ValueError as error:
        raise ValueError(f"{name} must be a number, got {raw!r}") from error


def consolidated_fallback_days() -> float:
    days = _float_from_env("CONSOLIDATED_FALLBACK_DAYS", DEFAULT_CONSOLIDATED_FALLBACK_DAYS)
    if days <= 0:
        raise ValueError(f"CONSOLIDATED_FALLBACK_DAYS must be positive, got {days}")
    return days


def consolidated_retrievability() -> float:
    retrievability = _float_from_env("CONSOLIDATED_RETRIEVABILITY", DEFAULT_CONSOLIDATED_RETRIEVABILITY)
    if not 0 < retrievability < 1:
        raise ValueError(f"CONSOLIDATED_RETRIEVABILITY must be between 0 and 1, got {retrievability}")
    return retrievability


def validate() -> None:
    consolidated_fallback_days()
    consolidated_retrievability()

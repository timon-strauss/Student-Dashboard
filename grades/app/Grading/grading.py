import json
from functools import cache
from pathlib import Path

from .exceptions import InvalidPointsError, UnsupportedMaxPointsError

TABLES_FILE = Path(__file__).resolve().parent / "tables.json"


@cache
def _tables() -> dict[int, list[tuple[float, float]]]:
    data = json.loads(TABLES_FILE.read_text(encoding="utf-8"))
    return {
        table["max_points"]: sorted(
            ((row["min_points"], row["grade"]) for row in table["thresholds"]), reverse=True
        )
        for table in data["tables"]
    }


def supported_max_points() -> list[int]:
    return sorted(_tables())


def is_supported(max_points: float) -> bool:
    return max_points in _tables()


def thresholds(max_points: float) -> list[tuple[float, float]]:
    tables = _tables()
    if max_points not in tables:
        raise UnsupportedMaxPointsError(max_points, supported_max_points())
    return list(tables[max_points])


def grade_for(max_points: float, reached_points: float) -> float:
    rows = thresholds(max_points)
    if reached_points < 0:
        raise InvalidPointsError("reached_points must not be negative")
    if reached_points > max_points:
        raise InvalidPointsError("reached_points must not exceed max_points")
    for min_points, grade in rows:
        if reached_points >= min_points:
            return grade
    return rows[-1][1]


def passing_points(max_points: float) -> float:
    return min(min_points for min_points, grade in thresholds(max_points) if grade <= 4.0)

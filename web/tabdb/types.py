from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from typing import Any

class ValidationError(ValueError):
    """Raised when a value cannot be validated/coerced into a given DB type."""

@dataclass(frozen=True)
class DateInvl:
    start: date
    end: date

    def __post_init__(self):
        if self.start > self.end:
            raise ValidationError("dateInvl: start date must be <= end date")

def parse_date(s: str) -> date:
    """
    Parse a date in ISO format YYYY-MM-DD.
    Raises ValidationError on failure.
    """
    try:
        parts = s.strip().split("-")
        if len(parts) != 3:
            raise ValueError("Date must be in YYYY-MM-DD format")
        y, m, d = map(int, parts)
        return date(y, m, d)  # validates calendar incl leap years
    except Exception as e:
        raise ValidationError(f"Invalid date '{s}': {e}") from e

def serialize_value(db_type: str, value: Any) -> Any:
    """
    Convert internal value into JSON-serializable representation.
    """
    t = db_type.lower()
    if t == "integer":
        return int(value)
    if t == "real":
        return float(value)
    if t in ("char", "string"):
        return str(value)
    if t == "date":
        if isinstance(value, date):
            return value.isoformat()
        return parse_date(str(value)).isoformat()
    if t == "dateinvl":
        if isinstance(value, DateInvl):
            return [value.start.isoformat(), value.end.isoformat()]
        a, b = value
        return [parse_date(str(a)).isoformat(), parse_date(str(b)).isoformat()]
    raise ValidationError(f"Unknown type '{db_type}'")

def coerce_value(db_type: str, raw: Any) -> Any:
    """
    Coerce user input (string/number/json) into internal typed value.
    """
    t = db_type.lower()
    if raw is None:
        raise ValidationError("Value is required")

    if t == "integer":
        try:
            return int(str(raw).strip())
        except Exception as e:
            raise ValidationError(f"Expected integer, got '{raw}'") from e

    if t == "real":
        try:
            return float(str(raw).strip())
        except Exception as e:
            raise ValidationError(f"Expected real number, got '{raw}'") from e

    if t == "char":
        s = str(raw)
        if len(s) != 1:
            raise ValidationError("Expected single character (char)")
        return s

    if t == "string":
        return str(raw)

    if t == "date":
        if isinstance(raw, date):
            return raw
        return parse_date(str(raw))

    if t == "dateinvl":
        if isinstance(raw, DateInvl):
            return raw
        if isinstance(raw, (tuple, list)) and len(raw) == 2:
            return DateInvl(parse_date(str(raw[0])), parse_date(str(raw[1])))
        s = str(raw).strip()
        if ".." in s:
            a, b = [p.strip() for p in s.split("..", 1)]
            return DateInvl(parse_date(a), parse_date(b))
        raise ValidationError("Expected dateInvl as 'YYYY-MM-DD..YYYY-MM-DD' or [start, end]")

    raise ValidationError(f"Unknown type '{db_type}'")

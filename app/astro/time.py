"""Use the pinned tzdata wheel, never the host OS timezone database."""

from datetime import datetime, time, timedelta, timezone
from importlib.resources import files
from zoneinfo import ZoneInfo
import tzdata
from app.models import BirthInput


class TimeResolutionError(ValueError):
    pass


def zone(name: str) -> ZoneInfo:
    if name.startswith("/") or ".." in name.split("/") or "\\" in name:
        raise TimeResolutionError("Invalid IANA timezone.")
    try:
        with files(tzdata).joinpath("zoneinfo", *name.split("/")).open("rb") as f:
            return ZoneInfo.from_file(f, key=name)
    except (FileNotFoundError, ValueError, IsADirectoryError) as e:
        raise TimeResolutionError(f"Unknown IANA timezone: {name}") from e


def resolve(naive: datetime, name: str, fold: int | None = None) -> datetime:
    z = zone(name)
    candidates = []
    for k in (0, 1):
        local = naive.replace(tzinfo=z, fold=k)
        utc = local.astimezone(timezone.utc)
        back = utc.astimezone(z)
        if back.replace(tzinfo=None) == naive and back.fold == k:
            candidates.append((k, utc))
    if not candidates:
        raise TimeResolutionError(
            "This civil time does not exist because the clock jumped forward. Correct it; it will not be shifted silently."
        )
    if len(candidates) > 1 and fold is None:
        raise TimeResolutionError(
            "This civil time occurred twice. Choose DST fold 0 (first occurrence) or 1 (second occurrence)."
        )
    if fold is not None and len(candidates) > 1:
        return dict(candidates)[fold]
    return candidates[0][1]


def birth_window(birth: BirthInput) -> tuple[datetime, datetime, datetime]:
    if birth.civil_offset_seconds is not None:
        # A sourced historical record can disagree with today's IANA zone, e.g. Bombay time.
        fixed = timezone(timedelta(seconds=birth.civil_offset_seconds))
        if birth.confidence == "unknown":
            start = datetime.combine(birth.date, time.min, fixed).astimezone(timezone.utc)
            end = start + timedelta(days=1)
            return start + timedelta(hours=12), start, end
        center = datetime.combine(birth.date, birth.time, fixed).astimezone(timezone.utc)
        minutes = {"exact": 0, "certificate": 5, "family": 30}.get(
            birth.confidence, birth.uncertainty_minutes
        )
        return center, center - timedelta(minutes=minutes), center + timedelta(minutes=minutes)
    if birth.confidence == "unknown":
        # An unknown time means the actual local civil day, including 23/25-hour DST days.
        start = resolve(datetime.combine(birth.date, time.min), birth.timezone, 0)
        end = resolve(datetime.combine(birth.date + timedelta(days=1), time.min), birth.timezone, 0)
        return start + (end - start) / 2, start, end
    center = resolve(datetime.combine(birth.date, birth.time), birth.timezone, birth.fold)
    minutes = {"exact": 0, "certificate": 5, "family": 30}.get(birth.confidence, birth.uncertainty_minutes)
    # Error around a remembered instant is elapsed-time uncertainty, not clock arithmetic.
    span = timedelta(minutes=minutes)
    return center, center - span, center + span

"""Timezone and Taiwan trading-date utilities.

Assumptions for Phase 1:
- Naive timestamps are treated as UTC.
- Taiwan trading-date assignment handles weekends only.
- TWSE holiday support is a TODO. The optional ``holidays`` argument accepts
  date objects or ISO date strings now, and can later be wired to a holiday CSV.
- The Taiwan pre-market cutoff is configurable and defaults to 08:45
  Asia/Taipei.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from src.config import TAIWAN_PREMARKET_CUTOFF, TAIWAN_TIMEZONE


TAIPEI_TZ = ZoneInfo(TAIWAN_TIMEZONE)
UTC_TZ = timezone.utc


def _parse_cutoff(cutoff_time: str | time) -> time:
    if isinstance(cutoff_time, time):
        return cutoff_time
    hour_text, minute_text = cutoff_time.split(":", maxsplit=1)
    return time(hour=int(hour_text), minute=int(minute_text))


def _coerce_datetime(value: datetime | str) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        normalized = value.strip().replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)
    raise TypeError(f"Expected datetime or ISO timestamp string, got {type(value)!r}")


def _coerce_date(value: date | datetime | str) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return date.fromisoformat(value)
    raise TypeError(f"Expected date, datetime, or ISO date string, got {type(value)!r}")


def _holiday_set(holidays: set[date | str] | list[date | str] | tuple[date | str, ...] | None) -> set[date]:
    if holidays is None:
        return set()
    return {_coerce_date(value) for value in holidays}


def normalize_to_utc(value: datetime | str) -> datetime:
    """Return a timezone-aware UTC datetime.

    Naive datetimes are treated as UTC for Phase 1 so missing source timezone
    behavior is explicit and reproducible.
    """

    parsed = _coerce_datetime(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC_TZ)
    return parsed.astimezone(UTC_TZ)


def utc_to_taipei(value: datetime | str) -> datetime:
    """Convert a timestamp to Asia/Taipei."""

    return normalize_to_utc(value).astimezone(TAIPEI_TZ)


def previous_weekday(date_value: date | datetime | str) -> date:
    """Return the same date if it is a weekday, otherwise the prior Friday."""

    current = _coerce_date(date_value)
    while current.weekday() >= 5:
        current -= timedelta(days=1)
    return current


def next_weekday(date_value: date | datetime | str) -> date:
    """Return the same date if it is a weekday, otherwise the next Monday."""

    current = _coerce_date(date_value)
    while current.weekday() >= 5:
        current += timedelta(days=1)
    return current


def _next_eligible_weekday(date_value: date, holidays: set[date]) -> date:
    current = next_weekday(date_value)
    while current in holidays:
        current = next_weekday(current + timedelta(days=1))
    return current


def is_before_taiwan_cutoff(
    news_timestamp: datetime | str,
    cutoff_time: str | time = TAIWAN_PREMARKET_CUTOFF,
) -> bool:
    """Return True when the timestamp is on or before the Taipei cutoff."""

    taipei_timestamp = utc_to_taipei(news_timestamp)
    return taipei_timestamp.time() <= _parse_cutoff(cutoff_time)


def assign_taiwan_trading_date(
    news_timestamp: datetime | str,
    cutoff_time: str | time = TAIWAN_PREMARKET_CUTOFF,
    holidays: set[date | str] | list[date | str] | tuple[date | str, ...] | None = None,
) -> date:
    """Assign a news timestamp to the Taiwan trading date it can inform.

    The timestamp is converted to Asia/Taipei first. Weekday items published on
    or before the cutoff are assigned to that Taiwan date. Items after the
    cutoff, or items published on weekends, roll forward to the next eligible
    weekday. Optional holidays are skipped when supplied.
    """

    taipei_timestamp = utc_to_taipei(news_timestamp)
    holiday_dates = _holiday_set(holidays)
    taipei_date = taipei_timestamp.date()

    if taipei_date.weekday() >= 5 or taipei_date in holiday_dates:
        return _next_eligible_weekday(taipei_date, holiday_dates)

    if taipei_timestamp.time() <= _parse_cutoff(cutoff_time):
        return taipei_date

    return _next_eligible_weekday(taipei_date + timedelta(days=1), holiday_dates)

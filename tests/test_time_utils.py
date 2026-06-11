from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

from src.time_utils import (
    assign_taiwan_trading_date,
    is_before_taiwan_cutoff,
    next_weekday,
    normalize_to_utc,
    utc_to_taipei,
)


def test_timezone_aware_timestamp_normalizes_to_utc():
    eastern = ZoneInfo("America/New_York")
    timestamp = datetime(2026, 6, 5, 20, 30, tzinfo=eastern)

    normalized = normalize_to_utc(timestamp)

    assert normalized.tzinfo == timezone.utc
    assert normalized.hour == 0
    assert normalized.date() == date(2026, 6, 6)


def test_utc_to_taipei_conversion():
    timestamp = datetime(2026, 6, 1, 0, 0, tzinfo=timezone.utc)

    converted = utc_to_taipei(timestamp)

    assert converted.tzinfo == ZoneInfo("Asia/Taipei")
    assert converted.hour == 8
    assert converted.date() == date(2026, 6, 1)


def test_friday_us_evening_saturday_taipei_maps_to_next_monday():
    eastern = ZoneInfo("America/New_York")
    timestamp = datetime(2026, 6, 5, 20, 30, tzinfo=eastern)

    assigned = assign_taiwan_trading_date(timestamp)

    assert assigned == date(2026, 6, 8)


def test_weekend_dates_roll_forward_to_monday():
    assert next_weekday(date(2026, 6, 6)) == date(2026, 6, 8)
    assert next_weekday(date(2026, 6, 7)) == date(2026, 6, 8)


def test_cutoff_logic_excludes_after_cutoff_for_same_day_assignment():
    before_cutoff = datetime(2026, 6, 1, 0, 44, tzinfo=timezone.utc)
    after_cutoff = datetime(2026, 6, 1, 0, 46, tzinfo=timezone.utc)

    assert is_before_taiwan_cutoff(before_cutoff, cutoff_time="08:45")
    assert not is_before_taiwan_cutoff(after_cutoff, cutoff_time="08:45")
    assert assign_taiwan_trading_date(before_cutoff) == date(2026, 6, 1)
    assert assign_taiwan_trading_date(after_cutoff) == date(2026, 6, 2)

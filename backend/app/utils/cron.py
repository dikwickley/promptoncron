from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from croniter import croniter


def compute_next_run_at(
    *,
    cron_expression: str,
    timezone: str,
    base_time_utc: datetime,
) -> datetime:
    tz = ZoneInfo(timezone)
    base_local = base_time_utc.astimezone(tz)
    itr = croniter(cron_expression, base_local)
    next_local = itr.get_next(datetime)
    # Persist timezone-aware datetime; in SQLite this will store as string, SQLAlchemy will parse.
    return next_local.astimezone(tz)


def ensure_min_cron_interval_minutes(
    *,
    cron_expression: str,
    timezone: str,
    base_time_utc: datetime,
    min_minutes: int = 15,
) -> None:
    tz = ZoneInfo(timezone)
    base_local = base_time_utc.astimezone(tz)
    itr = croniter(cron_expression, base_local)
    first = itr.get_next(datetime)
    second = itr.get_next(datetime)
    if (second - first) < timedelta(minutes=min_minutes):
        raise ValueError(f"Cron interval must be >= {min_minutes} minutes")



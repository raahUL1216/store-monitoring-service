from datetime import datetime, timedelta
from dateutil import parser, tz

def get_report_intervals(now: datetime) -> dict:
    last_hour_start = now - timedelta(hours=1, minutes=now.minute, seconds=now.second)
    last_hour_end = last_hour_start + timedelta(hours=1)

    last_day_start = now - timedelta(days=1, hours=now.hour, minutes=now.minute, seconds=now.second)
    last_day_end = last_day_start + timedelta(days=1)
    
    last_week_start = now - timedelta(weeks=1, days=now.weekday(), hours=now.hour, minutes=now.minute, seconds=now.second)
    last_week_end = last_week_start + timedelta(weeks=1)

    return {
        "last_hour_start": last_hour_start,
        "last_hour_end": last_hour_end,
        "last_day_start": last_day_start,
        "last_day_end": last_day_end,
        "last_week_start": last_week_start,
        "last_week_end": last_week_end
    }

def convert_utc_to_local(timestamp: datetime, timezone: str) -> datetime:
    utc_datetime = parser.parse(timestamp)
    target_tz = tz.gettz(timezone)

    return utc_datetime.astimezone(target_tz)

def convert_local_to_utc(local_time: datetime.time, timezone: str) -> datetime.time:
    # Create a dummy date to combine with the local_time
    dummy_date = datetime(2023, 1, 1)

    # Combine the local_time and dummy_date to create a datetime object
    local_datetime = datetime.combine(dummy_date, local_time)

    local_timezone = tz.gettz(timezone)

    local_datetime_with_tz = local_datetime.replace(tzinfo=local_timezone)
    utc_datetime = local_datetime_with_tz.astimezone(tz.UTC)

    # Extract the time component
    utc_time = utc_datetime.time()

    return utc_time





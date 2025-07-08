from dateutil import parser, relativedelta, rrule, easter, tz
from datetime import datetime, timedelta, date

def test_dateutil_basic():
    # 1. Parsing
    dt = parser.parse("2025-07-08T12:34:56Z")
    assert dt.year == 2025 and dt.hour == 12, "Failed parsing ISO 8601 datetime"

    # 2. Relative Delta
    dt2 = dt + relativedelta.relativedelta(months=+1, days=+10)
    assert dt2.month == 8 and dt2.day == 18, "Failed relativedelta calculation"

    # 3. Recurrence Rules
    rule = rrule.rrule(rrule.DAILY, count=3, dtstart=dt)
    dates = list(rule)
    assert dates[1] == dt + timedelta(days=1), "Failed rrule daily recurrence"

    # 4. Easter Calculation
    easter_date = easter.easter(2025)
    assert isinstance(easter_date, date), "Easter date is not date"

    # 5. Timezone Handling
    utc_zone = tz.UTC
    local_zone = tz.tzlocal()
    dt_utc = dt.replace(tzinfo=utc_zone)
    dt_local = dt_utc.astimezone(local_zone)
    assert dt_local.tzinfo is not None, "Timezone conversion failed"

    print("All dateutil basic tests passed.")

if __name__ == "__main__":
    test_dateutil_basic()
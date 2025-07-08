from datetime import datetime, timedelta
import pytz

def test_list_all_timezones():
    assert 'UTC' in pytz.all_timezones
    assert 'America/New_York' in pytz.all_timezones
    assert 'Asia/Tokyo' in pytz.all_timezones
    print("✅ Timezone listing passed.")

def test_localize_naive_datetime():
    tz = pytz.timezone('Europe/London')
    naive = datetime(2025, 7, 1, 12, 0, 0)
    localized = tz.localize(naive)
    assert localized.tzinfo.zone == 'Europe/London'
    assert localized.dst() != timedelta(0)  # Should be in DST
    print("✅ Localization passed.")

def test_convert_between_timezones():
    ny = pytz.timezone('America/New_York')
    tokyo = pytz.timezone('Asia/Tokyo')
    ny_dt = ny.localize(datetime(2025, 1, 1, 12, 0, 0))  # Standard Time (no DST)
    tokyo_dt = ny_dt.astimezone(tokyo)
    expected_hour = (12 + 14) % 24  # EST (UTC-5) to JST (UTC+9) = +14h
    assert tokyo_dt.hour == expected_hour
    assert tokyo_dt.tzinfo.zone == 'Asia/Tokyo'
    print("✅ Timezone conversion passed.")

def test_utc_localization_and_conversion():
    utc = pytz.utc
    naive = datetime(2025, 12, 25, 15, 0, 0)
    utc_dt = utc.localize(naive)
    assert utc_dt.tzinfo.zone == 'UTC'

    paris = pytz.timezone('Europe/Paris')
    paris_dt = utc_dt.astimezone(paris)
    assert paris_dt.tzinfo.zone == 'Europe/Paris'
    print("✅ UTC localization and conversion passed.")

def test_dst_transition():
    tz = pytz.timezone('America/New_York')
    before = tz.localize(datetime(2025, 3, 9, 1, 30))  # Before DST starts
    after_unadjusted = before + timedelta(hours=1)
    after = tz.normalize(after_unadjusted)  # Correct DST adjustment
    assert after.hour == 3  # Skips 2 AM
    assert after.dst() == timedelta(hours=1)  # Now in DST
    print("✅ DST transition passed.")

if __name__ == "__main__":
    test_list_all_timezones()
    test_localize_naive_datetime()
    test_convert_between_timezones()
    test_utc_localization_and_conversion()
    test_dst_transition()
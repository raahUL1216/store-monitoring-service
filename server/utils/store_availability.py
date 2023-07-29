from datetime import datetime, timedelta
import bisect

def calculate_uptime_downtime(store_data, db, report) -> None:
    # Function to compute the final solution for uptime and downtime
    # Interpolate/extrapolate downtime and uptime for missing observations
    restaurant_status = store_data['restaurant_status']
    business_hours = store_data['business_hours']
    timezones = store_data['timezones']

    # Step 1: Prepare data structures for faster access
    restaurant_status.sort(key=lambda x: (x[0], x[1]))  # Sort by store_id and timestamp_utc

    business_hours_dict = {}  # {store_id: {dayOfWeek: (start_time_local, end_time_local)}}
    for entry in business_hours:
        store_id, dayOfWeek, start_time_local, end_time_local = entry
        if store_id not in business_hours_dict:
            business_hours_dict[store_id] = {}
        business_hours_dict[store_id][dayOfWeek] = (start_time_local, end_time_local)

    valid_stores = set()  # Set of restaurant store_ids with business hours and timezone information
    for entry in timezones:
        store_id, timezone_str = entry
        if store_id in business_hours_dict:
            valid_stores.add(store_id)

    # Step 2: Calculate downtime and check business hours
    final_report = []
    for store_id in valid_stores:
        timezone_str = timezones[store_id]

        daily_business_hours = business_hours_dict[store_id]
        start_time_utc = datetime.utcnow() - timedelta(weeks=1)

        status_entries = [entry for entry in restaurant_status if entry[0] == store_id and entry[1] >= start_time_utc]

        downtime_last_hour = 0
        downtime_last_day = 0
        downtime_last_week = 0
        uptime_last_hour = 0
        uptime_last_day = 0
        uptime_last_week = 0

        now = datetime.utcnow()  # Current time in UTC
        one_hour_ago = now - timedelta(hours=1)
        one_day_ago = now - timedelta(days=1)

        for i in range(len(status_entries)):
            timestamp_utc, status = status_entries[i]

            if status == 'inactive':
                next_status_change = None
                next_index = bisect.bisect_left(status_entries, (store_id, timestamp_utc, ''), i + 1)
                if next_index < len(status_entries):
                    next_status_change = status_entries[next_index][1]

                # Calculate downtime duration
                downtime_duration = 0
                if next_status_change and next_status_change > timestamp_utc:
                    downtime_duration = (next_status_change - timestamp_utc).total_seconds()

                # Check if downtime occurred during business hours
                local_time = convert_utc_to_local(timestamp_utc, timezone_str)
                day_of_week = local_time.weekday()
                start_time_local, end_time_local = daily_business_hours.get(day_of_week, (None, None))

                if start_time_local and end_time_local and start_time_local <= local_time.time() <= end_time_local:
                    if timestamp_utc >= one_hour_ago:
                        downtime_last_hour += downtime_duration
                    if timestamp_utc >= one_day_ago:
                        downtime_last_day += downtime_duration
                    if timestamp_utc >= start_time_utc:
                        downtime_last_week += downtime_duration

        # Calculate uptime based on downtime
        total_business_hours_last_hour = 3600
        total_business_hours_last_day = 3600 * len(daily_business_hours)
        total_business_hours_last_week = 3600 * len(daily_business_hours) * 7

        uptime_last_hour = total_business_hours_last_hour - downtime_last_hour
        uptime_last_day = total_business_hours_last_day - downtime_last_day
        uptime_last_week = total_business_hours_last_week - downtime_last_week

        final_report.append({
            'store_id': store_id,
            'uptime_last_hour': uptime_last_hour,
            'uptime_last_day': uptime_last_day,
            'uptime_last_week': uptime_last_week,
            'downtime_last_hour': downtime_last_hour,
            'downtime_last_day': downtime_last_day,
            'downtime_last_week': downtime_last_week
        })

    report.status = 'Completed'
    report.report_csv_url = 'TODO'
    db.commit()

    return None
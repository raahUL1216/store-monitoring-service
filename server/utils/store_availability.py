import os

from sqlalchemy.orm import Session

from server.models.store import Report 

from datetime import datetime, time
from server.utils.datetime_utils import convert_utc_to_local

import csv

report_fields = ['store_id', 'uptime_last_hour', 'uptime_last_day', 'uptime_last_week', 'downtime_last_hour', 'downtime_last_day', 'downtime_last_week']

def get_store_running_time_by_interval(business_hours: dict, day_of_week: int) -> dict:
    days_in_week = 7
    hours_in_day = 24
    seconds_in_min = 60
    seconds_in_hour = seconds_in_min * 60

    last_week = 0

    for i in range(days_in_week):
        start_time_local, end_time_local = business_hours.get(i, (None, None))

        if start_time_local and end_time_local:
            start_time_seconds = start_time_local.hour * seconds_in_hour + start_time_local.minute * seconds_in_min + start_time_local.second
            end_time_seconds = end_time_local.hour * seconds_in_hour + end_time_local.minute * seconds_in_min + end_time_local.second

            store_running_time = (end_time_seconds - start_time_seconds)
        else:
            # store is open all day when business_hours is not available
            store_running_time = (hours_in_day * seconds_in_hour)

        # store running time for given day
        if i == day_of_week:
            last_day = store_running_time

        # store running time for last week
        last_week += store_running_time

    return {
        "last_hour": seconds_in_hour,
        "last_day": last_day,
        "last_week": last_week
    }

def calculate_downtime(downtime_start: datetime, downtime_end: datetime, business_hours: dict, store_timezone: str, report_intervals: dict) -> dict:
    downtime_start_day = downtime_start.weekday()

    # get business hours of day when downtime started and convert it to utc. note that day_start and day_end will be considered as business hours when this data is not available
    start_time_local, end_time_local = business_hours.get(downtime_start_day, (None, None))

    day_start = time()
    day_end = time(23, 59, 59)

    store_start = start_time_local if start_time_local else day_start
    store_end = end_time_local if end_time_local else day_end

    # if downtime_end is not passed, then end time of business_hours on that will be downtime_end. this happens when last observation status was `inactive` and we need to extrapolate downtime
    downtime_end = downtime_end if downtime_end else store_end

    downtime_start_local = convert_utc_to_local(downtime_start, store_timezone)

    # Check if the downtime occurred during business hours
    if store_start <= downtime_start_local.time() <= store_end:
        downtime_end_day = downtime_end.weekday()

        # if observations are of different days, downtime_end will be end of business hours for that day
        if downtime_start_day != downtime_end_day:
            downtime_end = datetime.combine(downtime_start.date(), store_end) 

        downtime_duration = (downtime_end - downtime_start).total_seconds()

        if downtime_end >= report_intervals['last_hour_start']:
            downtime_last_hour += downtime_duration
        elif downtime_end >= report_intervals['last_day_start']:
            downtime_last_day += downtime_duration
        elif downtime_end >= report_intervals['last_week_start']:
            downtime_last_week += downtime_duration

    return {
        "last_hour": downtime_last_hour,
        "last_day": downtime_last_day,
        "last_week": downtime_last_week
    }


def generate_store_availability_report(db: Session, store_data: dict, report_intervals: dict, report: Report) -> None:
    stores = store_data['stores']
    business_hours = store_data['business_hours']
    timezones = store_data['timezones']

    report_file = None
    filename = f"report-{str(report_intervals['now'].date())}.csv"
    file_path = os.path.join(os.getcwd(), "server", "static", "reports", filename)

    seconds_in_minute = 60
    seconds_in_hour = seconds_in_minute * 60

    try:        
        with open(f'{file_path}', 'w', newline='') as report_file:
            writer = csv.DictWriter(report_file, fieldnames=report_fields)
            writer.writeheader()

            # Iterate through all store and calculate downtime and uptime
            for store_id, status_entries in stores.items():
                store_business_hours = business_hours[store_id]
                store_running_time = get_store_running_time_by_interval(
                    store_business_hours,
                    report_intervals['last_day_start'].weekday()
                )

                store_timezone = timezones.get(store_id, 'America/Chicago')

                print(store_id)
                print(store_running_time)

                downtime_start = None
                downtime_end = None
                total_downtime = {
                    "last_hour": 0,
                    "last_day": 0,
                    "last_week": 0
                }
                total_uptime = {
                    "last_hour": 0,
                    "last_day": 0,
                    "last_week": 0
                }

                # Iterate through all observations of current store, find `inactive -> .... -> active` pattern and add it to downtime
                for index in range(len(status_entries)):
                    timestamp_utc, status = status_entries[index]

                    if downtime_start and status == 'active':
                        downtime_end = timestamp_utc

                        downtime = calculate_downtime(
                            downtime_start,
                            downtime_end,
                            store_business_hours,
                            store_timezone,
                            report_intervals
                        )

                        # add downtime to total_downtime by hour, day and week
                        for key, value in downtime.items():
                            total_downtime[key] += value

                        # reset downtime 
                        downtime_start = None

                    if status == 'inactive':
                        # downtime started
                        downtime_start = status_entries[index][0]
                        continue

                if downtime_start:
                    downtime_end = None
                    # process last observation and extrapolate downtime
                    downtime = calculate_downtime(
                        downtime_start,
                        downtime_end,
                        store_business_hours,
                        store_timezone,
                        report_intervals
                    )    

                    # add downtime to total_downtime by hour, day and week
                    for key, value in downtime.items():
                        total_downtime[key] += value            

                # Calculate uptime based on downtime
                total_uptime = { key: (store_running_time[key] - total_downtime[key]) for key in store_running_time }

                print(total_uptime)

                writer.writerow({
                    'store_id': store_id,
                    'uptime_last_hour': (total_uptime['last_hour']//seconds_in_minute),
                    'uptime_last_day': (total_uptime['last_day']//seconds_in_hour),
                    'uptime_last_week': (total_uptime['last_week']//seconds_in_hour),
                    'downtime_last_hour': (total_downtime['last_hour']//seconds_in_minute),
                    'downtime_last_day': (total_downtime['last_day']//seconds_in_hour),
                    'downtime_last_week': (total_downtime['last_week']//seconds_in_hour)
                })

                break

            report.status = 'Completed'
            report.report_csv_url = f'localhost:8000/static/reports/{filename}'
            db.commit()

            return None
    except Exception as e:
        print(e)
        report.status = 'Failed'
        report.report_csv_url = ''
        db.commit()
    finally:
        if report_file:
            report_file.close()
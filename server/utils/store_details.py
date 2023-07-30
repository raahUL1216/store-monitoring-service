from functools import lru_cache
from fastapi import Depends

from sqlalchemy.orm import Session
from sqlalchemy import asc, or_, and_

from server.database import get_db
from server.models.store import BusinessHours, RestaurantTimezone, RestaurantStatus
from server.utils.datetime_utils import convert_local_to_utc


@lru_cache(maxsize=None)  # Set an appropriate cache size (None means unlimited cache size)
def get_store_data(db: Session = Depends(get_db)) -> dict:
    business_hours = db.query(BusinessHours).all()
    timezones = db.query(RestaurantTimezone).all()

    print('Getting business hours and timezone for all stores...')

    # store timezones and business_hours in dictionary for faster access
    timezones_dict = {}
    # format {store_id: timezone_str}

    for store_timezone in timezones:
        store_id, timezone_str = store_timezone.store_id, store_timezone.timezone_str

        timezones_dict[store_id] = timezone_str

    business_hours_dict = {}  
    # format {store_id: {day_of_week: (start_time_local, end_time_local)}}

    for business_hour in business_hours:
        store_id = business_hour.store_id
        day_of_week = business_hour.day_of_week
        start_time_local = business_hour.start_time_local
        end_time_local = business_hour.end_time_local
        
        if store_id not in business_hours_dict:
            business_hours_dict[store_id] = {}

        business_hours_dict[store_id][day_of_week] = (start_time_local, end_time_local)

    return {
        "business_hours": business_hours_dict,
        "timezones": timezones_dict
    }

def get_restaurant_status(db: Session, report_intervals: dict) -> dict:
    restaurant_status = db.query(RestaurantStatus).filter(
            or_(
                and_(
                    RestaurantStatus.timestamp_utc >= report_intervals['last_hour_start'],
                    RestaurantStatus.timestamp_utc <= report_intervals['last_hour_end']
                ),
                and_(
                    RestaurantStatus.timestamp_utc >= report_intervals['last_day_start'],
                    RestaurantStatus.timestamp_utc <= report_intervals['last_day_end']
                ),
                and_(
                    RestaurantStatus.timestamp_utc >= report_intervals['last_week_start'],
                    RestaurantStatus.timestamp_utc <= report_intervals['last_week_end']
                ),
            )
        ).order_by(
            asc(RestaurantStatus.store_id), 
            asc(RestaurantStatus.timestamp_utc)
        ).all()
    
    stores = {}  
    # {store_id: [(timestamp_utc, status), ...]}

    for observation in restaurant_status:
        store_id = observation.store_id
        timestamp_utc = observation.timestamp_utc
        status = observation.status
        
        if store_id not in stores:
            stores[store_id] = []
            
        stores[store_id].append((timestamp_utc, status))
    
    return stores
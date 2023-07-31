from functools import lru_cache
import traceback
from fastapi import Depends

from sqlalchemy.orm import Session
from sqlalchemy import asc, or_, and_

from server.database import SessionLocal
from server.models.store import BusinessHours, RestaurantTimezone, RestaurantStatus


@lru_cache(maxsize=None)  # (None means unlimited cache size)
def get_store_data() -> dict:
    '''
    cache store business hours and timezones in dictionary, so these data can be reused for every `trigger_report/` api call
    '''
    try:
        db: Session = SessionLocal()
        
        business_hours = db.query(BusinessHours).all()
        timezones = db.query(RestaurantTimezone).all()

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
    except Exception as e:
        print(e)
        print(traceback.format_exc())
    finally:
        db.close()

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
    
    # store observation in dictionary for faster access
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
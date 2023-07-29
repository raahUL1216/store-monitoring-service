from functools import lru_cache
from fastapi import Depends
from sqlalchemy.orm import Session

from server.database import get_db
from server.models.store import BusinessHours, RestaurantTimezone

@lru_cache(maxsize=None)  # Set an appropriate cache size (None means unlimited cache size)
def get_store_data(db: Session = Depends(get_db)):
    business_hours = db.query(BusinessHours).all()  # Replace 'Store' with your model representing store data
    timezones = db.query(RestaurantTimezone).all()  # Replace 'Timezone' with your model representing timezone data

    store_data = {
        "timezones": timezones,
        "business_hours": business_hours
    }

    return store_data

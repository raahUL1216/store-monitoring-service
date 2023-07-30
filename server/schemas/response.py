from enum import Enum
from pydantic import BaseModel

from datetime import datetime

class ReportStatus(Enum):
    RUNNING='Running',
    COMPLETED='Completed',
    FAILED='Failed'


class HealthResponse(BaseModel):
    status: str

class ReportBase(BaseModel):
    report_id: int
    status: str
    report_csv_url: str

    class Config:
        orm_mode = True

class RestaurantStatusBase(BaseModel):
    observation_id: int
    store_id: int
    timestamp_utc: datetime
    status: str

    class Config:
        orm_mode = True
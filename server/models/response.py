from enum import Enum
from pydantic import BaseModel

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

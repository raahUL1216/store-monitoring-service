from fastapi import FastAPI, Depends, status, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy.orm import Session
from sqlalchemy import asc, or_, and_

from .database import get_db
from .models.response import HealthResponse, ReportBase
from .models.store import Report, RestaurantStatus

from .utils.store_availability import calculate_uptime_downtime
from .utils.store_details import get_store_data

from datetime import datetime, timedelta

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/", status_code=status.HTTP_200_OK)
async def health() -> HealthResponse:
    return HealthResponse(status="Ok")


@app.post("/trigger_report", status_code=status.HTTP_201_CREATED)
async def trigger_report(background_tasks: BackgroundTasks, store_data: dict = Depends(get_store_data), db: Session = Depends(get_db)) -> int:
    """
    generates store availability report in background and returns report_id
    """
    try:
        # generate report_id
        report = Report()
        db.add(report)
        db.commit()
        db.refresh(report)

        # Get the current datetime and calculate the datetime ranges for the filters
        now = datetime.utcnow()

        previous_week_start = now - timedelta(weeks=1, days=now.weekday(), hours=now.hour, minutes=now.minute, seconds=now.second, microseconds=now.microsecond)
        previous_week_end = previous_week_start + timedelta(weeks=1)

        last_day_start = now - timedelta(days=1, hours=now.hour, minutes=now.minute, seconds=now.second, microseconds=now.microsecond)
        last_day_end = now

        last_hour_start = now - timedelta(hours=1)
        last_hour_end = now

        # get all relevant restaurant availability observations
        store_data['restaurant_status'] = db.query(RestaurantStatus).filter(
            or_(
                and_(
                    RestaurantStatus.timestamp_utc >= previous_week_start, RestaurantStatus.timestamp_utc < previous_week_end
                ),
                and_(
                    RestaurantStatus.timestamp_utc >= last_day_start, RestaurantStatus.timestamp_utc <= last_day_end
                ),
                and_(
                    RestaurantStatus.timestamp_utc >= last_hour_start, RestaurantStatus.timestamp_utc <= last_hour_end
                )
            )
        ).order_by(
            asc(RestaurantStatus.store_id), 
            asc(RestaurantStatus.timestamp_utc)
        ).all()

        # generate report in background
        background_tasks.add_task(
            calculate_uptime_downtime, 
            store_data, 
            db,
            report
        )

        return report
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Error while generating report."
        )
    

@app.get("/get_report", status_code=status.HTTP_200_OK)
async def get_report(report_id: int, db: Session = Depends(get_db)) -> ReportBase:
    """
    returns store availability report
    @report_id: report_id is generated through `/trigger_report` API
    """
    try:
        if not report_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="report_id is required."
            )

        report = db.query(Report).filter(Report.id == report_id).first()

        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f'No report found with report_id: {report_id}'
            )

        return report
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Error while getting report."
        )
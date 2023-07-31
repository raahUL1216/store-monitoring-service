from fastapi import FastAPI, Depends, status, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from sqlalchemy.orm import Session

from server.database import get_db
from server.schemas.response import HealthResponse, ReportBase
from server.models.store import Report

from server.utils.store_availability import generate_store_availability_report
from server.utils.store_details import get_store_data
from server.utils.report import get_report_by_id
from server.utils.datetime_utils import get_report_intervals

from datetime import datetime, timezone

import traceback

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

app.mount("/static", StaticFiles(directory="server/static"), name="static")


@app.get("/", status_code=status.HTTP_200_OK)
async def health() -> HealthResponse:
    return HealthResponse(status="Ok")


@app.post("/trigger_report", status_code=status.HTTP_201_CREATED)
async def trigger_report(background_tasks: BackgroundTasks, store_data: dict = Depends(get_store_data), db: Session = Depends(get_db)) -> dict:
    """
    generates store availability report in background and returns report_id
    """
    try:
        # generate report_id
        report = Report(status='Running')
        db.add(report)
        db.commit()
        db.refresh(report)

        # now value is hard coded with max timestamp among all the given observations as given data is static. 
        # TODO: Replace now with `datetime.utcnow()` in future
        now = datetime(2023, 1, 25, 18, 13, 22, 0, tzinfo=timezone.utc)

        # get time range(e.g. last_hour, last_day, last_week) for which report needs to be generated
        report_intervals = get_report_intervals(now)

        # generate report in background
        background_tasks.add_task(
            generate_store_availability_report, 
            db,
            store_data,
            report_intervals,
            report
        )

        return { "report_id": report.report_id }
    except Exception as e:
        print(e)
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Error while generating report."
        )
    

@app.get("/get_report", status_code=status.HTTP_200_OK)
async def get_report(report_id: int, db: Session = Depends(get_db)):
    """
    returns store availability report
    """
    try:
        if not report_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="report_id is required."
            )

        report = get_report_by_id(db, report_id)

        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f'No report found with report_id: {report_id}'
            )

        return report
    except Exception as e:
        print(e)
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Error while getting report."
        )

from sqlalchemy.orm import Session

from server.models.store import Report
from server.schemas.response import ReportBase


def get_report_by_id(db: Session, report_id: int) -> ReportBase:
    filter_by_id = Report.report_id == report_id

    return db.query(Report).filter(filter_by_id).first()

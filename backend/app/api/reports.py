from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.reports import DashboardReportRequest, DashboardReportResponse
from app.services.forecasting import ForecastingError
from app.services.reporting import DashboardReportService

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.post("/dashboard", response_model=DashboardReportResponse)
def generate_dashboard_report(
    request: DashboardReportRequest,
    db: Session = Depends(get_db),
) -> DashboardReportResponse:
    try:
        return DashboardReportService().generate(db, request)
    except ForecastingError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "message": exc.message,
                "skipped": [
                    skipped.model_dump() for skipped in exc.skipped
                ],
            },
        ) from exc
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Report data could not be loaded."},
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "The dashboard report could not be generated."},
        ) from exc

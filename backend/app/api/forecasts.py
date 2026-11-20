import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.forecast import ForecastRequest, ForecastResponse
from app.services.forecasting import EnrollmentForecastService, ForecastingError
from app.services.response_cache import cache_key, forecast_cache, get_or_set

router = APIRouter(prefix="/api/forecasts", tags=["forecasts"])


@router.post("/generate", response_model=ForecastResponse)
def generate_forecast(
    request: ForecastRequest,
    db: Session = Depends(get_db),
) -> ForecastResponse:
    key = cache_key(
        "forecast",
        json.dumps(request.model_dump(mode="json"), sort_keys=True),
    )

    def compute() -> ForecastResponse:
        return EnrollmentForecastService().generate(db, request)

    try:
        return get_or_set(forecast_cache, key, compute)
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
            detail={"message": "Historical enrollment data could not be loaded."},
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "The enrollment forecast could not be generated."},
        ) from exc

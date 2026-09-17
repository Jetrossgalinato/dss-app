from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.sections import (
    SectionRecommendationRequest,
    SectionRecommendationResponse,
)
from app.services.forecasting import ForecastingError
from app.services.section_planning import SectionPlanningService

router = APIRouter(prefix="/api/sections", tags=["sections"])


@router.post("/recommendations", response_model=SectionRecommendationResponse)
def generate_section_recommendations(
    request: SectionRecommendationRequest,
    db: Session = Depends(get_db),
) -> SectionRecommendationResponse:
    try:
        return SectionPlanningService().generate(db, request)
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
            detail={"message": "Section recommendations could not be generated."},
        ) from exc

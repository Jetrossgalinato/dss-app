import math

from sqlalchemy.orm import Session

from app.schemas.forecast import ForecastRequest
from app.schemas.sections import (
    ClassSectionRecommendations,
    SectionRecommendation,
    SectionRecommendationRequest,
    SectionRecommendationResponse,
)
from app.services.forecasting import EnrollmentForecastService


def compute_section_recommendation(
    predicted_enrollment: int,
    max_class_size: int,
) -> tuple[int, int]:
    """Return the required section count and largest planned section size."""
    if predicted_enrollment < 0:
        raise ValueError("Predicted enrollment cannot be negative.")
    if max_class_size < 1:
        raise ValueError("Maximum class size must be at least 1.")
    if predicted_enrollment == 0:
        return 0, 0

    recommended_sections = math.ceil(predicted_enrollment / max_class_size)
    planned_class_size = math.ceil(predicted_enrollment / recommended_sections)
    return recommended_sections, planned_class_size


class SectionPlanningService:
    def generate(
        self,
        db: Session,
        request: SectionRecommendationRequest,
    ) -> SectionRecommendationResponse:
        forecast = EnrollmentForecastService().generate(
            db,
            ForecastRequest(
                horizon=request.horizon,
                class_levels=request.class_levels,
            ),
        )

        series: list[ClassSectionRecommendations] = []
        for forecast_series in forecast.series:
            recommendations: list[SectionRecommendation] = []
            for point in forecast_series.forecast:
                section_count, planned_size = compute_section_recommendation(
                    point.predicted_count,
                    request.max_class_size,
                )
                recommendations.append(
                    SectionRecommendation(
                        academic_year=point.academic_year,
                        predicted_enrollment=point.predicted_count,
                        max_class_size=request.max_class_size,
                        recommended_sections=section_count,
                        planned_class_size=planned_size,
                    )
                )

            series.append(
                ClassSectionRecommendations(
                    class_level=forecast_series.class_level,
                    method=forecast_series.method,
                    observations_used=forecast_series.observations_used,
                    recommendations=recommendations,
                )
            )

        return SectionRecommendationResponse(
            generated_at=forecast.generated_at,
            horizon=forecast.horizon,
            max_class_size=request.max_class_size,
            series=series,
            skipped=forecast.skipped,
        )

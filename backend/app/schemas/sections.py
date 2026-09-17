from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.forecast import ForecastRequest, SkippedForecastSeries


class SectionRecommendationRequest(ForecastRequest):
    max_class_size: int = Field(default=25, ge=1, le=100)


class SectionRecommendation(BaseModel):
    academic_year: str
    predicted_enrollment: int = Field(ge=0)
    max_class_size: int = Field(ge=1)
    recommended_sections: int = Field(ge=0)
    planned_class_size: int = Field(ge=0)


class ClassSectionRecommendations(BaseModel):
    class_level: str
    method: Literal["arima", "linear_trend"]
    observations_used: int = Field(ge=2)
    recommendations: list[SectionRecommendation]


class SectionRecommendationResponse(BaseModel):
    generated_at: datetime
    horizon: int
    max_class_size: int
    series: list[ClassSectionRecommendations]
    skipped: list[SkippedForecastSeries]

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.forecast import HistoricalEnrollmentPoint, SkippedForecastSeries
from app.schemas.sections import SectionRecommendationRequest


class DashboardReportRequest(SectionRecommendationRequest):
    pass


class HistoricalBreakdownPoint(BaseModel):
    academic_year: str
    class_level: str
    male: int = Field(ge=0)
    female: int = Field(ge=0)
    total: int = Field(ge=0)


class ReportProjectionPoint(BaseModel):
    academic_year: str
    predicted_enrollment: int = Field(ge=0)
    recommended_sections: int = Field(ge=0)
    planned_class_size: int = Field(ge=0)


class DashboardForecastSeries(BaseModel):
    class_level: str
    method: Literal["arima", "linear_trend"]
    observations_used: int = Field(ge=2)
    history: list[HistoricalEnrollmentPoint]
    projections: list[ReportProjectionPoint]


class DashboardSummary(BaseModel):
    latest_academic_year: str
    latest_enrollment: int = Field(ge=0)
    year_over_year_change_percent: float | None
    next_academic_year: str
    next_year_forecast: int = Field(ge=0)
    next_year_recommended_sections: int = Field(ge=0)


class DashboardReportResponse(BaseModel):
    generated_at: datetime
    horizon: int
    max_class_size: int
    available_class_levels: list[str]
    summary: DashboardSummary
    historical: list[HistoricalBreakdownPoint]
    series: list[DashboardForecastSeries]
    skipped: list[SkippedForecastSeries]

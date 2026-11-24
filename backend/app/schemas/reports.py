from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.forecast import (
    HistoricalEnrollmentPoint,
    SeriesForecastExplanation,
    SkippedForecastSeries,
)
from app.schemas.sections import SectionRecommendationRequest


class DashboardReportRequest(SectionRecommendationRequest):
    pass


class HistoricalBreakdownPoint(BaseModel):
    academic_year: str
    program: str
    year_level: str
    location: str
    male: int = Field(ge=0)
    female: int = Field(ge=0)
    total: int = Field(ge=0)


class ReportProjectionPoint(BaseModel):
    academic_year: str
    predicted_enrollment: int = Field(ge=0)
    recommended_sections: int = Field(ge=0)
    planned_class_size: int = Field(ge=0)


class DashboardForecastSeries(BaseModel):
    program: str
    year_level: str
    location: str
    method: Literal["arima", "linear_trend"]
    observations_used: int = Field(ge=2)
    history: list[HistoricalEnrollmentPoint]
    projections: list[ReportProjectionPoint]
    explanation: SeriesForecastExplanation


class DashboardSummary(BaseModel):
    latest_academic_year: str
    latest_enrollment: int = Field(ge=0)
    year_over_year_change_percent: float | None
    next_academic_year: str
    total_forecast: int = Field(ge=0)
    forecast_horizon_start: str
    forecast_horizon_end: str
    next_year_recommended_sections: int = Field(ge=0)


class DashboardReportResponse(BaseModel):
    generated_at: datetime
    horizon: int
    max_class_size: int
    available_programs: list[str]
    available_year_levels: list[str]
    available_locations: list[str]
    summary: DashboardSummary
    historical: list[HistoricalBreakdownPoint]
    series: list[DashboardForecastSeries]
    skipped: list[SkippedForecastSeries]

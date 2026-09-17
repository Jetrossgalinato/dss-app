from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ForecastRequest(BaseModel):
    horizon: int = Field(default=3, ge=1, le=5)
    class_levels: list[str] | None = Field(default=None, min_length=1)

    @field_validator("class_levels")
    @classmethod
    def normalize_class_levels(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None

        normalized: list[str] = []
        seen: set[str] = set()
        for class_level in value:
            cleaned = class_level.strip()
            if not cleaned:
                raise ValueError("Class levels cannot be empty.")
            key = cleaned.casefold()
            if key in seen:
                raise ValueError("Class levels must be unique.")
            seen.add(key)
            normalized.append(cleaned)
        return normalized


class HistoricalEnrollmentPoint(BaseModel):
    academic_year: str
    enrollment_count: int = Field(ge=0)


class ForecastPoint(BaseModel):
    academic_year: str
    predicted_count: int = Field(ge=0)


class ClassLevelForecast(BaseModel):
    class_level: str
    method: Literal["arima", "linear_trend"]
    observations_used: int = Field(ge=2)
    history: list[HistoricalEnrollmentPoint]
    forecast: list[ForecastPoint]


class SkippedForecastSeries(BaseModel):
    class_level: str
    reason: str


class ForecastResponse(BaseModel):
    generated_at: datetime
    horizon: int
    series: list[ClassLevelForecast]
    skipped: list[SkippedForecastSeries]

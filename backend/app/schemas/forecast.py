from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.domain.enrollment_dims import (
    ALLOWED_PROGRAMS,
    ALLOWED_YEAR_LEVELS,
    normalize_location,
    normalize_program,
    normalize_year_level,
)


class ForecastRequest(BaseModel):
    horizon: int = Field(default=3, ge=1, le=5)
    programs: list[str] | None = Field(default=None, min_length=1)
    year_levels: list[str] | None = Field(default=None, min_length=1)
    locations: list[str] | None = Field(default=None, min_length=1)

    @field_validator("programs")
    @classmethod
    def normalize_programs(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        normalized: list[str] = []
        seen: set[str] = set()
        for item in value:
            program = normalize_program(item)
            if program is None:
                raise ValueError(
                    "Program must be one of: " + ", ".join(ALLOWED_PROGRAMS) + "."
                )
            if program in seen:
                raise ValueError("Programs must be unique.")
            seen.add(program)
            normalized.append(program)
        return normalized

    @field_validator("year_levels")
    @classmethod
    def normalize_year_levels(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        normalized: list[str] = []
        seen: set[str] = set()
        for item in value:
            year_level = normalize_year_level(item)
            if year_level is None:
                raise ValueError(
                    "Year level must be one of: "
                    + ", ".join(ALLOWED_YEAR_LEVELS)
                    + "."
                )
            if year_level in seen:
                raise ValueError("Year levels must be unique.")
            seen.add(year_level)
            normalized.append(year_level)
        return normalized

    @field_validator("locations")
    @classmethod
    def normalize_locations(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        normalized: list[str] = []
        seen: set[str] = set()
        for item in value:
            location = normalize_location(item)
            if not location:
                raise ValueError("Locations cannot be empty.")
            key = location.casefold()
            if key in seen:
                raise ValueError("Locations must be unique.")
            seen.add(key)
            normalized.append(location)
        return normalized


class HistoricalEnrollmentPoint(BaseModel):
    academic_year: str
    enrollment_count: int = Field(ge=0)


class ForecastPoint(BaseModel):
    academic_year: str
    predicted_count: int = Field(ge=0)


class SeriesForecast(BaseModel):
    program: str
    year_level: str
    location: str
    method: Literal["arima", "linear_trend"]
    observations_used: int = Field(ge=2)
    history: list[HistoricalEnrollmentPoint]
    forecast: list[ForecastPoint]


class SkippedForecastSeries(BaseModel):
    program: str
    year_level: str
    location: str
    reason: str


class ForecastResponse(BaseModel):
    generated_at: datetime
    horizon: int
    series: list[SeriesForecast]
    skipped: list[SkippedForecastSeries]

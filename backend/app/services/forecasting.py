from collections import defaultdict
from datetime import datetime, timezone
import math
import re
import warnings

import numpy as np
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from statsmodels.tsa.arima.model import ARIMA

from app.domain.enrollment_dims import normalize_location
from app.models.enrollment import EnrollmentRecord
from app.schemas.forecast import (
    ForecastPoint,
    ForecastRequest,
    ForecastResponse,
    HistoricalEnrollmentPoint,
    SeriesForecast,
    SkippedForecastSeries,
)

ACADEMIC_YEAR_PATTERN = re.compile(r"^(\d{4})-(\d{4})$")
MINIMUM_OBSERVATIONS = 2
ARIMA_MINIMUM_OBSERVATIONS = 5

SeriesKey = tuple[str, str, str]


class ForecastingError(ValueError):
    def __init__(
        self,
        message: str,
        skipped: list[SkippedForecastSeries] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.skipped = skipped or []


class EnrollmentForecastService:
    def generate(self, db: Session, request: ForecastRequest) -> ForecastResponse:
        history_by_series = self._load_history(db)
        selected = self._select_series(history_by_series, request)

        forecasts: list[SeriesForecast] = []
        skipped: list[SkippedForecastSeries] = []
        for key, history in selected:
            program, year_level, location = key
            try:
                forecasts.append(
                    self._forecast_series(
                        program=program,
                        year_level=year_level,
                        location=location,
                        history=history,
                        horizon=request.horizon,
                    )
                )
            except ForecastingError as exc:
                skipped.append(
                    SkippedForecastSeries(
                        program=program,
                        year_level=year_level,
                        location=location,
                        reason=exc.message,
                    )
                )

        if not forecasts:
            message = (
                "No program/year level/location series has enough usable "
                "historical data to forecast."
                if history_by_series
                else "No historical enrollment data is available."
            )
            raise ForecastingError(message, skipped)

        return ForecastResponse(
            generated_at=datetime.now(timezone.utc),
            horizon=request.horizon,
            series=forecasts,
            skipped=skipped,
        )

    def _load_history(
        self,
        db: Session,
    ) -> dict[SeriesKey, list[tuple[str, int]]]:
        rows = db.execute(
            select(
                EnrollmentRecord.program,
                EnrollmentRecord.year_level,
                EnrollmentRecord.location,
                EnrollmentRecord.academic_year,
                func.sum(EnrollmentRecord.enrollment_count).label("total"),
            )
            .group_by(
                EnrollmentRecord.program,
                EnrollmentRecord.year_level,
                EnrollmentRecord.location,
                EnrollmentRecord.academic_year,
            )
            .order_by(
                EnrollmentRecord.program,
                EnrollmentRecord.year_level,
                EnrollmentRecord.location,
                EnrollmentRecord.academic_year,
            )
        ).all()

        grouped: dict[SeriesKey, list[tuple[str, int]]] = defaultdict(list)
        for program, year_level, location, academic_year, total in rows:
            grouped[(program, year_level, location)].append(
                (academic_year, int(total))
            )
        return dict(grouped)

    def _select_series(
        self,
        history_by_series: dict[SeriesKey, list[tuple[str, int]]],
        request: ForecastRequest,
    ) -> list[tuple[SeriesKey, list[tuple[str, int]]]]:
        programs = request.programs
        year_levels = request.year_levels
        locations = request.locations

        if programs is None and year_levels is None and locations is None:
            return sorted(
                history_by_series.items(),
                key=lambda item: (
                    item[0][0].casefold(),
                    item[0][1].casefold(),
                    item[0][2].casefold(),
                ),
            )

        program_filter = (
            {value.casefold() for value in programs} if programs else None
        )
        year_filter = (
            {value.casefold() for value in year_levels} if year_levels else None
        )
        location_filter = (
            {normalize_location(value).casefold() for value in locations}
            if locations
            else None
        )

        selected = [
            (key, history)
            for key, history in history_by_series.items()
            if (program_filter is None or key[0].casefold() in program_filter)
            and (year_filter is None or key[1].casefold() in year_filter)
            and (location_filter is None or key[2].casefold() in location_filter)
        ]
        selected.sort(
            key=lambda item: (
                item[0][0].casefold(),
                item[0][1].casefold(),
                item[0][2].casefold(),
            )
        )

        # Include explicitly requested combinations that have no history so they
        # can be reported as skipped with a clear reason.
        if programs and year_levels and locations:
            existing = {key for key, _ in selected}
            for program in programs:
                for year_level in year_levels:
                    for location in locations:
                        key = (program, year_level, location)
                        if key not in existing:
                            selected.append((key, []))

        return selected

    def _forecast_series(
        self,
        program: str,
        year_level: str,
        location: str,
        history: list[tuple[str, int]],
        horizon: int,
    ) -> SeriesForecast:
        if not history:
            raise ForecastingError("No historical enrollment data was found.")

        parsed: list[tuple[int, str, int]] = []
        for academic_year, count in history:
            match = ACADEMIC_YEAR_PATTERN.fullmatch(academic_year)
            if not match or int(match.group(2)) != int(match.group(1)) + 1:
                raise ForecastingError(
                    f"Historical academic year '{academic_year}' is invalid."
                )
            parsed.append((int(match.group(1)), academic_year, count))

        parsed.sort(key=lambda point: point[0])
        if len(parsed) < MINIMUM_OBSERVATIONS:
            raise ForecastingError(
                "At least 2 historical academic years are required."
            )

        start_years = np.asarray([point[0] for point in parsed], dtype=float)
        values = np.asarray([point[2] for point in parsed], dtype=float)
        contiguous = all(
            current == previous + 1
            for previous, current in zip(start_years, start_years[1:])
        )

        method = "linear_trend"
        predictions: np.ndarray
        if len(parsed) >= ARIMA_MINIMUM_OBSERVATIONS and contiguous:
            try:
                predictions = self._forecast_arima(values, horizon)
                method = "arima"
            except (ValueError, RuntimeError, ArithmeticError, np.linalg.LinAlgError):
                predictions = self._forecast_linear(start_years, values, horizon)
        else:
            predictions = self._forecast_linear(start_years, values, horizon)

        if len(predictions) != horizon or not np.all(np.isfinite(predictions)):
            raise ForecastingError("The forecasting model produced invalid results.")

        final_start_year = int(start_years[-1])
        projected = [
            ForecastPoint(
                academic_year=f"{final_start_year + step}-{final_start_year + step + 1}",
                predicted_count=self._normalize_prediction(float(value)),
            )
            for step, value in enumerate(predictions, start=1)
        ]
        historical = [
            HistoricalEnrollmentPoint(
                academic_year=academic_year,
                enrollment_count=count,
            )
            for _, academic_year, count in parsed
        ]

        return SeriesForecast(
            program=program,
            year_level=year_level,
            location=location,
            method=method,
            observations_used=len(parsed),
            history=historical,
            forecast=projected,
        )

    def _forecast_arima(self, values: np.ndarray, horizon: int) -> np.ndarray:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            fitted = ARIMA(values, order=(1, 1, 0), trend="t").fit()

        convergence = getattr(fitted, "mle_retvals", {}).get("converged", True)
        if convergence is False:
            raise RuntimeError("ARIMA did not converge.")
        predictions = np.asarray(fitted.forecast(steps=horizon), dtype=float)
        if not np.all(np.isfinite(predictions)):
            raise ArithmeticError("ARIMA produced non-finite values.")
        return predictions

    def _forecast_linear(
        self,
        start_years: np.ndarray,
        values: np.ndarray,
        horizon: int,
    ) -> np.ndarray:
        centered_years = start_years - start_years[0]
        design = np.column_stack((centered_years, np.ones(len(centered_years))))
        slope, intercept = np.linalg.lstsq(design, values, rcond=None)[0]
        future_years = np.arange(
            centered_years[-1] + 1,
            centered_years[-1] + horizon + 1,
            dtype=float,
        )
        return slope * future_years + intercept

    @staticmethod
    def _normalize_prediction(value: float) -> int:
        if not math.isfinite(value):
            raise ForecastingError("The forecasting model produced an invalid value.")
        return max(0, int(math.floor(value + 0.5)))

from collections import defaultdict
from datetime import datetime, timezone
import math
import re
import warnings

import numpy as np
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from statsmodels.tsa.arima.model import ARIMA

from app.models.enrollment import EnrollmentRecord
from app.schemas.forecast import (
    ClassLevelForecast,
    ForecastPoint,
    ForecastRequest,
    ForecastResponse,
    HistoricalEnrollmentPoint,
    SkippedForecastSeries,
)

ACADEMIC_YEAR_PATTERN = re.compile(r"^(\d{4})-(\d{4})$")
MINIMUM_OBSERVATIONS = 2
ARIMA_MINIMUM_OBSERVATIONS = 5


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
        history_by_level = self._load_history(db)
        selected = self._select_class_levels(history_by_level, request.class_levels)

        forecasts: list[ClassLevelForecast] = []
        skipped: list[SkippedForecastSeries] = []
        for class_level, history in selected:
            try:
                forecasts.append(
                    self._forecast_class_level(
                        class_level=class_level,
                        history=history,
                        horizon=request.horizon,
                    )
                )
            except ForecastingError as exc:
                skipped.append(
                    SkippedForecastSeries(class_level=class_level, reason=exc.message)
                )

        if not forecasts:
            message = (
                "No class level has enough usable historical data to forecast."
                if history_by_level
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
    ) -> dict[str, list[tuple[str, int]]]:
        rows = db.execute(
            select(
                EnrollmentRecord.class_level,
                EnrollmentRecord.academic_year,
                func.sum(EnrollmentRecord.enrollment_count).label("total"),
            )
            .group_by(
                EnrollmentRecord.class_level,
                EnrollmentRecord.academic_year,
            )
            .order_by(
                EnrollmentRecord.class_level,
                EnrollmentRecord.academic_year,
            )
        ).all()

        grouped: dict[str, list[tuple[str, int]]] = defaultdict(list)
        for class_level, academic_year, total in rows:
            grouped[class_level].append((academic_year, int(total)))
        return dict(grouped)

    def _select_class_levels(
        self,
        history_by_level: dict[str, list[tuple[str, int]]],
        requested: list[str] | None,
    ) -> list[tuple[str, list[tuple[str, int]]]]:
        if requested is None:
            return sorted(history_by_level.items(), key=lambda item: item[0].casefold())

        canonical = {
            class_level.casefold(): class_level for class_level in history_by_level
        }
        selected: list[tuple[str, list[tuple[str, int]]]] = []
        for requested_level in requested:
            class_level = canonical.get(requested_level.casefold())
            if class_level is None:
                selected.append((requested_level, []))
            else:
                selected.append((class_level, history_by_level[class_level]))
        return selected

    def _forecast_class_level(
        self,
        class_level: str,
        history: list[tuple[str, int]],
        horizon: int,
    ) -> ClassLevelForecast:
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

        return ClassLevelForecast(
            class_level=class_level,
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

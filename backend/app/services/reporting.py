from collections import defaultdict

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.enrollment import EnrollmentRecord
from app.schemas.forecast import ForecastRequest
from app.schemas.reports import (
    DashboardForecastSeries,
    DashboardReportRequest,
    DashboardReportResponse,
    DashboardSummary,
    HistoricalBreakdownPoint,
    ReportProjectionPoint,
)
from app.services.forecasting import EnrollmentForecastService
from app.services.section_planning import compute_section_recommendation


class DashboardReportService:
    def generate(
        self,
        db: Session,
        request: DashboardReportRequest,
    ) -> DashboardReportResponse:
        aggregate_rows = self._load_demographic_history(db)
        available_class_levels = sorted(
            {row[1] for row in aggregate_rows},
            key=str.casefold,
        )

        forecast = EnrollmentForecastService().generate(
            db,
            ForecastRequest(
                horizon=request.horizon,
                class_levels=request.class_levels,
            ),
        )
        selected_levels = (
            {level.casefold() for level in request.class_levels}
            if request.class_levels
            else {level.casefold() for level in available_class_levels}
        )
        historical = self._build_historical_points(aggregate_rows, selected_levels)

        report_series: list[DashboardForecastSeries] = []
        for series in forecast.series:
            projections: list[ReportProjectionPoint] = []
            for point in series.forecast:
                section_count, planned_size = compute_section_recommendation(
                    point.predicted_count,
                    request.max_class_size,
                )
                projections.append(
                    ReportProjectionPoint(
                        academic_year=point.academic_year,
                        predicted_enrollment=point.predicted_count,
                        recommended_sections=section_count,
                        planned_class_size=planned_size,
                    )
                )
            report_series.append(
                DashboardForecastSeries(
                    class_level=series.class_level,
                    method=series.method,
                    observations_used=series.observations_used,
                    history=series.history,
                    projections=projections,
                )
            )

        return DashboardReportResponse(
            generated_at=forecast.generated_at,
            horizon=forecast.horizon,
            max_class_size=request.max_class_size,
            available_class_levels=available_class_levels,
            summary=self._build_summary(historical, report_series),
            historical=historical,
            series=report_series,
            skipped=forecast.skipped,
        )

    def _load_demographic_history(
        self,
        db: Session,
    ) -> list[tuple[str, str, str, int]]:
        rows = db.execute(
            select(
                EnrollmentRecord.academic_year,
                EnrollmentRecord.class_level,
                EnrollmentRecord.sex,
                func.sum(EnrollmentRecord.enrollment_count).label("total"),
            )
            .group_by(
                EnrollmentRecord.academic_year,
                EnrollmentRecord.class_level,
                EnrollmentRecord.sex,
            )
            .order_by(
                EnrollmentRecord.academic_year,
                EnrollmentRecord.class_level,
                EnrollmentRecord.sex,
            )
        ).all()
        return [
            (academic_year, class_level, sex, int(total))
            for academic_year, class_level, sex, total in rows
        ]

    def _build_historical_points(
        self,
        rows: list[tuple[str, str, str, int]],
        selected_levels: set[str],
    ) -> list[HistoricalBreakdownPoint]:
        grouped: dict[tuple[str, str], dict[str, int]] = defaultdict(
            lambda: {"Male": 0, "Female": 0}
        )
        for academic_year, class_level, sex, total in rows:
            if class_level.casefold() in selected_levels:
                grouped[(academic_year, class_level)][sex] += total

        return [
            HistoricalBreakdownPoint(
                academic_year=academic_year,
                class_level=class_level,
                male=counts["Male"],
                female=counts["Female"],
                total=counts["Male"] + counts["Female"],
            )
            for (academic_year, class_level), counts in sorted(
                grouped.items(),
                key=lambda item: (item[0][0], item[0][1].casefold()),
            )
        ]

    def _build_summary(
        self,
        historical: list[HistoricalBreakdownPoint],
        series: list[DashboardForecastSeries],
    ) -> DashboardSummary:
        totals_by_year: dict[str, int] = defaultdict(int)
        for point in historical:
            totals_by_year[point.academic_year] += point.total

        ordered_years = sorted(totals_by_year)
        latest_year = ordered_years[-1]
        latest_enrollment = totals_by_year[latest_year]
        previous_enrollment = (
            totals_by_year[ordered_years[-2]] if len(ordered_years) > 1 else None
        )
        change = (
            round(
                (latest_enrollment - previous_enrollment)
                / previous_enrollment
                * 100,
                2,
            )
            if previous_enrollment
            else None
        )

        first_projections = [
            report_series.projections[0]
            for report_series in series
            if report_series.projections
        ]
        next_academic_year = first_projections[0].academic_year
        return DashboardSummary(
            latest_academic_year=latest_year,
            latest_enrollment=latest_enrollment,
            year_over_year_change_percent=change,
            next_academic_year=next_academic_year,
            next_year_forecast=sum(
                point.predicted_enrollment for point in first_projections
            ),
            next_year_recommended_sections=sum(
                point.recommended_sections for point in first_projections
            ),
        )

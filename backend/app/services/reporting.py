from collections import defaultdict

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.enrollment_dims import normalize_location
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
        available_programs = sorted(
            {row[1] for row in aggregate_rows},
            key=str.casefold,
        )
        available_year_levels = sorted(
            {row[2] for row in aggregate_rows},
            key=str.casefold,
        )
        available_locations = sorted(
            {row[3] for row in aggregate_rows},
            key=str.casefold,
        )

        forecast = EnrollmentForecastService().generate(
            db,
            ForecastRequest(
                horizon=request.horizon,
                programs=request.programs,
                year_levels=request.year_levels,
                locations=request.locations,
            ),
        )
        historical = self._build_historical_points(aggregate_rows, request)

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
                    program=series.program,
                    year_level=series.year_level,
                    location=series.location,
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
            available_programs=available_programs,
            available_year_levels=available_year_levels,
            available_locations=available_locations,
            summary=self._build_summary(historical, report_series),
            historical=historical,
            series=report_series,
            skipped=forecast.skipped,
        )

    def _load_demographic_history(
        self,
        db: Session,
    ) -> list[tuple[str, str, str, str, str, int]]:
        rows = db.execute(
            select(
                EnrollmentRecord.academic_year,
                EnrollmentRecord.program,
                EnrollmentRecord.year_level,
                EnrollmentRecord.location,
                EnrollmentRecord.sex,
                func.sum(EnrollmentRecord.enrollment_count).label("total"),
            )
            .group_by(
                EnrollmentRecord.academic_year,
                EnrollmentRecord.program,
                EnrollmentRecord.year_level,
                EnrollmentRecord.location,
                EnrollmentRecord.sex,
            )
            .order_by(
                EnrollmentRecord.academic_year,
                EnrollmentRecord.program,
                EnrollmentRecord.year_level,
                EnrollmentRecord.location,
                EnrollmentRecord.sex,
            )
        ).all()
        return [
            (academic_year, program, year_level, location, sex, int(total))
            for academic_year, program, year_level, location, sex, total in rows
        ]

    def _build_historical_points(
        self,
        rows: list[tuple[str, str, str, str, str, int]],
        request: DashboardReportRequest,
    ) -> list[HistoricalBreakdownPoint]:
        program_filter = (
            {value.casefold() for value in request.programs}
            if request.programs
            else None
        )
        year_filter = (
            {value.casefold() for value in request.year_levels}
            if request.year_levels
            else None
        )
        location_filter = (
            {normalize_location(value).casefold() for value in request.locations}
            if request.locations
            else None
        )

        grouped: dict[tuple[str, str, str, str], dict[str, int]] = defaultdict(
            lambda: {"Male": 0, "Female": 0}
        )
        for academic_year, program, year_level, location, sex, total in rows:
            if program_filter is not None and program.casefold() not in program_filter:
                continue
            if year_filter is not None and year_level.casefold() not in year_filter:
                continue
            if (
                location_filter is not None
                and location.casefold() not in location_filter
            ):
                continue
            grouped[(academic_year, program, year_level, location)][sex] += total

        return [
            HistoricalBreakdownPoint(
                academic_year=academic_year,
                program=program,
                year_level=year_level,
                location=location,
                male=counts["Male"],
                female=counts["Female"],
                total=counts["Male"] + counts["Female"],
            )
            for (academic_year, program, year_level, location), counts in sorted(
                grouped.items(),
                key=lambda item: (
                    item[0][0],
                    item[0][1].casefold(),
                    item[0][2].casefold(),
                    item[0][3].casefold(),
                ),
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
        all_projections = [
            point
            for report_series in series
            for point in report_series.projections
        ]
        projection_years = sorted({point.academic_year for point in all_projections})
        next_academic_year = first_projections[0].academic_year
        return DashboardSummary(
            latest_academic_year=latest_year,
            latest_enrollment=latest_enrollment,
            year_over_year_change_percent=change,
            next_academic_year=next_academic_year,
            total_forecast=sum(
                point.predicted_enrollment for point in all_projections
            ),
            forecast_horizon_start=projection_years[0],
            forecast_horizon_end=projection_years[-1],
            next_year_recommended_sections=sum(
                point.recommended_sections for point in first_projections
            ),
        )

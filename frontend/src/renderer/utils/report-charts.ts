import type { ChartData } from 'chart.js'

import type {
  DashboardForecastSeries,
  HistoricalBreakdownPoint,
} from '../../shared/reports'

export const REPORT_COLORS = {
  blue: '#2563eb',
  blueSoft: 'rgba(37, 99, 235, 0.18)',
  amber: '#d97706',
  emerald: '#059669',
  rose: '#e11d48',
  slate: '#64748b',
} as const

function yearStart(value: string): number {
  const parsed = Number.parseInt(value.split('-')[0], 10)
  return Number.isFinite(parsed) ? parsed : Number.MAX_SAFE_INTEGER
}

export function sortAcademicYears(years: Iterable<string>): string[] {
  return Array.from(new Set(Array.from(years))).sort(
    (left, right) => yearStart(left) - yearStart(right) || left.localeCompare(right),
  )
}

function sumByYear(
  points: Array<{ academic_year: string; value: number }>,
): Map<string, number> {
  const totals = new Map<string, number>()
  for (const point of points) {
    totals.set(point.academic_year, (totals.get(point.academic_year) ?? 0) + point.value)
  }
  return totals
}

export function buildEnrollmentTrendData(
  series: DashboardForecastSeries[],
): ChartData<'line', Array<number | null>, string> {
  const actual = sumByYear(
    series.flatMap((item) =>
      item.history.map((point) => ({
        academic_year: point.academic_year,
        value: point.enrollment_count,
      })),
    ),
  )
  const forecast = sumByYear(
    series.flatMap((item) =>
      item.projections.map((point) => ({
        academic_year: point.academic_year,
        value: point.predicted_enrollment,
      })),
    ),
  )
  const labels = sortAcademicYears([
    ...Array.from(actual.keys()),
    ...Array.from(forecast.keys()),
  ])
  const lastActualYear = sortAcademicYears(actual.keys()).at(-1)

  return {
    labels,
    datasets: [
      {
        label: 'Historical enrollment',
        data: labels.map((year) => actual.get(year) ?? null),
        borderColor: REPORT_COLORS.blue,
        backgroundColor: REPORT_COLORS.blueSoft,
        pointBackgroundColor: REPORT_COLORS.blue,
        tension: 0.25,
        spanGaps: false,
      },
      {
        label: 'Forecast enrollment',
        data: labels.map((year) =>
          year === lastActualYear ? (actual.get(year) ?? null) : (forecast.get(year) ?? null),
        ),
        borderColor: REPORT_COLORS.amber,
        backgroundColor: REPORT_COLORS.amber,
        pointBackgroundColor: REPORT_COLORS.amber,
        borderDash: [7, 5],
        tension: 0.25,
        spanGaps: false,
      },
    ],
  }
}

export function buildDemographicData(
  historical: HistoricalBreakdownPoint[],
): ChartData<'bar', number[], string> {
  const male = sumByYear(
    historical.map((point) => ({
      academic_year: point.academic_year,
      value: point.male,
    })),
  )
  const female = sumByYear(
    historical.map((point) => ({
      academic_year: point.academic_year,
      value: point.female,
    })),
  )
  const labels = sortAcademicYears([
    ...Array.from(male.keys()),
    ...Array.from(female.keys()),
  ])

  return {
    labels,
    datasets: [
      {
        label: 'Male',
        data: labels.map((year) => male.get(year) ?? 0),
        backgroundColor: REPORT_COLORS.blue,
        borderRadius: 4,
      },
      {
        label: 'Female',
        data: labels.map((year) => female.get(year) ?? 0),
        backgroundColor: REPORT_COLORS.rose,
        borderRadius: 4,
      },
    ],
  }
}

export function buildSectionRecommendationData(
  series: DashboardForecastSeries[],
): ChartData<'bar', number[], string> {
  const enrollment = sumByYear(
    series.flatMap((item) =>
      item.projections.map((point) => ({
        academic_year: point.academic_year,
        value: point.predicted_enrollment,
      })),
    ),
  )
  const sections = sumByYear(
    series.flatMap((item) =>
      item.projections.map((point) => ({
        academic_year: point.academic_year,
        value: point.recommended_sections,
      })),
    ),
  )
  const labels = sortAcademicYears([
    ...Array.from(enrollment.keys()),
    ...Array.from(sections.keys()),
  ])

  return {
    labels,
    datasets: [
      {
        label: 'Projected enrollment',
        data: labels.map((year) => enrollment.get(year) ?? 0),
        backgroundColor: REPORT_COLORS.emerald,
        borderRadius: 4,
        yAxisID: 'y',
      },
      {
        label: 'Recommended sections',
        data: labels.map((year) => sections.get(year) ?? 0),
        backgroundColor: REPORT_COLORS.amber,
        borderRadius: 4,
        yAxisID: 'sections',
      },
    ],
  }
}

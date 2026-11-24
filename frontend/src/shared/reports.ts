import type { ApiResult } from './enrollment'

export interface DashboardReportRequest {
  horizon: number
  max_class_size: number
  programs?: string[] | null
  year_levels?: string[] | null
  locations?: string[] | null
}

export interface HistoricalBreakdownPoint {
  academic_year: string
  program: string
  year_level: string
  location: string
  male: number
  female: number
  total: number
}

export interface ReportHistoryPoint {
  academic_year: string
  enrollment_count: number
}

export interface ReportProjectionPoint {
  academic_year: string
  predicted_enrollment: number
  recommended_sections: number
  planned_class_size: number
}

export interface ForecastHistoryExplainRow {
  academic_year: string
  actual_enrollment: number
  yearly_change: number
  model_error: number | null
}

export interface ForecastCalculationExplain {
  method: 'arima' | 'linear_trend'
  model_label: string
  latest_enrollment: number
  latest_change: number
  predicted_change: number
  raw_forecast: number
  final_forecast: number
  ar_coefficient: number | null
  trend_coefficient: number | null
  slope: number | null
  intercept: number | null
  total_abs_error: number | null
}

export interface SeriesForecastExplanation {
  history_rows: ForecastHistoryExplainRow[]
  calculation: ForecastCalculationExplain
}

export interface DashboardForecastSeries {
  program: string
  year_level: string
  location: string
  method: 'arima' | 'linear_trend'
  observations_used: number
  history: ReportHistoryPoint[]
  projections: ReportProjectionPoint[]
  explanation: SeriesForecastExplanation
}

export interface SkippedReportSeries {
  program: string
  year_level: string
  location: string
  reason: string
}

export interface DashboardSummary {
  latest_academic_year: string
  latest_enrollment: number
  year_over_year_change_percent: number | null
  next_academic_year: string
  total_forecast: number
  forecast_horizon_start: string
  forecast_horizon_end: string
  next_year_recommended_sections: number
}

export interface DashboardReportResponse {
  generated_at: string
  horizon: number
  max_class_size: number
  available_programs: string[]
  available_year_levels: string[]
  available_locations: string[]
  summary: DashboardSummary
  historical: HistoricalBreakdownPoint[]
  series: DashboardForecastSeries[]
  skipped: SkippedReportSeries[]
}

export interface ReportsApi {
  getDashboardReport: (
    request: DashboardReportRequest,
  ) => Promise<ApiResult<DashboardReportResponse>>
}

export function seriesLabel(series: {
  program: string
  year_level: string
  location: string
}): string {
  return `${series.program} ${series.year_level} · ${series.location}`
}

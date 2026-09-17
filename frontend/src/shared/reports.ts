import type { ApiResult } from './enrollment'

export interface DashboardReportRequest {
  horizon: number
  max_class_size: number
  class_levels?: string[] | null
}

export interface HistoricalBreakdownPoint {
  academic_year: string
  class_level: string
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

export interface DashboardForecastSeries {
  class_level: string
  method: 'arima' | 'linear_trend'
  observations_used: number
  history: ReportHistoryPoint[]
  projections: ReportProjectionPoint[]
}

export interface SkippedReportSeries {
  class_level: string
  reason: string
}

export interface DashboardSummary {
  latest_academic_year: string
  latest_enrollment: number
  year_over_year_change_percent: number | null
  next_academic_year: string
  next_year_forecast: number
  next_year_recommended_sections: number
}

export interface DashboardReportResponse {
  generated_at: string
  horizon: number
  max_class_size: number
  available_class_levels: string[]
  summary: DashboardSummary
  historical: HistoricalBreakdownPoint[]
  series: DashboardForecastSeries[]
  skipped: SkippedReportSeries[]
}

export interface ReportsApi {
  getDashboardReport: (
    request: DashboardReportRequest
  ) => Promise<ApiResult<DashboardReportResponse>>
}

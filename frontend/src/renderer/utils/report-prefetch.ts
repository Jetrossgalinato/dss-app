import type {
  DashboardReportRequest,
  DashboardReportResponse,
} from '../../shared/reports'
import { getCached, setCached } from './api-cache'

export const REPORT_CACHE_ENDPOINT = 'reports/dashboard'
export const DEFAULT_REPORT_HORIZON = 3
export const DEFAULT_REPORT_MAX_CLASS_SIZE = 25

export function defaultDashboardRequest(): DashboardReportRequest {
  return {
    horizon: DEFAULT_REPORT_HORIZON,
    max_class_size: DEFAULT_REPORT_MAX_CLASS_SIZE,
    programs: null,
    year_levels: null,
    locations: null,
  }
}

export function getCachedDashboardReport(
  request: DashboardReportRequest = defaultDashboardRequest(),
): DashboardReportResponse | undefined {
  return getCached<DashboardReportResponse>(REPORT_CACHE_ENDPOINT, request)
}

export function setCachedDashboardReport(
  request: DashboardReportRequest,
  data: DashboardReportResponse,
): void {
  setCached(REPORT_CACHE_ENDPOINT, request, data)
}

/** Warm the default reports dashboard cache in the background. Errors are ignored. */
export async function prefetchDefaultDashboardReport(): Promise<void> {
  if (typeof window === 'undefined' || !window.api?.getDashboardReport) return

  const request = defaultDashboardRequest()
  if (getCachedDashboardReport(request)) return

  try {
    const result = await window.api.getDashboardReport(request)
    if (result.ok) {
      setCachedDashboardReport(request, result.data)
    }
  } catch {
    // Prefetch is best-effort; ignore failures.
  }
}

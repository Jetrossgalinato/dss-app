import { contextBridge, ipcRenderer } from 'electron'

import type {
  ApiError,
  ApiResult,
  EnrollmentApi,
  EnrollmentFilters,
  HealthResult,
} from '../shared/enrollment'
import type {
  SectionPlanningApi,
  SectionRecommendationRequest,
  SectionRecommendationResponse,
} from '../shared/section-planning'
import type {
  DashboardReportRequest,
  DashboardReportResponse,
  ReportsApi,
} from '../shared/reports'

interface BackendRuntimeConfig {
  url: string
  token: string
}

let runtimeConfigPromise: Promise<BackendRuntimeConfig> | null = null

function getRuntimeConfig(): Promise<BackendRuntimeConfig> {
  runtimeConfigPromise ??= ipcRenderer.invoke(
    'dss:get-backend-config',
  ) as Promise<BackendRuntimeConfig>
  return runtimeConfigPromise
}

async function backendFetch(path: string, init: RequestInit = {}): Promise<Response> {
  const config = await getRuntimeConfig()
  const headers = new Headers(init.headers)
  if (config.token) headers.set('X-DSS-Token', config.token)
  return fetch(`${config.url}${path}`, { ...init, headers })
}

async function parseResponse<T>(response: Response): Promise<ApiResult<T>> {
  if (response.ok) {
    return { ok: true, data: (await response.json()) as T }
  }

  let error: ApiError = {
    message: `Request failed with HTTP ${response.status}.`,
    errors: [],
  }
  try {
    const body = (await response.json()) as {
      detail?: string | ApiError
    }
    if (typeof body.detail === 'string') {
      error = { message: body.detail, errors: [] }
    } else if (body.detail) {
      error = body.detail
    }
  } catch {
    // Preserve the generic HTTP error when the body is not JSON.
  }
  return { ok: false, error }
}

function connectionError(error: unknown): ApiError {
  return {
    message: error instanceof Error ? error.message : 'Could not reach the backend.',
    errors: [],
  }
}

const api: EnrollmentApi & SectionPlanningApi & ReportsApi = {
  getBackendHealth: async (): Promise<HealthResult> => {
    try {
      const response = await backendFetch('/health')
      if (!response.ok) {
        return { ok: false, error: `HTTP ${response.status}` }
      }
      const data = (await response.json()) as { status?: string }
      return { ok: true, status: data.status ?? 'unknown' }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Request failed'
      return { ok: false, error: message }
    }
  },
  importEnrollments: async (filename, bytes) => {
    try {
      const payload = new Uint8Array(bytes.byteLength)
      payload.set(bytes)
      const form = new FormData()
      form.append('file', new Blob([payload.buffer], { type: 'text/csv' }), filename)
      return await parseResponse(
        await backendFetch('/api/enrollments/import', {
          method: 'POST',
          body: form,
        }),
      )
    } catch (error) {
      return { ok: false, error: connectionError(error) }
    }
  },
  listEnrollments: async (filters: EnrollmentFilters) => {
    try {
      const query = new URLSearchParams()
      query.set('page', String(filters.page ?? 1))
      query.set('page_size', String(filters.pageSize ?? 20))
      if (filters.academicYear) query.set('academic_year', filters.academicYear)
      if (filters.classLevel) query.set('class_level', filters.classLevel)
      if (filters.sex) query.set('sex', filters.sex)
      return await parseResponse(
        await backendFetch(`/api/enrollments?${query.toString()}`),
      )
    } catch (error) {
      return { ok: false, error: connectionError(error) }
    }
  },
  deleteEnrollment: async (id) => {
    try {
      return await parseResponse(
        await backendFetch(`/api/enrollments/${id}`, { method: 'DELETE' }),
      )
    } catch (error) {
      return { ok: false, error: connectionError(error) }
    }
  },
  clearEnrollments: async () => {
    try {
      return await parseResponse(
        await backendFetch('/api/enrollments', { method: 'DELETE' }),
      )
    } catch (error) {
      return { ok: false, error: connectionError(error) }
    }
  },
  getEnrollmentTemplate: async () => {
    try {
      const response = await backendFetch('/api/enrollments/template')
      if (!response.ok) return await parseResponse(response)
      return { ok: true, data: await response.text() }
    } catch (error) {
      return { ok: false, error: connectionError(error) }
    }
  },
  getSectionRecommendations: async (
    request: SectionRecommendationRequest,
  ) => {
    try {
      return await parseResponse<SectionRecommendationResponse>(
        await backendFetch('/api/sections/recommendations', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(request),
        }),
      )
    } catch (error) {
      return { ok: false, error: connectionError(error) }
    }
  },
  getDashboardReport: async (request: DashboardReportRequest) => {
    try {
      return await parseResponse<DashboardReportResponse>(
        await backendFetch('/api/reports/dashboard', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(request),
        }),
      )
    } catch (error) {
      return { ok: false, error: connectionError(error) }
    }
  },
}

contextBridge.exposeInMainWorld('api', api)

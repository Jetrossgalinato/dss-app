export type HealthResult =
  | { ok: true; status: string }
  | { ok: false; error: string }

export interface EnrollmentRecord {
  id: number
  academic_year: string
  class_level: string
  sex: 'Male' | 'Female'
  enrollment_count: number
  created_at: string
  updated_at: string
}

export interface EnrollmentFilters {
  page?: number
  pageSize?: number
  academicYear?: string
  classLevel?: string
  sex?: '' | 'Male' | 'Female'
}

export interface EnrollmentList {
  items: EnrollmentRecord[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface ImportRowError {
  row: number | null
  field: string | null
  message: string
}

export interface ImportSummary {
  inserted: number
  updated: number
  total: number
}

export interface ApiError {
  message: string
  errors: ImportRowError[]
}

export type ApiResult<T> = { ok: true; data: T } | { ok: false; error: ApiError }

export interface EnrollmentApi {
  getBackendHealth: () => Promise<HealthResult>
  importEnrollments: (
    filename: string,
    bytes: Uint8Array,
  ) => Promise<ApiResult<ImportSummary>>
  listEnrollments: (filters: EnrollmentFilters) => Promise<ApiResult<EnrollmentList>>
  deleteEnrollment: (id: number) => Promise<ApiResult<{ deleted: boolean; id: number }>>
  getEnrollmentTemplate: () => Promise<ApiResult<string>>
}

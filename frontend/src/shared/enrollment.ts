export type HealthResult =
  | { ok: true; status: string }
  | { ok: false; error: string }

export const ALLOWED_YEAR_LEVELS = [
  '1st Year',
  '2nd Year',
  '3rd Year',
  '4th Year',
] as const

export type YearLevel = (typeof ALLOWED_YEAR_LEVELS)[number]

export interface EnrollmentRecord {
  id: number
  academic_year: string
  program: string
  year_level: string
  sex: 'Male' | 'Female'
  location: string
  enrollment_count: number
  created_at: string
  updated_at: string
}

export interface EnrollmentFilters {
  page?: number
  pageSize?: number
  academicYear?: string
  program?: string
  yearLevel?: string
  location?: string
  sex?: '' | 'Male' | 'Female'
}

export interface EnrollmentList {
  items: EnrollmentRecord[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface EnrollmentFilterOptions {
  programs: string[]
  year_levels: string[]
  locations: string[]
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

export interface EnrollmentUpsertPayload {
  academic_year: string
  program: string
  year_level: string
  sex: 'Male' | 'Female'
  location: string
  enrollment_count: number
}

export interface EnrollmentUpsertResult {
  created: boolean
  record: EnrollmentRecord
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
  upsertEnrollment: (
    payload: EnrollmentUpsertPayload,
  ) => Promise<ApiResult<EnrollmentUpsertResult>>
  listEnrollments: (filters: EnrollmentFilters) => Promise<ApiResult<EnrollmentList>>
  getEnrollmentFilterOptions: () => Promise<ApiResult<EnrollmentFilterOptions>>
  deleteEnrollment: (id: number) => Promise<ApiResult<{ deleted: boolean; id: number }>>
  clearEnrollments: () => Promise<ApiResult<{ deleted: boolean; deleted_count: number }>>
  getEnrollmentTemplate: () => Promise<ApiResult<string>>
}

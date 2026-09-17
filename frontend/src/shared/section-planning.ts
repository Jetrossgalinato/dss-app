import type { ApiResult } from './enrollment'

export interface SectionRecommendationRequest {
  horizon: number
  max_class_size: number
  class_levels?: string[] | null
}

export interface SectionRecommendation {
  academic_year: string
  predicted_enrollment: number
  max_class_size: number
  recommended_sections: number
  planned_class_size: number
}

export interface ClassSectionRecommendations {
  class_level: string
  method: 'arima' | 'linear_trend'
  observations_used: number
  recommendations: SectionRecommendation[]
}

export interface SkippedSectionSeries {
  class_level: string
  reason: string
}

export interface SectionRecommendationResponse {
  generated_at: string
  horizon: number
  max_class_size: number
  series: ClassSectionRecommendations[]
  skipped: SkippedSectionSeries[]
}

export interface SectionPlanningApi {
  getSectionRecommendations: (
    request: SectionRecommendationRequest,
  ) => Promise<ApiResult<SectionRecommendationResponse>>
}

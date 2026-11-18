import type { ApiResult } from './enrollment'

export interface SectionRecommendationRequest {
  horizon: number
  max_class_size: number
  programs?: string[] | null
  year_levels?: string[] | null
  locations?: string[] | null
}

export interface SectionRecommendation {
  academic_year: string
  predicted_enrollment: number
  max_class_size: number
  recommended_sections: number
  planned_class_size: number
}

export interface SeriesSectionRecommendations {
  program: string
  year_level: string
  location: string
  method: 'arima' | 'linear_trend'
  observations_used: number
  recommendations: SectionRecommendation[]
}

export interface SkippedSectionSeries {
  program: string
  year_level: string
  location: string
  reason: string
}

export interface SectionRecommendationResponse {
  generated_at: string
  horizon: number
  max_class_size: number
  series: SeriesSectionRecommendations[]
  skipped: SkippedSectionSeries[]
}

export interface SectionPlanningApi {
  getSectionRecommendations: (
    request: SectionRecommendationRequest,
  ) => Promise<ApiResult<SectionRecommendationResponse>>
}

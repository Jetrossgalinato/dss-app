import { describe, expect, it } from 'vitest'

import type {
  DashboardForecastSeries,
  HistoricalBreakdownPoint,
} from '../../shared/reports'
import {
  buildDemographicData,
  buildEnrollmentTrendData,
  buildSectionRecommendationData,
  sortAcademicYears,
} from './report-charts'

const series: DashboardForecastSeries[] = [
  {
    class_level: 'Nursery',
    method: 'linear_trend',
    observations_used: 2,
    history: [
      { academic_year: '2023-2024', enrollment_count: 22 },
      { academic_year: '2022-2023', enrollment_count: 20 },
    ],
    projections: [
      {
        academic_year: '2024-2025',
        predicted_enrollment: 24,
        recommended_sections: 2,
        planned_class_size: 12,
      },
    ],
  },
  {
    class_level: 'Kindergarten',
    method: 'linear_trend',
    observations_used: 2,
    history: [
      { academic_year: '2022-2023', enrollment_count: 30 },
      { academic_year: '2023-2024', enrollment_count: 33 },
    ],
    projections: [
      {
        academic_year: '2024-2025',
        predicted_enrollment: 36,
        recommended_sections: 2,
        planned_class_size: 18,
      },
    ],
  },
]

describe('report chart dataset builders', () => {
  it('orders academic years chronologically', () => {
    expect(sortAcademicYears(['2024-2025', '2022-2023', '2023-2024'])).toEqual([
      '2022-2023',
      '2023-2024',
      '2024-2025',
    ])
  })

  it('joins actual and forecast lines at the latest actual year', () => {
    const data = buildEnrollmentTrendData(series)

    expect(data.labels).toEqual(['2022-2023', '2023-2024', '2024-2025'])
    expect(data.datasets[0].data).toEqual([50, 55, null])
    expect(data.datasets[1].data).toEqual([null, 55, 60])
  })

  it('builds stacked demographic totals by year', () => {
    const history: HistoricalBreakdownPoint[] = [
      {
        academic_year: '2023-2024',
        class_level: 'Nursery',
        male: 12,
        female: 10,
        total: 22,
      },
      {
        academic_year: '2023-2024',
        class_level: 'Kindergarten',
        male: 15,
        female: 18,
        total: 33,
      },
    ]

    const data = buildDemographicData(history)
    expect(data.labels).toEqual(['2023-2024'])
    expect(data.datasets[0].data).toEqual([27])
    expect(data.datasets[1].data).toEqual([28])
  })

  it('aggregates projected enrollment and sections', () => {
    const data = buildSectionRecommendationData(series)
    expect(data.labels).toEqual(['2024-2025'])
    expect(data.datasets[0].data).toEqual([60])
    expect(data.datasets[1].data).toEqual([4])
  })

  it('returns valid empty datasets', () => {
    expect(buildEnrollmentTrendData([]).labels).toEqual([])
    expect(buildDemographicData([]).datasets[0].data).toEqual([])
    expect(buildSectionRecommendationData([]).labels).toEqual([])
  })
})

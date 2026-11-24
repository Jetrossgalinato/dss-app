import { describe, expect, it } from 'vitest'

import {
  buildReportNarrative,
  buildSectionPlanNarrative,
  countSeriesMethods,
} from './forecast-narrative'

describe('forecast-narrative', () => {
  it('counts series methods', () => {
    expect(
      countSeriesMethods([
        { method: 'arima' },
        { method: 'arima' },
        { method: 'linear_trend' },
      ]),
    ).toEqual({ arimaCount: 2, linearCount: 1 })
  })

  it('describes a mixed ARIMA-dominant plan', () => {
    const narrative = buildSectionPlanNarrative({
      seriesCount: 240,
      horizon: 3,
      projectedLearners: 21309,
      recommendedSections: 1180,
      maxClassSize: 25,
      arimaCount: 210,
      linearCount: 30,
      skippedCount: 0,
    })

    expect(narrative).toContain('Across 240 series over 3 academic years')
    expect(narrative).toContain('the plan projects 21,309 learners')
    expect(narrative).toContain('recommends 1,180 sections')
    expect(narrative).toContain('maximum class size 25')
    expect(narrative).toContain('Most series used ARIMA (210 ARIMA, 30 linear trend).')
  })

  it('describes an all-linear report with skipped series', () => {
    const narrative = buildReportNarrative({
      seriesCount: 12,
      horizon: 1,
      projectedLearners: 400,
      recommendedSections: 20,
      maxClassSize: 25,
      arimaCount: 0,
      linearCount: 12,
      skippedCount: 2,
    })

    expect(narrative).toContain('the report projects 400 learners')
    expect(narrative).toContain('All 12 series used a linear trend.')
    expect(narrative).toContain('2 series were skipped.')
  })

  it('describes an even method split', () => {
    const narrative = buildSectionPlanNarrative({
      seriesCount: 10,
      horizon: 2,
      projectedLearners: 100,
      recommendedSections: 8,
      maxClassSize: 25,
      arimaCount: 5,
      linearCount: 5,
      skippedCount: 0,
    })

    expect(narrative).toContain(
      'Series used ARIMA and linear trend evenly (5 ARIMA, 5 linear trend).',
    )
  })
})

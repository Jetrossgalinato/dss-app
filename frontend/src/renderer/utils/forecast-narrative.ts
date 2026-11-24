export type ForecastMethod = 'arima' | 'linear_trend'

export interface ForecastNarrativeInput {
  seriesCount: number
  horizon: number
  projectedLearners: number
  recommendedSections: number
  maxClassSize: number
  arimaCount: number
  linearCount: number
  skippedCount: number
}

function formatCount(value: number): string {
  return value.toLocaleString()
}

function horizonPhrase(horizon: number): string {
  return `${horizon} academic ${horizon === 1 ? 'year' : 'years'}`
}

export function countSeriesMethods(
  series: ReadonlyArray<{ method: ForecastMethod }>,
): { arimaCount: number; linearCount: number } {
  let arimaCount = 0
  let linearCount = 0
  for (const item of series) {
    if (item.method === 'arima') arimaCount += 1
    else linearCount += 1
  }
  return { arimaCount, linearCount }
}

function methodSentence(arimaCount: number, linearCount: number): string {
  if (arimaCount === 0 && linearCount === 0) {
    return 'No forecast methods were recorded.'
  }
  if (linearCount === 0) {
    return `All ${formatCount(arimaCount)} series used ARIMA.`
  }
  if (arimaCount === 0) {
    return `All ${formatCount(linearCount)} series used a linear trend.`
  }
  if (arimaCount === linearCount) {
    return `Series used ARIMA and linear trend evenly (${formatCount(arimaCount)} ARIMA, ${formatCount(linearCount)} linear trend).`
  }
  if (arimaCount > linearCount) {
    return `Most series used ARIMA (${formatCount(arimaCount)} ARIMA, ${formatCount(linearCount)} linear trend).`
  }
  return `Most series used a linear trend (${formatCount(linearCount)} linear trend, ${formatCount(arimaCount)} ARIMA).`
}

function skippedClause(skippedCount: number): string {
  if (skippedCount <= 0) return ''
  return ` ${formatCount(skippedCount)} series ${skippedCount === 1 ? 'was' : 'were'} skipped.`
}

function buildNarrative(
  kind: 'plan' | 'report',
  input: ForecastNarrativeInput,
): string {
  const subject = kind === 'plan' ? 'the plan' : 'the report'
  const lead = `Across ${formatCount(input.seriesCount)} series over ${horizonPhrase(input.horizon)}, ${subject} projects ${formatCount(input.projectedLearners)} learners and recommends ${formatCount(input.recommendedSections)} sections (maximum class size ${formatCount(input.maxClassSize)}).`
  return `${lead} ${methodSentence(input.arimaCount, input.linearCount)}${skippedClause(input.skippedCount)}`
}

export function buildSectionPlanNarrative(input: ForecastNarrativeInput): string {
  return buildNarrative('plan', input)
}

export function buildReportNarrative(input: ForecastNarrativeInput): string {
  return buildNarrative('report', input)
}

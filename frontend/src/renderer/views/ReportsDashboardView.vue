<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { toast } from 'vue-sonner'

import type { DashboardReportRequest, DashboardReportResponse } from '../../shared/reports'
import { seriesLabel } from '../../shared/reports'
import {
  DEFAULT_REPORT_HORIZON,
  DEFAULT_REPORT_MAX_CLASS_SIZE,
  getCachedDashboardReport,
  setCachedDashboardReport,
} from '../utils/report-prefetch'
import ForecastExplanation from '../components/ForecastExplanation.vue'
import DemographicBreakdownChart from '../components/reports/DemographicBreakdownChart.vue'
import EnrollmentTrendChart from '../components/reports/EnrollmentTrendChart.vue'
import ReportDataTables from '../components/reports/ReportDataTables.vue'
import ReportFilters from '../components/reports/ReportFilters.vue'
import ReportSummaryCards from '../components/reports/ReportSummaryCards.vue'
import SectionRecommendationChart from '../components/reports/SectionRecommendationChart.vue'
import {
  buildReportNarrative,
  countSeriesMethods,
} from '../utils/forecast-narrative'

const DEFAULT_HORIZON = DEFAULT_REPORT_HORIZON
const DEFAULT_MAX_CLASS_SIZE = DEFAULT_REPORT_MAX_CLASS_SIZE

const route = useRoute()
const isReportsRoute = computed(() => route.name === 'reports')

const report = ref<DashboardReportResponse | null>(null)
const programs = ref<string[]>([])
const yearLevels = ref<string[]>([])
const locations = ref<string[]>([])
const selectedProgram = ref('')
const selectedYearLevel = ref('')
const selectedLocation = ref('')
const horizon = ref(DEFAULT_HORIZON)
const maxClassSize = ref(DEFAULT_MAX_CLASS_SIZE)
const loading = ref(true)
const refreshing = ref(false)
const errorMessage = ref('')

const canPrint = computed(() => report.value !== null && !loading.value)

const reportNarrative = computed(() => {
  if (!report.value || report.value.series.length === 0) return ''
  const methods = countSeriesMethods(report.value.series)
  return buildReportNarrative({
    seriesCount: report.value.series.length,
    horizon: report.value.horizon,
    projectedLearners: report.value.summary.total_forecast,
    recommendedSections: report.value.summary.next_year_recommended_sections,
    maxClassSize: report.value.max_class_size,
    arimaCount: methods.arimaCount,
    linearCount: methods.linearCount,
    skippedCount: report.value.skipped.length,
  })
})

const printScope = computed(() => ({
  program: selectedProgram.value || 'All programs',
  yearLevel: selectedYearLevel.value || 'All year levels',
  location: selectedLocation.value || 'All locations',
  horizon: `${horizon.value} academic ${horizon.value === 1 ? 'year' : 'years'}`,
  maxClassSize: String(maxClassSize.value),
}))

const printGeneratedAt = computed(() => {
  if (!report.value) return ''
  return new Date(report.value.generated_at).toLocaleString()
})

function reportRequest(): DashboardReportRequest {
  return {
    horizon: horizon.value,
    max_class_size: maxClassSize.value,
    programs: selectedProgram.value ? [selectedProgram.value] : null,
    year_levels: selectedYearLevel.value ? [selectedYearLevel.value] : null,
    locations: selectedLocation.value ? [selectedLocation.value] : null,
  }
}

function applyReport(data: DashboardReportResponse): void {
  report.value = data
  programs.value = data.available_programs
  yearLevels.value = data.available_year_levels
  locations.value = data.available_locations
}

function hydrateFromCache(): boolean {
  const cached = getCachedDashboardReport(reportRequest())
  if (!cached) return false
  applyReport(cached)
  errorMessage.value = ''
  loading.value = false
  return true
}

hydrateFromCache()

async function loadReport(showSuccess = false): Promise<void> {
  const request = reportRequest()
  const cached = getCachedDashboardReport(request)
  if (cached) {
    applyReport(cached)
    errorMessage.value = ''
    loading.value = false
    refreshing.value = false
    if (showSuccess) {
      toast.success('Report refreshed', {
        description: 'Showing cached report for these filters.',
        class: 'dss-progress-toast',
      })
    }
    return
  }

  const hasExisting = report.value !== null
  if (hasExisting) {
    refreshing.value = true
  } else {
    loading.value = true
  }
  errorMessage.value = ''

  const result = await window.api.getDashboardReport(request)

  if (result.ok) {
    setCachedDashboardReport(request, result.data)
    applyReport(result.data)
    if (showSuccess) {
      toast.success('Report refreshed', {
        description: 'Charts and tables now use the latest report data.',
        class: 'dss-progress-toast',
      })
    }
  } else if (!hasExisting) {
    errorMessage.value = result.error.message
    toast.error('Could not generate report', {
      description: result.error.message,
      class: 'dss-progress-toast dss-progress-toast--error',
      duration: 6000,
    })
  } else {
    toast.error('Could not refresh report', {
      description: result.error.message,
      class: 'dss-progress-toast dss-progress-toast--error',
      duration: 6000,
    })
  }
  loading.value = false
  refreshing.value = false
}

function applyFilters(filters: {
  program: string
  yearLevel: string
  location: string
  horizon: number
  maxClassSize: number
}): void {
  if (
    filters.horizon < 1 ||
    filters.horizon > 5 ||
    filters.maxClassSize < 1 ||
    filters.maxClassSize > 100
  ) {
    toast.warning('Check report filters', {
      description: 'Horizon must be 1–5 years and class size must be 1–100.',
      class: 'dss-progress-toast dss-progress-toast--error',
    })
    return
  }
  selectedProgram.value = filters.program
  selectedYearLevel.value = filters.yearLevel
  selectedLocation.value = filters.location
  horizon.value = filters.horizon
  maxClassSize.value = filters.maxClassSize
  void loadReport(true)
}

function resetFilters(): void {
  selectedProgram.value = ''
  selectedYearLevel.value = ''
  selectedLocation.value = ''
  horizon.value = DEFAULT_HORIZON
  maxClassSize.value = DEFAULT_MAX_CLASS_SIZE
  void loadReport(true)
}

function printReport(): void {
  if (!canPrint.value) return
  window.print()
}

onMounted(() => {
  if (!report.value) {
    void loadReport()
  }
})
</script>

<template>
  <div class="space-y-6">
    <Teleport v-if="isReportsRoute" to="#page-actions" defer>
      <button
        class="no-print inline-flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 shadow-sm transition hover:bg-slate-50 focus:ring-2 focus:ring-slate-400 focus:outline-none disabled:cursor-not-allowed disabled:opacity-50"
        type="button"
        :disabled="!canPrint"
        @click="printReport"
      >
        <svg aria-hidden="true" class="h-4 w-4" viewBox="0 0 24 24" fill="none">
          <path
            d="M7 8V4h10v4M7 16H5a2 2 0 0 1-2-2v-4a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v4a2 2 0 0 1-2 2h-2M7 12h10v8H7v-8Z"
            stroke="currentColor"
            stroke-width="1.75"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
        </svg>
        Print report
      </button>
    </Teleport>

    <ReportFilters
      class="no-print"
      :programs="programs"
      :year-levels="yearLevels"
      :locations="locations"
      :selected-program="selectedProgram"
      :selected-year-level="selectedYearLevel"
      :selected-location="selectedLocation"
      :horizon="horizon"
      :max-class-size="maxClassSize"
      :default-horizon="DEFAULT_HORIZON"
      :default-max-class-size="DEFAULT_MAX_CLASS_SIZE"
      :loading="loading || refreshing"
      @submit="applyFilters"
      @reset="resetFilters"
    />

    <ForecastExplanation
      v-if="report && report.series.length > 0"
      title="Report summary"
      :narrative="reportNarrative"
    />

    <div
      v-if="loading && !report"
      class="no-print space-y-4"
      aria-live="polite"
      aria-label="Loading report"
    >
      <div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <div
          v-for="index in 4"
          :key="index"
          class="h-32 animate-pulse rounded-2xl bg-slate-200"
        />
      </div>
      <div class="grid gap-6 lg:grid-cols-2">
        <div class="h-96 animate-pulse rounded-2xl bg-slate-200" />
        <div class="h-96 animate-pulse rounded-2xl bg-slate-200" />
      </div>
    </div>

    <div
      v-else-if="errorMessage && !report"
      class="no-print rounded-2xl border border-rose-200 bg-rose-50 p-6 text-rose-800"
      role="alert"
    >
      <h3 class="font-semibold">Report unavailable</h3>
      <p class="mt-1 text-sm">{{ errorMessage }}</p>
      <p class="mt-2 text-sm">
        Import at least two academic years of enrollment data, then try again.
      </p>
    </div>

    <div
      v-else-if="!report || report.series.length === 0"
      class="no-print rounded-2xl border border-slate-200 bg-white p-10 text-center shadow-sm"
    >
      <h3 class="font-semibold text-slate-900">No report data</h3>
      <p class="mt-1 text-sm text-slate-500">
        Import historical enrollment records before opening this dashboard.
      </p>
    </div>

    <div v-else class="print-report space-y-6">
      <header class="print-only print-letterhead">
        <p class="print-letterhead__org">Charismatic Tutorial Learning Center</p>
        <p class="print-letterhead__product">Enrollment Forecasting DSS</p>
        <hr class="print-letterhead__rule" />
        <h1 class="print-letterhead__title">Enrollment &amp; Section Forecast Report</h1>
        <dl class="print-meta">
          <div>
            <dt>Generated</dt>
            <dd>{{ printGeneratedAt }}</dd>
          </div>
          <div>
            <dt>Program</dt>
            <dd>{{ printScope.program }}</dd>
          </div>
          <div>
            <dt>Year level</dt>
            <dd>{{ printScope.yearLevel }}</dd>
          </div>
          <div>
            <dt>Location</dt>
            <dd>{{ printScope.location }}</dd>
          </div>
          <div>
            <dt>Forecast horizon</dt>
            <dd>{{ printScope.horizon }}</dd>
          </div>
          <div>
            <dt>Maximum class size</dt>
            <dd>{{ printScope.maxClassSize }}</dd>
          </div>
        </dl>
      </header>

      <div
        v-if="report.skipped.length"
        class="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900 print-note"
        role="status"
      >
        <p class="font-semibold">Some series were skipped</p>
        <ul class="mt-1 list-disc pl-5">
          <li
            v-for="item in report.skipped"
            :key="`${item.program}-${item.year_level}-${item.location}`"
          >
            {{ seriesLabel(item) }}: {{ item.reason }}
          </li>
        </ul>
      </div>

      <section class="print-section" aria-labelledby="print-section-summary">
        <h2 id="print-section-summary" class="print-only print-section__title">
          1. Executive summary
        </h2>
        <ReportSummaryCards :summary="report.summary" />
      </section>

      <section class="print-section" aria-labelledby="print-section-trend">
        <h2 id="print-section-trend" class="print-only print-section__title">
          2. Enrollment trend
        </h2>
        <EnrollmentTrendChart :series="report.series" />
      </section>

      <div class="grid gap-6 lg:grid-cols-2 print-chart-grid">
        <section class="print-section" aria-labelledby="print-section-demo">
          <h2 id="print-section-demo" class="print-only print-section__title">
            3. Demographic breakdown
          </h2>
          <DemographicBreakdownChart :historical="report.historical" />
        </section>
        <section class="print-section" aria-labelledby="print-section-sections">
          <h2 id="print-section-sections" class="print-only print-section__title">
            4. Section recommendations
          </h2>
          <SectionRecommendationChart :series="report.series" />
        </section>
      </div>

      <section class="print-section" aria-labelledby="print-section-tables">
        <h2 id="print-section-tables" class="print-only print-section__title">
          5. Detailed data
        </h2>
        <ReportDataTables
          :historical="report.historical"
          :series="report.series"
          :max-class-size="report.max_class_size"
        />
      </section>

      <p class="no-print text-right text-xs text-slate-400">
        Generated {{ new Date(report.generated_at).toLocaleString() }}
        <span v-if="refreshing"> · Refreshing…</span>
      </p>

      <footer class="print-only print-footer">
        Confidential · internal planning use · Charismatic Tutorial Learning Center
      </footer>
    </div>
  </div>
</template>

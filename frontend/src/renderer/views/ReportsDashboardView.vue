<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { toast } from 'vue-sonner'

import type { DashboardReportResponse } from '../../shared/reports'
import DemographicBreakdownChart from '../components/reports/DemographicBreakdownChart.vue'
import EnrollmentTrendChart from '../components/reports/EnrollmentTrendChart.vue'
import ReportDataTables from '../components/reports/ReportDataTables.vue'
import ReportFilters from '../components/reports/ReportFilters.vue'
import ReportSummaryCards from '../components/reports/ReportSummaryCards.vue'
import SectionRecommendationChart from '../components/reports/SectionRecommendationChart.vue'

const DEFAULT_HORIZON = 3
const DEFAULT_MAX_CLASS_SIZE = 25

const report = ref<DashboardReportResponse | null>(null)
const classLevels = ref<string[]>([])
const selectedClassLevel = ref('')
const horizon = ref(DEFAULT_HORIZON)
const maxClassSize = ref(DEFAULT_MAX_CLASS_SIZE)
const loading = ref(true)
const errorMessage = ref('')

async function loadReport(showSuccess = false): Promise<void> {
  loading.value = true
  errorMessage.value = ''
  report.value = null

  const result = await window.api.getDashboardReport({
    horizon: horizon.value,
    max_class_size: maxClassSize.value,
    class_levels: selectedClassLevel.value ? [selectedClassLevel.value] : null,
  })

  if (result.ok) {
    report.value = result.data
    classLevels.value = result.data.available_class_levels
    if (showSuccess) {
      toast.success('Report refreshed', {
        description: 'Charts and tables now use the latest report data.',
        class: 'dss-progress-toast',
      })
    }
  } else {
    errorMessage.value = result.error.message
    toast.error('Could not generate report', {
      description: result.error.message,
      class: 'dss-progress-toast dss-progress-toast--error',
      duration: 6000,
    })
  }
  loading.value = false
}

function applyFilters(filters: {
  classLevel: string
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
  selectedClassLevel.value = filters.classLevel
  horizon.value = filters.horizon
  maxClassSize.value = filters.maxClassSize
  void loadReport(true)
}

function resetFilters(): void {
  selectedClassLevel.value = ''
  horizon.value = DEFAULT_HORIZON
  maxClassSize.value = DEFAULT_MAX_CLASS_SIZE
  void loadReport(true)
}

onMounted(() => {
  void loadReport()
})
</script>

<template>
  <div class="space-y-6">
    <ReportFilters
      :class-levels="classLevels"
      :selected-class-level="selectedClassLevel"
      :horizon="horizon"
      :max-class-size="maxClassSize"
      :loading="loading"
      @submit="applyFilters"
      @reset="resetFilters"
    />

    <div v-if="loading" class="space-y-4" aria-live="polite" aria-label="Loading report">
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
      v-else-if="errorMessage"
      class="rounded-2xl border border-rose-200 bg-rose-50 p-6 text-rose-800"
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
      class="rounded-2xl border border-slate-200 bg-white p-10 text-center shadow-sm"
    >
      <h3 class="font-semibold text-slate-900">No report data</h3>
      <p class="mt-1 text-sm text-slate-500">
        Import historical enrollment records before opening this dashboard.
      </p>
    </div>

    <template v-else>
      <div
        v-if="report.skipped.length"
        class="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900"
        role="status"
      >
        <p class="font-semibold">Some class levels were skipped</p>
        <ul class="mt-1 list-disc pl-5">
          <li v-for="item in report.skipped" :key="item.class_level">
            {{ item.class_level }}: {{ item.reason }}
          </li>
        </ul>
      </div>

      <ReportSummaryCards :summary="report.summary" />
      <EnrollmentTrendChart :series="report.series" />
      <div class="grid gap-6 lg:grid-cols-2">
        <DemographicBreakdownChart :historical="report.historical" />
        <SectionRecommendationChart :series="report.series" />
      </div>
      <ReportDataTables
        :historical="report.historical"
        :series="report.series"
        :max-class-size="report.max_class_size"
      />
      <p class="text-right text-xs text-slate-400">
        Generated {{ new Date(report.generated_at).toLocaleString() }}
      </p>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

import type { DashboardForecastSeries } from '../../../shared/reports'
import { seriesLabel } from '../../../shared/reports'

const props = defineProps<{
  series: DashboardForecastSeries[]
  selectedKey: string
}>()

const emit = defineEmits<{
  'update:selectedKey': [value: string]
}>()

function seriesKey(item: DashboardForecastSeries): string {
  return `${item.program}||${item.year_level}||${item.location}`
}

const selectedSeries = computed(() => {
  const match = props.series.find((item) => seriesKey(item) === props.selectedKey)
  return match ?? props.series[0] ?? null
})

const nextAcademicYear = computed(
  () => selectedSeries.value?.projections[0]?.academic_year ?? '',
)

const calculationRows = computed(() => {
  const series = selectedSeries.value
  if (!series) return []
  const calc = series.explanation.calculation
  const rows: Array<{ label: string; value: string; emphasize?: boolean }> = []

  if (calc.method === 'arima') {
    if (calc.ar_coefficient !== null) {
      rows.push({
        label: 'AR coefficient (φ)',
        value: formatNumber(calc.ar_coefficient, 9),
      })
    }
    if (calc.trend_coefficient !== null) {
      rows.push({
        label: 'Trend coefficient',
        value: formatNumber(calc.trend_coefficient, 9),
      })
    }
  } else {
    if (calc.slope !== null) {
      rows.push({ label: 'Slope', value: formatNumber(calc.slope, 9) })
    }
    if (calc.intercept !== null) {
      rows.push({ label: 'Intercept', value: formatNumber(calc.intercept, 9) })
    }
  }

  rows.push(
    { label: 'Latest enrollment', value: formatInteger(calc.latest_enrollment) },
    { label: 'Latest change', value: formatSignedInteger(calc.latest_change) },
    { label: 'Predicted change', value: formatNumber(calc.predicted_change, 2) },
    { label: 'Raw forecast', value: formatNumber(calc.raw_forecast, 2) },
    {
      label: 'Final forecast',
      value: formatInteger(calc.final_forecast),
      emphasize: true,
    },
  )

  if (calc.total_abs_error !== null) {
    rows.push({
      label: 'Total absolute error',
      value: formatNumber(calc.total_abs_error, 4),
    })
  }

  return rows
})

function formatInteger(value: number): string {
  return value.toLocaleString()
}

function formatSignedInteger(value: number): string {
  if (value > 0) return `+${value.toLocaleString()}`
  return value.toLocaleString()
}

function formatNumber(value: number, digits: number): string {
  return value.toLocaleString(undefined, {
    minimumFractionDigits: 0,
    maximumFractionDigits: digits,
  })
}

function formatError(value: number | null): string {
  if (value === null) return '—'
  return formatNumber(value, 4)
}
</script>

<template>
  <section
    v-if="selectedSeries"
    class="print-calc-panel overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm"
    aria-labelledby="forecast-calculation-title"
  >
    <div
      class="flex flex-wrap items-start justify-between gap-3 border-b border-slate-200 bg-slate-900 px-5 py-4 text-white"
    >
      <div>
        <h3 id="forecast-calculation-title" class="text-lg font-semibold tracking-wide uppercase">
          Forecast calculation
        </h3>
        <p class="mt-1 text-sm text-slate-300">
          {{ seriesLabel(selectedSeries) }} ·
          {{ selectedSeries.explanation.calculation.model_label }}
          <span v-if="nextAcademicYear"> · SY {{ nextAcademicYear }}</span>
        </p>
      </div>
      <label
        v-if="series.length > 1"
        class="no-print block text-xs font-semibold tracking-wide text-slate-300 uppercase"
      >
        Series
        <select
          class="mt-1 block min-w-56 rounded-lg border border-slate-600 bg-slate-800 px-3 py-2 text-sm font-medium text-white outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-500/40"
          :value="selectedKey"
          @change="
            emit(
              'update:selectedKey',
              ($event.target as HTMLSelectElement).value,
            )
          "
        >
          <option
            v-for="item in series"
            :key="seriesKey(item)"
            :value="seriesKey(item)"
          >
            {{ seriesLabel(item) }}
          </option>
        </select>
      </label>
    </div>

    <div class="grid gap-0 lg:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)]">
      <div class="overflow-x-auto border-b border-slate-200 lg:border-r lg:border-b-0">
        <table class="w-full min-w-[420px] border-collapse text-left text-sm">
          <thead class="bg-slate-100 text-xs tracking-wide text-slate-600 uppercase">
            <tr>
              <th class="px-4 py-3 font-semibold">Academic year</th>
              <th class="px-4 py-3 text-right font-semibold">Actual enrollment</th>
              <th class="px-4 py-3 text-right font-semibold">Yearly change</th>
              <th class="px-4 py-3 text-right font-semibold">Model error</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr
              v-for="row in selectedSeries.explanation.history_rows"
              :key="row.academic_year"
            >
              <td class="px-4 py-2.5 font-medium text-slate-900">
                {{ row.academic_year }}
              </td>
              <td class="px-4 py-2.5 text-right text-slate-700">
                {{ formatInteger(row.actual_enrollment) }}
              </td>
              <td class="px-4 py-2.5 text-right text-slate-700">
                {{ formatSignedInteger(row.yearly_change) }}
              </td>
              <td class="px-4 py-2.5 text-right text-slate-700">
                {{ formatError(row.model_error) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="overflow-x-auto">
        <table class="w-full border-collapse text-left text-sm">
          <thead class="bg-slate-100 text-xs tracking-wide text-slate-600 uppercase">
            <tr>
              <th class="px-4 py-3 font-semibold">Calculation</th>
              <th class="px-4 py-3 text-right font-semibold">Value</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr
              v-for="row in calculationRows"
              :key="row.label"
              :class="row.emphasize ? 'bg-emerald-50' : undefined"
            >
              <td
                class="px-4 py-2.5 font-medium"
                :class="row.emphasize ? 'text-emerald-900' : 'text-slate-800'"
              >
                {{ row.label }}
              </td>
              <td
                class="px-4 py-2.5 text-right font-semibold"
                :class="row.emphasize ? 'text-emerald-800' : 'text-slate-900'"
              >
                {{ row.value }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </section>
</template>

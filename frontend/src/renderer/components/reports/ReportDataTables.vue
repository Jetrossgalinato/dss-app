<script setup lang="ts">
import type {
  DashboardForecastSeries,
  HistoricalBreakdownPoint,
} from '../../../shared/reports'

defineProps<{
  historical: HistoricalBreakdownPoint[]
  series: DashboardForecastSeries[]
  maxClassSize: number
}>()
</script>

<template>
  <div class="grid gap-6 xl:grid-cols-2">
    <section class="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div class="border-b border-slate-200 px-5 py-4">
        <h3 class="font-semibold text-slate-900">Forecast and section details</h3>
        <p class="text-sm text-slate-500">Maximum {{ maxClassSize }} students per section</p>
      </div>
      <div class="max-h-96 overflow-auto">
        <table class="w-full border-collapse text-left text-sm">
          <thead class="sticky top-0 bg-slate-50 text-xs tracking-wide text-slate-500 uppercase">
            <tr>
              <th class="px-4 py-3">Class level</th>
              <th class="px-4 py-3">Year</th>
              <th class="px-4 py-3 text-right">Forecast</th>
              <th class="px-4 py-3 text-right">Sections</th>
              <th class="px-4 py-3 text-right">Class size</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <template v-for="item in series" :key="item.class_level">
              <tr v-for="point in item.projections" :key="`${item.class_level}-${point.academic_year}`">
                <td class="px-4 py-3 font-medium text-slate-900">
                  {{ item.class_level }}
                  <span class="block text-xs font-normal text-slate-400">
                    {{ item.method === 'arima' ? 'ARIMA' : 'Linear trend' }}
                  </span>
                </td>
                <td class="px-4 py-3 text-slate-600">{{ point.academic_year }}</td>
                <td class="px-4 py-3 text-right">{{ point.predicted_enrollment }}</td>
                <td class="px-4 py-3 text-right">{{ point.recommended_sections }}</td>
                <td class="px-4 py-3 text-right">{{ point.planned_class_size }}</td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>
    </section>

    <section class="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div class="border-b border-slate-200 px-5 py-4">
        <h3 class="font-semibold text-slate-900">Historical details</h3>
        <p class="text-sm text-slate-500">Exact enrollment totals by sex</p>
      </div>
      <div class="max-h-96 overflow-auto">
        <table class="w-full border-collapse text-left text-sm">
          <thead class="sticky top-0 bg-slate-50 text-xs tracking-wide text-slate-500 uppercase">
            <tr>
              <th class="px-4 py-3">Year</th>
              <th class="px-4 py-3">Class level</th>
              <th class="px-4 py-3 text-right">Male</th>
              <th class="px-4 py-3 text-right">Female</th>
              <th class="px-4 py-3 text-right">Total</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr
              v-for="point in historical"
              :key="`${point.academic_year}-${point.class_level}`"
            >
              <td class="px-4 py-3 text-slate-600">{{ point.academic_year }}</td>
              <td class="px-4 py-3 font-medium text-slate-900">{{ point.class_level }}</td>
              <td class="px-4 py-3 text-right">{{ point.male }}</td>
              <td class="px-4 py-3 text-right">{{ point.female }}</td>
              <td class="px-4 py-3 text-right font-semibold">{{ point.total }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>

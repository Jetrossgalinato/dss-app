<script setup lang="ts">
import type { ChartOptions } from 'chart.js'
import { computed } from 'vue'
import { Bar } from 'vue-chartjs'

import type { DashboardForecastSeries } from '../../../shared/reports'
import { buildSectionRecommendationData } from '../../utils/report-charts'
import '../../utils/chart-setup'

const props = defineProps<{ series: DashboardForecastSeries[] }>()
const data = computed(() => buildSectionRecommendationData(props.series))
const options: ChartOptions<'bar'> = {
  responsive: true,
  maintainAspectRatio: false,
  interaction: { intersect: false, mode: 'index' },
  plugins: { legend: { position: 'bottom' } },
  scales: {
    x: { grid: { display: false } },
    y: {
      beginAtZero: true,
      position: 'left',
      title: { display: true, text: 'Students' },
    },
    sections: {
      beginAtZero: true,
      position: 'right',
      title: { display: true, text: 'Sections' },
      grid: { drawOnChartArea: false },
      ticks: { precision: 0 },
    },
  },
}
</script>

<template>
  <section class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
    <div class="mb-4">
      <h3 class="font-semibold text-slate-900">Section recommendations</h3>
      <p class="text-sm text-slate-500">Projected students and required sections</p>
    </div>
    <div class="h-80">
      <Bar :data="data" :options="options" aria-label="Section recommendation chart" />
    </div>
  </section>
</template>

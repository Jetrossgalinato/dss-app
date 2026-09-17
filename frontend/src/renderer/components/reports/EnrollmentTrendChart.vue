<script setup lang="ts">
import type { ChartOptions } from 'chart.js'
import { computed } from 'vue'
import { Line } from 'vue-chartjs'

import type { DashboardForecastSeries } from '../../../shared/reports'
import { buildEnrollmentTrendData } from '../../utils/report-charts'
import '../../utils/chart-setup'

const props = defineProps<{ series: DashboardForecastSeries[] }>()
const data = computed(() => buildEnrollmentTrendData(props.series))
const options: ChartOptions<'line'> = {
  responsive: true,
  maintainAspectRatio: false,
  interaction: { intersect: false, mode: 'index' },
  plugins: {
    legend: { position: 'bottom' },
    tooltip: { callbacks: { label: (context) => `${context.dataset.label}: ${context.parsed.y}` } },
  },
  scales: {
    y: { beginAtZero: true, title: { display: true, text: 'Students' } },
    x: { grid: { display: false } },
  },
}
</script>

<template>
  <section class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
    <div class="mb-4">
      <h3 class="font-semibold text-slate-900">Enrollment trend</h3>
      <p class="text-sm text-slate-500">Historical totals and projected enrollment</p>
    </div>
    <div class="h-80">
      <Line :data="data" :options="options" aria-label="Enrollment trend chart" />
    </div>
  </section>
</template>

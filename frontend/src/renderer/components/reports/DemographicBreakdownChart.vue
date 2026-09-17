<script setup lang="ts">
import type { ChartOptions } from 'chart.js'
import { computed } from 'vue'
import { Bar } from 'vue-chartjs'

import type { HistoricalBreakdownPoint } from '../../../shared/reports'
import { buildDemographicData } from '../../utils/report-charts'
import '../../utils/chart-setup'

const props = defineProps<{ historical: HistoricalBreakdownPoint[] }>()
const data = computed(() => buildDemographicData(props.historical))
const options: ChartOptions<'bar'> = {
  responsive: true,
  maintainAspectRatio: false,
  interaction: { intersect: false, mode: 'index' },
  plugins: { legend: { position: 'bottom' } },
  scales: {
    x: { stacked: true, grid: { display: false } },
    y: {
      stacked: true,
      beginAtZero: true,
      title: { display: true, text: 'Students' },
    },
  },
}
</script>

<template>
  <section class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
    <div class="mb-4">
      <h3 class="font-semibold text-slate-900">Demographic breakdown</h3>
      <p class="text-sm text-slate-500">Male and female enrollment by academic year</p>
    </div>
    <div class="h-80">
      <Bar :data="data" :options="options" aria-label="Demographic enrollment chart" />
    </div>
  </section>
</template>

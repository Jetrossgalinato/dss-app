<script setup lang="ts">
import { computed } from 'vue'

import type { DashboardSummary } from '../../../shared/reports'

const props = defineProps<{ summary: DashboardSummary }>()

const changeLabel = computed(() => {
  const change = props.summary.year_over_year_change_percent
  if (change === null) return 'Not enough history'
  return `${change > 0 ? '+' : ''}${change.toFixed(2)}%`
})

const changeClass = computed(() => {
  const change = props.summary.year_over_year_change_percent
  if (change === null || change === 0) return 'text-slate-600'
  return change > 0 ? 'text-emerald-700' : 'text-rose-700'
})
</script>

<template>
  <section class="grid gap-4 sm:grid-cols-2 xl:grid-cols-4" aria-label="Report summary">
    <article class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <p class="text-xs font-semibold tracking-wide text-slate-500 uppercase">
        Latest enrollment
      </p>
      <p class="mt-2 text-3xl font-bold text-slate-900">
        {{ summary.latest_enrollment.toLocaleString() }}
      </p>
      <p class="mt-1 text-sm text-slate-500">{{ summary.latest_academic_year }}</p>
    </article>
    <article class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <p class="text-xs font-semibold tracking-wide text-slate-500 uppercase">
        Year-over-year
      </p>
      <p class="mt-2 text-3xl font-bold" :class="changeClass">{{ changeLabel }}</p>
      <p class="mt-1 text-sm text-slate-500">From the previous academic year</p>
    </article>
    <article class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <p class="text-xs font-semibold tracking-wide text-slate-500 uppercase">
        Next-year forecast
      </p>
      <p class="mt-2 text-3xl font-bold text-blue-700">
        {{ summary.next_year_forecast.toLocaleString() }}
      </p>
      <p class="mt-1 text-sm text-slate-500">{{ summary.next_academic_year }}</p>
    </article>
    <article class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <p class="text-xs font-semibold tracking-wide text-slate-500 uppercase">
        Recommended sections
      </p>
      <p class="mt-2 text-3xl font-bold text-amber-700">
        {{ summary.next_year_recommended_sections.toLocaleString() }}
      </p>
      <p class="mt-1 text-sm text-slate-500">{{ summary.next_academic_year }}</p>
    </article>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { Toaster } from 'vue-sonner'

import EnrollmentDataView from './views/EnrollmentDataView.vue'

const healthLabel = ref('Checking backend…')
const healthOk = ref<boolean | null>(null)

onMounted(async () => {
  const result = await window.api.getBackendHealth()
  if (result.ok) {
    healthOk.value = true
    healthLabel.value = `Backend healthy (${result.status})`
  } else {
    healthOk.value = false
    healthLabel.value = `Backend unreachable — ${result.error}`
  }
})
</script>

<template>
  <div class="min-h-full">
    <Toaster
      position="top-right"
      close-button
      close-button-position="top-right"
      rich-colors
      :duration="5000"
      :offset="{ top: '20px', right: '20px' }"
    />
    <header class="border-b border-slate-200 bg-white/90 px-6 py-4 backdrop-blur">
      <div class="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3">
        <div>
          <p class="text-xs font-semibold tracking-[0.16em] text-blue-700 uppercase">
            Charismatic Tutorial Learning Center
          </p>
          <h1 class="mt-1 text-xl font-semibold text-slate-900">Enrollment Forecasting DSS</h1>
        </div>
        <div
          class="inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-xs font-medium"
          :class="
            healthOk === true
              ? 'bg-emerald-100 text-emerald-800'
              : healthOk === false
                ? 'bg-rose-100 text-rose-800'
                : 'bg-slate-200 text-slate-700'
          "
        >
          <span
            class="h-2 w-2 rounded-full"
            :class="
              healthOk === true
                ? 'bg-emerald-500'
                : healthOk === false
                  ? 'bg-rose-500'
                  : 'bg-slate-500'
            "
          />
          {{ healthLabel }}
        </div>
      </div>
    </header>

    <main class="mx-auto max-w-6xl px-6 py-8">
      <div
        v-if="healthOk === false"
        class="mb-6 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800"
      >
        Start the local FastAPI backend before importing or viewing enrollment data.
      </div>
      <div class="mb-6">
        <h2 class="text-2xl font-semibold tracking-tight text-slate-900">Enrollment data</h2>
        <p class="mt-1 text-sm text-slate-600">
          Upload and manage historical enrollment totals used by forecasting.
        </p>
      </div>
      <EnrollmentDataView />
    </main>
  </div>
</template>

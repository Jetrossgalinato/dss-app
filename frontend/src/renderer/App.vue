<script setup lang="ts">
import { onMounted, ref } from 'vue'

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
  <main class="flex min-h-full items-center justify-center px-6 py-10">
    <section class="w-full max-w-xl text-center">
      <p class="text-sm font-semibold tracking-[0.2em] text-slate-500 uppercase">
        Charismatic Tutorial Learning Center
      </p>
      <h1 class="mt-3 text-4xl font-semibold tracking-tight text-slate-900">
        Enrollment Forecasting DSS
      </h1>
      <p class="mt-3 text-base text-slate-600">
        Offline decision support for preschool enrollment planning.
      </p>

      <div
        class="mt-8 inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium"
        :class="
          healthOk === true
            ? 'bg-emerald-100 text-emerald-800'
            : healthOk === false
              ? 'bg-rose-100 text-rose-800'
              : 'bg-slate-200 text-slate-700'
        "
      >
        <span
          class="h-2.5 w-2.5 rounded-full"
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
    </section>
  </main>
</template>

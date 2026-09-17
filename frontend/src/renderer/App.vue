<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, RouterView, useRoute } from 'vue-router'
import { Toaster } from 'vue-sonner'

const healthOk = ref<boolean | null>(null)
const route = useRoute()
const pageTitle = computed(() => String(route.meta.title ?? 'Enrollment Forecasting DSS'))
const pageDescription = computed(() => String(route.meta.description ?? ''))

onMounted(async () => {
  const result = await window.api.getBackendHealth()
  if (result.ok) {
    healthOk.value = true
  } else {
    healthOk.value = false
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
      <div class="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4">
        <div>
          <p class="text-xs font-semibold tracking-[0.16em] text-blue-700 uppercase">
            Charismatic Tutorial Learning Center
          </p>
          <h1 class="mt-1 text-xl font-semibold text-slate-900">Enrollment Forecasting DSS</h1>
        </div>
        <nav class="flex rounded-lg bg-slate-100 p-1" aria-label="Primary navigation">
          <RouterLink
            to="/"
            class="rounded-md px-3 py-1.5 text-sm font-medium text-slate-600 transition hover:text-slate-900"
            active-class="bg-white text-blue-700 shadow-sm"
            exact-active-class="bg-white text-blue-700 shadow-sm"
          >
            Enrollment
          </RouterLink>
          <RouterLink
            to="/reports"
            class="rounded-md px-3 py-1.5 text-sm font-medium text-slate-600 transition hover:text-slate-900"
            active-class="bg-white text-blue-700 shadow-sm"
          >
            Reports
          </RouterLink>
        </nav>
      </div>
    </header>

    <main class="mx-auto max-w-7xl px-6 py-8">
      <div
        v-if="healthOk === false"
        class="mb-6 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800"
      >
        The local data service is unavailable. Restart the application; if the
        problem continues, check the backend log in the application data folder.
      </div>
      <div class="mb-6">
        <h2 class="text-2xl font-semibold tracking-tight text-slate-900">{{ pageTitle }}</h2>
        <p class="mt-1 text-sm text-slate-600">{{ pageDescription }}</p>
      </div>
      <RouterView />
    </main>
  </div>
</template>

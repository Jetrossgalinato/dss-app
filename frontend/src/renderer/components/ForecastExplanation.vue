<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  title: string
  narrative: string
}>()

const titleId = computed(
  () => `forecast-summary-${props.title.replace(/\s+/g, '-').toLowerCase()}`,
)
</script>

<template>
  <aside
    class="rounded-xl border border-blue-100 bg-blue-50 px-4 py-3 text-sm text-slate-700"
    :aria-labelledby="titleId"
  >
    <div class="flex gap-3">
      <svg
        aria-hidden="true"
        class="mt-0.5 h-5 w-5 shrink-0 text-blue-700"
        viewBox="0 0 24 24"
        fill="none"
      >
        <circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="1.75" />
        <path
          d="M12 11v5M12 8h.01"
          stroke="currentColor"
          stroke-width="1.75"
          stroke-linecap="round"
        />
      </svg>
      <div class="min-w-0">
        <h3 :id="titleId" class="font-semibold text-blue-900">{{ title }}</h3>
        <p class="mt-1.5 text-slate-700">{{ narrative }}</p>
      </div>
    </div>
  </aside>
</template>

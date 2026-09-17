<script setup lang="ts">
import { ref, watch } from 'vue'

const props = defineProps<{
  classLevels: string[]
  selectedClassLevel: string
  horizon: number
  maxClassSize: number
  loading: boolean
}>()

const emit = defineEmits<{
  submit: [filters: { classLevel: string; horizon: number; maxClassSize: number }]
  reset: []
}>()

const classLevel = ref(props.selectedClassLevel)
const horizon = ref(props.horizon)
const maxClassSize = ref(props.maxClassSize)

watch(
  () => [props.selectedClassLevel, props.horizon, props.maxClassSize] as const,
  ([nextLevel, nextHorizon, nextMax]) => {
    classLevel.value = nextLevel
    horizon.value = nextHorizon
    maxClassSize.value = nextMax
  },
)

function submit(): void {
  emit('submit', {
    classLevel: classLevel.value,
    horizon: Number(horizon.value),
    maxClassSize: Number(maxClassSize.value),
  })
}
</script>

<template>
  <form
    class="grid gap-4 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm md:grid-cols-[1fr_10rem_12rem_auto_auto] md:items-end"
    @submit.prevent="submit"
  >
    <label class="grid gap-1.5 text-sm font-medium text-slate-700">
      Class level
      <select
        v-model="classLevel"
        class="rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
        :disabled="loading"
      >
        <option value="">All class levels</option>
        <option v-for="level in classLevels" :key="level" :value="level">{{ level }}</option>
      </select>
    </label>
    <label class="grid gap-1.5 text-sm font-medium text-slate-700">
      Forecast horizon
      <select
        v-model.number="horizon"
        class="rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
        :disabled="loading"
      >
        <option v-for="year in 5" :key="year" :value="year">
          {{ year }} {{ year === 1 ? 'year' : 'years' }}
        </option>
      </select>
    </label>
    <label class="grid gap-1.5 text-sm font-medium text-slate-700">
      Maximum class size
      <input
        v-model.number="maxClassSize"
        type="number"
        min="1"
        max="100"
        required
        class="rounded-lg border border-slate-300 px-3 py-2 text-slate-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
        :disabled="loading"
      />
    </label>
    <button
      type="submit"
      class="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
      :disabled="loading"
    >
      {{ loading ? 'Refreshing…' : 'Refresh report' }}
    </button>
    <button
      type="button"
      class="rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:opacity-60"
      :disabled="loading"
      @click="emit('reset')"
    >
      Reset
    </button>
  </form>
</template>

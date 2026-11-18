<script setup lang="ts">
import { ref, watch } from 'vue'

const props = defineProps<{
  programs: string[]
  yearLevels: string[]
  locations: string[]
  selectedProgram: string
  selectedYearLevel: string
  selectedLocation: string
  horizon: number
  maxClassSize: number
  loading: boolean
}>()

const emit = defineEmits<{
  submit: [
    filters: {
      program: string
      yearLevel: string
      location: string
      horizon: number
      maxClassSize: number
    },
  ]
  reset: []
}>()

const program = ref(props.selectedProgram)
const yearLevel = ref(props.selectedYearLevel)
const location = ref(props.selectedLocation)
const horizon = ref(props.horizon)
const maxClassSize = ref(props.maxClassSize)

watch(
  () =>
    [
      props.selectedProgram,
      props.selectedYearLevel,
      props.selectedLocation,
      props.horizon,
      props.maxClassSize,
    ] as const,
  ([nextProgram, nextYearLevel, nextLocation, nextHorizon, nextMax]) => {
    program.value = nextProgram
    yearLevel.value = nextYearLevel
    location.value = nextLocation
    horizon.value = nextHorizon
    maxClassSize.value = nextMax
  },
)

function submit(): void {
  emit('submit', {
    program: program.value,
    yearLevel: yearLevel.value,
    location: location.value,
    horizon: Number(horizon.value),
    maxClassSize: Number(maxClassSize.value),
  })
}
</script>

<template>
  <form
    class="grid gap-4 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm md:grid-cols-2 xl:grid-cols-6 xl:items-end"
    @submit.prevent="submit"
  >
    <label class="grid gap-1.5 text-sm font-medium text-slate-700">
      Program
      <select
        v-model="program"
        class="rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
        :disabled="loading"
      >
        <option value="">All programs</option>
        <option v-for="item in programs" :key="item" :value="item">{{ item }}</option>
      </select>
    </label>
    <label class="grid gap-1.5 text-sm font-medium text-slate-700">
      Year level
      <select
        v-model="yearLevel"
        class="rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
        :disabled="loading"
      >
        <option value="">All year levels</option>
        <option v-for="item in yearLevels" :key="item" :value="item">{{ item }}</option>
      </select>
    </label>
    <label class="grid gap-1.5 text-sm font-medium text-slate-700">
      Location
      <select
        v-model="location"
        class="rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
        :disabled="loading"
      >
        <option value="">All locations</option>
        <option v-for="item in locations" :key="item" :value="item">{{ item }}</option>
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
    <div class="flex gap-2">
      <button
        type="submit"
        class="flex-1 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
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
    </div>
  </form>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'

const props = defineProps<{
  programs: string[]
  yearLevels: string[]
  locations: string[]
  selectedProgram: string
  selectedYearLevel: string
  selectedLocation: string
  horizon: number
  maxClassSize: number
  defaultHorizon: number
  defaultMaxClassSize: number
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

const filtersAltered = computed(
  () =>
    program.value !== '' ||
    yearLevel.value !== '' ||
    location.value !== '' ||
    Number(horizon.value) !== props.defaultHorizon ||
    Number(maxClassSize.value) !== props.defaultMaxClassSize,
)

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
    <div class="grid gap-1.5">
      <span class="text-sm font-medium text-transparent select-none" aria-hidden="true">
        Actions
      </span>
      <div class="flex gap-2">
        <button
          type="submit"
          class="inline-flex h-10 flex-1 items-center justify-center rounded-lg bg-blue-700 px-4 text-sm font-semibold whitespace-nowrap text-white transition hover:bg-blue-800 focus:ring-2 focus:ring-blue-500 focus:outline-none disabled:cursor-not-allowed disabled:opacity-60"
          :disabled="loading"
        >
          {{ loading ? 'Refreshing…' : 'Refresh' }}
        </button>
        <button
          type="button"
          class="inline-flex h-10 items-center justify-center rounded-lg border border-slate-300 bg-white px-4 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 focus:ring-2 focus:ring-slate-400 focus:outline-none disabled:cursor-not-allowed disabled:opacity-40"
          :disabled="loading || !filtersAltered"
          @click="emit('reset')"
        >
          Clear
        </button>
      </div>
    </div>
  </form>
</template>

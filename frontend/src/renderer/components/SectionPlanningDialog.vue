<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'

import type {
  SectionRecommendation,
  SectionRecommendationResponse,
} from '../../shared/section-planning'

const props = defineProps<{ open: boolean }>()
const emit = defineEmits<{ close: [] }>()

const maxClassSize = ref(25)
const horizon = ref(3)
const loading = ref(false)
const error = ref('')
const result = ref<SectionRecommendationResponse | null>(null)
const maxSizeInput = ref<HTMLInputElement | null>(null)

interface RecommendationRow extends SectionRecommendation {
  classLevel: string
  method: 'arima' | 'linear_trend'
}

const rows = computed<RecommendationRow[]>(() =>
  (result.value?.series ?? []).flatMap((series) =>
    series.recommendations.map((recommendation) => ({
      ...recommendation,
      classLevel: series.class_level,
      method: series.method,
    })),
  ),
)
const totalSections = computed(() =>
  rows.value.reduce((total, row) => total + row.recommended_sections, 0),
)
const totalEnrollment = computed(() =>
  rows.value.reduce((total, row) => total + row.predicted_enrollment, 0),
)

function close(): void {
  if (!loading.value) emit('close')
}

function handleKeydown(event: KeyboardEvent): void {
  if (event.key === 'Escape') close()
}

function clearPlan(): void {
  result.value = null
  error.value = ''
}

async function generate(): Promise<void> {
  error.value = ''
  if (
    !Number.isInteger(maxClassSize.value) ||
    maxClassSize.value < 1 ||
    maxClassSize.value > 100
  ) {
    error.value = 'Maximum class size must be a whole number from 1 to 100.'
    return
  }

  loading.value = true
  const response = await window.api.getSectionRecommendations({
    horizon: horizon.value,
    max_class_size: maxClassSize.value,
    class_levels: null,
  })
  loading.value = false

  if (!response.ok) {
    error.value = response.error.message
    return
  }
  result.value = response.data
}

watch(
  () => props.open,
  async (open) => {
    if (!open) return
    error.value = ''
    await nextTick()
    maxSizeInput.value?.focus()
  },
)
</script>

<template>
  <Teleport to="body">
    <Transition name="planning-dialog">
      <div
        v-if="open"
        class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/55 p-4 backdrop-blur-[2px]"
        role="presentation"
        @click.self="close"
        @keydown="handleKeydown"
      >
        <section
          class="relative flex max-h-[92vh] w-full max-w-5xl flex-col overflow-hidden rounded-2xl border border-slate-200 bg-slate-50 shadow-2xl"
          role="dialog"
          aria-modal="true"
          aria-labelledby="planning-dialog-title"
          aria-describedby="planning-dialog-description"
        >
          <header class="flex items-start justify-between border-b border-slate-200 bg-white px-6 py-5">
            <div class="pr-10">
              <p class="text-xs font-semibold tracking-[0.15em] text-blue-700 uppercase">
                Decision support
              </p>
              <h2 id="planning-dialog-title" class="mt-1 text-xl font-semibold text-slate-900">
                Forecast &amp; section planning
              </h2>
              <p id="planning-dialog-description" class="mt-1 text-sm text-slate-500">
                Generate enrollment forecasts and recommended preschool sections.
              </p>
            </div>
            <button
              class="absolute top-5 right-5 rounded-full p-2 text-slate-400 transition hover:bg-slate-100 hover:text-slate-700 focus:ring-2 focus:ring-blue-500 focus:outline-none disabled:opacity-40"
              type="button"
              aria-label="Close section planning dialog"
              :disabled="loading"
              @click="close"
            >
              <svg aria-hidden="true" class="h-5 w-5" viewBox="0 0 24 24" fill="none">
                <path
                  d="M6 6l12 12M18 6L6 18"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                />
              </svg>
            </button>
          </header>

          <div class="overflow-y-auto p-6">
            <form
              class="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"
              @submit.prevent="generate"
            >
              <div class="grid items-end gap-4 sm:grid-cols-[1fr_1fr_auto]">
                <label class="block">
                  <span class="text-sm font-semibold text-slate-700">Maximum class size</span>
                  <input
                    ref="maxSizeInput"
                    v-model.number="maxClassSize"
                    class="mt-1.5 w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                    type="number"
                    min="1"
                    max="100"
                    step="1"
                  />
                </label>
                <label class="block">
                  <span class="text-sm font-semibold text-slate-700">Forecast horizon</span>
                  <select
                    v-model.number="horizon"
                    class="mt-1.5 w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                  >
                    <option v-for="year in 5" :key="year" :value="year">
                      {{ year }} academic {{ year === 1 ? 'year' : 'years' }}
                    </option>
                  </select>
                </label>
                <div class="flex gap-2">
                  <button
                    v-if="result"
                    class="rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 transition hover:bg-slate-100 focus:ring-2 focus:ring-slate-400 focus:outline-none disabled:opacity-50"
                    type="button"
                    :disabled="loading"
                    @click="clearPlan"
                  >
                    Clear
                  </button>
                  <button
                    class="inline-flex min-w-40 flex-1 items-center justify-center gap-2 rounded-lg bg-blue-700 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-800 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:outline-none disabled:cursor-wait disabled:opacity-60"
                    type="submit"
                    :disabled="loading"
                  >
                    <span
                      v-if="loading"
                      class="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white"
                      aria-hidden="true"
                    />
                    {{ loading ? 'Generating…' : result ? 'Refresh plan' : 'Generate plan' }}
                  </button>
                </div>
              </div>
              <p class="mt-3 text-xs text-slate-500">
                One maximum is applied to every class level. Forecasts are not saved.
              </p>
            </form>

            <div
              v-if="error"
              class="mt-5 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800"
              role="alert"
            >
              {{ error }}
            </div>

            <template v-if="result">
              <div class="mt-5 grid gap-3 sm:grid-cols-3">
                <div class="rounded-xl border border-slate-200 bg-white p-4">
                  <p class="text-xs font-semibold tracking-wide text-slate-500 uppercase">
                    Class levels
                  </p>
                  <p class="mt-1 text-2xl font-semibold text-slate-900">
                    {{ result.series.length }}
                  </p>
                </div>
                <div class="rounded-xl border border-slate-200 bg-white p-4">
                  <p class="text-xs font-semibold tracking-wide text-slate-500 uppercase">
                    Projected learners
                  </p>
                  <p class="mt-1 text-2xl font-semibold text-slate-900">
                    {{ totalEnrollment }}
                  </p>
                </div>
                <div class="rounded-xl border border-blue-200 bg-blue-50 p-4">
                  <p class="text-xs font-semibold tracking-wide text-blue-700 uppercase">
                    Recommended sections
                  </p>
                  <p class="mt-1 text-2xl font-semibold text-blue-900">{{ totalSections }}</p>
                </div>
              </div>

              <div
                v-if="result.skipped.length"
                class="mt-5 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900"
              >
                <p class="font-semibold">Some class levels were skipped</p>
                <ul class="mt-1 list-inside list-disc">
                  <li v-for="item in result.skipped" :key="item.class_level">
                    {{ item.class_level }}: {{ item.reason }}
                  </li>
                </ul>
              </div>

              <div class="mt-5 overflow-hidden rounded-xl border border-slate-200 bg-white">
                <div class="overflow-x-auto">
                  <table class="w-full min-w-[760px] text-left text-sm">
                    <thead class="bg-slate-100 text-xs tracking-wide text-slate-600 uppercase">
                      <tr>
                        <th class="px-4 py-3 font-semibold">Class level</th>
                        <th class="px-4 py-3 font-semibold">Academic year</th>
                        <th class="px-4 py-3 text-right font-semibold">Forecast</th>
                        <th class="px-4 py-3 text-right font-semibold">Maximum</th>
                        <th class="px-4 py-3 text-right font-semibold">Sections</th>
                        <th class="px-4 py-3 text-right font-semibold">Planned size</th>
                        <th class="px-4 py-3 font-semibold">Method</th>
                      </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-100">
                      <tr v-for="row in rows" :key="`${row.classLevel}-${row.academic_year}`">
                        <td class="px-4 py-3 font-medium text-slate-900">{{ row.classLevel }}</td>
                        <td class="px-4 py-3 text-slate-700">{{ row.academic_year }}</td>
                        <td class="px-4 py-3 text-right text-slate-700">
                          {{ row.predicted_enrollment }}
                        </td>
                        <td class="px-4 py-3 text-right text-slate-700">
                          {{ row.max_class_size }}
                        </td>
                        <td class="px-4 py-3 text-right font-semibold text-blue-800">
                          {{ row.recommended_sections }}
                        </td>
                        <td class="px-4 py-3 text-right text-slate-700">
                          {{ row.planned_class_size }}
                        </td>
                        <td class="px-4 py-3">
                          <span
                            class="rounded-full px-2.5 py-1 text-xs font-medium"
                            :class="
                              row.method === 'arima'
                                ? 'bg-violet-100 text-violet-800'
                                : 'bg-slate-100 text-slate-700'
                            "
                          >
                            {{ row.method === 'arima' ? 'ARIMA' : 'Linear trend' }}
                          </span>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </template>

            <div
              v-else-if="!loading && !error"
              class="mt-5 rounded-xl border border-dashed border-slate-300 bg-white px-6 py-10 text-center"
            >
              <p class="font-medium text-slate-700">No plan generated yet</p>
              <p class="mt-1 text-sm text-slate-500">
                Choose the controls above, then generate recommendations.
              </p>
            </div>
          </div>

          <footer class="flex justify-end border-t border-slate-200 bg-white px-6 py-4">
            <button
              class="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-100 focus:ring-2 focus:ring-slate-400 focus:outline-none disabled:opacity-50"
              type="button"
              :disabled="loading"
              @click="close"
            >
              Close
            </button>
          </footer>
        </section>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.planning-dialog-enter-active,
.planning-dialog-leave-active {
  transition: opacity 180ms ease;
}

.planning-dialog-enter-active section,
.planning-dialog-leave-active section {
  transition:
    transform 240ms cubic-bezier(0.22, 1, 0.36, 1),
    opacity 180ms ease;
}

.planning-dialog-enter-from,
.planning-dialog-leave-to {
  opacity: 0;
}

.planning-dialog-enter-from section,
.planning-dialog-leave-to section {
  opacity: 0;
  transform: translateY(14px) scale(0.98);
}

@media (prefers-reduced-motion: reduce) {
  .planning-dialog-enter-active,
  .planning-dialog-leave-active,
  .planning-dialog-enter-active section,
  .planning-dialog-leave-active section {
    transition-duration: 1ms;
  }
}
</style>

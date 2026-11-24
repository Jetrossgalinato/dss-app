<script setup lang="ts">
import { nextTick, ref, watch } from 'vue'

import { ALLOWED_YEAR_LEVELS, type YearLevel } from '../../shared/enrollment'

const props = defineProps<{ open: boolean }>()
const emit = defineEmits<{
  close: []
  saved: [payload: { created: boolean; label: string }]
}>()

const ACADEMIC_YEAR_PATTERN = /^(\d{4})-(\d{4})$/

const academicYear = ref('')
const program = ref('')
const yearLevel = ref<YearLevel | ''>('')
const location = ref('')
const sex = ref<'' | 'Male' | 'Female'>('')
const enrollmentCount = ref<number | null>(null)
const error = ref('')
const saving = ref(false)
const firstInput = ref<HTMLInputElement | null>(null)

function resetForm(): void {
  academicYear.value = ''
  program.value = ''
  yearLevel.value = ''
  location.value = ''
  sex.value = ''
  enrollmentCount.value = null
  error.value = ''
}

function close(): void {
  if (!saving.value) emit('close')
}

function handleKeydown(event: KeyboardEvent): void {
  if (event.key === 'Escape') close()
}

function validate(): string | null {
  const year = academicYear.value.trim()
  const match = ACADEMIC_YEAR_PATTERN.exec(year)
  if (!match || Number(match[2]) !== Number(match[1]) + 1) {
    return 'Academic year must use consecutive years in YYYY-YYYY format.'
  }
  if (!program.value.trim()) {
    return 'Program is required.'
  }
  if (!yearLevel.value) {
    return 'Select a year level.'
  }
  if (!location.value.trim()) {
    return 'Location is required.'
  }
  if (sex.value !== 'Male' && sex.value !== 'Female') {
    return 'Select Male or Female.'
  }
  if (
    enrollmentCount.value === null ||
    !Number.isInteger(enrollmentCount.value) ||
    enrollmentCount.value < 0
  ) {
    return 'Enrollment count must be a whole number of 0 or more.'
  }
  return null
}

async function submit(): Promise<void> {
  error.value = ''
  const validationError = validate()
  if (validationError) {
    error.value = validationError
    return
  }

  saving.value = true
  const result = await window.api.upsertEnrollment({
    academic_year: academicYear.value.trim(),
    program: program.value.trim(),
    year_level: yearLevel.value,
    sex: sex.value as 'Male' | 'Female',
    location: location.value.trim(),
    enrollment_count: enrollmentCount.value as number,
  })
  saving.value = false

  if (!result.ok) {
    const detail = result.error.errors?.[0]?.message
    error.value = detail || result.error.message
    return
  }

  const record = result.data.record
  emit('saved', {
    created: result.data.created,
    label: `${record.academic_year} ${record.program} ${record.year_level} · ${record.location} (${record.sex})`,
  })
  resetForm()
  emit('close')
}

watch(
  () => props.open,
  async (open) => {
    if (!open) return
    resetForm()
    await nextTick()
    firstInput.value?.focus()
  },
)
</script>

<template>
  <Teleport to="body">
    <Transition name="add-enrollment-dialog">
      <div
        v-if="open"
        class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4 backdrop-blur-[2px]"
        role="presentation"
        @click.self="close"
        @keydown="handleKeydown"
      >
        <section
          class="relative w-full max-w-lg overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl"
          role="dialog"
          aria-modal="true"
          aria-labelledby="add-enrollment-title"
        >
          <button
            class="absolute top-4 right-4 rounded-full p-1.5 text-slate-400 transition hover:bg-slate-100 hover:text-slate-700 focus:ring-2 focus:ring-blue-500 focus:outline-none disabled:opacity-40"
            type="button"
            aria-label="Close add record dialog"
            :disabled="saving"
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

          <form @submit.prevent="submit">
            <div class="px-6 pt-6 pb-5">
              <h2 id="add-enrollment-title" class="text-lg font-semibold text-slate-900">
                Add enrollment record
              </h2>
              <p class="mt-1 text-sm text-slate-500">
                Enter one demographic group. Matching records update the enrollment
                count.
              </p>

              <div class="mt-5 grid gap-3 sm:grid-cols-2">
                <label class="block text-sm font-medium text-slate-700">
                  Academic year
                  <input
                    ref="firstInput"
                    v-model="academicYear"
                    class="mt-1.5 w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                    type="text"
                    placeholder="2024-2025"
                    autocomplete="off"
                    :disabled="saving"
                  />
                </label>
                <label class="block text-sm font-medium text-slate-700">
                  Program
                  <input
                    v-model="program"
                    class="mt-1.5 w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm uppercase outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                    type="text"
                    placeholder="BSIT"
                    autocomplete="off"
                    :disabled="saving"
                  />
                </label>
                <label class="block text-sm font-medium text-slate-700">
                  Year level
                  <select
                    v-model="yearLevel"
                    class="mt-1.5 w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                    :disabled="saving"
                  >
                    <option value="">Select year level</option>
                    <option v-for="level in ALLOWED_YEAR_LEVELS" :key="level" :value="level">
                      {{ level }}
                    </option>
                  </select>
                </label>
                <label class="block text-sm font-medium text-slate-700">
                  Sex
                  <select
                    v-model="sex"
                    class="mt-1.5 w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                    :disabled="saving"
                  >
                    <option value="">Select sex</option>
                    <option value="Female">Female</option>
                    <option value="Male">Male</option>
                  </select>
                </label>
                <label class="block text-sm font-medium text-slate-700 sm:col-span-2">
                  Location
                  <input
                    v-model="location"
                    class="mt-1.5 w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                    type="text"
                    placeholder="Cebu City"
                    autocomplete="off"
                    :disabled="saving"
                  />
                </label>
                <label class="block text-sm font-medium text-slate-700 sm:col-span-2">
                  Enrollment count
                  <input
                    v-model.number="enrollmentCount"
                    class="mt-1.5 w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                    type="number"
                    min="0"
                    step="1"
                    placeholder="0"
                    :disabled="saving"
                  />
                </label>
              </div>

              <p
                v-if="error"
                class="mt-4 rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-800"
                role="alert"
              >
                {{ error }}
              </p>
            </div>

            <div class="flex justify-end gap-3 border-t border-slate-200 bg-slate-50 px-6 py-4">
              <button
                class="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-100 focus:ring-2 focus:ring-slate-400 focus:outline-none disabled:opacity-50"
                type="button"
                :disabled="saving"
                @click="close"
              >
                Cancel
              </button>
              <button
                class="inline-flex min-w-32 items-center justify-center gap-2 rounded-lg bg-blue-700 px-4 py-2 text-sm font-semibold text-white transition hover:bg-blue-800 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:outline-none disabled:cursor-wait disabled:opacity-60"
                type="submit"
                :disabled="saving"
              >
                <span
                  v-if="saving"
                  class="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white"
                  aria-hidden="true"
                />
                {{ saving ? 'Saving…' : 'Save record' }}
              </button>
            </div>
          </form>
        </section>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.add-enrollment-dialog-enter-active,
.add-enrollment-dialog-leave-active {
  transition: opacity 180ms ease;
}

.add-enrollment-dialog-enter-active section,
.add-enrollment-dialog-leave-active section {
  transition:
    transform 220ms cubic-bezier(0.22, 1, 0.36, 1),
    opacity 180ms ease;
}

.add-enrollment-dialog-enter-from,
.add-enrollment-dialog-leave-to {
  opacity: 0;
}

.add-enrollment-dialog-enter-from section,
.add-enrollment-dialog-leave-to section {
  opacity: 0;
  transform: translateY(10px) scale(0.97);
}

@media (prefers-reduced-motion: reduce) {
  .add-enrollment-dialog-enter-active,
  .add-enrollment-dialog-leave-active,
  .add-enrollment-dialog-enter-active section,
  .add-enrollment-dialog-leave-active section {
    transition-duration: 1ms;
  }
}
</style>

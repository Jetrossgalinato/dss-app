<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { toast } from 'vue-sonner'

import type {
  EnrollmentFilterOptions,
  EnrollmentFilters,
  EnrollmentList,
  EnrollmentRecord,
} from '../../shared/enrollment'
import { getCached, invalidateAll, setCached } from '../utils/api-cache'
import { prefetchDefaultDashboardReport } from '../utils/report-prefetch'
import ConfirmDeleteDialog from './ConfirmDeleteDialog.vue'

const props = defineProps<{ refreshKey: number }>()

const FILTER_OPTIONS_ENDPOINT = 'enrollments/filter-options'
const LIST_ENDPOINT = 'enrollments/list'

const records = ref<EnrollmentList>({
  items: [],
  total: 0,
  page: 1,
  page_size: 10,
  pages: 0,
})
const filterOptions = ref<EnrollmentFilterOptions>({
  programs: [],
  year_levels: [],
  locations: [],
})
const academicYear = ref('')
const program = ref('')
const yearLevel = ref('')
const location = ref('')
const sex = ref<'' | 'Male' | 'Female'>('')
const loading = ref(false)
const error = ref('')
const deletingId = ref<number | null>(null)
const pendingDelete = ref<EnrollmentRecord | null>(null)
const clearDialogOpen = ref(false)
const clearing = ref(false)

function recordLabel(record: EnrollmentRecord): string {
  return `${record.academic_year} ${record.program} ${record.year_level} · ${record.location} (${record.sex})`
}

function listFilters(page: number): EnrollmentFilters {
  return {
    page,
    pageSize: records.value.page_size,
    academicYear: academicYear.value.trim(),
    program: program.value.trim(),
    yearLevel: yearLevel.value.trim(),
    location: location.value.trim(),
    sex: sex.value,
  }
}

function syncFilterSelections(options: EnrollmentFilterOptions): void {
  filterOptions.value = options
  if (program.value && !options.programs.includes(program.value)) {
    program.value = ''
  }
  if (yearLevel.value && !options.year_levels.includes(yearLevel.value)) {
    yearLevel.value = ''
  }
}

async function loadFilterOptions(): Promise<boolean> {
  const cached = getCached<EnrollmentFilterOptions>(FILTER_OPTIONS_ENDPOINT)
  if (cached) {
    syncFilterSelections(cached)
    return true
  }
  const result = await window.api.getEnrollmentFilterOptions()
  if (!result.ok) return false
  setCached(FILTER_OPTIONS_ENDPOINT, null, result.data)
  syncFilterSelections(result.data)
  return true
}

async function load(page = 1): Promise<void> {
  error.value = ''
  const filters = listFilters(page)
  const cachedList = getCached<EnrollmentList>(LIST_ENDPOINT, filters)
  const cachedFilters = getCached<EnrollmentFilterOptions>(FILTER_OPTIONS_ENDPOINT)

  if (cachedFilters) {
    syncFilterSelections(cachedFilters)
  }
  if (cachedList && cachedFilters) {
    records.value = cachedList
    if (cachedList.total > 0) {
      void prefetchDefaultDashboardReport()
    }
    return
  }

  loading.value = true
  await loadFilterOptions()
  const freshFilters = listFilters(page)
  const listFromCache = getCached<EnrollmentList>(LIST_ENDPOINT, freshFilters)
  if (listFromCache) {
    records.value = listFromCache
    loading.value = false
    if (listFromCache.total > 0) {
      void prefetchDefaultDashboardReport()
    }
    return
  }

  const result = await window.api.listEnrollments(freshFilters)
  loading.value = false
  if (!result.ok) {
    error.value = result.error.message
    return
  }
  setCached(LIST_ENDPOINT, freshFilters, result.data)
  records.value = result.data
  if (result.data.total > 0) {
    void prefetchDefaultDashboardReport()
  }
}

function requestDelete(record: EnrollmentRecord): void {
  pendingDelete.value = record
}

function cancelDelete(): void {
  if (deletingId.value === null) pendingDelete.value = null
}

async function confirmDelete(): Promise<void> {
  const record = pendingDelete.value
  if (!record) return
  const id = record.id
  deletingId.value = id
  const result = await window.api.deleteEnrollment(id)
  deletingId.value = null
  if (!result.ok) {
    pendingDelete.value = null
    error.value = result.error.message
    toast.error('Record could not be deleted', {
      description: result.error.message,
      closeButton: true,
      closeButtonPosition: 'top-right',
      duration: 6000,
      class: 'dss-progress-toast dss-progress-toast--error',
    })
    return
  }
  pendingDelete.value = null
  invalidateAll()
  toast.success('Enrollment record deleted', {
    description: `${recordLabel(record)} was removed.`,
    closeButton: true,
    closeButtonPosition: 'top-right',
    duration: 5000,
    class: 'dss-progress-toast',
  })
  const targetPage =
    records.value.items.length === 1 && records.value.page > 1
      ? records.value.page - 1
      : records.value.page
  await load(targetPage)
  void prefetchDefaultDashboardReport()
}

function requestClearAll(): void {
  if (records.value.total > 0) clearDialogOpen.value = true
}

function cancelClearAll(): void {
  if (!clearing.value) clearDialogOpen.value = false
}

async function confirmClearAll(): Promise<void> {
  clearing.value = true
  const result = await window.api.clearEnrollments()
  clearing.value = false
  clearDialogOpen.value = false

  if (!result.ok) {
    error.value = result.error.message
    toast.error('Records could not be cleared', {
      description: result.error.message,
      closeButton: true,
      closeButtonPosition: 'top-right',
      duration: 6000,
      class: 'dss-progress-toast dss-progress-toast--error',
    })
    return
  }

  invalidateAll()
  toast.success('Historical records cleared', {
    description: `${result.data.deleted_count} enrollment records were permanently removed.`,
    closeButton: true,
    closeButtonPosition: 'top-right',
    duration: 5000,
    class: 'dss-progress-toast',
  })
  await load(1)
}

function clearFilters(): void {
  academicYear.value = ''
  program.value = ''
  yearLevel.value = ''
  location.value = ''
  sex.value = ''
  void load(1)
}

onMounted(() => load())
watch(
  () => props.refreshKey,
  () => load(1),
)
</script>

<template>
  <section class="rounded-2xl border border-slate-200 bg-white shadow-sm">
    <div class="border-b border-slate-200 p-6">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 class="text-lg font-semibold text-slate-900">Historical records</h2>
          <p class="mt-1 text-sm text-slate-500">{{ records.total }} demographic groups</p>
        </div>
        <button
          class="inline-flex items-center gap-2 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm font-semibold text-rose-700 transition hover:bg-rose-100 focus:ring-2 focus:ring-rose-400 focus:outline-none disabled:cursor-not-allowed disabled:opacity-40"
          type="button"
          :disabled="loading || clearing || deletingId !== null || records.total === 0"
          @click="requestClearAll"
        >
          <svg aria-hidden="true" class="h-4 w-4" viewBox="0 0 24 24" fill="none">
            <path
              d="M9 3h6m-9 4h12m-10 0 .7 12h6.6L16 7M10 10v6m4-6v6"
              stroke="currentColor"
              stroke-width="1.8"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </svg>
          Delete Records
        </button>
      </div>

      <form class="mt-4 grid gap-3 md:grid-cols-3 xl:grid-cols-6" @submit.prevent="load(1)">
        <input
          v-model="academicYear"
          class="rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-blue-500"
          placeholder="Academic year"
        />
        <select
          v-model="program"
          class="rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-blue-500"
        >
          <option value="">All programs</option>
          <option v-for="item in filterOptions.programs" :key="item" :value="item">
            {{ item }}
          </option>
        </select>
        <select
          v-model="yearLevel"
          class="rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-blue-500"
        >
          <option value="">All year levels</option>
          <option v-for="item in filterOptions.year_levels" :key="item" :value="item">
            {{ item }}
          </option>
        </select>
        <input
          v-model="location"
          class="rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-blue-500"
          placeholder="Location"
        />
        <select
          v-model="sex"
          class="rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-blue-500"
        >
          <option value="">All sexes</option>
          <option value="Female">Female</option>
          <option value="Male">Male</option>
        </select>
        <div class="flex gap-2">
          <button
            class="flex-1 rounded-lg bg-slate-800 px-3 py-2 text-sm font-semibold text-white hover:bg-slate-900"
            type="submit"
          >
            Filter
          </button>
          <button
            class="rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium hover:bg-slate-50"
            type="button"
            @click="clearFilters"
          >
            Clear
          </button>
        </div>
      </form>
    </div>

    <div v-if="error" class="m-6 rounded-lg bg-rose-50 px-4 py-3 text-sm text-rose-800">
      {{ error }}
    </div>

    <div class="overflow-x-auto">
      <table class="w-full text-left text-sm">
        <thead class="bg-slate-50 text-xs tracking-wide text-slate-500 uppercase">
          <tr>
            <th class="px-6 py-3 font-semibold">Academic year</th>
            <th class="px-6 py-3 font-semibold">Program</th>
            <th class="px-6 py-3 font-semibold">Year level</th>
            <th class="px-6 py-3 font-semibold">Location</th>
            <th class="px-6 py-3 font-semibold">Sex</th>
            <th class="px-6 py-3 text-right font-semibold">Enrollment</th>
            <th class="px-6 py-3 text-right font-semibold">Action</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100">
          <tr v-if="loading">
            <td class="px-6 py-8 text-center text-slate-500" colspan="7">Loading records…</td>
          </tr>
          <tr v-else-if="!records.items.length">
            <td class="px-6 py-8 text-center text-slate-500" colspan="7">
              No enrollment records found.
            </td>
          </tr>
          <tr v-for="record in records.items" v-else :key="record.id" class="hover:bg-slate-50">
            <td class="px-6 py-4 font-medium text-slate-900">{{ record.academic_year }}</td>
            <td class="px-6 py-4 text-slate-700">{{ record.program }}</td>
            <td class="px-6 py-4 text-slate-700">{{ record.year_level }}</td>
            <td class="px-6 py-4 text-slate-700">{{ record.location }}</td>
            <td class="px-6 py-4 text-slate-700">{{ record.sex }}</td>
            <td class="px-6 py-4 text-right font-semibold text-slate-900">
              {{ record.enrollment_count }}
            </td>
            <td class="px-6 py-4 text-right">
              <button
                class="inline-flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-sm font-medium text-rose-700 transition hover:bg-rose-50 hover:text-rose-900 focus:ring-2 focus:ring-rose-400 focus:outline-none disabled:cursor-not-allowed disabled:opacity-50"
                type="button"
                :disabled="clearing || deletingId === record.id"
                @click="requestDelete(record)"
              >
                <svg
                  v-if="deletingId === record.id"
                  aria-hidden="true"
                  class="h-4 w-4 animate-spin"
                  viewBox="0 0 24 24"
                  fill="none"
                >
                  <circle
                    class="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    stroke-width="3"
                  />
                  <path
                    class="opacity-90"
                    d="M4 12a8 8 0 0 1 8-8"
                    stroke="currentColor"
                    stroke-width="3"
                    stroke-linecap="round"
                  />
                </svg>
                <svg
                  v-else
                  aria-hidden="true"
                  class="h-4 w-4"
                  viewBox="0 0 24 24"
                  fill="none"
                >
                  <path
                    d="M9 3h6m-9 4h12m-10 0 .7 12h6.6L16 7M10 10v6m4-6v6"
                    stroke="currentColor"
                    stroke-width="1.8"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  />
                </svg>
                {{ deletingId === record.id ? 'Deleting…' : 'Delete' }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="flex items-center justify-between border-t border-slate-200 px-6 py-4 text-sm">
      <span class="text-slate-500">
        Page {{ records.pages ? records.page : 0 }} of {{ records.pages }}
      </span>
      <div class="flex gap-2">
        <button
          class="rounded-lg border border-slate-300 px-3 py-1.5 font-medium disabled:opacity-40"
          type="button"
          :disabled="loading || records.page <= 1"
          @click="load(records.page - 1)"
        >
          Previous
        </button>
        <button
          class="rounded-lg border border-slate-300 px-3 py-1.5 font-medium disabled:opacity-40"
          type="button"
          :disabled="loading || records.page >= records.pages"
          @click="load(records.page + 1)"
        >
          Next
        </button>
      </div>
    </div>
  </section>

  <ConfirmDeleteDialog
    :open="pendingDelete !== null"
    :loading="deletingId !== null"
    :record-label="pendingDelete ? recordLabel(pendingDelete) : ''"
    :record-details="
      pendingDelete
        ? `${pendingDelete.enrollment_count} enrolled · ${pendingDelete.sex}`
        : ''
    "
    @cancel="cancelDelete"
    @confirm="confirmDelete"
  />

  <ConfirmDeleteDialog
    :open="clearDialogOpen"
    :loading="clearing"
    title="Delete all historical records?"
    confirm-label="Delete all records"
    loading-label="Clearing…"
    :record-label="`all ${records.total} historical enrollment records`"
    record-details="Forecasting and section planning will have no source data until another CSV is imported."
    @cancel="cancelClearAll"
    @confirm="confirmClearAll"
  />
</template>

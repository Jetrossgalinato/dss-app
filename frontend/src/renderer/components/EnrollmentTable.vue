<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'

import type { EnrollmentList } from '../../shared/enrollment'

const props = defineProps<{ refreshKey: number }>()

const records = ref<EnrollmentList>({
  items: [],
  total: 0,
  page: 1,
  page_size: 20,
  pages: 0,
})
const academicYear = ref('')
const classLevel = ref('')
const sex = ref<'' | 'Male' | 'Female'>('')
const loading = ref(false)
const error = ref('')
const deletingId = ref<number | null>(null)

async function load(page = 1): Promise<void> {
  loading.value = true
  error.value = ''
  const result = await window.api.listEnrollments({
    page,
    pageSize: records.value.page_size,
    academicYear: academicYear.value.trim(),
    classLevel: classLevel.value.trim(),
    sex: sex.value,
  })
  loading.value = false
  if (!result.ok) {
    error.value = result.error.message
    return
  }
  records.value = result.data
}

async function remove(id: number): Promise<void> {
  if (!window.confirm('Delete this enrollment record?')) return
  deletingId.value = id
  const result = await window.api.deleteEnrollment(id)
  deletingId.value = null
  if (!result.ok) {
    error.value = result.error.message
    return
  }
  const targetPage =
    records.value.items.length === 1 && records.value.page > 1
      ? records.value.page - 1
      : records.value.page
  await load(targetPage)
}

function clearFilters(): void {
  academicYear.value = ''
  classLevel.value = ''
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
      </div>

      <form class="mt-4 grid gap-3 md:grid-cols-4" @submit.prevent="load(1)">
        <input
          v-model="academicYear"
          class="rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-blue-500"
          placeholder="Academic year"
        />
        <input
          v-model="classLevel"
          class="rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-blue-500"
          placeholder="Class level"
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
            <th class="px-6 py-3 font-semibold">Class level</th>
            <th class="px-6 py-3 font-semibold">Sex</th>
            <th class="px-6 py-3 text-right font-semibold">Enrollment</th>
            <th class="px-6 py-3 text-right font-semibold">Action</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100">
          <tr v-if="loading">
            <td class="px-6 py-8 text-center text-slate-500" colspan="5">Loading records…</td>
          </tr>
          <tr v-else-if="!records.items.length">
            <td class="px-6 py-8 text-center text-slate-500" colspan="5">
              No enrollment records found.
            </td>
          </tr>
          <tr v-for="record in records.items" v-else :key="record.id" class="hover:bg-slate-50">
            <td class="px-6 py-4 font-medium text-slate-900">{{ record.academic_year }}</td>
            <td class="px-6 py-4 text-slate-700">{{ record.class_level }}</td>
            <td class="px-6 py-4 text-slate-700">{{ record.sex }}</td>
            <td class="px-6 py-4 text-right font-semibold text-slate-900">
              {{ record.enrollment_count }}
            </td>
            <td class="px-6 py-4 text-right">
              <button
                class="font-medium text-rose-700 hover:text-rose-900 disabled:opacity-50"
                type="button"
                :disabled="deletingId === record.id"
                @click="remove(record.id)"
              >
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
</template>

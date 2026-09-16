<script setup lang="ts">
import { ref } from 'vue'
import { toast } from 'vue-sonner'

import type { ImportRowError, ImportSummary } from '../../shared/enrollment'

const emit = defineEmits<{ imported: [] }>()

const file = ref<File | null>(null)
const dragging = ref(false)
const importing = ref(false)
const summary = ref<ImportSummary | null>(null)
const errors = ref<ImportRowError[]>([])
const message = ref('')

function chooseFile(event: Event): void {
  const input = event.target as HTMLInputElement
  setFile(input.files?.[0] ?? null)
}

function setFile(nextFile: File | null): void {
  summary.value = null
  errors.value = []
  message.value = ''
  if (nextFile && !nextFile.name.toLowerCase().endsWith('.csv')) {
    file.value = null
    message.value = 'Please select a .csv file.'
    return
  }
  file.value = nextFile
}

function dropFile(event: DragEvent): void {
  dragging.value = false
  setFile(event.dataTransfer?.files[0] ?? null)
}

async function upload(): Promise<void> {
  if (!file.value || importing.value) return
  importing.value = true
  summary.value = null
  errors.value = []
  message.value = ''

  const selected = file.value
  const result = await window.api.importEnrollments(
    selected.name,
    new Uint8Array(await selected.arrayBuffer()),
  )
  importing.value = false

  if (!result.ok) {
    message.value = result.error.message
    errors.value = result.error.errors
    return
  }
  summary.value = result.data
  message.value = 'Import completed successfully.'
  emit('imported')
}

async function downloadTemplate(): Promise<void> {
  const result = await window.api.getEnrollmentTemplate()
  if (!result.ok) {
    toast.error('Template download failed', {
      description: result.error.message,
      closeButton: true,
      closeButtonPosition: 'top-right',
      duration: 6000,
      class: 'download-template-toast download-template-toast--error',
    })
    return
  }
  const url = URL.createObjectURL(new Blob([result.data], { type: 'text/csv' }))
  const link = document.createElement('a')
  link.href = url
  link.download = 'enrollment-template.csv'
  link.click()
  URL.revokeObjectURL(url)
  toast.success('CSV template downloaded', {
    description: 'enrollment-template.csv is ready to use.',
    closeButton: true,
    closeButtonPosition: 'top-right',
    duration: 5000,
    class: 'download-template-toast',
  })
}
</script>

<template>
  <section class="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div>
        <h2 class="text-lg font-semibold text-slate-900">Import enrollment data</h2>
        <p class="mt-1 text-sm text-slate-500">
          Required columns: academic_year, class_level, sex, enrollment_count.
        </p>
      </div>
      <button
        class="text-sm font-semibold text-blue-700 hover:text-blue-900"
        type="button"
        @click="downloadTemplate"
      >
        Download CSV template
      </button>
    </div>

    <label
      class="mt-5 flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed px-6 py-8 text-center transition"
      :class="dragging ? 'border-blue-500 bg-blue-50' : 'border-slate-300 hover:border-blue-400'"
      @dragenter.prevent="dragging = true"
      @dragover.prevent
      @dragleave.prevent="dragging = false"
      @drop.prevent="dropFile"
    >
      <input class="sr-only" type="file" accept=".csv,text/csv" @change="chooseFile" />
      <span class="font-medium text-slate-800">
        {{ file?.name ?? 'Drop a CSV here or click to browse' }}
      </span>
      <span class="mt-1 text-xs text-slate-500">UTF-8 CSV, maximum 5 MB</span>
    </label>

    <div class="mt-4 flex items-center justify-between gap-4">
      <p class="text-xs text-slate-500">Existing year, level, and sex groups are updated.</p>
      <button
        class="rounded-lg bg-blue-700 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-800 disabled:cursor-not-allowed disabled:opacity-50"
        type="button"
        :disabled="!file || importing"
        @click="upload"
      >
        {{ importing ? 'Importing…' : 'Import CSV' }}
      </button>
    </div>

    <div
      v-if="message"
      class="mt-4 rounded-lg px-4 py-3 text-sm"
      :class="summary ? 'bg-emerald-50 text-emerald-800' : 'bg-rose-50 text-rose-800'"
      role="status"
    >
      <p class="font-medium">{{ message }}</p>
      <p v-if="summary" class="mt-1">
        {{ summary.inserted }} inserted, {{ summary.updated }} updated,
        {{ summary.total }} processed.
      </p>
    </div>

    <ul v-if="errors.length" class="mt-3 max-h-44 space-y-1 overflow-auto text-sm text-rose-700">
      <li v-for="(error, index) in errors" :key="index">
        <span v-if="error.row">Row {{ error.row }}: </span>
        <span v-if="error.field">{{ error.field }} — </span>{{ error.message }}
      </li>
    </ul>
  </section>
</template>

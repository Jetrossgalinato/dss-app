<script setup lang="ts">
import { ref } from 'vue'

import EnrollmentTable from '../components/EnrollmentTable.vue'
import EnrollmentUpload from '../components/EnrollmentUpload.vue'
import SectionPlanningDialog from '../components/SectionPlanningDialog.vue'

const refreshKey = ref(0)
const planningOpen = ref(false)

function refreshRecords(): void {
  refreshKey.value += 1
}
</script>

<template>
  <div class="space-y-6">
    <div class="flex justify-end">
      <button
        class="inline-flex items-center gap-2 rounded-lg bg-blue-700 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-800 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:outline-none"
        type="button"
        @click="planningOpen = true"
      >
        <svg aria-hidden="true" class="h-4 w-4" viewBox="0 0 24 24" fill="none">
          <path
            d="M4 19V9m6 10V5m6 14v-7m4 7H2"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
        </svg>
        Forecast &amp; Sections
      </button>
    </div>
    <EnrollmentUpload @imported="refreshRecords" />
    <EnrollmentTable :refresh-key="refreshKey" />
    <SectionPlanningDialog :open="planningOpen" @close="planningOpen = false" />
  </div>
</template>

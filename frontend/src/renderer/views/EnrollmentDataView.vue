<script setup lang="ts">
import { ref } from 'vue'

import EnrollmentTable from '../components/EnrollmentTable.vue'
import EnrollmentUpload from '../components/EnrollmentUpload.vue'

const refreshKey = ref(0)

function refreshRecords(): void {
  refreshKey.value += 1
}
</script>

<template>
  <div class="space-y-6">
    <EnrollmentUpload @imported="refreshRecords" />
    <EnrollmentTable :refresh-key="refreshKey" />
  </div>
</template>

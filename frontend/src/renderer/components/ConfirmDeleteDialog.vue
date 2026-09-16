<script setup lang="ts">
import { nextTick, ref, watch } from 'vue'

const props = defineProps<{
  open: boolean
  loading?: boolean
  recordLabel: string
  recordDetails: string
}>()

const emit = defineEmits<{
  cancel: []
  confirm: []
}>()

const confirmButton = ref<HTMLButtonElement | null>(null)

function cancel(): void {
  if (!props.loading) emit('cancel')
}

function handleKeydown(event: KeyboardEvent): void {
  if (event.key === 'Escape') cancel()
}

watch(
  () => props.open,
  async (open) => {
    if (!open) return
    await nextTick()
    confirmButton.value?.focus()
  },
)
</script>

<template>
  <Teleport to="body">
    <Transition name="delete-dialog">
      <div
        v-if="open"
        class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4 backdrop-blur-[2px]"
        role="presentation"
        @click.self="cancel"
        @keydown="handleKeydown"
      >
        <section
          class="relative w-full max-w-md overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl"
          role="alertdialog"
          aria-modal="true"
          aria-labelledby="delete-dialog-title"
          aria-describedby="delete-dialog-description"
        >
          <button
            class="absolute top-4 right-4 rounded-full p-1.5 text-slate-400 transition hover:bg-slate-100 hover:text-slate-700 focus:ring-2 focus:ring-blue-500 focus:outline-none disabled:opacity-40"
            type="button"
            aria-label="Close confirmation dialog"
            :disabled="loading"
            @click="cancel"
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

          <div class="px-6 pt-6 pb-5">
            <div
              class="flex h-11 w-11 items-center justify-center rounded-full bg-rose-100 text-rose-700"
            >
              <svg aria-hidden="true" class="h-5 w-5" viewBox="0 0 24 24" fill="none">
                <path
                  d="M9 3h6m-9 4h12m-10 0 .7 12h6.6L16 7M10 10v6m4-6v6"
                  stroke="currentColor"
                  stroke-width="1.8"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
              </svg>
            </div>

            <h2 id="delete-dialog-title" class="mt-4 text-lg font-semibold text-slate-900">
              Delete enrollment record?
            </h2>
            <p id="delete-dialog-description" class="mt-2 text-sm leading-6 text-slate-600">
              This permanently removes
              <strong class="font-semibold text-slate-900">{{ recordLabel }}</strong>.
              This action cannot be undone.
            </p>

            <div class="mt-4 rounded-xl bg-slate-50 px-4 py-3">
              <p class="text-xs font-semibold tracking-wide text-slate-500 uppercase">Record</p>
              <p class="mt-1 text-sm font-medium text-slate-800">{{ recordDetails }}</p>
            </div>
          </div>

          <div class="flex justify-end gap-3 border-t border-slate-200 bg-slate-50 px-6 py-4">
            <button
              class="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-100 focus:ring-2 focus:ring-slate-400 focus:outline-none disabled:opacity-50"
              type="button"
              :disabled="loading"
              @click="cancel"
            >
              Keep record
            </button>
            <button
              ref="confirmButton"
              class="inline-flex min-w-32 items-center justify-center gap-2 rounded-lg bg-rose-700 px-4 py-2 text-sm font-semibold text-white transition hover:bg-rose-800 focus:ring-2 focus:ring-rose-500 focus:ring-offset-2 focus:outline-none disabled:cursor-wait disabled:opacity-60"
              type="button"
              :disabled="loading"
              @click="emit('confirm')"
            >
              <span
                v-if="loading"
                class="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white"
                aria-hidden="true"
              />
              {{ loading ? 'Deleting…' : 'Delete record' }}
            </button>
          </div>
        </section>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.delete-dialog-enter-active,
.delete-dialog-leave-active {
  transition: opacity 180ms ease;
}

.delete-dialog-enter-active section,
.delete-dialog-leave-active section {
  transition:
    transform 220ms cubic-bezier(0.22, 1, 0.36, 1),
    opacity 180ms ease;
}

.delete-dialog-enter-from,
.delete-dialog-leave-to {
  opacity: 0;
}

.delete-dialog-enter-from section,
.delete-dialog-leave-to section {
  opacity: 0;
  transform: translateY(10px) scale(0.97);
}

@media (prefers-reduced-motion: reduce) {
  .delete-dialog-enter-active,
  .delete-dialog-leave-active,
  .delete-dialog-enter-active section,
  .delete-dialog-leave-active section {
    transition-duration: 1ms;
  }
}
</style>

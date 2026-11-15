<script setup lang="ts">
import { computed, ref } from 'vue'
import { getApi } from '@/api/client'
import { ApiError } from '@/api/errors'
import ErrorNotice from '@/components/ErrorNotice.vue'
import { ACCEPT_ATTR, checkFile } from '@/lib/files'
import { formatBytes } from '@/lib/format'
import { useCase } from '@/state/caseStore'

// Выбор квитанции ParkNYC (kind: evidence) среди загруженных + загрузка новой с прогрессом. До 4 файлов.
const props = defineProps<{ modelValue: string | null; inputId: string; invalid?: boolean }>()
const emit = defineEmits<{ 'update:modelValue': [v: string | null] }>()

const store = useCase()
const MAX = 4
const evidence = computed(() => store.current.value.documents.filter((d) => d.kind === 'evidence'))
const progress = ref<number | null>(null)
const fileError = ref('')
const error = ref<unknown>(null)
const busy = computed(() => progress.value !== null)

async function onPick(e: Event) {
  const input = e.target as HTMLInputElement
  const f = input.files?.[0]
  input.value = ''
  fileError.value = ''; error.value = null
  if (!f) return
  fileError.value = checkFile(f)
  if (fileError.value) return
  progress.value = 0
  try {
    const doc = await (await getApi()).uploadDocument(store.caseId, 'evidence', f, (p) => { progress.value = p })
    await store.refresh()
    emit('update:modelValue', doc.document_id)
  } catch (err) {
    error.value = err instanceof ApiError ? err : new ApiError('unknown', 'The upload failed. Try again.', 0)
  } finally { progress.value = null }
}
</script>

<template>
  <div class="evidence">
    <p v-if="!evidence.length" class="muted small">No receipt uploaded yet. Synthetic documents only (PDF, JPG or PNG, up to 8 MB).</p>
    <div v-else role="radiogroup" :aria-labelledby="`${inputId}-label`" class="ev-list">
      <label v-for="d in evidence" :key="d.document_id" class="ev-item" :class="{ on: modelValue === d.document_id }">
        <input type="radio" :name="inputId" :value="d.document_id" :checked="modelValue === d.document_id" :disabled="busy"
          @change="emit('update:modelValue', d.document_id)" />
        <span><strong>{{ d.filename }}</strong> <span class="muted small">· {{ formatBytes(d.size_bytes) }}</span>
          <span v-if="modelValue === d.document_id" class="badge ok">Selected</span></span>
      </label>
    </div>

    <div v-if="evidence.length < MAX" class="row" style="margin-top:8px">
      <label class="btn secondary sm" :class="{ disabled: busy }" :for="inputId">{{ evidence.length ? 'Add another file' : 'Upload receipt' }}</label>
      <input :id="inputId" class="visually-hidden" type="file" :accept="ACCEPT_ATTR" :disabled="busy" :aria-invalid="invalid" @change="onPick" />
    </div>
    <p v-else class="muted small">Maximum of {{ MAX }} receipt files reached.</p>

    <div v-if="busy" class="progress-wrap" role="status">
      <progress max="100" :value="progress ?? 0" aria-label="Upload progress"></progress>
      <span class="small">Uploading… {{ progress }}%</span>
    </div>
    <p v-if="fileError" class="err small" role="alert">{{ fileError }}</p>
    <ErrorNotice :error="error" />
  </div>
</template>

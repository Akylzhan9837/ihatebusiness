<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getApi } from '@/api/client'
import { ApiError } from '@/api/errors'
import ErrorNotice from '@/components/ErrorNotice.vue'
import { ACCEPT_ATTR, checkFile } from '@/lib/files'
import { STATES } from '@/lib/jurisdictions'
import { formatBytes } from '@/lib/format'

const router = useRouter()
const route = useRoute()
const mode = ref<'upload' | 'manual'>(route.query.mode === 'manual' ? 'manual' : 'upload')
watch(() => route.query.mode, (value) => { mode.value = value === 'manual' ? 'manual' : 'upload' })
const acknowledged = ref(false)
const state = ref("")
const file = ref<File | null>(null)
const fileError = ref('')
const dragging = ref(false)
const stage = ref<'idle' | 'creating' | 'uploading' | 'reading'>('idle')
const progress = ref(0)
const error = ref<unknown>(null)
// Дело и загруженный файл переживают повторные попытки: не создаём второе дело и не грузим файл дважды.
const caseId = ref('')
const uploaded = ref(false)

const busy = computed(() => stage.value !== 'idle')
const canRead = computed(() => acknowledged.value && !!state.value && !!file.value && !busy.value)
const stageText = computed(() => ({
  idle: '', creating: 'Creating your private case…', uploading: `Uploading… ${progress.value}%`,
  reading: 'Reading the ticket. This can take up to a minute.',
}[stage.value]))

function setFile(f: File | null) {
  fileError.value = ''
  if (!f) return
  fileError.value = checkFile(f)
  file.value = fileError.value ? null : f
}
const onPick = (e: Event) => { setFile((e.target as HTMLInputElement).files?.[0] ?? null); (e.target as HTMLInputElement).value = '' }
function onDrop(e: DragEvent) {
  dragging.value = false
  if (acknowledged.value && !busy.value && !uploaded.value) setFile(e.dataTransfer?.files?.[0] ?? null)
}

const goDetails = () => router.push({ name: 'details', params: { id: caseId.value } })

async function ensureCase() {
  if (!caseId.value) { stage.value = 'creating'; caseId.value = (await (await getApi()).createCase(state.value)).case_id }
}

async function readTicket() {
  if (!canRead.value || !file.value) return
  error.value = null
  try {
    const api = await getApi()
    await ensureCase()
    if (!uploaded.value) {
      stage.value = 'uploading'; progress.value = 0
      try {
        await api.uploadDocument(caseId.value, 'ticket', file.value, (p) => { progress.value = p })
      } catch (e) {
        // Файл уже был принят в прошлой попытке — идём дальше к чтению.
        if (!(e instanceof ApiError && e.code === 'document_limit')) throw e
      }
      uploaded.value = true
    }
    stage.value = 'reading'
    await api.extract(caseId.value)
    await goDetails()
  } catch (e) { error.value = e } finally { stage.value = 'idle' }
}

async function manual() {
  if (!acknowledged.value || !state.value || busy.value) return
  error.value = null
  try { await ensureCase(); await goDetails() } catch (e) { error.value = e } finally { stage.value = 'idle' }
}

// Если дело создано, а чтение не удалось, пользователь может продолжить вручную.
const canContinueManually = computed(() => !!caseId.value && !!error.value && !busy.value)
onBeforeUnmount(() => { error.value = null })
</script>

<template>
  <section>
    <h1>Start a ticket review</h1>
    <p class="muted">Choose the state where the notice was issued, then upload the ticket or enter its details.</p>

    <div class="field">
      <label for="intake-state">Where was the ticket issued?</label>
      <select id="intake-state" v-model="state" :disabled="busy || !!caseId">
        <option value="" disabled>Select a U.S. state or DC</option>
        <option v-for="[code, name] in STATES" :key="code" :value="code">{{ name }}</option>
      </select>
    </div>

    <div class="notice warn synth" role="note">
      <strong>Synthetic documents only.</strong>
      This is a demo. Upload only made-up tickets and receipts. Do not upload real tickets, IDs or personal documents.
      <label class="opt check ack">
        <input v-model="acknowledged" type="checkbox" :disabled="busy" />
        <span>I understand. I will use synthetic documents only.</span>
      </label>
    </div>

    <ErrorNotice :error="error" retry-label="Try again" @retry="readTicket" />
    <div v-if="canContinueManually" class="notice warn">
      Reading did not finish. Your case is saved, so you can enter the ticket details yourself.
      <button class="btn sm secondary" type="button" style="margin-left:8px" @click="goDetails">Enter details manually</button>
    </div>

    <div class="tabs" role="group" aria-label="How to add the ticket">
      <button class="tab" type="button" :aria-pressed="mode === 'upload'" :disabled="busy" @click="mode = 'upload'">Upload a file</button>
      <button class="tab" type="button" :aria-pressed="mode === 'manual'" :disabled="busy" @click="mode = 'manual'">Enter manually</button>
    </div>

    <div v-show="mode === 'upload'" class="card">
      <h2>Upload a ticket</h2>
      <div class="drop" :class="{ over: dragging, off: !acknowledged }" @dragover.prevent="dragging = acknowledged"
        @dragleave="dragging = false" @drop.prevent="onDrop">
        <p v-if="!file" class="muted">Drop a PDF, JPG or PNG here (up to 8 MB), or choose a file.</p>
        <p v-else><strong>{{ file.name }}</strong> <span class="muted small">({{ formatBytes(file.size) }})</span></p>
        <label class="btn secondary" :class="{ disabled: !acknowledged || !state || busy || uploaded }" for="ticket-file">{{ file ? 'Replace file' : 'Choose file' }}</label>
        <input id="ticket-file" class="visually-hidden" type="file" :accept="ACCEPT_ATTR" :disabled="!acknowledged || !state || busy || uploaded" @change="onPick" />
        <button v-if="file && !uploaded" class="btn danger" type="button" :disabled="busy" style="margin-left:8px" @click="file = null">Remove</button>
        <p v-if="!acknowledged" class="muted small" style="margin:12px 0 0">Confirm the notice above to enable uploads.</p>
        <p v-if="fileError" class="notice err" role="alert" style="margin:12px 0 0">{{ fileError }}</p>
      </div>

      <div v-if="stage === 'uploading'" class="progress-wrap" role="status">
        <progress max="100" :value="progress" aria-label="Upload progress"></progress>
        <span class="small">{{ stageText }}</span>
      </div>
      <p v-else-if="busy" class="row" role="status"><span class="spinner" aria-hidden="true"></span>{{ stageText }}</p>

      <div class="row" style="margin-top:16px">
        <button class="btn" type="button" :disabled="!canRead" @click="readTicket">Read my ticket</button>
      </div>
      <p class="muted small" style="margin:12px 0 0">Only the ticket is sent for automatic reading. You will confirm every detail before anything is used.</p>
    </div>

    <div v-show="mode === 'manual'" class="card">
      <h2>Enter the details yourself</h2>
      <p class="muted small">No upload needed. You will type the ticket details on the next screen.</p>
      <button class="btn secondary" type="button" :disabled="!acknowledged || !state || busy" @click="manual">Continue to manual entry</button>
    </div>
  </section>
</template>

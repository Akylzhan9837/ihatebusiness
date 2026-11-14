<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getApi } from '@/api/client'
import type { AppConfig } from '@/api/types'
import ErrorNotice from '@/components/ErrorNotice.vue'
import { formatBytes } from '@/lib/format'

const router = useRouter()
const config = ref<AppConfig | null>(null)
const file = ref<File | null>(null)
const fileError = ref('')
const busy = ref(false)
const stage = ref('')
const error = ref<unknown>(null)

const ACCEPT = ['application/pdf', 'image/jpeg', 'image/png']
const allowed = computed(() => config.value?.allowed_types ?? ACCEPT)
const limitText = computed(() =>
  config.value?.max_file_bytes ? `Max file size: ${formatBytes(config.value.max_file_bytes)}.` : '')

onMounted(async () => {
  try { config.value = await (await getApi()).getConfig() } catch { /* ограничения просто не показываем */ }
})

function pick(e: Event) {
  fileError.value = ''
  const f = (e.target as HTMLInputElement).files?.[0] ?? null
  if (!f) return
  // Клиентская проверка — только удобство; сервер проверяет заново.
  if (!allowed.value.includes(f.type)) { fileError.value = 'Use a PDF, JPG or PNG file.'; file.value = null; return }
  const max = config.value?.max_file_bytes
  if (max && f.size > max) { fileError.value = `File is too large (limit ${formatBytes(max)}).`; file.value = null; return }
  file.value = f
}

async function start(manual: boolean) {
  error.value = null; busy.value = true
  let id = ''
  try {
    const api = await getApi()
    stage.value = 'Creating your case…'
    id = (await api.createCase()).id
    if (!manual && file.value) {
      stage.value = 'Uploading…'
      await api.uploadDocument(id, file.value)
      stage.value = 'Reading the document… this can take a little while.'
      await api.extract(id)
    }
    router.push(`/cases/${id}/details`)
  } catch (e) {
    error.value = e
    // Если дело уже создано, пользователь может продолжить вручную — ошибку не маскируем.
  } finally { busy.value = false; stage.value = '' }
}
</script>

<template>
  <section>
    <h1>Review a ticket</h1>
    <div class="notice warn"><strong>Demo — synthetic documents only.</strong> Do not upload real tickets.</div>
    <ErrorNotice :error="error" />

    <div class="card">
      <h2>Upload a ticket</h2>
      <div class="drop">
        <p v-if="!file" class="muted">PDF, JPG or PNG. {{ limitText }}</p>
        <p v-else><strong>{{ file.name }}</strong> <span class="muted small">({{ formatBytes(file.size) }})</span></p>
        <label class="btn secondary" for="file">{{ file ? 'Replace file' : 'Choose file' }}</label>
        <input id="file" type="file" accept="application/pdf,image/jpeg,image/png" @change="pick" :disabled="busy"
          style="position:absolute;opacity:0;width:1px;height:1px" />
        <button v-if="file" class="btn danger" type="button" :disabled="busy" @click="file = null" style="margin-left:8px">Remove</button>
        <p v-if="fileError" class="notice err" role="alert" style="margin-top:12px">{{ fileError }}</p>
      </div>
      <div class="row" style="margin-top:16px">
        <button class="btn" type="button" :disabled="!file || busy" @click="start(false)">Read my ticket</button>
        <span v-if="busy" class="row" role="status"><span class="spinner" aria-hidden="true"></span>{{ stage }}</span>
      </div>
    </div>

    <div class="card">
      <h2>Or enter the details yourself</h2>
      <p class="muted small">You will type the ticket details on the next screen.</p>
      <button class="btn secondary" type="button" :disabled="busy" @click="start(true)">Enter manually</button>
    </div>
  </section>
</template>

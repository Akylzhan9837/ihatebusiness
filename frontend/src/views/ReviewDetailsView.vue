<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { getApi } from '@/api/client'
import { ApiError } from '@/api/errors'
import type { CaseData, ExtractedField, FieldKey } from '@/api/types'
import ErrorNotice from '@/components/ErrorNotice.vue'

const props = defineProps<{ id: string }>()

const LABELS: Record<FieldKey, string> = {
  ticket_number: 'Ticket number', issuing_authority: 'Issuing authority', city: 'City',
  violation_code: 'Violation code', violation_description: 'Violation description',
  issue_date: 'Date of violation', issue_time: 'Time of violation', location: 'Location',
  fine_amount: 'Fine amount (USD)', license_plate: 'License plate', plate_state: 'Plate state',
}
const ORDER = Object.keys(LABELS) as FieldKey[]
// TODO(contract): какие поля обязательны определяет backend; пока считаем обязательными все.
const REQUIRED = new Set<FieldKey>(ORDER)
const TYPE: Partial<Record<FieldKey, string>> = { issue_date: 'date', issue_time: 'time' }

const loading = ref(true)
const saving = ref(false)
const error = ref<unknown>(null)
const caseData = ref<CaseData | null>(null)
const values = reactive<Record<string, string>>({})
const touched = reactive<Record<string, boolean>>({})
const fieldErrors = reactive<Record<string, string>>({})

const byKey = computed(() => {
  const m = new Map<FieldKey, ExtractedField>()
  caseData.value?.fields.forEach((f) => m.set(f.key, f))
  return m
})

function load(c: CaseData) {
  caseData.value = c
  ORDER.forEach((k) => { values[k] = byKey.value.get(k)?.value ?? '' })
}

onMounted(async () => {
  try { load(await (await getApi()).getCase(props.id)) }
  catch (e) { error.value = e }
  finally { loading.value = false }
})

function quality(k: FieldKey) {
  if (touched[k]) return values[k] ? 'ok' : 'missing'
  return byKey.value.get(k)?.quality ?? 'missing'
}

function validate(): boolean {
  let ok = true
  for (const k of ORDER) {
    fieldErrors[k] = ''
    if (REQUIRED.has(k) && !values[k].trim()) { fieldErrors[k] = `${LABELS[k]} is required.`; ok = false }
  }
  if (values.fine_amount && !/^\d+(\.\d{1,2})?$/.test(values.fine_amount.trim())) {
    fieldErrors.fine_amount = 'Enter an amount like 115.00.'; ok = false
  }
  if (values.plate_state && !/^[A-Za-z]{2}$/.test(values.plate_state.trim())) {
    fieldErrors.plate_state = 'Use a 2-letter state code, e.g. NY.'; ok = false
  }
  return ok
}

async function confirm() {
  error.value = null
  if (!validate()) return
  saving.value = true
  try {
    const patch: Partial<Record<FieldKey, string>> = {}
    ORDER.forEach((k) => { patch[k] = values[k].trim() })
    load(await (await getApi()).updateCase(props.id, { fields: patch }))
    // Следующий шаг (questions → analyze) добавим вместе с соответствующими экранами.
  } catch (e) {
    if (e instanceof ApiError && e.fieldErrors) Object.assign(fieldErrors, e.fieldErrors)
    error.value = e
  } finally { saving.value = false }
}
</script>

<template>
  <section>
    <h1>Check the ticket details</h1>
    <p class="muted">Fix anything that is wrong or missing. Highlighted fields were hard to read or are missing.</p>
    <ErrorNotice :error="error" />
    <p v-if="loading" class="row" role="status"><span class="spinner" aria-hidden="true"></span>Loading…</p>

    <form v-else-if="caseData" class="card" novalidate @submit.prevent="confirm">
      <div v-for="k in ORDER" :key="k" class="field" :class="{ low: quality(k) === 'low_confidence', missing: quality(k) === 'missing' }">
        <label :for="`f-${k}`">
          {{ LABELS[k] }}
          <span v-if="quality(k) === 'low_confidence'" class="badge low">Please check</span>
          <span v-else-if="quality(k) === 'missing'" class="badge missing">Needed</span>
        </label>
        <input :id="`f-${k}`" v-model="values[k]" :type="TYPE[k] ?? 'text'" autocomplete="off"
          :aria-invalid="!!fieldErrors[k]" :aria-describedby="`e-${k} s-${k}`" @input="touched[k] = true" />
        <div v-if="byKey.get(k)?.source_text" :id="`s-${k}`" class="src">
          From your document: “{{ byKey.get(k)?.source_text }}”<span v-if="byKey.get(k)?.page"> (page {{ byKey.get(k)?.page }})</span>
        </div>
        <div v-if="fieldErrors[k]" :id="`e-${k}`" class="err" role="alert">{{ fieldErrors[k] }}</div>
      </div>
      <button class="btn" type="submit" :disabled="saving">{{ saving ? 'Saving…' : 'Confirm details' }}</button>
    </form>
  </section>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getApi } from '@/api/client'
import { FIELD_KEYS, type FieldKey } from '@/api/types'
import ErrorNotice from '@/components/ErrorNotice.vue'
import { CANONICAL_AUTHORITY, CANONICAL_CITY, FIELD_LABELS, REQUIRED_FIELDS, normalizeExtracted, validateField } from '@/lib/validate'
import { useCase } from '@/state/caseStore'

const store = useCase()
const router = useRouter()
const c = store.current

const INPUT: Partial<Record<FieldKey, { type: string; inputmode?: 'numeric' | 'decimal' | 'text'; maxlength?: number; placeholder?: string }>> = {
  ticket_number: { type: 'text', inputmode: 'numeric', maxlength: 10, placeholder: '10 digits' },
  violation_code: { type: 'text', inputmode: 'numeric', maxlength: 3 },
  violation_description: { type: 'text', placeholder: 'e.g. No parking, speeding, red light' },
  issue_date: { type: 'date' },
  issue_time: { type: 'time' },
  amount: { type: 'text', inputmode: 'decimal', placeholder: '65.00' },
  plate_state: { type: 'text', maxlength: 2, placeholder: 'NY' },
  plate_number: { type: 'text', maxlength: 12 },
}

// Что уже подтверждено — берём его. Иначе подставляем распознанное значение (оно остаётся «непроверенным», пока пользователь не нажмёт Confirm).
const values = reactive<Record<FieldKey, string>>(Object.fromEntries(FIELD_KEYS.map((k) => {
  const confirmed = c.value.confirmed_fields[k]
  return [k, confirmed !== null ? confirmed : normalizeExtracted(k, c.value.extraction?.fields[k]?.value ?? null)]
})) as Record<FieldKey, string>)
const wasConfirmed = (k: FieldKey) => c.value.confirmed_fields[k] !== null
const extracted = (k: FieldKey) => c.value.extraction?.fields[k]
const touched = reactive<Record<string, boolean>>({})
const errors = reactive<Record<string, string>>({})

const hasExtraction = computed(() => !!c.value.extraction)
const hasTicket = computed(() => c.value.documents.some((d) => d.kind === 'ticket'))
const manualEmpty = computed(() => !hasExtraction.value)
const warnings = computed(() => c.value.extraction?.warnings ?? [])
const codeNotice = computed(() => values.violation_code.trim() !== '' && values.violation_code.trim() !== '38'
  ? 'Automatic review is currently available for violation code 38 (parking, failure to display). You can still save and continue with other road fines, but the review may say this ticket is outside the demo.' : '')

function badge(k: FieldKey): '' | 'check' | 'missing' | 'confirmed' {
  if (touched[k]) return ''
  if (wasConfirmed(k)) return 'confirmed'
  if (!hasExtraction.value) return ''
  return extracted(k)?.value ? 'check' : 'missing'
}

const reading = ref(false)
const readError = ref<unknown>(null)
async function retryRead() {
  reading.value = true; readError.value = null
  try { await (await getApi()).extract(store.caseId); await store.refresh()
    // Подставляем только в пустые поля, чтобы не затирать ввод пользователя.
    for (const k of FIELD_KEYS) if (!values[k]) values[k] = normalizeExtracted(k, c.value.extraction?.fields[k]?.value ?? null)
  } catch (e) { readError.value = e } finally { reading.value = false }
}

const saving = ref(false)
const error = ref<unknown>(null)
const summary = computed(() => Object.values(errors).filter(Boolean).length)

function validateAll(): boolean {
  let ok = true
  for (const k of FIELD_KEYS) { errors[k] = validateField(k, values[k]); if (errors[k]) ok = false }
  return ok
}

async function confirm() {
  error.value = null
  if (!validateAll()) return
  saving.value = true
  try {
    const patch: Partial<Record<FieldKey, string | null>> = {}
    for (const k of FIELD_KEYS) patch[k] = values[k].trim() === '' ? null : (k === 'plate_state' || k === 'plate_number' ? values[k].trim().toUpperCase() : values[k].trim())
    await store.patch({ confirmed_fields: patch })
    await router.push({ name: 'receipt', params: { id: store.caseId } })
  } catch (e) { error.value = e } finally { saving.value = false }
}
</script>

<template>
  <div>
    <h1>Check the ticket details</h1>
    <p class="muted">Step 2 of 4 · Compare each field with your ticket. Nothing is used until you confirm it.</p>

    <div v-if="manualEmpty && !hasTicket" class="notice info" role="status">
      You chose to enter the details yourself, so every field is empty. Fill in what is on your ticket.
    </div>
    <div v-else-if="manualEmpty && hasTicket" class="notice warn" role="status">
      The ticket has been uploaded but not read yet.
      <button class="btn sm secondary" type="button" :disabled="reading" style="margin-left:8px" @click="retryRead">{{ reading ? 'Reading…' : 'Read it now' }}</button>
      You can also type the details yourself.
    </div>
    <ErrorNotice :error="readError" @retry="retryRead" />

    <div v-if="warnings.length" class="notice warn" role="status">
      <strong>Reading notes</strong>
      <ul class="plain"><li v-for="w in warnings" :key="w">{{ w }}</li></ul>
    </div>

    <ErrorNotice :error="error" />
    <div v-if="summary" class="notice err" role="alert">{{ summary }} field{{ summary === 1 ? ' needs' : 's need' }} attention.</div>

    <form class="card" novalidate @submit.prevent="confirm">
      <div v-for="k in FIELD_KEYS" :key="k" class="field"
        :class="{ low: badge(k) === 'check', missing: badge(k) === 'missing' || !!errors[k], bad: !!errors[k] }">
        <label :for="`f-${k}`">
          {{ FIELD_LABELS[k] }}<span v-if="REQUIRED_FIELDS.includes(k)" class="req" aria-hidden="true"> *</span>
          <span v-if="badge(k) === 'check'" class="badge low">Check against your ticket</span>
          <span v-else-if="badge(k) === 'missing'" class="badge missing">Not found. Enter it</span>
          <span v-else-if="badge(k) === 'confirmed'" class="badge ok">Confirmed</span>
        </label>
        <input :id="`f-${k}`" v-model="values[k]" :type="INPUT[k]?.type ?? 'text'" :inputmode="INPUT[k]?.inputmode"
          :maxlength="INPUT[k]?.maxlength ?? 250" :placeholder="INPUT[k]?.placeholder" autocomplete="off"
          :list="k === 'city' ? 'dl-city' : k === 'issuing_authority' ? 'dl-auth' : undefined"
          :required="REQUIRED_FIELDS.includes(k)" :aria-invalid="!!errors[k]"
          :aria-describedby="[errors[k] ? `e-${k}` : '', extracted(k)?.source_text ? `s-${k}` : ''].filter(Boolean).join(' ') || undefined"
          @input="touched[k] = true; errors[k] = ''" />
        <div v-if="extracted(k)?.source_text" :id="`s-${k}`" class="src">
          From your document: “{{ extracted(k)?.source_text }}”<span v-if="extracted(k)?.page"> (page {{ extracted(k)?.page }})</span>
        </div>
        <div v-if="k === 'violation_code' && codeNotice" class="src warnnote">{{ codeNotice }}</div>
        <div v-if="errors[k]" :id="`e-${k}`" class="err" role="alert">{{ errors[k] }}</div>
      </div>
      <datalist id="dl-city"><option :value="CANONICAL_CITY" /></datalist>
      <datalist id="dl-auth"><option :value="CANONICAL_AUTHORITY" /></datalist>
      <p class="muted small">Use <strong>{{ CANONICAL_CITY }}</strong> and <strong>{{ CANONICAL_AUTHORITY }}</strong> for the city and authority of an NYC ticket. Times are NYC local time.</p>
      <div class="row">
        <button class="btn" type="submit" :disabled="saving">{{ saving ? 'Saving…' : 'Confirm details and continue' }}</button>
      </div>
    </form>
  </div>
</template>

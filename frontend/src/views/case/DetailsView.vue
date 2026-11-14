<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { onBeforeRouteLeave, useRouter } from 'vue-router'
import { getApi } from '@/api/client'
import { FIELD_KEYS, type FieldKey } from '@/api/types'
import ErrorNotice from '@/components/ErrorNotice.vue'
import { CANONICAL_AUTHORITY, CANONICAL_CITY, isParkNYCCase, FIELD_LABELS, REQUIRED_FIELDS, normalizeExtracted, validateField } from '@/lib/validate'
import { STATES } from '@/lib/jurisdictions'
import { useCase } from '@/state/caseStore'

const store = useCase()
const router = useRouter()
const c = store.current
const pending = store.pending.details

const INPUT: Partial<Record<FieldKey, { type: string; inputmode?: 'numeric' | 'decimal' | 'text'; maxlength?: number; placeholder?: string }>> = {
  ticket_number: { type: 'text', maxlength: 64 },
  violation_code: { type: 'text', maxlength: 64 },
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
  return [k, pending?.fields[k] ?? (confirmed != null ? confirmed : normalizeExtracted(k, c.value.extraction?.fields[k]?.value ?? null))]
})) as Record<FieldKey, string>)
const wasConfirmed = (k: FieldKey) => c.value.confirmed_fields[k] != null
const extracted = (k: FieldKey) => c.value.extraction?.fields[k]
const touched = reactive<Record<string, boolean>>({})
const errors = reactive<Record<string, string>>({})

const hasExtraction = computed(() => !!c.value.extraction)
const hasTicket = computed(() => c.value.documents.some((d) => d.kind === 'ticket'))
const manualEmpty = computed(() => !hasExtraction.value)
const warnings = computed(() => c.value.extraction?.warnings ?? [])
const circumstances = ref(pending?.circumstances ?? c.value.circumstances ?? '')
const usesParkNYC = computed(() => isParkNYCCase(values))
const initial = JSON.stringify([values, circumstances.value])
let confirmedOnServer = false
onBeforeRouteLeave(() => {
  if (confirmedOnServer) delete store.pending.details
  else if (JSON.stringify([values, circumstances.value]) !== initial) {
    store.pending.details = { fields: { ...values }, circumstances: circumstances.value }
  }
})

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
    if (usesParkNYC.value) {
      patch.city = CANONICAL_CITY
      patch.issuing_authority = CANONICAL_AUTHORITY
    }
    await store.patch({ confirmed_fields: patch, circumstances: circumstances.value.trim() || null })
    confirmedOnServer = true
    await router.push({ name: usesParkNYC.value ? 'receipt' : 'report', params: { id: store.caseId } })
  } catch (e) { error.value = e } finally { saving.value = false }
}
</script>

<template>
  <div>
    <h1>Check the ticket details</h1>
    <p class="muted">Compare these details with your notice before continuing.</p>

    <p v-if="c.draft && !c.draft.stale" class="notice info">Changes to confirmed ticket details may require a new draft.</p>

    <div v-if="manualEmpty && !hasTicket" class="notice info" role="status">
      You chose to enter the details yourself, so every field is empty. Fill in what is on your ticket.
    </div>
    <div v-else-if="manualEmpty && hasTicket" class="notice warn" role="status">
      The ticket has been uploaded but not read yet.
      <button class="btn sm secondary" type="button" :disabled="reading" style="margin-left:8px" @click="retryRead">{{ reading ? 'Reading…' : 'Read it now' }}</button>
      You can also type the details yourself.
    </div>
    <ErrorNotice :error="readError" @retry="retryRead" />

    <p v-if="extracted('jurisdiction_state')?.value && extracted('jurisdiction_state')?.value !== values.jurisdiction_state"
      class="notice warn">The document appears to name a different state. Verify where the ticket was issued before continuing.</p>

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
        <select v-if="k === 'jurisdiction_state'" :id="`f-${k}`" v-model="values[k]">
          <option value="" disabled>Select a state</option>
          <option v-for="[code, name] in STATES" :key="code" :value="code">{{ name }}</option>
        </select>
        <select v-else-if="k === 'ticket_type'" :id="`f-${k}`" v-model="values[k]">
          <option value="" disabled>Select a ticket type</option>
          <option value="parking">Parking ticket</option>
          <option value="camera">Camera violation</option>
          <option value="moving">Officer-issued traffic ticket</option>
          <option value="other_civil">Other civil citation</option>
          <option value="unknown">Other or unsure</option>
        </select>
        <input v-else :id="`f-${k}`" v-model="values[k]" :type="INPUT[k]?.type ?? 'text'" :inputmode="INPUT[k]?.inputmode"
          :maxlength="INPUT[k]?.maxlength ?? 250" :placeholder="INPUT[k]?.placeholder" autocomplete="off"
          :list="k === 'city' ? 'dl-city' : k === 'issuing_authority' ? 'dl-auth' : undefined"
          :required="REQUIRED_FIELDS.includes(k)" :aria-invalid="!!errors[k]"
          :aria-describedby="[errors[k] ? `e-${k}` : '', extracted(k)?.source_text ? `s-${k}` : ''].filter(Boolean).join(' ') || undefined"
          @input="touched[k] = true; errors[k] = ''" />
        <div v-if="extracted(k)?.source_text" :id="`s-${k}`" class="src">
          From your document: “{{ extracted(k)?.source_text }}”<span v-if="extracted(k)?.page"> (page {{ extracted(k)?.page }})</span>
        </div>
        <div v-if="errors[k]" :id="`e-${k}`" class="err" role="alert">{{ errors[k] }}</div>
      </div>
      <datalist id="dl-city"><option :value="CANONICAL_CITY" /></datalist>
      <datalist id="dl-auth"><option :value="CANONICAL_AUTHORITY" /></datalist>
      <div v-if="!usesParkNYC" class="field">
        <label for="ticket-statement">What happened, and what should the authority review?</label>
        <textarea id="ticket-statement" v-model="circumstances" rows="4" maxlength="4000"></textarea>
      </div>
      <div class="row">
        <button class="btn" type="submit" :disabled="saving">{{ saving ? 'Saving…' : 'Confirm details and continue' }}</button>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import type { Question } from '@/api/types'
import ErrorNotice from '@/components/ErrorNotice.vue'
import QuestionField from '@/components/QuestionField.vue'
import { useAnswersForm } from '@/composables/useAnswersForm'
import { useCase } from '@/state/caseStore'

const store = useCase()
const router = useRouter()
const c = store.current

const PAYMENT: Question = {
  id: 'payment_method', prompt: 'How did you pay for parking?', type: 'choice',
  options: [
    { value: 'parknyc', label: 'Through ParkNYC (app, website or phone)' },
    { value: 'other', label: 'Another way (for example a muni-meter or cash)' },
    { value: 'none', label: 'I did not pay' },
    { value: 'unknown', label: "I'm not sure" },
  ],
}
const PARKNYC: Question[] = [
  { id: 'evidence_document_id', prompt: 'ParkNYC receipt file', type: 'evidence', options: [] },
  { id: 'session_start', prompt: 'Parking session start (NYC local time)', type: 'datetime', options: [] },
  { id: 'session_end', prompt: 'Parking session end (NYC local time)', type: 'datetime', options: [] },
  { id: 'session_plate_number', prompt: 'Plate number shown on the receipt', type: 'text', options: [] },
  { id: 'session_plate_state', prompt: 'Plate state shown on the receipt', type: 'text', options: [] },
  { id: 'session_zone', prompt: 'ParkNYC zone number (6 digits)', type: 'text', options: [] },
  { id: 'zone_matches_ticket_location', prompt: 'I checked that this ParkNYC zone matches the location on my ticket.', type: 'boolean', options: [] },
  { id: 'receipt_details_confirmed', prompt: 'I checked that the details above match the receipt file I uploaded.', type: 'boolean', options: [] },
]

// Видимые вопросы: при ParkNYC добавляем детали сессии; validate/toPatch работают только по ним.
const isParkingTicket = computed(() => {
  const code = c.value.confirmed_fields.violation_code?.trim()
  return !code || code === '38'
})
const isParkNyc = computed(() => values.payment_method === 'parknyc')
const visible = computed<Question[]>(() => (isParkNyc.value ? [PAYMENT, ...PARKNYC] : [PAYMENT]))
const { values, errors, reset, validate, toPatch } = useAnswersForm(visible)
reset(c.value.answers)

const circumstances = ref(c.value.circumstances ?? '')
const LIMIT = 4000
const circError = computed(() => (circumstances.value.length > LIMIT ? `Keep this under ${LIMIT} characters.` : ''))

const saving = ref(false)
const error = ref<unknown>(null)

async function next() {
  error.value = null
  const ok = validate()
  if (!ok || circError.value) return
  saving.value = true
  try {
    await store.patch({ answers: toPatch(), circumstances: circumstances.value.trim() || null })
    await router.push({ name: 'report', params: { id: store.caseId } })
  } catch (e) { error.value = e } finally { saving.value = false }
}
</script>

<template>
  <div>
    <h1>How did you pay for parking?</h1>
    <p class="muted">Step 3 of 4 · For parking tickets only. This demo checks tickets paid through ParkNYC. You type the receipt details; we do not read the receipt for you.</p>

    <ErrorNotice :error="error" />

    <div v-if="!isParkingTicket" class="notice info" role="status">
      This step is about paying for parking. If your ticket is for something else, such as speeding or a red light, you can skip it.
      <router-link :to="{ name: 'report', params: { id: store.caseId } }" class="btn sm secondary" style="margin-left:8px">Skip to review</router-link>
    </div>

    <form class="card" novalidate @submit.prevent="next">
      <QuestionField v-for="q in visible" :key="q.id" :question="q" :model-value="values[q.id] ?? null" :error="errors[q.id]"
        @update:model-value="values[q.id] = $event; errors[q.id] = ''" />

      <p v-if="isParkNyc" class="muted small">
        Copy the plate, state, zone and times exactly as shown on your ParkNYC receipt. You are responsible for their accuracy,
        and the review relies on what you type.
      </p>

      <div class="field">
        <label for="circ">Anything else you want in your statement? <span class="muted small">(optional)</span></label>
        <textarea id="circ" v-model="circumstances" rows="4" :maxlength="LIMIT + 200" :aria-invalid="!!circError"></textarea>
        <div class="src">{{ circumstances.length }} / {{ LIMIT }}</div>
        <div v-if="circError" class="err" role="alert">{{ circError }}</div>
      </div>

      <div class="row">
        <router-link :to="{ name: 'details', params: { id: store.caseId } }" class="btn secondary">Back</router-link>
        <button class="btn" type="submit" :disabled="saving">{{ saving ? 'Saving…' : 'Save and review my ticket' }}</button>
      </div>
    </form>
  </div>
</template>

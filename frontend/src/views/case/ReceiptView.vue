<script setup lang="ts">
import { computed, nextTick, ref } from 'vue'
import { onBeforeRouteLeave, useRouter } from 'vue-router'
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
const isParkNyc = computed(() => values.payment_method === 'parknyc')
const visible = computed<Question[]>(() => (isParkNyc.value ? [PAYMENT, ...PARKNYC] : [PAYMENT]))
const { values, errors, reset, validate, toPatch } = useAnswersForm(visible)
reset(c.value.answers)
const pending = store.pending.receipt
if (pending) Object.assign(values, pending.answers)

const circumstances = ref(pending?.circumstances ?? c.value.circumstances ?? '')
const initial = JSON.stringify([values, circumstances.value])
let savedOnServer = false
onBeforeRouteLeave(() => {
  if (savedOnServer) delete store.pending.receipt
  else if (JSON.stringify([values, circumstances.value]) !== initial) {
    store.pending.receipt = { answers: { ...values }, circumstances: circumstances.value }
  }
})
const LIMIT = 4000
const circError = computed(() => (circumstances.value.length > LIMIT ? `Keep this under ${LIMIT} characters.` : ''))

const saving = ref(false)
const error = ref<unknown>(null)
const form = ref<HTMLFormElement | null>(null)
const requestError = ref<HTMLElement | null>(null)
const invalidQuestions = computed(() => visible.value.filter((question) => !!errors[question.id]))

async function next() {
  if (saving.value) return
  error.value = null
  const ok = validate()
  if (!ok || circError.value) {
    await nextTick()
    const firstInvalid = form.value?.querySelector<HTMLElement>('.field.bad') ??
      form.value?.querySelector<HTMLElement>('#circ')
    firstInvalid?.scrollIntoView({ block: 'center' })
    const control = firstInvalid?.matches('textarea') ? firstInvalid :
      firstInvalid?.querySelector<HTMLElement>('input:not(:disabled)')
    control?.focus({ preventScroll: true })
    return
  }
  saving.value = true
  try {
    await store.patch({ answers: toPatch(), circumstances: circumstances.value.trim() || null })
    savedOnServer = true
    await router.push({ name: 'report', params: { id: store.caseId } })
  } catch (e) {
    error.value = e
    await nextTick()
    requestError.value?.focus()
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div>
    <h1>How did you pay for parking?</h1>
    <p class="muted">Enter the details from your ParkNYC receipt so Ticky can compare the session with your ticket.</p>

    <div v-if="error" ref="requestError" tabindex="-1"><ErrorNotice :error="error" @retry="next" /></div>

    <form ref="form" class="card" novalidate :aria-busy="saving" @submit.prevent="next">
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

      <div v-if="invalidQuestions.length" class="notice err" role="alert">
        <strong>Check the highlighted fields before continuing.</strong>
        <ul class="plain bullets">
          <li v-for="question in invalidQuestions" :key="question.id">{{ question.prompt }} {{ errors[question.id] }}</li>
        </ul>
      </div>

      <div class="row">
        <router-link :to="{ name: 'details', params: { id: store.caseId } }" class="btn secondary">Back</router-link>
        <button class="btn" type="submit" :disabled="saving">{{ saving ? 'Saving…' : 'Save and review my ticket' }}</button>
      </div>
    </form>
  </div>
</template>

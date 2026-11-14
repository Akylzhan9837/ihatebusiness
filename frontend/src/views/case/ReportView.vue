<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ANSWER_KEYS, type AnalysisStatus, type Question } from '@/api/types'
import ErrorNotice from '@/components/ErrorNotice.vue'
import QuestionField from '@/components/QuestionField.vue'
import { useAnswersForm } from '@/composables/useAnswersForm'
import { safeUrl } from '@/lib/clipboard'
import { formatCents, formatStamp } from '@/lib/format'
import { describeFact } from '@/lib/validate'
import { useCase } from '@/state/caseStore'

const store = useCase()
const router = useRouter()
const c = store.current
const analysis = computed(() => c.value.analysis)

const running = ref(false)
const error = ref<unknown>(null)
async function run() {
  running.value = true; error.value = null
  try { await store.analyze() } catch (e) { error.value = e } finally { running.value = false }
}
onMounted(() => { if (!c.value.analysis) run() })

const STATUS: Record<AnalysisStatus, { label: string; tone: string }> = {
  unsupported: { label: 'Outside this demo', tone: 'neutral' },
  needs_information: { label: 'More information needed', tone: 'warn' },
  no_supported_ground_identified: { label: 'No supported ground identified', tone: 'neutral' },
  ready_for_draft: { label: 'Ready for a draft', tone: 'ok' },
}

const sourceById = (id: string) => analysis.value?.sources.find((s) => s.id === id)

// Вопросы из анализа (needs_information): id соответствует ключу answers.
const questions = computed<Question[]>(() => (analysis.value?.questions ?? []).filter((q) => (ANSWER_KEYS as readonly string[]).includes(q.id)))
const { values, errors, reset, validate, toPatch } = useAnswersForm(questions)
reset(c.value.answers)
watch(() => c.value.analysis, () => reset(c.value.answers))

const answering = ref(false)
const answerError = ref<unknown>(null)
async function submitAnswers() {
  answerError.value = null
  if (!validate()) return
  answering.value = true
  try { await store.patch({ answers: toPatch() }); await run() }
  catch (e) { answerError.value = e } finally { answering.value = false }
}

// Предложение и demo access.
const demoBusy = ref(false)
const demoError = ref<unknown>(null)
const draft = computed(() => c.value.draft)
const draftCurrent = computed(() => !!draft.value && !draft.value.stale)
async function useDemo() {
  demoBusy.value = true; demoError.value = null
  try { await store.createDraft(); await router.push({ name: 'draft', params: { id: store.caseId } }) }
  catch (e) { demoError.value = e } finally { demoBusy.value = false }
}
const openDraft = () => router.push({ name: 'draft', params: { id: store.caseId } })
</script>

<template>
  <div>
    <h1>Your review</h1>
    <p class="muted">Step 4 of 4 · Based on the details you confirmed and typed. It is information, not legal advice.</p>

    <p v-if="running" class="row" role="status"><span class="spinner" aria-hidden="true"></span>Reviewing your ticket against official sources…</p>

    <div v-else-if="error && !analysis" class="card">
      <h2>We couldn't complete the review</h2>
      <ErrorNotice :error="error" retry-label="Run the review again" @retry="run" />
      <div class="row">
        <button class="btn" type="button" @click="run">Run the review again</button>
        <router-link :to="{ name: 'details', params: { id: store.caseId } }" class="btn secondary">Edit ticket details</router-link>
      </div>
    </div>

    <template v-else-if="analysis">
      <ErrorNotice :error="error" @retry="run" />

      <div class="status" :class="STATUS[analysis.status].tone" role="status">
        <span class="chip">{{ STATUS[analysis.status].label }}</span>
        <p>{{ analysis.summary }}</p>
      </div>

      <div v-if="draft?.stale" class="notice warn">
        Your saved draft is out of date because your details changed.
        <router-link :to="{ name: 'draft', params: { id: store.caseId } }">View the previous text</router-link>
        <span v-if="analysis.status === 'ready_for_draft'"> or prepare an updated draft below.</span>
      </div>

      <!-- unsupported -->
      <div v-if="analysis.status === 'unsupported'" class="card">
        <h2>This ticket is outside what the demo supports</h2>
        <p>Check the jurisdiction and issuing authority shown on your notice before proceeding.</p>
        <p class="muted small">If a detail was read or typed wrongly, you can fix it and review again.</p>
        <div class="row">
          <router-link :to="{ name: 'details', params: { id: store.caseId } }" class="btn secondary">Edit ticket details</router-link>
        </div>
      </div>

      <!-- needs_information -->
      <div v-if="analysis.status === 'needs_information'" class="card">
        <h2>What we still need</h2>
        <ul v-if="analysis.missing_information.length" class="plain bullets">
          <li v-for="m in analysis.missing_information" :key="m">{{ m }}</li>
        </ul>
        <p v-else class="muted">Add the details below, then run the review again.</p>

        <form v-if="questions.length" novalidate @submit.prevent="submitAnswers">
          <ErrorNotice :error="answerError" />
          <QuestionField v-for="q in questions" :key="q.id" :question="q" :model-value="values[q.id] ?? null" :error="errors[q.id]"
            @update:model-value="values[q.id] = $event; errors[q.id] = ''" />
          <button class="btn" type="submit" :disabled="answering || running">{{ answering || running ? 'Checking…' : 'Save and check again' }}</button>
        </form>
        <div v-else class="row">
          <router-link :to="{ name: 'details', params: { id: store.caseId } }" class="btn secondary">Edit ticket details</router-link>
          <router-link v-if="c.answers.payment_method" :to="{ name: 'receipt', params: { id: store.caseId } }" class="btn secondary">Edit payment details</router-link>
        </div>
      </div>

      <!-- findings -->
      <div v-if="analysis.status !== 'unsupported' && analysis.status !== 'needs_information'" class="card">
        <h2>Findings</h2>
        <p v-if="!analysis.findings.length" class="muted">No findings were reported for this review.</p>
        <article v-for="f in analysis.findings" :key="f.id" class="finding">
          <h3>{{ f.title }}</h3>
          <p>{{ f.explanation }}</p>
          <template v-if="f.supporting_fact_ids.length">
            <h4>Facts this relies on</h4>
            <dl class="facts">
              <template v-for="id in f.supporting_fact_ids" :key="id">
                <template v-if="describeFact(id, c)">
                  <dt>{{ describeFact(id, c)?.label }}</dt><dd>{{ describeFact(id, c)?.value }}</dd>
                </template>
              </template>
            </dl>
          </template>
          <template v-if="f.limitations.length">
            <h4>Limits of this finding</h4>
            <ul class="plain bullets"><li v-for="l in f.limitations" :key="l">{{ l }}</li></ul>
          </template>
          <p v-if="f.suggested_next_step" class="next-step"><strong>Suggested next step:</strong> {{ f.suggested_next_step }}</p>
          <p v-if="f.source_ids.length" class="small">
            <strong>Sources:</strong>
            <template v-for="(sid, i) in f.source_ids" :key="sid">
              <template v-if="sourceById(sid)">{{ i ? ', ' : ' ' }}<a :href="safeUrl(sourceById(sid)!.url)" target="_blank" rel="noopener noreferrer">{{ sourceById(sid)!.title }}</a></template>
            </template>
          </p>
        </article>
        <p class="muted small">These details were entered or confirmed by you. The check compares them with each other and cannot verify them against the original documents, so please re-read your ticket and receipt yourself.</p>
      </div>

      <div v-if="analysis.next_steps.length" class="card">
        <h2>Suggested next steps</h2>
        <ol class="bullets"><li v-for="s in analysis.next_steps" :key="s">{{ s }}</li></ol>
      </div>

      <div v-if="analysis.sources.length" class="card">
        <h2>Official sources</h2>
        <ul class="plain sources">
          <li v-for="s in analysis.sources" :key="s.id">
            <a :href="safeUrl(s.url)" target="_blank" rel="noopener noreferrer">{{ s.title }}</a>
            <span class="muted small"> · {{ s.jurisdiction }} · {{ s.topic }} · checked {{ s.accessed_at }}</span>
            <blockquote v-if="s.relevant_excerpt">{{ s.relevant_excerpt }}</blockquote>
          </li>
        </ul>
      </div>

      <!-- offer -->
      <div v-if="analysis.status === 'ready_for_draft' && analysis.draft_available" class="card offer">
        <p class="eyebrow">Next step</p>
        <h2>{{ analysis.draft_kind === 'factual' ? 'Factual statement draft' : 'Dispute draft' }}</h2>
        <div class="price">{{ formatCents(c.offer.price_cents, c.offer.currency) }}<small> test price</small></div>
        <ul class="plain checks">
          <li>An editable dispute draft built from your confirmed facts</li>
          <li>Official resources for checking how to file</li>
          <li>Copy as text or download as PDF. You submit it yourself</li>
        </ul>

        <ErrorNotice :error="demoError" @retry="useDemo" />

        <div v-if="draftCurrent" class="row">
          <button class="btn" type="button" @click="openDraft">Open your saved draft</button>
          <span class="muted small">Saved {{ formatStamp(draft?.updated_at) }}</span>
        </div>
        <template v-else>
          <p v-if="draft?.stale" class="small warnnote">Preparing a new draft replaces the previous text. Copy anything you want to keep first.</p>
          <div class="row">
            <button class="btn" type="button" disabled aria-describedby="pay-note">Pay {{ formatCents(c.offer.price_cents, c.offer.currency) }}</button>
            <span class="muted small">or</span>
            <button class="btn dark" type="button" :disabled="c.offer.mode !== 'demo' || demoBusy" @click="useDemo">
              {{ demoBusy ? 'Preparing your draft…' : 'Use demo access' }}
            </button>
          </div>
          <p id="pay-note" class="small muted">
            <template v-if="c.offer.mode === 'demo'">Demo access is separate from payment and is free. Nothing is charged.</template>
            <template v-else>Demo access is unavailable right now, and payments are not enabled in this demo. Nothing is charged.</template>
          </p>
        </template>
      </div>

      <div class="row" style="margin-top:8px">
        <button class="btn secondary" type="button" :disabled="running" @click="run">Run the review again</button>
        <router-link :to="{ name: 'details', params: { id: store.caseId } }" class="btn secondary">Edit ticket details</router-link>
        <router-link v-if="c.answers.payment_method" :to="{ name: 'receipt', params: { id: store.caseId } }" class="btn secondary">Edit payment details</router-link>
      </div>
    </template>

    <div v-else class="card">
      <p class="muted">There is no review yet.</p>
      <button class="btn" type="button" @click="run">Run the review</button>
    </div>
  </div>
</template>

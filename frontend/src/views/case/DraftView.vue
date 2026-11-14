<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { onBeforeRouteLeave } from 'vue-router'
import { getApi } from '@/api/client'
import type { Outcome } from '@/api/types'
import ErrorNotice from '@/components/ErrorNotice.vue'
import { copyText, downloadBlob, safeUrl } from '@/lib/clipboard'
import { formatStamp } from '@/lib/format'
import { useCase } from '@/state/caseStore'

const store = useCase()
const c = store.current
const draft = computed(() => c.value.draft)
const stale = computed(() => !!draft.value?.stale)
const LIMIT = 16000

const text = ref(draft.value?.text ?? '')
const dirty = computed(() => !!draft.value && text.value !== draft.value.text)
const tooLong = computed(() => text.value.length > LIMIT)
const empty = computed(() => text.value.trim() === '')

const saving = ref(false)
const saveError = ref<unknown>(null)
const justSaved = ref(false)
async function save(): Promise<boolean> {
  if (!dirty.value || stale.value || tooLong.value || empty.value) return !dirty.value
  saving.value = true; saveError.value = null
  try {
    await (await getApi()).patchDraft(store.caseId, text.value)
    await store.refresh()
    text.value = draft.value?.text ?? text.value
    justSaved.value = true; setTimeout(() => { justSaved.value = false }, 3000)
    return true
  } catch (e) { saveError.value = e; return false } finally { saving.value = false }
}

const copyState = ref<'' | 'ok' | 'fail'>('')
async function copy() {
  copyState.value = (await copyText(text.value)) ? 'ok' : 'fail'
  setTimeout(() => { copyState.value = '' }, 4000)
}

const exporting = ref(false)
const exportError = ref<unknown>(null)
async function download() {
  exporting.value = true; exportError.value = null
  try {
    // PDF строится из сохранённого текста: сначала сохраняем правки.
    if (!(await save())) return
    downloadBlob(await (await getApi()).exportPdf(store.caseId), 'ticky-draft.pdf')
  } catch (e) { exportError.value = e } finally { exporting.value = false }
}

const OUTCOMES: { value: Outcome; label: string }[] = [
  { value: 'submitted', label: 'I submitted the dispute' },
  { value: 'dismissed', label: 'The ticket was dismissed' },
  { value: 'upheld', label: 'The ticket was upheld' },
  { value: 'other', label: 'Something else happened' },
]
const outcomeError = ref<unknown>(null)
const outcomeSaving = ref(false)
async function setOutcome(e: Event) {
  const v = (e.target as HTMLSelectElement).value
  outcomeSaving.value = true; outcomeError.value = null
  try { await store.patch({ outcome: (v || null) as Outcome | null }) }
  catch (err) { outcomeError.value = err } finally { outcomeSaving.value = false }
}

// Не теряем несохранённые правки.
const warn = (e: BeforeUnloadEvent) => { if (dirty.value) { e.preventDefault(); e.returnValue = '' } }
onMounted(() => window.addEventListener('beforeunload', warn))
onBeforeUnmount(() => window.removeEventListener('beforeunload', warn))
onBeforeRouteLeave(() => (dirty.value ? window.confirm('You have unsaved changes to your draft. Leave without saving?') : true))
</script>

<template>
  <div>
    <h1>Your draft</h1>

    <div v-if="!draft" class="card">
      <h2>No draft yet</h2>
      <p class="muted">Finish your ticket review and choose demo access to prepare a draft.</p>
      <router-link :to="{ name: 'report', params: { id: store.caseId } }" class="btn">Go to your review</router-link>
    </div>

    <template v-else>
      <div v-if="stale" class="notice warn" role="status">
        <strong>This draft is out of date.</strong> Your details changed after it was prepared. You can still copy the saved text below,
        but editing and PDF download are available only for an up-to-date draft.
        <div style="margin-top:8px"><router-link :to="{ name: 'report', params: { id: store.caseId } }" class="btn sm">Review again and prepare a new draft</router-link></div>
      </div>
      <p v-else class="muted">Edit the text so it is accurate and in your own words. Review the filing instructions before you submit it yourself.</p>

      <div class="card">
        <label for="draft-text" class="lbl">Dispute draft</label>
        <textarea id="draft-text" v-model="text" class="draft" rows="16" :readonly="stale" :aria-invalid="tooLong || empty"
          aria-describedby="draft-meta"></textarea>
        <div id="draft-meta" class="src row" style="justify-content:space-between">
          <span :class="{ err: tooLong }">{{ text.length }} / {{ LIMIT }}</span>
          <span v-if="draft.updated_at">Saved {{ formatStamp(draft.updated_at) }}<template v-if="dirty"> · unsaved changes</template></span>
        </div>
        <div v-if="tooLong" class="err" role="alert">The draft is too long. Keep it under {{ LIMIT }} characters.</div>
        <div v-else-if="empty && !stale" class="err" role="alert">The draft can't be empty.</div>

        <ErrorNotice :error="saveError" @retry="save" />
        <ErrorNotice :error="exportError" @retry="download" />
        <p v-if="exportError" class="small muted">You can still copy the text and paste it where you file.</p>

        <div class="row">
          <button class="btn" type="button" :disabled="stale || !dirty || saving || tooLong || empty" @click="save">{{ saving ? 'Saving…' : 'Save changes' }}</button>
          <button class="btn secondary" type="button" @click="copy">Copy text</button>
          <button class="btn secondary" type="button" :disabled="stale || exporting || tooLong || empty" @click="download">{{ exporting ? 'Preparing PDF…' : 'Download PDF' }}</button>
          <span v-if="justSaved" class="small" role="status">Saved.</span>
          <span v-if="copyState === 'ok'" class="small" role="status">Copied to clipboard.</span>
          <span v-else-if="copyState === 'fail'" class="small err" role="alert">Couldn't copy. Select the text and copy it manually.</span>
        </div>
      </div>

      <div class="card">
        <h2>Attach to your filing</h2>
        <ul v-if="draft.attachments.length" class="plain bullets"><li v-for="a in draft.attachments" :key="a.document_id">{{ a.filename }}</li></ul>
        <p v-else class="muted">No attachments are listed.</p>
        <p class="muted small">The PDF contains only the text and this list. Attach any supporting documents separately if the filing instructions call for them.</p>
      </div>

      <div class="card">
        <h2>How to submit it</h2>
        <ol class="bullets">
          <li v-for="s in draft.submission_steps" :key="s.text">
            {{ s.text }} <a v-if="safeUrl(s.url)" :href="safeUrl(s.url)" target="_blank" rel="noopener noreferrer">Official resource</a>
          </li>
        </ol>
        <p class="muted small">Check the official page for deadlines and options. Verify your deadline with the office named on your notice.</p>
      </div>

      <div class="card">
        <h2>What happened?</h2>
        <p class="muted small">Optional note for yourself. It does not change your draft.</p>
        <label for="outcome" class="visually-hidden">Outcome</label>
        <select id="outcome" :value="c.outcome ?? ''" :disabled="outcomeSaving" @change="setOutcome">
          <option value="">Not set</option>
          <option v-for="o in OUTCOMES" :key="o.value" :value="o.value">{{ o.label }}</option>
        </select>
        <ErrorNotice :error="outcomeError" />
      </div>
    </template>
  </div>
</template>

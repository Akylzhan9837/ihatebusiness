<script setup lang="ts">
import { computed, onMounted, provide, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getApi } from '@/api/client'
import { access, privateLink } from '@/api/access'
import { ApiError, isNotFound, userMessage } from '@/api/errors'
import ErrorNotice from '@/components/ErrorNotice.vue'
import { copyText } from '@/lib/clipboard'
import { CASE_KEY, createCaseStore } from '@/state/caseStore'

const props = defineProps<{ id: string }>()
const route = useRoute()
const router = useRouter()

const caseId = props.id.toLowerCase()
const store = createCaseStore(caseId)
provide(CASE_KEY, store)

const loading = ref(true)
const loadError = ref<unknown>(null)
const hasKey = ref(!!access.get(caseId))
const linkCopied = ref<'' | 'ok' | 'fail'>('')
const deleting = ref(false)
const deleteError = ref<unknown>(null)

const STEPS = [
  { name: 'details', label: 'Ticket details' },
  { name: 'receipt', label: 'ParkNYC receipt' },
  { name: 'report', label: 'Review' },
  { name: 'draft', label: 'Draft' },
] as const
const current = computed(() => STEPS.findIndex((s) => s.name === route.name))
const done = computed<boolean[]>(() => {
  const c = store.data.value
  if (!c) return [false, false, false, false]
  return [
    Object.values(c.confirmed_fields).some((v) => v !== null),
    c.answers.payment_method !== null,
    c.analysis !== null,
    c.draft !== null && !c.draft.stale,
  ]
})
// Нужна ли «ссылка недоступна» (нет ключа в этой вкладке) или «дело не найдено».
const noAccess = computed(() => !hasKey.value || (loadError.value !== null && isNotFound(loadError.value)))

function nextStep(): (typeof STEPS)[number]['name'] {
  const c = store.data.value
  if (!c) return 'details'
  if (c.draft) return 'draft'
  if (c.analysis) return 'report'
  if (Object.values(c.confirmed_fields).some((v) => v !== null)) return 'receipt'
  return 'details'
}

async function load() {
  loading.value = true; loadError.value = null
  hasKey.value = !!access.get(caseId)
  if (!hasKey.value) { loading.value = false; return }
  try {
    await store.refresh()
    // /case/{id} без шага — открыть тот шаг, где пользователь остановился (в т.ч. сохранённый черновик).
    if (route.name === 'case-home') await router.replace({ name: nextStep(), params: { id: caseId } })
  } catch (e) { loadError.value = e } finally { loading.value = false }
}
onMounted(load)

async function copyLink() {
  const link = privateLink(caseId)
  linkCopied.value = link && (await copyText(link)) ? 'ok' : 'fail'
  setTimeout(() => { linkCopied.value = '' }, 4000)
}

async function remove() {
  if (!window.confirm('Delete this case and all uploaded files? This cannot be undone.')) return
  deleting.value = true; deleteError.value = null
  try { await (await getApi()).deleteCase(caseId); await router.push('/') }
  catch (e) { deleteError.value = e instanceof ApiError ? e : new ApiError('unknown', userMessage(e), 0) }
  finally { deleting.value = false }
}
</script>

<template>
  <section>
    <p v-if="loading" class="row" role="status"><span class="spinner" aria-hidden="true"></span>Opening your case…</p>

    <div v-else-if="noAccess" class="card">
      <h1>This case can't be opened</h1>
      <p>Cases open only from their private link, the one that ends in <code>#key=…</code>. Open the link you saved when you created the case.</p>
      <p class="muted small">The link is not stored on our side. If you no longer have it, you can start a new case.</p>
      <div class="row"><router-link to="/new" class="btn">Start a new case</router-link><router-link to="/" class="btn secondary">Back to home</router-link></div>
    </div>

    <div v-else-if="loadError" class="card">
      <h1>We couldn't load your case</h1>
      <ErrorNotice :error="loadError" @retry="load" />
      <button class="btn secondary" type="button" @click="load">Try again</button>
    </div>

    <template v-else-if="store.data.value">
      <nav class="steps" aria-label="Progress">
        <ol>
          <li v-for="(s, i) in STEPS" v-show="s.name !== 'receipt' || !store.data.value?.confirmed_fields.ticket_type || (store.data.value.confirmed_fields.ticket_type === 'parking' && store.data.value.confirmed_fields.jurisdiction_state === 'NY' && /^0*38$/.test(store.data.value.confirmed_fields.violation_code ?? ''))" :key="s.name" :class="{ cur: i === current, done: done[i] }">
            <router-link :to="{ name: s.name, params: { id: caseId } }" :aria-current="s.name === route.name ? 'step' : undefined">
              <span class="n" aria-hidden="true">{{ done[i] && i !== current ? '✓' : i + 1 }}</span>{{ s.label }}
            </router-link>
          </li>
        </ol>
      </nav>

      <details class="keybox">
        <summary>Save your private link</summary>
        <p class="small">This link is the only way to reopen this case later or on another device. Anyone who has it can open the case, so keep it private.</p>
        <div class="row">
          <button class="btn sm secondary" type="button" @click="copyLink">Copy private link</button>
          <span v-if="linkCopied === 'ok'" class="small" role="status">Copied.</span>
          <span v-else-if="linkCopied === 'fail'" class="small err" role="alert">Couldn't copy. Open this case in a tab where it was created.</span>
        </div>
      </details>

      <router-view />

      <div class="case-foot">
        <ErrorNotice :error="deleteError" />
        <button class="btn danger sm" type="button" :disabled="deleting" @click="remove">{{ deleting ? 'Deleting…' : 'Delete this case' }}</button>
      </div>
    </template>
  </section>
</template>

import { computed, inject, ref, type ComputedRef, type InjectionKey, type Ref } from 'vue'
import { getApi } from '@/api/client'
import type { Analysis, CaseData, Draft, PatchCase } from '@/api/types'

// Общее состояние дела для всех шагов мастера. Создаётся в CaseShell, шаги читают через useCase().
export interface CaseStore {
  caseId: string
  data: Ref<CaseData | null>
  /** Только внутри шагов: Shell рендерит их после успешной загрузки. */
  current: ComputedRef<CaseData>
  refresh(): Promise<CaseData>
  patch(p: PatchCase): Promise<CaseData>
  analyze(): Promise<Analysis>
  createDraft(): Promise<Draft>
}

export const CASE_KEY: InjectionKey<CaseStore> = Symbol('case')

export function createCaseStore(caseId: string): CaseStore {
  const data = ref<CaseData | null>(null) as Ref<CaseData | null>
  const current = computed(() => data.value as CaseData)
  async function refresh() { const c = await (await getApi()).getCase(caseId); data.value = c; return c }
  return {
    caseId, data, current, refresh,
    async patch(p) { const c = await (await getApi()).patchCase(caseId, p); data.value = c; return c },
    // После analyze/draft перечитываем дело: сервер сам расставляет stale и сбрасывает устаревшее.
    async analyze() { const a = await (await getApi()).analyze(caseId); await refresh(); return a },
    async createDraft() { const d = await (await getApi()).createDraft(caseId); await refresh(); return d },
  }
}

export function useCase(): CaseStore {
  const s = inject(CASE_KEY)
  if (!s) throw new Error('useCase() must be used inside CaseShell')
  return s
}

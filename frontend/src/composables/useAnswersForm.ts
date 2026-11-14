import { reactive } from 'vue'
import { ANSWER_KEYS, type AnswerValue, type Answers, type Question } from '@/api/types'
import { validateAnswer } from '@/lib/validate'

// Общая форма для структурированных ответов (шаг ParkNYC и вопросы из анализа).
export function useAnswersForm(questions: { readonly value: Question[] }) {
  const values = reactive<Record<string, AnswerValue>>({})
  const errors = reactive<Record<string, string>>({})

  function reset(a: Answers) {
    for (const k of ANSWER_KEYS) values[k] = a[k] ?? null
    for (const k of Object.keys(errors)) errors[k] = ''
  }

  function validate(): boolean {
    let ok = true
    for (const q of questions.value) {
      errors[q.id] = validateAnswer(q, values[q.id] ?? null, values)
      if (errors[q.id]) ok = false
    }
    return ok
  }

  /** PATCH только по видимым вопросам; пустое → null (очищает значение). */
  function toPatch(): Partial<Answers> {
    const patch: Record<string, AnswerValue> = {}
    for (const q of questions.value) {
      const v = values[q.id] ?? null
      if (q.type === 'boolean') patch[q.id] = v === true
      else {
        const s = typeof v === 'string' ? v.trim() : ''
        patch[q.id] = s ? (q.id === 'session_plate_state' || q.id === 'session_plate_number' ? s.toUpperCase() : s) : null
      }
    }
    return patch as Partial<Answers>
  }

  return { values, errors, reset, validate, toPatch }
}

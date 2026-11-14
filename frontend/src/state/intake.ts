import type { ApiError } from '@/api/errors'

export interface PreviousIntake {
  mode: 'upload' | 'manual'
  state: string
  acknowledged: boolean
  file: File | null
  caseId: string
  uploaded: boolean
  error: ApiError | null
}

let previous: PreviousIntake | undefined

export function restoreIntake(): PreviousIntake | undefined {
  if (previous?.caseId === history.state?.tickyIntake) return previous
}

export function rememberIntake(snapshot: PreviousIntake) {
  previous = snapshot
  history.replaceState({ ...history.state, tickyIntake: snapshot.caseId }, '')
}

export function forgetIntake(caseId: string) {
  if (previous?.caseId === caseId) previous = undefined
}

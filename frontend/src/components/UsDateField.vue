<script setup lang="ts">
import { computed, ref } from 'vue'
import { DATE_PLACEHOLDER, isoToUsDate, parseUsDate } from '@/lib/usdate'

const props = defineProps<{
  modelValue: string
  inputId: string
  calendarLabel: string
  invalid?: boolean
  required?: boolean
  describedby?: string
}>()
const emit = defineEmits<{ 'update:modelValue': [value: string] }>()
const picker = ref<HTMLInputElement | null>(null)
const supportsPicker = 'showPicker' in HTMLInputElement.prototype
const isoDate = computed(() => parseUsDate(props.modelValue) ?? '')

function onInput(event: Event) {
  const input = event.target as HTMLInputElement
  const raw = input.value
  let value = raw
  if (/^\d{4}-\d{2}-\d{2}$/.test(raw.trim())) {
    value = isoToUsDate(raw.trim())
  } else if (input.selectionEnd === raw.length) {
    // Keep edits in the middle of the date and manually typed slashes intact.
    value = raw.replace(/^(\d{2})(\d{1,2})$/, '$1/$2')
      .replace(/^(\d{2})\/?(\d{2})\/?(\d{1,4})$/, '$1/$2/$3')
  }
  if (value !== raw) input.value = value
  emit('update:modelValue', value)
}

function normalize() {
  const formatted = isoToUsDate(isoDate.value)
  if (formatted && formatted !== props.modelValue) emit('update:modelValue', formatted)
}

function selectDate(event: Event) {
  const value = (event.target as HTMLInputElement).value
  emit('update:modelValue', isoToUsDate(value))
}
</script>

<template>
  <div class="us-date">
    <input :id="inputId" :value="modelValue" type="text" inputmode="numeric" autocomplete="off"
      maxlength="16" :placeholder="DATE_PLACEHOLDER" :required="required" :aria-invalid="invalid"
      :aria-describedby="describedby" @input="onInput" @blur="normalize" />
    <div v-if="supportsPicker" class="calendar">
      <input ref="picker" class="calendar-input" type="date" :value="isoDate" tabindex="-1" aria-hidden="true"
        min="0001-01-01" max="9999-12-31" @change="selectDate" />
      <button type="button" class="calendar-button" :aria-label="calendarLabel"
        @click="picker?.showPicker()">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75"
          stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <rect x="3" y="5" width="18" height="16" rx="2" />
          <path d="M16 3v4M8 3v4M3 10h18" />
        </svg>
      </button>
    </div>
  </div>
</template>

<style scoped>
.us-date {
  display: flex;
  gap: 4px;
  max-width: 260px;
}

.us-date > input {
  min-width: 0;
}

.calendar {
  position: relative;
  flex: 0 0 44px;
}

.field .calendar .calendar-input {
  position: absolute;
  inset: 0;
  opacity: 0;
  pointer-events: none;
}

.calendar-button {
  position: relative;
  display: grid;
  place-items: center;
  width: 100%;
  height: 100%;
  min-height: 44px;
  padding: 0;
  border: 1px solid #6b7a8c;
  border-radius: 8px;
  background: #fff;
  color: var(--ink);
  cursor: pointer;
}

.calendar-button:hover {
  background: #f2f6fa;
}
</style>

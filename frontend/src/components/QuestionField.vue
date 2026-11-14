<script setup lang="ts">
import type { AnswerValue, Question } from '@/api/types'
import EvidenceField from './EvidenceField.vue'

// Универсальный рендер вопроса по type: choice | text | datetime | boolean | evidence.
const props = defineProps<{ question: Question; modelValue: AnswerValue; error?: string }>()
const emit = defineEmits<{ 'update:modelValue': [v: AnswerValue] }>()

const id = `q-${props.question.id}`
const TEXT_ATTRS: Record<string, { maxlength: number; inputmode?: 'numeric' | 'text'; autocapitalize?: 'characters'; placeholder?: string }> = {
  session_zone: { maxlength: 6, inputmode: 'numeric', placeholder: '6 digits' },
  session_plate_state: { maxlength: 2, autocapitalize: 'characters', placeholder: 'NY' },
  session_plate_number: { maxlength: 12, autocapitalize: 'characters' },
}
const attrs = TEXT_ATTRS[props.question.id] ?? { maxlength: 250 }
const val = (e: Event) => (e.target as HTMLInputElement).value
</script>

<template>
  <div class="field" :class="{ bad: !!error }">
    <fieldset v-if="question.type === 'choice'" class="choice">
      <legend :id="`${id}-label`">{{ question.prompt }}</legend>
      <label v-for="o in question.options" :key="o.value" class="opt">
        <input type="radio" :name="id" :value="o.value" :checked="modelValue === o.value"
          :aria-describedby="error ? `${id}-err` : undefined" @change="emit('update:modelValue', o.value)" />
        <span>{{ o.label }}</span>
      </label>
    </fieldset>

    <label v-else-if="question.type === 'boolean'" class="opt check">
      <input type="checkbox" :checked="modelValue === true" :aria-invalid="!!error" :aria-describedby="error ? `${id}-err` : undefined"
        @change="emit('update:modelValue', ($event.target as HTMLInputElement).checked)" />
      <span>{{ question.prompt }}</span>
    </label>

    <template v-else-if="question.type === 'evidence'">
      <span :id="`${id}-label`" class="lbl">{{ question.prompt }}</span>
      <EvidenceField :model-value="typeof modelValue === 'string' ? modelValue : null" :input-id="id" :invalid="!!error"
        @update:model-value="emit('update:modelValue', $event)" />
    </template>

    <template v-else>
      <label :for="id" class="lbl">{{ question.prompt }}</label>
      <input v-if="question.type === 'datetime'" :id="id" type="datetime-local" :value="typeof modelValue === 'string' ? modelValue : ''"
        :aria-invalid="!!error" :aria-describedby="error ? `${id}-err` : undefined" @input="emit('update:modelValue', val($event))" />
      <input v-else :id="id" type="text" autocomplete="off" :value="typeof modelValue === 'string' ? modelValue : ''"
        :maxlength="attrs.maxlength" :inputmode="attrs.inputmode" :autocapitalize="attrs.autocapitalize" :placeholder="attrs.placeholder"
        :aria-invalid="!!error" :aria-describedby="error ? `${id}-err` : undefined" @input="emit('update:modelValue', val($event))" />
    </template>

    <div v-if="error" :id="`${id}-err`" class="err" role="alert">{{ error }}</div>
  </div>
</template>

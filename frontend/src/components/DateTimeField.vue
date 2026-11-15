<script setup lang="ts">
import { ref, watch } from 'vue'
import { DATE_EXAMPLE, DATE_PLACEHOLDER, TIME_EXAMPLE, TIME_PLACEHOLDER, joinIsoDateTime, splitIsoDateTime } from '@/lib/usdate'

// Дата и время — два текстовых поля с явным американским форматом, поэтому вид не зависит от локали устройства.
// Наружу уходит ISO 'YYYY-MM-DDTHH:MM' (местное время NYC, без UTC). Пока ввод неполный или неверный,
// наружу уходит сырой текст 'дата|время': валидатор отдаёт по нему точную подсказку (lib/validate.ts).
const props = defineProps<{ modelValue: string | null; inputId: string; invalid?: boolean; describedby?: string }>()
const emit = defineEmits<{ 'update:modelValue': [v: string] }>()

const init = splitIsoDateTime(props.modelValue)
const date = ref(init.date || (props.modelValue?.includes('|') ? props.modelValue.split('|')[0] : ''))
const time = ref(init.time || (props.modelValue?.includes('|') ? props.modelValue.split('|')[1] : ''))

// Внешнее значение изменилось (например, сброс формы): подставляем его, не затирая ввод в процессе.
watch(() => props.modelValue, (v) => {
  const p = splitIsoDateTime(v)
  if (p.date && joinIsoDateTime(date.value, time.value) !== v) { date.value = p.date; time.value = p.time }
  if (!v) { date.value = ''; time.value = '' }
})
function push() { emit('update:modelValue', joinIsoDateTime(date.value, time.value) ?? `${date.value.trim()}|${time.value.trim()}`) }
</script>

<template>
  <div class="dt" role="group" :aria-labelledby="`${inputId}-label`">
    <div class="dt-part">
      <label :for="`${inputId}-date`" class="sub">Date</label>
      <input :id="`${inputId}-date`" v-model="date" type="text" autocomplete="off" maxlength="10"
        :placeholder="DATE_PLACEHOLDER" :aria-invalid="invalid" :aria-describedby="[`${inputId}-hint`, describedby].filter(Boolean).join(' ')" @input="push" />
    </div>
    <div class="dt-part">
      <label :for="`${inputId}-time`" class="sub">Time</label>
      <input :id="`${inputId}-time`" v-model="time" type="text" autocomplete="off" maxlength="12"
        :placeholder="TIME_PLACEHOLDER" :aria-invalid="invalid" :aria-describedby="[`${inputId}-hint`, describedby].filter(Boolean).join(' ')" @input="push" />
    </div>
    <p :id="`${inputId}-hint`" class="hint">Example: {{ DATE_EXAMPLE }} and {{ TIME_EXAMPLE }}.</p>
  </div>
</template>

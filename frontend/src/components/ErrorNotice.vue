<script setup lang="ts">
import { computed } from 'vue'
import { isRetryable, userMessage } from '@/api/errors'

const props = defineProps<{ error: unknown; retryLabel?: string }>()
const emit = defineEmits<{ retry: [] }>()
const canRetry = computed(() => isRetryable(props.error))
</script>

<template>
  <div v-if="error" class="notice err" role="alert">
    <span>{{ userMessage(error) }}</span>
    <button v-if="canRetry" class="btn sm secondary retry" type="button" @click="emit('retry')">{{ retryLabel ?? 'Try again' }}</button>
  </div>
</template>

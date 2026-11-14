<script setup lang="ts">
import { userMessage } from '@/api/errors'
defineProps<{ error: unknown }>()
</script>
<template>
  <div v-if="error" class="notice err" role="alert">{{ userMessage(error) }}</div>
</template>

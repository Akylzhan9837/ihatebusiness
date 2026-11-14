<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { BRAND, USE_MOCK } from '@/config'

const route = useRoute()
const isHome = computed(() => route.path === '/')
</script>

<template>
  <a class="skip" href="#main">Skip to content</a>
  <div v-if="USE_MOCK" class="devbar" role="status">DEV MOCK DATA — not a real backend result</div>
  <div class="strip">Demo — synthetic documents only. Not a government website.</div>
  <header class="nav">
    <router-link to="/" class="brand">{{ BRAND }}</router-link>
    <nav class="nav-links" aria-label="Main">
      <router-link v-if="isHome" :to="{ path: '/', hash: '#how' }" class="nav-link">How it works</router-link>
      <router-link v-if="isHome" :to="{ path: '/', hash: '#what' }" class="nav-link">What you get</router-link>
      <router-link v-if="isHome" :to="{ path: '/', hash: '#pricing' }" class="nav-link">Pricing</router-link>
      <router-link to="/new" class="btn sm">Check my ticket <span aria-hidden="true">↗</span></router-link>
    </nav>
  </header>
  <main id="main" tabindex="-1" :class="{ wide: isHome }"><router-view /></main>
  <footer class="site-foot">
    <div class="foot-inner">
      <div>
        <div class="brand">{{ BRAND }}</div>
        <p class="foot-tag">Help with civil and traffic notices.</p>
      </div>
      <p class="foot-legal">
        {{ BRAND }} is independent. It helps you organize your facts and prepare a statement for your own review.
        Filing and deadlines are your responsibility. This demo accepts synthetic documents only.
      </p>
    </div>
  </footer>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { scrollToSection } from '@/lib/scroll'
import { BRAND, USE_MOCK } from '@/config'

const route = useRoute()
const isHome = computed(() => route.name === 'home')
</script>

<template>
  <a class="skip" href="#main">Skip to content</a>
  <div v-if="USE_MOCK" class="devbar" role="status">DEV MOCK DATA — not a real backend result</div>
  <div class="strip">Demo — synthetic documents only. Not a government website.</div>
  <header class="nav">
    <router-link to="/" class="brand">{{ BRAND }}</router-link>
    <nav class="nav-links" aria-label="Main">
      <a v-if="isHome" href="#how" class="nav-link" @click.prevent="scrollToSection('how')">How it works</a>
      <a v-if="isHome" href="#what" class="nav-link" @click.prevent="scrollToSection('what')">What you get</a>
      <a v-if="isHome" href="#pricing" class="nav-link" @click.prevent="scrollToSection('pricing')">Pricing</a>
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

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
  <main id="main" tabindex="-1" :class="{ wide: isHome }">
    <router-view v-slot="{ Component }">
      <Transition name="page" mode="out-in">
        <component :is="Component" :key="route.params.id || route.matched[0]?.path" />
      </Transition>
    </router-view>
  </main>
  <footer class="site-foot">
    <div class="foot-inner">
      <div>
        <router-link to="/" class="brand">{{ BRAND }}</router-link>
        <p class="foot-tag">Understand your ticket.<br />Prepare your next step.</p>
      </div>
      <nav class="foot-links" aria-label="Explore Ticky">
        <h2>Explore</h2>
        <router-link to="/#how">How it works</router-link>
        <router-link to="/#pricing">Pricing</router-link>
        <router-link to="/new">Check my ticket</router-link>
      </nav>
      <div class="foot-note">
        <h2>Your case, at your pace</h2>
        <p>Save your private case link to return, add evidence, or edit your statement. You can delete your case and uploaded files from your case page.</p>
      </div>
    </div>
    <div class="foot-bottom">
      <p class="foot-legal">{{ BRAND }} is an independent document preparation service. You review and submit your own appeal. Dismissal is not guaranteed.</p>
      <span>Synthetic documents only · Demo access</span>
    </div>
  </footer>
</template>

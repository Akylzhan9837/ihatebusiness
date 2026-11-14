<script setup lang="ts">
const steps = [
  { title: 'Choose the state', text: 'Select where the notice was issued. Upload a synthetic PDF or image, or enter the details yourself.' },
  { title: 'Confirm what happened', text: 'Check the ticket number, issuing authority, and type of violation. Add your account in your own words.' },
  { title: 'Prepare your response', text: 'Review the official resources we found, then edit, save, or download your statement as a PDF.' },
]
</script>

<template>
  <div>
    <section class="hero">
      <div class="lp-wrap hero-grid">
        <div>
          <h1>Understand your ticket.<br />Prepare your response.</h1>
          <p class="lede">Ticky helps you organize the details, find official filing resources, and put your account of what happened into a statement you can review and download.</p>
          <div class="row">
            <router-link to="/new" class="btn">Check my ticket <span aria-hidden="true">↗</span></router-link>
            <router-link :to="{ path: '/', hash: '#how' }" class="btn dark">How it works</router-link>
          </div>
        </div>
        <div class="dash ticket-preview">
          <div class="dash-bar"><span>Example case</span><span>SYNTHETIC NOTICE</span></div>
          <div class="preview-body">
            <h2>New York City camera violation</h2>
            <dl class="preview-facts">
              <div><dt>State of issuance</dt><dd>New York</dd></div>
              <div><dt>Issuing authority</dt><dd>NYC Department of Finance</dd></div>
              <div><dt>Notice number</dt><dd>0000000012</dd></div>
            </dl>
            <div class="preview-next">
              <strong>Where to check filing instructions</strong>
              <span>NYC Department of Finance hearing options</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section id="how" class="lp-sec">
      <div class="lp-wrap">
        <h2 class="lp-h2">How it works</h2>
        <div class="cols3">
          <div v-for="step in steps" :key="step.title" class="step">
            <h3>{{ step.title }}</h3>
            <p>{{ step.text }}</p>
          </div>
        </div>
      </div>
    </section>

    <section id="what" class="lp-sec alt">
      <div class="lp-wrap">
        <h2 class="lp-h2">What you can review</h2>
        <div class="cols2">
          <div class="feat">
            <h3>Civil and traffic notices across the U.S.</h3>
            <p>Choose any state or DC. Get a factual statement and official filing resources where available. Verify the process and deadline on your notice before filing.</p>
          </div>
          <div class="feat">
            <h3>NYC parking paid with ParkNYC</h3>
            <p>For NYC Department of Finance code 38, Ticky can check whether your confirmed parking session matches the ticket details and include your receipt in the evidence checklist.</p>
          </div>
        </div>
      </div>
    </section>

    <section id="pricing" class="lp-sec">
      <div class="lp-wrap">
        <h2 class="lp-h2">Try the demo for free</h2>
        <p class="lp-lead">Review, draft, and PDF export are free in the demo. The $19 price shown for draft preparation is a test price. You submit the statement yourself.</p>
        <router-link to="/new" class="btn">Start a case</router-link>
      </div>
    </section>
  </div>
</template>

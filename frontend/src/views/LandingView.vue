<script setup lang="ts">
import { BRAND, PRICE_MONTHLY, PRICE_YEARLY, YEARLY_SAVING } from '@/config'
import { scrollToSection } from '@/lib/scroll'

const steps = [
  { n: '01', t: 'Upload or enter your ticket', d: 'Upload a PDF, JPG or PNG, or type the details in by hand. Either way, you check every field yourself.' },
  { n: '02', t: 'Review the findings', d: 'See what your ticket says, what we could verify against official sources, and what is still needed.' },
  { n: '03', t: 'Prepare your dispute', d: 'If a supported ground is found, you can get an editable draft and filing instructions. You submit it yourself.' },
]
const sections = [
  { h: 'What your ticket says', d: 'The details we read from your document, shown for you to confirm.' },
  { h: 'What we could verify', d: 'Facts checked against official sources.' },
  { h: 'Information still needed', d: 'Anything missing that could change the review.' },
  { h: 'Issues to review', d: 'Each with an explanation, supporting facts and the limits of the finding.' },
  { h: 'Official sources', d: 'Links to the pages the review relies on.' },
  { h: 'Suggested next steps', d: 'Plain-English options. You decide what to do.' },
]
const features = [
  { n: '01 / TICKET DETAILS', h: 'Ticket details', d: 'Understand your ticket, the alleged violation, and the details that matter.', c: 'TICKET READ  →  DETAILS ORGANIZED' },
  { n: '02 / ISSUES TO REVIEW', h: 'Issues to review', d: 'Spot possible omissions and inconsistencies worth checking against the original.', c: 'REVIEW NEEDED  /  EXPLAINED' },
  { n: '03 / EDITABLE DRAFT', h: 'Editable draft', d: 'When a supported ground is found, start with a draft based on your facts and edit it yourself.', c: 'YOUR FACTS  →  YOUR DRAFT' },
  { n: '04 / OFFICIAL SOURCES', h: 'Official sources', d: 'See the references behind each finding and where to file, in plain English.', c: 'SOURCE-LINKED  /  PLAIN-LANGUAGE' },
]
const principles = [
  { n: '01', h: 'Not a government service', d: 'Independent from the NYC Department of Finance.' },
  { n: '02', h: 'Demo: synthetic documents only', d: 'Please do not upload real tickets or personal documents.' },
  { n: '03', h: 'You file it yourself', d: 'Nothing is ever submitted on your behalf.' },
]
</script>

<template>
  <div>
    <!-- Hero -->
    <section class="hero">
      <div class="lp-wrap">
        <div class="hero-grid">
          <div>
            <div class="pill"><span aria-hidden="true">✦</span> YOUR TICKET. YOUR OPTIONS.</div>
            <h1>Got a ticket?<br />Let's look closer.</h1>
            <p class="lede">Understand your NYC road fine, whether it is for parking, speeding, a red light or something else, and prepare a clear dispute. Upload your ticket or enter its details by hand, and we'll check them against official sources and show what is still needed.</p>
            <div class="row">
              <router-link to="/new" class="btn">Check my ticket <span aria-hidden="true">↗</span></router-link>
              <router-link :to="{ name: 'new', query: { mode: 'manual' } }" class="btn dark">Enter details manually</router-link>
              <a href="#how" class="btn dark" @click.prevent="scrollToSection('how')">How it works</a>
            </div>
            <p class="fine">Free initial review · Demo: no payment is taken · Parking, speeding, red-light, bus-lane and other road fines</p>
          </div>

          <div class="dash" role="img" aria-label="Illustrative example of a ticket review. Not a real case.">
            <div class="dash-bar"><span>{{ BRAND }} / Ticket review</span><span>ILLUSTRATIVE EXAMPLE</span></div>
            <div class="dash-body" aria-hidden="true">
              <div class="doc">
                <div class="t1">NEW YORK CITY</div>
                <div class="t2">VIOLATION NOTICE</div>
                <div class="note">SAMPLE · NOT A REAL TICKET</div>
                <hr />
                <div><div class="k">SUMMONS NO.</div><div class="v">0000000000</div></div>
                <div><div class="k">DATE / TIME</div><div class="v">Mar 4, 2026 · 9:15 AM</div></div>
                <div><div class="k">LOCATION</div><div class="v">Example St near 1st Ave</div></div>
                <div><div class="k">FINE</div><div class="v">$115.00</div></div>
              </div>
              <div class="finds">
                <h3>2 items to confirm</h3>
                <div class="find"><div class="n">01 / DETAIL TO CHECK</div><div class="h">Location is hard to read</div><p class="d">Compare with your original ticket.</p></div>
                <div class="find"><div class="n">02 / INFORMATION NEEDED</div><div class="h">Photos or receipts</div><p class="d">Add anything that shows what happened.</p></div>
                <p class="dash-note">Illustrative only. Not a prediction of any outcome.</p>
              </div>
            </div>
            <div class="dash-foot" aria-hidden="true"><span>✓ You confirm every detail</span><span>Sources shown with each finding</span></div>
          </div>
        </div>
        <div class="assure">
          <b>SCOPE</b><span>NYC road fines: parking, speeding, red light and more</span><span>Clear explanations, not promises</span><span>You file the dispute yourself</span>
        </div>
      </div>
    </section>

    <!-- How it works -->
    <section id="how" class="lp-sec">
      <div class="lp-wrap">
        <p class="eyebrow">01 / How it works</p>
        <h2 class="lp-h2">A clear path forward.</h2>
        <p class="lp-lead">Less guesswork. More clarity on what to do next.</p>
        <div class="cols3">
          <div v-for="s in steps" :key="s.n" class="step"><div class="no">{{ s.n }}</div><h3>{{ s.t }}</h3><p>{{ s.d }}</p></div>
        </div>
      </div>
    </section>

    <!-- Inside the review -->
    <section class="lp-sec alt">
      <div class="lp-wrap">
        <p class="eyebrow">02 / Inside the review</p>
        <h2 class="lp-h2">See what your ticket isn't telling you.</h2>
        <p class="lp-lead">Your ticket on one side. A source-linked review on the other.</p>
        <div class="demo">
          <div class="demo-bar"><span>{{ BRAND }} / Your case workspace</span><span>ILLUSTRATIVE EXAMPLE</span></div>
          <div class="demo-grid">
            <div class="demo-doc" aria-hidden="true">
              <div class="lbl">SAMPLE TICKET</div>
              <div class="doc">
                <div class="t1">NEW YORK CITY</div><div class="t2">VIOLATION NOTICE</div><div class="note">SAMPLE · NOT A REAL TICKET</div><hr />
                <div><div class="k">SUMMONS NO.</div><div class="v">0000000000</div></div>
                <div><div class="k">DATE / TIME</div><div class="v">Mar 4, 2026 · 9:15 AM</div></div>
                <div><div class="k">LOCATION</div><div class="v">Example St near 1st Ave</div></div>
                <div><div class="k">FINE</div><div class="v">$115.00</div></div>
                <hr /><div class="note">Sample document for demonstration only.</div>
              </div>
              <p class="cap">Original document preserved</p>
            </div>
            <div class="report">
              <h3>What the review covers</h3>
              <p class="sub">These sections help you evaluate your options. They do not establish a defense or guarantee dismissal.</p>
              <div v-for="(s, i) in sections" :key="s.h" class="rep-item">
                <div class="n">0{{ i + 1 }} / SECTION</div><div class="h">{{ s.h }}</div><p class="d">{{ s.d }}</p>
              </div>
              <div class="next"><div class="n">YOUR NEXT STEP</div><div class="h">Check the details. Gather supporting evidence.</div><p class="d">Then decide whether to prepare a dispute.</p></div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Features -->
    <section id="what" class="lp-sec">
      <div class="lp-wrap">
        <p class="eyebrow">03 / What you get</p>
        <h2 class="lp-h2">A little structure.<br />A lot more clarity.</h2>
        <p class="lp-lead">Tools that turn a confusing ticket into an informed decision.</p>
        <div class="cols2">
          <div v-for="f in features" :key="f.h" class="feat"><div class="n">{{ f.n }}</div><h3>{{ f.h }}</h3><p>{{ f.d }}</p><div class="cap">{{ f.c }}</div></div>
        </div>
      </div>
    </section>

    <!-- Trust -->
    <section class="lp-sec dark">
      <div class="lp-wrap">
        <div class="trust-lead">
          <div>
            <p class="eyebrow">04 / Clear about what this is</p>
            <h2 class="lp-h2">Information, not<br />promises.</h2>
            <p class="lp-lead" style="margin-bottom:0">You deserve to know what this service does and what it does not do.</p>
          </div>
          <div class="promise">
            <hr />
            <p class="big">Clarity over certainty.</p>
            <p>We show the finding, the reasoning and the source. You stay in control of the decision.</p>
            <small>No guaranteed outcomes. No hidden legal claims.</small>
          </div>
        </div>
        <div class="cols3">
          <div v-for="p in principles" :key="p.n" class="step"><div class="no">{{ p.n }}</div><h3>{{ p.h }}</h3><p>{{ p.d }}</p></div>
        </div>
      </div>
    </section>

    <!-- Pricing -->
    <section id="pricing" class="lp-sec">
      <div class="lp-wrap">
        <p class="eyebrow">05 / Simple, upfront pricing</p>
        <h2 class="lp-h2">Start with clarity.<br />Only pay for the next step.</h2>
        <p class="lp-lead">See your initial review for free. Then choose monthly or yearly if you want a dispute draft.</p>
        <div class="plans">
          <div class="plan">
            <div class="tag">START HERE</div><h3>Initial review</h3>
            <div class="price">$0<small>free</small></div>
            <p class="muted small" style="margin:0">Know what you're looking at before you decide anything.</p>
            <ul><li>Ticket upload or manual entry</li><li>Initial review</li><li>Issues to review, clearly explained</li><li>No card required</li></ul>
            <router-link to="/new" class="btn dark">Check my ticket <span aria-hidden="true">↗</span></router-link>
            <p class="fine">No commitment to purchase.</p>
          </div>
          <div class="plan">
            <div class="tag">MONTHLY</div><h3>{{ BRAND }} Monthly</h3>
            <div class="price">${{ PRICE_MONTHLY }}<small>per month</small></div>
            <p class="muted small" style="margin:0">Pay month by month. Editable drafts that you submit yourself.</p>
            <ul><li>Everything in the free review</li><li>Editable dispute drafts</li><li>List of attachments</li><li>Filing instructions</li></ul>
            <router-link to="/new" class="btn dark">Start with a free review <span aria-hidden="true">↗</span></router-link>
            <p class="fine">Demo access — no payment charged. No guarantee of dismissal.</p>
          </div>
          <div class="plan pro">
            <div class="tag">BEST VALUE · SAVE ${{ YEARLY_SAVING }} A YEAR</div><h3>{{ BRAND }} Yearly</h3>
            <div class="price">${{ PRICE_YEARLY }}<small>per year</small></div>
            <p class="small" style="margin:0;color:var(--on-dark-2)">The full year for less than twelve monthly payments.</p>
            <ul><li>Everything in Monthly</li><li>Editable dispute drafts</li><li>List of attachments</li><li>Filing instructions</li></ul>
            <router-link to="/new" class="btn">Start with a free review <span aria-hidden="true">↗</span></router-link>
            <p class="fine">Demo access — no payment charged. Does not include automatic filing or any guarantee of dismissal.</p>
          </div>
        </div>
        <p class="muted small" style="margin-top:24px">Procedures may change. You remain responsible for deadlines, filing, and verifying all information.</p>
      </div>
    </section>

    <!-- Final CTA -->
    <section class="cta">
      <div class="lp-wrap">
        <p class="eyebrow">YOUR NEXT MOVE STARTS HERE</p>
        <h2>Don't just pay it.<br />Understand your options.</h2>
        <p>One upload. A clearer picture of what comes next.</p>
        <router-link to="/new" class="btn">Check my ticket <span aria-hidden="true">↗</span></router-link>
        <p class="fine">PDF, JPG or PNG, or enter it by hand · Free initial review · Synthetic documents only</p>
      </div>
    </section>
  </div>
</template>

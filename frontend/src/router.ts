import { createRouter, createWebHistory } from 'vue-router'

const UUID = '[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}'

export const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', name: 'home', component: () => import('./views/LandingView.vue') },
    { path: '/new', name: 'new', component: () => import('./views/UploadView.vue') },
    {
      // Ссылка на дело: /case/{id}#key={secret}. Фрагмент читает main.ts, роутер его не видит.
      path: `/case/:id(${UUID})`,
      component: () => import('./views/case/CaseShell.vue'),
      props: true,
      children: [
        { path: '', name: 'case-home', component: { render: () => null } }, // Shell перенаправит на нужный шаг
        { path: 'details', name: 'details', component: () => import('./views/case/DetailsView.vue') },
        { path: 'receipt', name: 'receipt', component: () => import('./views/case/ReceiptView.vue') },
        { path: 'report', name: 'report', component: () => import('./views/case/ReportView.vue') },
        { path: 'draft', name: 'draft', component: () => import('./views/case/DraftView.vue') },
      ],
    },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
  // Якоря лендинга (#how, #pricing) плавно скроллят к секции, остальные переходы — наверх.
  scrollBehavior: (to) => (to.hash ? { el: to.hash, top: 72, behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' } : { top: 0 }),
})

import { createRouter, createWebHistory } from 'vue-router'

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: () => import('./views/LandingView.vue') },
    { path: '/new', component: () => import('./views/UploadView.vue') },
    { path: '/cases/:id/details', component: () => import('./views/ReviewDetailsView.vue'), props: true },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
  // Якоря лендинга (#how, #pricing) скроллят к секции, остальные переходы — наверх.
  scrollBehavior: (to) => (to.hash ? { el: to.hash, top: 72 } : { top: 0 }),
})

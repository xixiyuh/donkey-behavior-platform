import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: () => import('../components/Detection.vue') },
    { path: '/detection', component: () => import('../components/Detection.vue') },
    { path: '/barns', component: () => import('../components/BarnManager.vue') },
    { path: '/pens', component: () => import('../components/PenManager.vue') },
    { path: '/cameras', component: () => import('../components/CameraManager.vue') },
    { path: '/camera-configs', component: () => import('../components/CameraConfigManager.vue') },
    { path: '/events', component: () => import('../components/EventRecord.vue') }
  ]
})

export default router

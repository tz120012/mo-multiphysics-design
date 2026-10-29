import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/LoginView.vue'),
    meta: { public: true },
  },
  {
    path: '/',
    component: () => import('@/layouts/AppLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        redirect: '/projects',
      },
      {
        path: 'projects',
        name: 'projects',
        component: () => import('@/views/ProjectListView.vue'),
      },
      {
        path: 'workspace',
        name: 'workspace',
        component: () => import('@/views/WorkspaceView.vue'),
      },
      {
        path: 'analytic',
        name: 'analytic',
        redirect: (to) => ({ name: 'workspace', query: { ...to.query, step: 'solve' } }),
      },
      {
        path: 'axial',
        name: 'axial',
        redirect: (to) => ({
          name: 'workspace',
          query: {
            ...to.query,
            step: 'geometry',
            topology: typeof to.query.topology === 'string' ? to.query.topology : 'AF',
            machineType: typeof to.query.machineType === 'string' ? to.query.machineType : 'PMSM',
          },
        }),
      },
      {
        path: 'field',
        name: 'field',
        redirect: (to) => ({ name: 'workspace', query: { ...to.query, step: 'post' } }),
      },
      {
        path: 'drive',
        name: 'drive',
        redirect: (to) => ({ name: 'workspace', query: { ...to.query, step: 'excitation' } }),
      },
      {
        path: 'compare',
        name: 'compare',
        redirect: (to) => ({ name: 'workspace', query: { ...to.query, step: 'post' } }),
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/projects',
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.meta.public) {
    if (auth.isAuthenticated && to.name === 'login') {
      return { name: 'projects' }
    }
    return true
  }
  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  return true
})

export default router

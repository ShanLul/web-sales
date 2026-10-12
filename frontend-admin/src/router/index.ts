import { createRouter, createWebHashHistory } from 'vue-router'

import AdminLayout from '../layouts/AdminLayout.vue'
import { useAuthStore } from '../stores/auth'

/**
 * 使用 hash 路由：Nginx 直接托管 dist 即可，无需 try_files 重写规则，
 * 与子系统保持一致，降低 2C2G 裸机部署的配置复杂度。
 */
const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/Login.vue'),
      meta: { public: true, title: '登录' },
    },
    {
      path: '/',
      component: AdminLayout,
      redirect: '/products',
      children: [
        {
          path: 'products',
          name: 'products',
          component: () => import('../views/ProductList.vue'),
          meta: { title: '商品管理', icon: 'package' },
        },
        {
          path: 'permission-templates',
          name: 'permission-templates',
          component: () => import('../views/PermissionTemplate.vue'),
          meta: { title: '权限模板', icon: 'shield' },
        },
        {
          path: 'temp-links',
          name: 'temp-links',
          component: () => import('../views/TempLinkList.vue'),
          meta: { title: '临时链接', icon: 'link' },
        },
        {
          path: 'orders',
          name: 'orders',
          component: () => import('../views/OrderList.vue'),
          meta: { title: '订单管理', icon: 'orders' },
        },
      ],
    },
    { path: '/:pathMatch(.*)*', redirect: '/products' },
  ],
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()

  if (to.meta.public) {
    return true
  }

  if (!auth.isLoggedIn) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }

  // 刷新后 admin 信息为空时补拉一次，避免顶部栏显示异常
  if (!auth.admin) {
    const restored = await auth.restore()
    if (!restored) {
      return { name: 'login', query: { redirect: to.fullPath } }
    }
  }

  return true
})

router.afterEach((to) => {
  const title = (to.meta.title as string) || ''
  document.title = title ? `${title} · 销售管理后台` : '销售管理后台'
})

export default router

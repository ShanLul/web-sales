import { createRouter, createWebHashHistory } from 'vue-router'

/**
 * hash 路由：Nginx 只需托管静态产物即可，无需 try_files 重写。
 * 链接形如 {PUBLIC_BASE_URL}/portal/#/order?t={token}。
 */
const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/', redirect: '/order' },
    {
      path: '/order',
      name: 'order',
      component: () => import('../views/ProductBrowse.vue'),
      meta: { title: '选购商品' },
    },
    {
      path: '/checkout',
      name: 'checkout',
      component: () => import('../views/Checkout.vue'),
      meta: { title: '填写收货信息' },
    },
    {
      path: '/result',
      name: 'result',
      component: () => import('../views/Result.vue'),
      meta: { title: '提交结果' },
    },
    { path: '/:pathMatch(.*)*', redirect: '/order' },
  ],
})

router.afterEach((to) => {
  const title = (to.meta.title as string) || ''
  document.title = title ? `${title} · 在线下单` : '在线下单'
})

export default router

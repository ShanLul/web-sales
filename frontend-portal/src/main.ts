import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import './index.css'

const app = createApp(App)

app.use(createPinia())
app.use(router)

// 这里刻意不 app.use(TDesignMobile) 全量注册：
// 全量注册会把整个移动端组件库的 JS 与 CSS 都打进产物（约 700KB JS / 250KB CSS），
// 对首屏敏感的 H5 页面代价太大。页面只用到 Toast，按需从子路径引入即可，
// 对应样式会随该模块一起被引入（见 views/Checkout.vue）。
app.mount('#app')

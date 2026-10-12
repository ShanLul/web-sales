import { fileURLToPath, URL } from 'node:url'

import vue from '@vitejs/plugin-vue'
import { defineConfig, loadEnv } from 'vite'

// 生产构建产物部署在 Nginx 的 /portal/ 子路径下，开发环境保持根路径
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')

  return {
    base: env.VITE_BASE || '/',
    plugins: [vue()],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
      },
    },
    server: {
      host: '0.0.0.0',
      port: 5174,
      allowedHosts: true,
      proxy: {
        '/api': {
          target: 'http://127.0.0.1:8000',
          changeOrigin: true,
        },
      },
    },
    build: {
      outDir: 'dist',
      chunkSizeWarningLimit: 1200,
      rollupOptions: {
        output: {
          // 移动端首屏体积敏感：把体积大且几乎不随业务变动的依赖单独拆包，
          // 发版后用户可命中浏览器缓存，只重新下载业务 chunk。
          // 注意不要把 tdesign-mobile-vue 写进来：它会被解析为包入口，
          // 等于强制引入整个组件库的 JS 与 CSS，与按需引入的初衷相违背。
          manualChunks: {
            'vendor-vue': ['vue', 'vue-router', 'pinia'],
            'vendor-utils': ['axios'],
          },
        },
      },
    },
  }
})

<template>
  <div class="flex min-h-screen w-full bg-white">
    <!-- 左侧品牌区 -->
    <section class="relative hidden flex-1 overflow-hidden bg-ink lg:flex">
      <div class="grid-texture absolute inset-0 opacity-70" />
      <div class="absolute -left-24 top-10 h-80 w-80 rounded-full bg-brand/35 blur-3xl animate-drift" />
      <div class="absolute bottom-0 right-0 h-96 w-96 rounded-full bg-brand-light/25 blur-3xl animate-drift [animation-delay:2s]" />
      <div class="absolute left-1/2 top-1/2 h-56 w-56 -translate-x-1/2 -translate-y-1/2 rounded-full bg-white/[0.04] blur-2xl" />

      <div class="relative z-10 flex w-full flex-col justify-between p-14">
        <div class="flex items-center gap-3">
          <div class="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-brand-light to-brand shadow-float">
            <Store class="h-5 w-5 text-white" />
          </div>
          <div>
            <p class="text-[17px] font-semibold leading-6 text-white">销售管理后台</p>
            <p class="text-[12px] leading-5 text-white/45">web-sales console</p>
          </div>
        </div>

        <div class="max-w-lg">
          <h1 class="text-[42px] font-semibold leading-[52px] text-white">
            一套系统
            <span class="bg-gradient-to-r from-[#7FB2FF] to-[#B7D4FF] bg-clip-text text-transparent">
              管好每一次对外报价
            </span>
          </h1>
          <p class="mt-6 text-[15px] leading-7 text-white/60">
            集中维护商品与权限模板，按需生成带有效期与可用次数约束的临时链接，
            外部客户无需注册即可下单，订单回流后台统一流转与导出。
          </p>

          <div class="mt-10 grid grid-cols-3 gap-4">
            <div v-for="stat in stats" :key="stat.label" class="rounded-xl border border-white/10 bg-white/[0.05] p-4 backdrop-blur-sm">
              <p class="text-[24px] font-semibold leading-8 text-white">{{ stat.value }}</p>
              <p class="mt-1 text-[12px] leading-5 text-white/50">{{ stat.label }}</p>
            </div>
          </div>
        </div>

        <p class="text-[12px] leading-5 text-white/35">
          © {{ year }} web-sales · 临时链接下单平台
        </p>
      </div>
    </section>

    <!-- 右侧登录卡 -->
    <section class="flex w-full flex-col items-center justify-center px-6 py-12 lg:w-[520px] lg:px-14">
      <div class="w-full max-w-[380px] animate-fade-up">
        <div class="mb-8 flex items-center gap-3 lg:hidden">
          <div class="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-brand-light to-brand">
            <Store class="h-5 w-5 text-white" />
          </div>
          <p class="text-[17px] font-semibold text-ink">销售管理后台</p>
        </div>

        <h2 class="text-[28px] font-semibold leading-9 text-ink">欢迎回来</h2>
        <p class="mt-2 text-[14px] leading-6 text-ink-muted">请使用管理员账号登录，管理商品、链接与订单</p>

        <form class="mt-9 space-y-5" :class="{ 'animate-shake': shake }" @submit.prevent="submit">
          <div>
            <label class="mb-2 block text-[13px] font-medium text-ink" for="username">管理员账号</label>
            <div class="relative">
              <UserRound class="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-muted/70" />
              <input
                id="username"
                v-model.trim="form.username"
                type="text"
                autocomplete="username"
                placeholder="请输入管理员账号"
                class="h-11 w-full rounded-lg border bg-white pl-10 pr-3 text-[14px] text-ink outline-none transition-all duration-200 placeholder:text-ink-muted/50 focus:ring-4"
                :class="
                  error
                    ? 'border-danger focus:border-danger focus:ring-danger/10'
                    : 'border-black/10 hover:border-brand/40 focus:border-brand focus:ring-brand/10'
                "
              />
            </div>
          </div>

          <div>
            <label class="mb-2 block text-[13px] font-medium text-ink" for="password">登录密码</label>
            <div class="relative">
              <Lock class="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-muted/70" />
              <input
                id="password"
                v-model="form.password"
                :type="showPassword ? 'text' : 'password'"
                autocomplete="current-password"
                placeholder="请输入登录密码"
                class="h-11 w-full rounded-lg border bg-white pl-10 pr-11 text-[14px] text-ink outline-none transition-all duration-200 placeholder:text-ink-muted/50 focus:ring-4"
                :class="
                  error
                    ? 'border-danger focus:border-danger focus:ring-danger/10'
                    : 'border-black/10 hover:border-brand/40 focus:border-brand focus:ring-brand/10'
                "
              />
              <button
                type="button"
                class="absolute right-2 top-1/2 flex h-8 w-8 -translate-y-1/2 cursor-pointer items-center justify-center rounded-md text-ink-muted transition-colors hover:bg-black/[0.04] hover:text-ink"
                :aria-label="showPassword ? '隐藏密码' : '显示密码'"
                @click="showPassword = !showPassword"
              >
                <EyeOff v-if="showPassword" class="h-4 w-4" />
                <Eye v-else class="h-4 w-4" />
              </button>
            </div>
          </div>

          <div class="flex items-center justify-between">
            <label class="flex cursor-pointer select-none items-center gap-2 text-[13px] text-ink-muted">
              <input v-model="remember" type="checkbox" class="h-4 w-4 cursor-pointer accent-[#0052D9]" />
              记住账号
            </label>
            <span class="text-[13px] text-ink-muted/70">忘记密码请联系系统管理员</span>
          </div>

          <p v-if="error" class="flex items-center gap-1.5 text-[13px] leading-5 text-danger">
            <AlertCircle class="h-4 w-4 shrink-0" />
            {{ error }}
          </p>

          <button
            type="submit"
            :disabled="auth.loading"
            class="flex h-11 w-full items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-brand to-brand-light text-[15px] font-medium text-white shadow-float transition-all duration-200 hover:brightness-110 active:scale-[0.99] disabled:cursor-not-allowed disabled:opacity-60"
          >
            <Loader2 v-if="auth.loading" class="h-4 w-4 animate-spin" />
            {{ auth.loading ? '登录中…' : '登 录' }}
          </button>
        </form>

        <div class="mt-8 rounded-lg border border-dashed border-black/10 bg-[#FAFBFC] p-3.5">
          <p class="text-[12px] leading-5 text-ink-muted">
            初始账号 <span class="font-medium text-ink">admin</span> / 初始密码
            <span class="font-medium text-ink">admin123</span>，登录后请尽快修改。
          </p>
        </div>

        <p class="mt-8 text-center text-[12px] leading-5 text-ink-muted/60">
          © {{ year }} web-sales · v1.0.0
        </p>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { MessagePlugin } from 'tdesign-vue-next'
import { AlertCircle, Eye, EyeOff, Loader2, Lock, Store, UserRound } from 'lucide-vue-next'

import { useAuthStore } from '../stores/auth'

const REMEMBER_KEY = 'web-sales-admin-remember'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const year = new Date().getFullYear()
const form = reactive({ username: '', password: '' })
const remember = ref(true)
const showPassword = ref(false)
const error = ref('')
const shake = ref(false)

const stats = [
  { value: '5', label: '核心管理模块' },
  { value: '2', label: '独立前端站点' },
  { value: '2C2G', label: '目标部署规格' },
]

onMounted(() => {
  const saved = localStorage.getItem(REMEMBER_KEY)
  if (saved) {
    form.username = saved
  }
})

function fail(message: string) {
  error.value = message
  shake.value = true
  window.setTimeout(() => (shake.value = false), 420)
}

async function submit() {
  error.value = ''
  if (!form.username) {
    fail('请输入管理员账号')
    return
  }
  if (!form.password) {
    fail('请输入登录密码')
    return
  }

  try {
    const admin = await auth.login(form.username, form.password)
    if (remember.value) {
      localStorage.setItem(REMEMBER_KEY, form.username)
    } else {
      localStorage.removeItem(REMEMBER_KEY)
    }
    MessagePlugin.success(`欢迎回来，${admin.name || admin.username}`)
    const redirect = (route.query.redirect as string) || '/products'
    router.replace(redirect)
  } catch (err) {
    console.error('登录失败', err)
    fail('账号或密码错误，请重新输入')
  }
}
</script>

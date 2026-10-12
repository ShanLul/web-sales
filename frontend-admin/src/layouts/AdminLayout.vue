<template>
  <div class="flex h-screen w-full overflow-hidden bg-[#F3F3F3]">
    <!-- 左侧深色导航 -->
    <aside
      class="relative flex shrink-0 flex-col bg-ink transition-[width] duration-300 ease-out"
      :class="collapsed ? 'w-[72px]' : 'w-[236px]'"
    >
      <div class="grid-texture pointer-events-none absolute inset-0 opacity-60" />
      <div class="pointer-events-none absolute -left-16 top-1/3 h-52 w-52 rounded-full bg-brand/25 blur-3xl" />

      <div class="relative flex h-16 items-center gap-3 px-5">
        <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-brand-light to-brand shadow-float">
          <Store class="h-[18px] w-[18px] text-white" />
        </div>
        <div v-if="!collapsed" class="min-w-0 animate-fade-up">
          <p class="truncate text-[15px] font-semibold leading-5 text-white">销售管理后台</p>
          <p class="truncate text-[11px] leading-4 text-white/45">web-sales console</p>
        </div>
      </div>

      <nav class="relative mt-2 flex-1 space-y-1 px-3">
        <router-link
          v-for="item in navItems"
          :key="item.name"
          :to="{ name: item.name }"
          class="group flex h-11 items-center gap-3 rounded-lg px-3 text-[14px] transition-all duration-200"
          :class="
            isActive(item.name)
              ? 'bg-gradient-to-r from-brand to-brand-light font-medium text-white shadow-float'
              : 'text-white/70 hover:bg-white/[0.08] hover:text-white'
          "
          :title="collapsed ? item.title : undefined"
        >
          <component :is="item.icon" class="h-[18px] w-[18px] shrink-0" />
          <span v-if="!collapsed" class="truncate">{{ item.title }}</span>
        </router-link>
      </nav>

      <div class="relative p-3">
        <button
          type="button"
          class="flex h-10 w-full cursor-pointer items-center gap-3 rounded-lg px-3 text-[13px] text-white/55 transition-colors hover:bg-white/[0.08] hover:text-white"
          @click="collapsed = !collapsed"
        >
          <PanelLeftClose v-if="!collapsed" class="h-[18px] w-[18px]" />
          <PanelLeftOpen v-else class="h-[18px] w-[18px]" />
          <span v-if="!collapsed">收起导航</span>
        </button>
      </div>
    </aside>

    <!-- 右侧工作区 -->
    <div class="flex min-w-0 flex-1 flex-col">
      <header class="flex h-16 shrink-0 items-center justify-between border-b border-black/[0.06] bg-white px-6">
        <div class="flex min-w-0 items-center gap-3">
          <h1 class="truncate text-[18px] font-medium leading-7 text-ink">{{ currentTitle }}</h1>
          <span class="hidden rounded-full bg-brand-soft px-2.5 py-0.5 text-[12px] leading-5 text-brand lg:inline">
            {{ currentHint }}
          </span>
        </div>

        <div class="flex items-center gap-4">
          <span class="hidden text-[13px] text-ink-muted xl:inline">{{ today }}</span>
          <t-dropdown :options="menuOptions" trigger="click" @click="onMenuClick">
            <button
              type="button"
              class="flex cursor-pointer items-center gap-2.5 rounded-full border border-black/[0.06] py-1 pl-1 pr-3 transition-colors hover:border-brand/30 hover:bg-brand-soft/60"
            >
              <span class="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-brand to-brand-light text-[13px] font-medium text-white">
                {{ auth.initial }}
              </span>
              <span class="text-[13px] text-ink">{{ auth.displayName }}</span>
              <ChevronDown class="h-4 w-4 text-ink-muted" />
            </button>
          </t-dropdown>
        </div>
      </header>

      <main class="min-w-0 flex-1 overflow-y-auto p-6">
        <router-view v-slot="{ Component }">
          <transition
            enter-active-class="transition duration-300 ease-out"
            enter-from-class="opacity-0 translate-y-2"
            leave-active-class="transition duration-150 ease-in"
            leave-to-class="opacity-0"
            mode="out-in"
          >
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { DialogPlugin, MessagePlugin } from 'tdesign-vue-next'
import {
  ChevronDown,
  ClipboardList,
  Link2,
  LogOut,
  Package,
  PanelLeftClose,
  PanelLeftOpen,
  ShieldCheck,
  Store,
  UserRound,
} from 'lucide-vue-next'

import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const collapsed = ref(false)

const navItems = [
  { name: 'products', title: '商品管理', icon: Package },
  { name: 'permission-templates', title: '权限模板', icon: ShieldCheck },
  { name: 'temp-links', title: '临时链接', icon: Link2 },
  { name: 'orders', title: '订单管理', icon: ClipboardList },
]

const hints: Record<string, string> = {
  products: '维护在售商品与分类',
  'permission-templates': '定义链接可见的商品集合',
  'temp-links': '生成与管理对外下单链接',
  orders: '查看订单并推进状态流转',
}

const currentTitle = computed(() => (route.meta.title as string) || '商品管理')
const currentHint = computed(() => hints[String(route.name)] || '')

const today = computed(() =>
  new Date().toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' }),
)

const menuOptions = [
  { content: '账号信息', value: 'profile' },
  { content: '退出登录', value: 'logout' },
]

function isActive(name: string) {
  return route.name === name
}

function onMenuClick(data: { value: string }) {
  if (data.value === 'profile') {
    MessagePlugin.info(`当前账号：${auth.admin?.username ?? '-'}`)
    return
  }
  const dialog = DialogPlugin.confirm({
    header: '退出登录',
    body: '确认退出当前账号？退出后需要重新输入账号密码。',
    confirmBtn: '确认退出',
    cancelBtn: '再想想',
    theme: 'warning',
    onConfirm: () => {
      auth.logout()
      dialog.destroy()
      router.replace({ name: 'login' })
    },
  })
}
</script>

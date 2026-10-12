<template>
  <div class="flex flex-1 flex-col items-center justify-center px-8 py-16 text-center">
    <div
      class="flex h-20 w-20 items-center justify-center rounded-full animate-check-pop"
      :class="meta.bg"
    >
      <component :is="meta.icon" class="h-9 w-9" :class="meta.color" />
    </div>

    <h2 class="mt-6 text-[20px] font-semibold leading-7 text-ink">{{ meta.title }}</h2>
    <p class="mt-3 max-w-[300px] text-[14px] leading-6 text-black/50">{{ meta.description }}</p>

    <div v-if="message" class="mt-5 w-full max-w-[320px] rounded-xl border border-black/[0.06] bg-white p-3.5">
      <p class="text-[12px] leading-5 text-black/45">系统提示：{{ message }}</p>
    </div>

    <button
      type="button"
      class="mt-8 h-11 w-full max-w-[320px] cursor-pointer rounded-full bg-gradient-to-r from-brand to-brand-light text-[15px] font-medium text-white shadow-float transition-all active:scale-[0.98]"
      @click="emit('retry')"
    >
      重新加载
    </button>

    <p class="mt-6 text-[12px] leading-5 text-black/35">
      如需继续下单，请联系业务人员重新获取链接
    </p>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Ban, Clock, FileQuestion, LinkIcon, PackageX } from 'lucide-vue-next'

import type { FailureReason } from '../api/types'

const props = defineProps<{ reason: FailureReason; message?: string }>()
const emit = defineEmits<{ (event: 'retry'): void }>()

interface Meta {
  title: string
  description: string
  icon: unknown
  bg: string
  color: string
}

const META: Record<FailureReason, Meta> = {
  LINK_NOT_FOUND: {
    title: '链接不存在',
    description: '该链接可能已被删除或输入有误，请核对后重新打开。',
    icon: FileQuestion,
    bg: 'bg-black/[0.04]',
    color: 'text-black/40',
  },
  LINK_EXPIRED: {
    title: '链接已过期',
    description: '这条链接的有效期已结束，商品信息不再对外展示。',
    icon: Clock,
    bg: 'bg-warning/10',
    color: 'text-warning',
  },
  LINK_EXHAUSTED: {
    title: '可用次数已耗尽',
    description: '该链接的下单次数已经用完，无法继续提交订单。',
    icon: PackageX,
    bg: 'bg-danger/10',
    color: 'text-danger',
  },
  LINK_DISABLED: {
    title: '链接已停用',
    description: '业务人员已暂停这条链接的访问权限，暂时无法下单。',
    icon: Ban,
    bg: 'bg-black/[0.04]',
    color: 'text-black/40',
  },
  LINK_VOIDED: {
    title: '链接已作废',
    description: '这条链接已被永久作废，请向业务人员索取新链接。',
    icon: LinkIcon,
    bg: 'bg-black/[0.04]',
    color: 'text-black/40',
  },
  UNKNOWN: {
    title: '暂时无法打开',
    description: '页面加载出现问题，请检查网络后重试。',
    icon: FileQuestion,
    bg: 'bg-black/[0.04]',
    color: 'text-black/40',
  },
}

const meta = computed(() => META[props.reason] ?? META.UNKNOWN)
</script>

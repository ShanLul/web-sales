<template>
  <span
    class="inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-[12px] leading-5"
    :class="style.cls"
  >
    <span class="h-1.5 w-1.5 rounded-full" :class="style.dot" />
    {{ style.label }}
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

type Kind = 'link' | 'order' | 'product'

const props = defineProps<{
  kind: Kind
  value: string
  /** 后端已给出的中文标签，优先展示，保证前后端文案一致 */
  label?: string
}>()

interface Style {
  label: string
  cls: string
  dot: string
}

const LINK_STYLES: Record<string, Style> = {
  unused: { label: '未使用', cls: 'border-brand/20 bg-brand-soft text-brand', dot: 'bg-brand' },
  in_use: { label: '使用中', cls: 'border-success/25 bg-success/10 text-success', dot: 'bg-success' },
  expired: { label: '已过期', cls: 'border-warning/25 bg-warning/10 text-warning', dot: 'bg-warning' },
  exhausted: { label: '次数耗尽', cls: 'border-danger/25 bg-danger/10 text-danger', dot: 'bg-danger' },
  disabled: { label: '已禁用', cls: 'border-black/10 bg-black/[0.05] text-ink-muted', dot: 'bg-ink-muted' },
  voided: { label: '已作废', cls: 'border-black/10 bg-black/[0.05] text-ink-muted', dot: 'bg-ink-muted' },
}

const ORDER_STYLES: Record<string, Style> = {
  pending: { label: '待发货', cls: 'border-warning/25 bg-warning/10 text-warning', dot: 'bg-warning' },
  shipped: { label: '已发货', cls: 'border-brand/20 bg-brand-soft text-brand', dot: 'bg-brand' },
  completed: { label: '已完成', cls: 'border-success/25 bg-success/10 text-success', dot: 'bg-success' },
  cancelled: { label: '已取消', cls: 'border-black/10 bg-black/[0.05] text-ink-muted', dot: 'bg-ink-muted' },
}

const PRODUCT_STYLES: Record<string, Style> = {
  on_sale: { label: '上架中', cls: 'border-success/25 bg-success/10 text-success', dot: 'bg-success' },
  off_shelf: { label: '已下架', cls: 'border-black/10 bg-black/[0.05] text-ink-muted', dot: 'bg-ink-muted' },
}

const MAPS: Record<Kind, Record<string, Style>> = {
  link: LINK_STYLES,
  order: ORDER_STYLES,
  product: PRODUCT_STYLES,
}

const FALLBACK: Style = {
  label: '未知状态',
  cls: 'border-black/10 bg-black/[0.05] text-ink-muted',
  dot: 'bg-ink-muted',
}

const style = computed<Style>(() => {
  const found = MAPS[props.kind][props.value] ?? FALLBACK
  return props.label ? { ...found, label: props.label } : found
})
</script>

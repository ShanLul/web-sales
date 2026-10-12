<template>
  <article
    class="h5-card flex flex-col overflow-hidden transition-transform duration-300"
    :class="{ 'animate-pop': bumped }"
  >
    <div
      class="relative aspect-[4/3] w-full overflow-hidden bg-[#F3F3F3]"
      :class="hasVariants && 'cursor-pointer'"
      @click="openPicker"
    >
      <img
        v-if="coverUrl"
        :src="coverUrl"
        :alt="product.name"
        class="h-full w-full object-cover"
        loading="lazy"
      />
      <div v-else class="flex h-full w-full items-center justify-center text-black/20">
        <ImageOff class="h-7 w-7" />
      </div>
      <span
        v-if="product.category_name"
        class="absolute left-1.5 top-1.5 max-w-[calc(100%-3rem)] truncate rounded-full bg-black/45 px-2 py-0.5 text-[10px] leading-4 text-white backdrop-blur-sm"
      >
        {{ product.category_name }}
      </span>
      <span
        v-if="quantity > 0"
        class="num absolute right-1.5 top-1.5 flex h-5 min-w-5 items-center justify-center rounded-full bg-brand px-1 text-[11px] font-medium text-white shadow-float"
      >
        ×{{ quantity }}
      </span>
      <!-- 多规格商品不在列表里铺开规格，只给一个「有规格」的信号 -->
      <span
        v-if="hasVariants"
        class="absolute bottom-1.5 left-1.5 rounded-full bg-white/85 px-2 py-0.5 text-[10px] leading-4 text-brand backdrop-blur-sm"
      >
        {{ variantCount }} 种规格
      </span>
    </div>

    <div class="flex flex-1 flex-col p-2.5">
      <h3
        class="line-clamp-2 min-h-[36px] text-[13px] font-medium leading-[18px] text-ink"
        :class="hasVariants && 'cursor-pointer'"
        @click="openPicker"
      >
        {{ product.name }}
      </h3>

      <!-- 放不下时（数量选择器展开）自动换行，保证价格完整不被截断 -->
      <div class="mt-auto flex flex-wrap items-end gap-x-1.5 gap-y-1.5 pt-2">
        <p class="num whitespace-nowrap text-[15px] font-semibold leading-5 text-brand">
          ¥{{ product.price.toFixed(2) }}
          <span v-if="hasVariants" class="text-[10px] font-normal">起</span>
          <span v-else class="text-[10px] font-normal text-black/40">/{{ product.unit }}</span>
        </p>

        <!-- 无规格 / 已选定唯一规格：直接给步进器，避免为简单商品多一步弹层 -->
        <QtyStepper
          v-if="!hasVariants || activeVariantId !== null"
          compact
          class="ml-auto shrink-0"
          :quantity="hasVariants ? activeQuantity : quantity"
          @increase="onIncrease"
          @decrease="emit('decrease', product.id, activeVariantId)"
          @set="(value) => emit('set', product.id, activeVariantId, value)"
        />

        <button
          v-else
          type="button"
          class="ml-auto shrink-0 cursor-pointer rounded-full border border-brand/30 bg-brand-soft px-2.5 py-1 text-[11px] font-medium leading-4 text-brand transition-all active:scale-95"
          @click.stop="emit('select', product.id)"
        >
          {{ selectedCount > 1 ? `已选 ${selectedCount} 种` : '选规格' }}
        </button>
      </div>
    </div>
  </article>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { ImageOff } from 'lucide-vue-next'

import QtyStepper from './QtyStepper.vue'
import type { CatalogProduct } from '../api/types'

const props = defineProps<{
  product: CatalogProduct
  /** 该商品所有规格的合计数量，用于封面角标 */
  quantity: number
  /** 唯一已选规格的 id；未选或选了多种规格时为 null */
  activeVariantId: number | null
  /** 唯一已选规格的数量，用于步进器回显 */
  activeQuantity: number
  /** 已选规格种类数 */
  selectedCount: number
}>()

const emit = defineEmits<{
  (event: 'increase', id: number, variantId: number | null): void
  (event: 'decrease', id: number, variantId: number | null): void
  (event: 'set', id: number, variantId: number | null, value: number): void
  (event: 'select', id: number): void
}>()

const bumped = ref(false)

const hasVariants = computed(() => (props.product.variants?.length ?? 0) > 0)
const variantCount = computed(() => props.product.variants?.length ?? 0)

/** 选中规格自带图片时优先用它，让客户确认选的是哪一款 */
const coverUrl = computed(() => {
  const picked = (props.product.variants ?? []).find((item) => item.id === props.activeVariantId)
  return picked?.image_url || props.product.image_url || ''
})

/** 加入购物车时给卡片一次轻微弹动反馈，让操作有即时响应。 */
function onIncrease() {
  emit('increase', props.product.id, props.activeVariantId)
  bumped.value = true
  window.setTimeout(() => (bumped.value = false), 340)
}

/** 多规格商品点封面或标题即进入规格选择，减少一次精确点击 */
function openPicker() {
  if (!hasVariants.value) return
  emit('select', props.product.id)
}
</script>

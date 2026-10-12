<template>
  <Teleport to="body">
    <Transition name="variant-sheet">
      <div v-if="visible && product" class="fixed inset-0 z-50">
        <div class="absolute inset-0 bg-black/45" @click="close" />

        <section
          class="absolute inset-x-0 bottom-0 mx-auto w-full max-w-[430px] rounded-t-2xl bg-white pb-[calc(0.75rem+env(safe-area-inset-bottom))] shadow-[0_-8px_32px_rgba(0,21,41,0.18)]"
        >
          <div class="mx-auto mt-2.5 h-1 w-9 rounded-full bg-black/15" />

          <div class="flex items-start gap-3 px-4 pt-3">
            <div class="h-16 w-16 shrink-0 overflow-hidden rounded-xl bg-[#F3F3F3]">
              <img
                v-if="coverUrl"
                :src="coverUrl"
                :alt="product.name"
                class="h-full w-full object-cover"
              />
              <div v-else class="flex h-full w-full items-center justify-center text-black/20">
                <ImageOff class="h-5 w-5" />
              </div>
            </div>
            <div class="min-w-0 flex-1">
              <p class="line-clamp-2 text-[15px] font-medium leading-5 text-ink">
                {{ product.name }}
              </p>
              <p class="num mt-1.5 text-[17px] font-semibold leading-6 text-brand">
                ¥{{ currentPrice.toFixed(2) }}
              </p>
            </div>
            <button
              type="button"
              aria-label="关闭规格选择"
              class="flex h-8 w-8 shrink-0 cursor-pointer items-center justify-center rounded-full text-black/35 transition-colors active:bg-black/[0.05]"
              @click="close"
            >
              <X class="h-4 w-4" />
            </button>
          </div>

          <div class="mt-3 px-4">
            <p class="text-[13px] text-black/55">选择规格</p>
            <div class="mt-2 max-h-[36vh] space-y-2 overflow-y-auto pb-1">
              <button
                v-for="variant in variants"
                :key="variant.id"
                type="button"
                class="flex w-full cursor-pointer items-center justify-between gap-3 rounded-xl border px-3 py-2.5 text-left transition-all active:scale-[0.99]"
                :class="
                  variant.id === selectedId
                    ? 'border-brand bg-brand-soft'
                    : 'border-black/[0.08] bg-white'
                "
                @click="select(variant.id)"
              >
                <span class="flex min-w-0 items-center gap-2">
                  <span
                    class="flex h-4 w-4 shrink-0 items-center justify-center rounded-full border"
                    :class="variant.id === selectedId ? 'border-brand bg-brand' : 'border-black/20'"
                  >
                    <Check v-if="variant.id === selectedId" class="h-3 w-3 text-white" />
                  </span>
                  <span
                    class="truncate text-[13px]"
                    :class="variant.id === selectedId ? 'text-brand' : 'text-ink'"
                  >
                    {{ variant.name }}
                  </span>
                </span>
                <span
                  class="num shrink-0 text-[13px] font-medium"
                  :class="variant.id === selectedId ? 'text-brand' : 'text-ink'"
                >
                  ¥{{ variant.price.toFixed(2) }}
                </span>
              </button>
            </div>
          </div>

          <div
            class="mt-3 flex items-center justify-between gap-3 border-t border-black/[0.06] px-4 pt-3"
          >
            <span class="text-[13px] text-black/55">购买数量</span>
            <QtyStepper
              :quantity="quantity"
              @increase="quantity = Math.min(9999, quantity + 1)"
              @decrease="quantity = Math.max(1, quantity - 1)"
              @set="onSetQuantity"
            />
          </div>

          <div class="mt-3 px-4">
            <button
              type="button"
              :disabled="selectedId === null"
              class="h-11 w-full cursor-pointer rounded-full bg-gradient-to-r from-brand to-brand-light text-[15px] font-medium text-white shadow-float transition-all active:scale-[0.98] disabled:cursor-not-allowed disabled:from-black/20 disabled:to-black/20 disabled:shadow-none"
              @click="confirm"
            >
              加入选购
            </button>
          </div>
        </section>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, onUnmounted, ref, watch } from 'vue'
import { Check, ImageOff, X } from 'lucide-vue-next'

import QtyStepper from './QtyStepper.vue'
import { usePortalStore } from '../stores/portal'
import type { CatalogProduct } from '../api/types'

const props = defineProps<{ product: CatalogProduct | null; visible: boolean }>()
const emit = defineEmits<{ (event: 'close'): void }>()

const store = usePortalStore()
const selectedId = ref<number | null>(null)
const quantity = ref(1)

const variants = computed(() => props.product?.variants ?? [])
const selectedVariant = computed(
  () => variants.value.find((item) => item.id === selectedId.value) ?? null,
)
/** 规格自带图片时优先展示，让客户确认选中的是哪一款 */
const coverUrl = computed(() => selectedVariant.value?.image_url || props.product?.image_url || '')
const currentPrice = computed(() => selectedVariant.value?.price ?? props.product?.price ?? 0)

/** 打开时默认定位到购物车里数量最多的那个规格，方便直接改数量而不是重选。 */
watch(
  () => [props.visible, props.product?.id] as const,
  () => {
    const product = props.product
    if (!props.visible || !product) return
    const list = product.variants ?? []
    let bestId: number | null = null
    let bestQuantity = 0
    for (const variant of list) {
      const picked = store.quantityOf(product.id, variant.id)
      if (picked > bestQuantity) {
        bestId = variant.id
        bestQuantity = picked
      }
    }
    selectedId.value = bestId ?? list[0]?.id ?? null
    quantity.value = Math.max(1, bestQuantity)
  },
  { immediate: true },
)

// 弹层展开时锁住背景滚动，避免滑动手势穿透到底层列表
watch(
  () => props.visible,
  (value) => {
    document.body.style.overflow = value ? 'hidden' : ''
  },
)

onUnmounted(() => {
  document.body.style.overflow = ''
})

function select(variantId: number) {
  const product = props.product
  if (!product) return
  selectedId.value = variantId
  // 切换规格时回显该规格已在购物车里的数量，避免重复加购
  quantity.value = Math.max(1, store.quantityOf(product.id, variantId))
}

function onSetQuantity(value: number) {
  quantity.value = Math.max(1, Math.min(9999, Math.trunc(value) || 1))
}

function close() {
  emit('close')
}

function confirm() {
  const product = props.product
  if (!product || selectedId.value === null) return
  store.setQuantity(product.id, selectedId.value, quantity.value)
  emit('close')
}
</script>

<style scoped>
.variant-sheet-enter-active,
.variant-sheet-leave-active {
  transition: opacity 0.22s ease;
}

.variant-sheet-enter-active section,
.variant-sheet-leave-active section {
  transition: transform 0.24s cubic-bezier(0.32, 0.72, 0, 1);
}

.variant-sheet-enter-from,
.variant-sheet-leave-to {
  opacity: 0;
}

.variant-sheet-enter-from section,
.variant-sheet-leave-to section {
  transform: translateY(100%);
}
</style>

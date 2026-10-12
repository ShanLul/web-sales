<template>
  <div class="flex min-h-screen flex-col">
    <!-- 顶部信息条：随页面滚动，不占据吸顶空间 -->
    <header class="bg-gradient-to-b from-brand-soft to-[#F5F6F8] px-4 pb-3 pt-4">
      <div class="flex items-start justify-between gap-3">
        <div class="min-w-0">
          <p class="truncate text-[16px] font-semibold leading-6 text-ink">
            {{ linkInfo?.template_name || (failure ? '链接不可用' : '专属选购清单') }}
          </p>
          <p class="mt-1 truncate text-[12px] leading-5 text-black/50">
            {{ linkInfo?.remark || (failure ? '请联系业务人员获取新的下单链接' : '以下商品为本链接专属可售范围') }}
          </p>
        </div>
        <span
          v-if="linkInfo"
          class="shrink-0 rounded-full bg-white/80 px-2.5 py-1 text-[11px] leading-4 text-brand shadow-sm backdrop-blur-sm"
        >
          {{ linkInfo.is_single_use ? '一次性链接' : '可多次下单' }}
        </span>
      </div>

      <div v-if="linkInfo" class="mt-3 flex flex-wrap items-center gap-2">
        <span class="flex items-center gap-1 rounded-full bg-white/80 px-2.5 py-1 text-[11px] leading-4 text-black/55">
          <Clock class="h-3 w-3" />
          {{ expireText }}
        </span>
        <span
          v-if="linkInfo?.remaining_uses !== null && linkInfo?.remaining_uses !== undefined"
          class="flex items-center gap-1 rounded-full bg-white/80 px-2.5 py-1 text-[11px] leading-4 text-black/55"
        >
          <Package class="h-3 w-3" />
          剩余可下单 {{ linkInfo.remaining_uses }} 次
        </span>
      </div>
    </header>

    <!-- 链接失效 -->
    <FailureCard
      v-if="failure"
      :reason="failure"
      :message="failureMessage"
      @retry="reload"
    />

    <template v-else>
      <!-- 筛选区：唯一吸顶元素，避免出现硬编码偏移 -->
      <div
        class="sticky top-0 z-20 space-y-2 bg-[#F5F6F8] px-4 pb-2.5 pt-2 shadow-[0_6px_12px_-10px_rgba(0,21,41,0.2)]"
      >
        <div class="flex items-center gap-2">
          <div class="relative min-w-0 flex-1">
            <Search class="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-black/35" />
            <input
              v-model.trim="keyword"
              type="search"
              placeholder="搜索商品名称"
              class="h-10 w-full rounded-full border border-black/[0.06] bg-white pl-10 pr-4 text-[14px] text-ink outline-none transition-all placeholder:text-black/30 focus:border-brand focus:ring-4 focus:ring-brand/10"
            />
          </div>
          <button
            type="button"
            class="flex h-10 shrink-0 cursor-pointer items-center gap-1 rounded-full border px-3 text-[13px] transition-all"
            :class="
              sortKey === 'default'
                ? 'border-black/[0.08] bg-white text-black/60'
                : 'border-brand bg-brand-soft text-brand'
            "
            @click="cycleSort"
          >
            <component :is="sortIcon" class="h-4 w-4" />
            <span>{{ sortLabel }}</span>
          </button>
        </div>

        <div class="flex gap-2 overflow-x-auto pb-0.5">
          <button
            type="button"
            class="h-7 shrink-0 cursor-pointer rounded-full border px-3 text-[12px] transition-all"
            :class="
              activeCategory === null
                ? 'border-brand bg-brand text-white'
                : 'border-black/[0.08] bg-white text-black/60'
            "
            @click="activeCategory = null"
          >
            全部
          </button>
          <button
            v-for="item in categories"
            :key="item.id"
            type="button"
            class="h-7 shrink-0 cursor-pointer rounded-full border px-3 text-[12px] transition-all"
            :class="
              activeCategory === item.id
                ? 'border-brand bg-brand text-white'
                : 'border-black/[0.08] bg-white text-black/60'
            "
            @click="activeCategory = item.id"
          >
            {{ item.name }}
          </button>
        </div>

        <div class="flex gap-2 overflow-x-auto pb-0.5">
          <button
            v-for="range in PRICE_RANGES"
            :key="range.key"
            type="button"
            class="num h-7 shrink-0 cursor-pointer rounded-full border px-3 text-[12px] transition-all"
            :class="
              activePrice === range.key
                ? 'border-brand bg-brand text-white'
                : 'border-black/[0.08] bg-white text-black/60'
            "
            @click="activePrice = range.key"
          >
            {{ range.label }}
          </button>
        </div>
      </div>

      <!-- 商品列表 -->
      <main class="flex-1 px-4 pb-[104px] pt-3">
        <p v-if="store.loading" class="flex items-center justify-center gap-2 py-20 text-[13px] text-black/45">
          <Loader2 class="h-4 w-4 animate-spin" />
          正在加载专属商品…
        </p>

        <div v-else-if="!visibleProducts.length" class="flex flex-col items-center gap-3 py-20">
          <PackageOpen class="h-12 w-12 text-black/20" />
          <p class="text-[14px] text-black/45">没有符合条件的商品</p>
        </div>

        <div v-else class="grid grid-cols-2 gap-2.5">
          <ProductCard
            v-for="item in visibleProducts"
            :key="item.id"
            :product="item"
            v-bind="store.cardState(item.id)"
            @increase="store.increase"
            @decrease="store.decrease"
            @set="store.setQuantity"
            @select="openVariantSheet"
          />
        </div>
      </main>

      <!-- 底部悬浮结算栏 -->
      <footer class="glass-bar fixed bottom-0 left-1/2 z-30 w-full max-w-[430px] -translate-x-1/2 border-t border-black/[0.06] px-4 pb-[calc(0.75rem+env(safe-area-inset-bottom))] pt-3">
        <div class="flex items-center justify-between gap-3">
          <button
            type="button"
            class="flex min-w-0 cursor-pointer items-center gap-2 text-left"
            @click="showCart"
          >
            <span class="relative flex h-10 w-10 items-center justify-center rounded-full bg-brand-soft">
              <ShoppingCart class="h-[18px] w-[18px] text-brand" />
              <span
                v-if="store.totalCount > 0"
                class="num absolute -right-1 -top-1 flex h-5 min-w-5 items-center justify-center rounded-full bg-danger px-1 text-[11px] font-medium text-white"
              >
                {{ store.totalCount }}
              </span>
            </span>
            <span class="min-w-0">
              <span class="block text-[12px] leading-4 text-black/45">合计金额</span>
              <span class="num block text-[18px] font-semibold leading-6 text-brand">
                ¥{{ store.totalAmount.toFixed(2) }}
              </span>
            </span>
          </button>

          <button
            type="button"
            :disabled="!store.totalCount"
            class="h-11 shrink-0 cursor-pointer rounded-full bg-gradient-to-r from-brand to-brand-light px-7 text-[15px] font-medium text-white shadow-float transition-all active:scale-[0.98] disabled:cursor-not-allowed disabled:from-black/20 disabled:to-black/20 disabled:shadow-none"
            @click="goCheckout"
          >
            {{ store.totalCount ? '去结算' : '请选择商品' }}
          </button>
        </div>
      </footer>

      <!-- 规格选择：列表页不铺开规格，按需从底部滑出 -->
      <VariantSheet
        :product="sheetProduct"
        :visible="sheetProduct !== null"
        @close="closeVariantSheet"
      />
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch, type Component } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  ArrowDown,
  ArrowUp,
  ArrowUpDown,
  Clock,
  Loader2,
  Package,
  PackageOpen,
  Search,
  ShoppingCart,
} from 'lucide-vue-next'

import FailureCard from '../components/FailureCard.vue'
import ProductCard from '../components/ProductCard.vue'
import VariantSheet from '../components/VariantSheet.vue'
import { usePortalStore } from '../stores/portal'
import { TOKEN_KEY } from '../utils/token'

interface PriceRange {
  key: string
  label: string
  min?: number
  max?: number
}

/** 价格区间：min 含、max 不含，保证区间之间不重叠不遗漏。 */
const PRICE_RANGES: PriceRange[] = [
  { key: 'all', label: '全部价格' },
  { key: 'lt50', label: '¥50 以下', max: 50 },
  { key: '50-100', label: '¥50-100', min: 50, max: 100 },
  { key: '100-300', label: '¥100-300', min: 100, max: 300 },
  { key: 'gte300', label: '¥300 以上', min: 300 },
]

type SortKey = 'default' | 'price-asc' | 'price-desc'

const SORTS: { key: SortKey; label: string }[] = [
  { key: 'default', label: '排序' },
  { key: 'price-asc', label: '价格 ↑' },
  { key: 'price-desc', label: '价格 ↓' },
]

const route = useRoute()
const router = useRouter()
const store = usePortalStore()

const keyword = ref('')
const activeCategory = ref<number | null>(null)
const activePrice = ref('all')
const sortIndex = ref(0)
const now = ref(Date.now())
let timer = 0

const linkInfo = computed(() => store.linkInfo)
const categories = computed(() => store.categories)
const failure = computed(() => store.failure)
const failureMessage = computed(() => store.failureMessage)

/** 规格弹层只存商品 id，商品对象从 store 派生，规格或价格变化会自动同步。 */
const sheetProductId = ref<number | null>(null)
const sheetProduct = computed(
  () => store.products.find((item) => item.id === sheetProductId.value) ?? null,
)

function openVariantSheet(productId: number) {
  sheetProductId.value = productId
}

function closeVariantSheet() {
  sheetProductId.value = null
}

const sortKey = computed(() => SORTS[sortIndex.value].key)
const sortLabel = computed(() => SORTS[sortIndex.value].label)
const sortIcon = computed<Component>(() => {
  if (sortKey.value === 'price-asc') return ArrowUp
  if (sortKey.value === 'price-desc') return ArrowDown
  return ArrowUpDown
})

function cycleSort() {
  sortIndex.value = (sortIndex.value + 1) % SORTS.length
}

const visibleProducts = computed(() => {
  const text = keyword.value.toLowerCase()
  const range = PRICE_RANGES.find((item) => item.key === activePrice.value)

  const list = store.products.filter((item) => {
    if (activeCategory.value !== null && item.category_id !== activeCategory.value) return false
    if (range) {
      if (range.min !== undefined && item.price < range.min) return false
      if (range.max !== undefined && item.price >= range.max) return false
    }
    if (!text) return true
    return item.name.toLowerCase().includes(text)
  })

  if (sortKey.value === 'price-asc') {
    return [...list].sort((a, b) => a.price - b.price)
  }
  if (sortKey.value === 'price-desc') {
    return [...list].sort((a, b) => b.price - a.price)
  }
  return list
})

const expireText = computed(() => {
  const expireAt = linkInfo.value?.expire_at
  if (!expireAt) return '长期有效'
  const remain = new Date(expireAt).getTime() - now.value
  if (remain <= 0) return '已过期'
  const totalMinutes = Math.floor(remain / 60000)
  const days = Math.floor(totalMinutes / 1440)
  const hours = Math.floor((totalMinutes % 1440) / 60)
  const minutes = totalMinutes % 60
  if (days > 0) return `剩余 ${days} 天 ${hours} 小时`
  if (hours > 0) return `剩余 ${hours} 小时 ${minutes} 分`
  return `剩余 ${Math.max(minutes, 1)} 分钟`
})

function resolveToken() {
  const fromQuery = route.query.t
  if (typeof fromQuery === 'string' && fromQuery) {
    sessionStorage.setItem(TOKEN_KEY, fromQuery)
    return fromQuery
  }
  return sessionStorage.getItem(TOKEN_KEY) || ''
}

async function reload() {
  await store.init(resolveToken())
}

function goCheckout() {
  if (!store.totalCount) return
  router.push({ name: 'checkout' })
}

function showCart() {
  if (!store.totalCount) return
  router.push({ name: 'checkout' })
}

/** 同一标签内链接 token 变化时组件不会重挂载，需显式重新拉取，避免展示上一条链接的授权商品。 */
watch(
  () => route.query.t,
  (value, previous) => {
    if (typeof value === 'string' && value && value !== previous) reload()
  },
)

onMounted(() => {
  reload()
  timer = window.setInterval(() => (now.value = Date.now()), 30000)
})

onUnmounted(() => {
  window.clearInterval(timer)
})
</script>

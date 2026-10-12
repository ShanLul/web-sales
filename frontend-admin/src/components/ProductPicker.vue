<template>
  <div class="grid gap-4 lg:grid-cols-[210px_1fr]">
    <!-- 分类侧栏 -->
    <div class="rounded-lg border border-black/[0.06] bg-[#FAFBFC] p-2">
      <button
        v-for="item in categoryOptions"
        :key="item.id ?? 'all'"
        type="button"
        class="flex h-9 w-full cursor-pointer items-center justify-between rounded-md px-3 text-[13px] transition-colors"
        :class="
          activeCategory === item.id
            ? 'bg-white font-medium text-brand shadow-sm'
            : 'text-ink-muted hover:bg-white/70 hover:text-ink'
        "
        @click="activeCategory = item.id"
      >
        <span class="truncate">{{ item.name }}</span>
        <span class="num ml-2 shrink-0 text-[12px] text-ink-muted/70">{{ item.count }}</span>
      </button>
    </div>

    <!-- 商品多选区 -->
    <div class="flex min-h-[320px] flex-col rounded-lg border border-black/[0.06] bg-white">
      <div class="flex flex-wrap items-center gap-3 border-b border-black/[0.06] px-4 py-3">
        <div class="relative min-w-[200px] flex-1">
          <Search class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-muted/70" />
          <input
            v-model.trim="keyword"
            type="text"
            placeholder="搜索商品名称或 SKU"
            class="h-9 w-full rounded-md border border-black/10 bg-white pl-9 pr-3 text-[13px] text-ink outline-none transition-all duration-200 placeholder:text-ink-muted/50 hover:border-brand/40 focus:border-brand focus:ring-4 focus:ring-brand/10"
          />
        </div>
        <button
          type="button"
          class="h-9 cursor-pointer rounded-md border border-black/10 px-3 text-[13px] text-ink transition-colors hover:border-brand/40 hover:bg-brand-soft/60 hover:text-brand"
          @click="selectVisible"
        >
          选中当前列表
        </button>
        <button
          type="button"
          class="h-9 cursor-pointer rounded-md border border-black/10 px-3 text-[13px] text-ink-muted transition-colors hover:border-danger/30 hover:bg-danger/5 hover:text-danger"
          @click="clearVisible"
        >
          取消当前列表
        </button>
      </div>

      <div class="flex-1 overflow-y-auto p-2" style="max-height: 380px">
        <p v-if="loading" class="flex items-center justify-center gap-2 py-16 text-[13px] text-ink-muted">
          <Loader2 class="h-4 w-4 animate-spin" />
          正在加载商品…
        </p>

        <div v-else-if="!visibleProducts.length" class="flex flex-col items-center justify-center gap-2 py-16">
          <PackageOpen class="h-10 w-10 text-ink-muted/40" />
          <p class="text-[13px] text-ink-muted">没有匹配的商品，换个关键词试试</p>
        </div>

        <label
          v-for="item in visibleProducts"
          v-else
          :key="item.id"
          class="flex cursor-pointer items-center gap-3 rounded-md px-3 py-2.5 transition-colors hover:bg-brand-soft/50"
        >
          <input
            type="checkbox"
            class="h-4 w-4 shrink-0 cursor-pointer accent-[#0052D9]"
            :checked="selected.includes(item.id)"
            @change="toggle(item.id)"
          />
          <img
            v-if="item.image_url"
            :src="item.image_url"
            :alt="item.name"
            class="h-10 w-10 shrink-0 rounded-md border border-black/[0.06] object-cover"
            loading="lazy"
          />
          <span
            v-else
            class="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-[#F3F3F3] text-ink-muted/50"
          >
            <ImageOff class="h-4 w-4" />
          </span>
          <span class="min-w-0 flex-1">
            <span class="block truncate text-[13px] text-ink">{{ item.name }}</span>
            <span class="mt-0.5 block truncate text-[12px] text-ink-muted">
              {{ item.category_name || '未分类' }}
              <template v-if="item.sku"> · {{ item.sku }}</template>
            </span>
          </span>
          <span class="num shrink-0 text-[13px] font-medium text-ink">¥{{ item.price.toFixed(2) }}</span>
        </label>
      </div>

      <div class="flex items-center justify-between border-t border-black/[0.06] bg-[#FAFBFC] px-4 py-2.5">
        <span class="text-[13px] text-ink-muted">
          已选 <span class="num font-medium text-brand">{{ selected.length }}</span> 个商品，共
          <span class="num">{{ products.length }}</span> 个可选
        </span>
        <button
          v-if="selected.length"
          type="button"
          class="cursor-pointer text-[13px] text-ink-muted transition-colors hover:text-danger"
          @click="emit('update:modelValue', [])"
        >
          清空全部
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { ImageOff, Loader2, PackageOpen, Search } from 'lucide-vue-next'

import { listCategories, listProducts } from '../api/products'
import type { Category, Product } from '../api/types'

const props = defineProps<{ modelValue: number[] }>()
const emit = defineEmits<{ (event: 'update:modelValue', value: number[]): void }>()

const products = ref<Product[]>([])
const categories = ref<Category[]>([])
const loading = ref(true)
const keyword = ref('')
const activeCategory = ref<number | null>(null)

const selected = computed(() => props.modelValue)

const categoryOptions = computed(() => [
  { id: null as number | null, name: '全部分类', count: products.value.length },
  ...categories.value.map((item) => ({
    id: item.id as number | null,
    name: item.name,
    count: products.value.filter((p) => p.category_id === item.id).length,
  })),
])

const visibleProducts = computed(() => {
  const text = keyword.value.toLowerCase()
  return products.value.filter((item) => {
    if (activeCategory.value && item.category_id !== activeCategory.value) return false
    if (!text) return true
    return (
      item.name.toLowerCase().includes(text) || (item.sku ?? '').toLowerCase().includes(text)
    )
  })
})

/** 商品选择需要全量数据，按 page_size 上限翻页拉取，避免只拿到第一页。 */
async function loadAllProducts() {
  loading.value = true
  try {
    const collected: Product[] = []
    let page = 1
    for (;;) {
      const result = await listProducts({ page, page_size: 100 })
      collected.push(...result.items)
      if (collected.length >= result.total || !result.items.length) break
      page += 1
    }
    products.value = collected
  } catch (error) {
    console.error('加载商品失败', error)
  } finally {
    loading.value = false
  }
}

async function loadCategories() {
  try {
    categories.value = await listCategories()
  } catch (error) {
    console.error('加载分类失败', error)
  }
}

function toggle(id: number) {
  const next = selected.value.includes(id)
    ? selected.value.filter((item) => item !== id)
    : [...selected.value, id]
  emit('update:modelValue', next)
}

function selectVisible() {
  const merged = new Set(selected.value)
  visibleProducts.value.forEach((item) => merged.add(item.id))
  emit('update:modelValue', [...merged])
}

function clearVisible() {
  const visible = new Set(visibleProducts.value.map((item) => item.id))
  emit(
    'update:modelValue',
    selected.value.filter((id) => !visible.has(id)),
  )
}

onMounted(() => {
  loadCategories()
  loadAllProducts()
})

// 切换分类时清空搜索词，避免两个筛选条件互相干扰造成「看不到东西」的困惑
watch(activeCategory, () => {
  keyword.value = ''
})
</script>

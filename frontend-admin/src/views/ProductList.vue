<template>
  <div class="space-y-4">
    <!-- 概览 + 主操作 -->
    <section class="admin-card admin-card-hover flex flex-wrap items-center justify-between gap-4 p-5">
      <div>
        <p class="page-title">商品管理</p>
        <p class="mt-1 text-[13px] leading-6 text-ink-muted">
          共 <span class="num font-medium text-brand">{{ total }}</span> 个商品，
          其中上架中 <span class="num font-medium text-success">{{ onSaleCount }}</span> 个。
          商品是权限模板与订单明细的数据来源。
        </p>
      </div>
      <div class="flex items-center gap-2">
        <button
          type="button"
          class="flex h-9 cursor-pointer items-center gap-1.5 rounded-md border border-black/10 px-3.5 text-[13px] text-ink transition-colors hover:border-brand/40 hover:bg-brand-soft/60 hover:text-brand"
          @click="exportExcel"
        >
          <Download class="h-4 w-4" />
          导出 Excel
        </button>
        <button
          type="button"
          class="flex h-9 cursor-pointer items-center gap-1.5 rounded-md bg-gradient-to-r from-brand to-brand-light px-3.5 text-[13px] font-medium text-white shadow-float transition-all hover:brightness-110 active:scale-[0.98]"
          @click="openCreate"
        >
          <Plus class="h-4 w-4" />
          新增商品
        </button>
      </div>
    </section>

    <!-- 筛选 -->
    <section class="admin-card p-4">
      <div class="flex flex-wrap items-center gap-3">
        <div class="relative min-w-[240px] flex-1">
          <Search class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-muted/70" />
          <input
            v-model.trim="filters.keyword"
            type="text"
            placeholder="搜索商品名称或 SKU"
            class="h-9 w-full rounded-md border border-black/10 bg-white pl-9 pr-3 text-[13px] text-ink outline-none transition-all placeholder:text-ink-muted/50 hover:border-brand/40 focus:border-brand focus:ring-4 focus:ring-brand/10"
            @keyup.enter="reload(1)"
          />
        </div>
        <select
          v-model="filters.category_id"
          class="h-9 min-w-[150px] cursor-pointer rounded-md border border-black/10 bg-white px-3 text-[13px] text-ink outline-none transition-all hover:border-brand/40 focus:border-brand"
        >
          <option :value="undefined">全部分类</option>
          <option v-for="item in categories" :key="item.id" :value="item.id">
            {{ item.name }}（{{ item.product_count }}）
          </option>
        </select>
        <select
          v-model="filters.status"
          class="h-9 min-w-[130px] cursor-pointer rounded-md border border-black/10 bg-white px-3 text-[13px] text-ink outline-none transition-all hover:border-brand/40 focus:border-brand"
        >
          <option value="">全部状态</option>
          <option value="on_sale">上架中</option>
          <option value="off_shelf">已下架</option>
        </select>
        <button
          type="button"
          class="h-9 cursor-pointer rounded-md bg-brand px-4 text-[13px] font-medium text-white transition-colors hover:bg-brand-light"
          @click="reload(1)"
        >
          查询
        </button>
        <button
          type="button"
          class="h-9 cursor-pointer rounded-md border border-black/10 px-4 text-[13px] text-ink-muted transition-colors hover:bg-black/[0.03] hover:text-ink"
          @click="resetFilters"
        >
          重置
        </button>
      </div>
    </section>

    <!-- 表格 -->
    <section class="admin-card overflow-hidden">
      <t-table
        row-key="id"
        :data="rows"
        :columns="columns"
        :loading="loading"
        :hover="true"
        table-layout="fixed"
        size="medium"
      >
        <template #name="{ row }">
          <div class="flex items-center gap-3">
            <img
              v-if="row.image_url"
              :src="row.image_url"
              :alt="row.name"
              class="h-10 w-10 shrink-0 rounded-md border border-black/[0.06] object-cover"
              loading="lazy"
            />
            <span
              v-else
              class="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-[#F3F3F3] text-ink-muted/50"
            >
              <ImageOff class="h-4 w-4" />
            </span>
            <div class="min-w-0">
              <p class="truncate text-[13px] font-medium text-ink">{{ row.name }}</p>
              <p class="mt-0.5 truncate text-[12px] text-ink-muted">{{ row.description || '暂无描述' }}</p>
            </div>
          </div>
        </template>
        <template #sku="{ row }">
          <span class="num text-[12px] text-ink-muted">{{ row.sku || '—' }}</span>
        </template>
        <template #category="{ row }">
          <span class="text-[13px] text-ink">{{ row.category_name || '未分类' }}</span>
        </template>
        <template #price="{ row }">
          <span class="num text-[13px] font-medium text-ink">
            ¥{{ row.price.toFixed(2) }}
            <span v-if="row.variant_count" class="text-[12px] font-normal text-ink-muted">起</span>
            <span v-else class="font-normal text-ink-muted">/ {{ row.unit }}</span>
          </span>
        </template>
        <template #variants="{ row }">
          <span
            v-if="row.variant_count"
            :title="variantSummary(row)"
            class="inline-flex cursor-help items-center rounded-full bg-brand-soft px-2 py-0.5 text-[12px] text-brand"
          >
            {{ row.variant_count }} 种规格
          </span>
          <span v-else class="text-[12px] text-ink-muted">单一价格</span>
        </template>
        <template #status="{ row }">
          <StatusTag kind="product" :value="row.status" />
        </template>
        <template #actions="{ row }">
          <div class="flex items-center gap-1">
            <button
              type="button"
              class="cursor-pointer rounded px-2 py-1 text-[13px] text-brand transition-colors hover:bg-brand-soft"
              @click="openEdit(row)"
            >
              编辑
            </button>
            <button
              type="button"
              class="cursor-pointer rounded px-2 py-1 text-[13px] text-ink-muted transition-colors hover:bg-black/[0.04] hover:text-ink"
              @click="toggleStatus(row)"
            >
              {{ row.status === 'on_sale' ? '下架' : '上架' }}
            </button>
            <button
              type="button"
              class="cursor-pointer rounded px-2 py-1 text-[13px] text-danger transition-colors hover:bg-danger/10"
              @click="remove(row)"
            >
              删除
            </button>
          </div>
        </template>
        <template #empty>
          <div class="flex flex-col items-center gap-2 py-14">
            <PackageOpen class="h-10 w-10 text-ink-muted/40" />
            <p class="text-[13px] text-ink-muted">还没有商品，点击右上角「新增商品」开始录入</p>
          </div>
        </template>
      </t-table>

      <div class="flex items-center justify-between border-t border-black/[0.06] px-4 py-3">
        <span class="text-[13px] text-ink-muted">
          第 {{ page }} 页 · 共 {{ total }} 条记录
        </span>
        <t-pagination
          v-model:current="page"
          v-model:page-size="pageSize"
          :total="total"
          :page-size-options="[10, 20, 50]"
          size="small"
          @current-change="load"
          @page-size-change="reload(1)"
        />
      </div>
    </section>

    <!-- 新增/编辑抽屉 -->
    <t-drawer
      v-model:visible="drawerVisible"
      :header="editing ? '编辑商品' : '新增商品'"
      size="480px"
      :footer="false"
      :close-on-overlay-click="false"
    >
      <form class="space-y-4" @submit.prevent="save">
        <div>
          <label class="mb-2 block text-[13px] font-medium text-ink" for="p-name">
            商品名称 <span class="text-danger">*</span>
          </label>
          <input
            id="p-name"
            v-model.trim="form.name"
            type="text"
            maxlength="100"
            placeholder="例如：北欧风实木餐桌 1.4m"
            class="h-10 w-full rounded-md border border-black/10 px-3 text-[14px] outline-none transition-all placeholder:text-ink-muted/50 hover:border-brand/40 focus:border-brand focus:ring-4 focus:ring-brand/10"
          />
        </div>

        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="mb-2 block text-[13px] font-medium text-ink" for="p-sku">商品 SKU</label>
            <input
              id="p-sku"
              v-model.trim="form.sku"
              type="text"
              maxlength="50"
              placeholder="例如：TB-1400-WAL"
              class="h-10 w-full rounded-md border border-black/10 px-3 text-[14px] outline-none transition-all placeholder:text-ink-muted/50 hover:border-brand/40 focus:border-brand focus:ring-4 focus:ring-brand/10"
            />
          </div>
          <div>
            <label class="mb-2 block text-[13px] font-medium text-ink" for="p-category">所属分类</label>
            <select
              id="p-category"
              v-model="form.category_id"
              class="h-10 w-full cursor-pointer rounded-md border border-black/10 bg-white px-3 text-[14px] outline-none transition-all hover:border-brand/40 focus:border-brand"
            >
              <option :value="null">未分类</option>
              <option v-for="item in categories" :key="item.id" :value="item.id">{{ item.name }}</option>
            </select>
          </div>
        </div>

        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="mb-2 block text-[13px] font-medium text-ink" for="p-price">
              销售单价（元）
              <span v-if="!hasVariants" class="text-danger">*</span>
            </label>
            <input
              id="p-price"
              v-model.number="form.price"
              type="number"
              min="0.01"
              step="0.01"
              placeholder="0.00"
              :disabled="hasVariants"
              class="num h-10 w-full rounded-md border border-black/10 px-3 text-[14px] outline-none transition-all placeholder:text-ink-muted/50 hover:border-brand/40 focus:border-brand focus:ring-4 focus:ring-brand/10 disabled:cursor-not-allowed disabled:border-black/[0.06] disabled:bg-black/[0.03] disabled:text-ink-muted"
            />
            <p v-if="hasVariants" class="mt-1.5 text-[12px] leading-5 text-ink-muted">
              已设置规格，单价取最低规格价 ¥{{ variantMinPrice.toFixed(2) }} 自动计算
            </p>
          </div>
          <div>
            <label class="mb-2 block text-[13px] font-medium text-ink" for="p-unit">计量单位</label>
            <input
              id="p-unit"
              v-model.trim="form.unit"
              type="text"
              maxlength="10"
              placeholder="件 / 套 / 箱"
              class="h-10 w-full rounded-md border border-black/10 px-3 text-[14px] outline-none transition-all placeholder:text-ink-muted/50 hover:border-brand/40 focus:border-brand focus:ring-4 focus:ring-brand/10"
            />
          </div>
        </div>

        <!-- 规格：内嵌在商品表单里一起保存，留空即单一价格商品 -->
        <div class="rounded-lg border border-black/[0.06] bg-[#FAFBFC] p-4">
          <div class="flex items-start justify-between gap-3">
            <div>
              <p class="text-[13px] font-medium text-ink">商品规格</p>
              <p class="mt-0.5 text-[12px] leading-5 text-ink-muted">
                口味、容量、型号等，客户下单时单选一个；留空则按上方单价销售
              </p>
            </div>
            <button
              type="button"
              class="flex h-8 shrink-0 cursor-pointer items-center gap-1 rounded-md border border-brand/30 bg-white px-2.5 text-[12px] text-brand transition-colors hover:bg-brand-soft"
              @click="addVariant"
            >
              <Plus class="h-3.5 w-3.5" />
              添加规格
            </button>
          </div>

          <p
            v-if="!form.variants.length"
            class="mt-3 rounded-md border border-dashed border-black/10 py-3 text-center text-[12px] text-ink-muted"
          >
            暂无规格
          </p>

          <div v-else class="mt-3 space-y-2">
            <div
              v-for="(variant, index) in form.variants"
              :key="index"
              class="rounded-md border border-black/[0.06] bg-white p-2.5"
            >
              <div class="flex items-center gap-2">
                <span
                  class="num flex h-6 w-6 shrink-0 items-center justify-center rounded bg-black/[0.04] text-[12px] text-ink-muted"
                >
                  {{ index + 1 }}
                </span>
                <input
                  v-model.trim="variant.name"
                  type="text"
                  maxlength="50"
                  placeholder="规格名，例如：100g / 香辣"
                  class="h-9 min-w-0 flex-1 rounded-md border border-black/10 px-2.5 text-[13px] outline-none transition-all placeholder:text-ink-muted/50 hover:border-brand/40 focus:border-brand focus:ring-4 focus:ring-brand/10"
                />
                <div class="relative w-28 shrink-0">
                  <span
                    class="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2 text-[13px] text-ink-muted"
                  >
                    ¥
                  </span>
                  <input
                    v-model.number="variant.price"
                    type="number"
                    min="0"
                    step="0.01"
                    placeholder="0.00"
                    class="num h-9 w-full rounded-md border border-black/10 pl-6 pr-2.5 text-[13px] outline-none transition-all placeholder:text-ink-muted/50 hover:border-brand/40 focus:border-brand focus:ring-4 focus:ring-brand/10"
                  />
                </div>
                <button
                  type="button"
                  title="删除该规格"
                  class="flex h-9 w-8 shrink-0 cursor-pointer items-center justify-center rounded-md text-ink-muted transition-colors hover:bg-danger/10 hover:text-danger"
                  @click="removeVariant(index)"
                >
                  <Trash2 class="h-4 w-4" />
                </button>
              </div>

              <div class="mt-2 flex items-center gap-2 pl-8">
                <input
                  v-model.trim="variant.sku"
                  type="text"
                  maxlength="50"
                  placeholder="规格 SKU（可选，需全局唯一）"
                  class="h-8 min-w-0 flex-1 rounded-md border border-black/10 px-2.5 text-[12px] outline-none transition-all placeholder:text-ink-muted/50 hover:border-brand/40 focus:border-brand focus:ring-4 focus:ring-brand/10"
                />
                <input
                  v-model.trim="variant.image_url"
                  type="text"
                  placeholder="规格图链接（可选，默认用主图）"
                  class="h-8 min-w-0 flex-1 rounded-md border border-black/10 px-2.5 text-[12px] outline-none transition-all placeholder:text-ink-muted/50 hover:border-brand/40 focus:border-brand focus:ring-4 focus:ring-brand/10"
                />
                <button
                  type="button"
                  role="switch"
                  :aria-checked="variant.status === 'on_sale'"
                  :title="variant.status === 'on_sale' ? '点击停售该规格' : '点击恢复在售'"
                  class="relative h-5 w-9 shrink-0 cursor-pointer rounded-full transition-colors duration-200"
                  :class="variant.status === 'on_sale' ? 'bg-brand' : 'bg-black/20'"
                  @click="variant.status = variant.status === 'on_sale' ? 'off_shelf' : 'on_sale'"
                >
                  <span
                    class="absolute top-0.5 h-4 w-4 rounded-full bg-white shadow transition-all duration-200"
                    :class="variant.status === 'on_sale' ? 'left-[18px]' : 'left-0.5'"
                  />
                </button>
              </div>
            </div>

            <p class="text-[12px] leading-5 text-ink-muted">
              共 {{ form.variants.length }} 个规格，客户侧展示起价 ¥{{ variantMinPrice.toFixed(2) }}
            </p>
          </div>
        </div>

        <div>
          <label class="mb-2 block text-[13px] font-medium text-ink" for="p-image">商品主图链接</label>
          <input
            id="p-image"
            v-model.trim="form.image_url"
            type="text"
            placeholder="https://images.unsplash.com/photo-..."
            class="h-10 w-full rounded-md border border-black/10 px-3 text-[13px] outline-none transition-all placeholder:text-ink-muted/50 hover:border-brand/40 focus:border-brand focus:ring-4 focus:ring-brand/10"
          />
          <img
            v-if="form.image_url"
            :src="form.image_url"
            alt="主图预览"
            class="mt-2 h-24 w-24 rounded-md border border-black/[0.06] object-cover"
          />
        </div>

        <div>
          <label class="mb-2 block text-[13px] font-medium text-ink" for="p-desc">商品描述</label>
          <textarea
            id="p-desc"
            v-model.trim="form.description"
            rows="3"
            maxlength="500"
            placeholder="例如：北美黑胡桃实木，环保水性漆，含 4 把餐椅"
            class="w-full resize-none rounded-md border border-black/10 px-3 py-2 text-[14px] leading-6 outline-none transition-all placeholder:text-ink-muted/50 hover:border-brand/40 focus:border-brand focus:ring-4 focus:ring-brand/10"
          />
        </div>

        <div class="flex items-center justify-between rounded-lg border border-black/[0.06] bg-[#FAFBFC] p-4">
          <div>
            <p class="text-[13px] font-medium text-ink">上架销售</p>
            <p class="mt-0.5 text-[12px] text-ink-muted">下架后客户在链接中不可见，也不可下单</p>
          </div>
          <button
            type="button"
            role="switch"
            :aria-checked="form.status === 'on_sale'"
            class="relative h-6 w-11 shrink-0 cursor-pointer rounded-full transition-colors duration-200"
            :class="form.status === 'on_sale' ? 'bg-brand' : 'bg-black/20'"
            @click="form.status = form.status === 'on_sale' ? 'off_shelf' : 'on_sale'"
          >
            <span
              class="absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-all duration-200"
              :class="form.status === 'on_sale' ? 'left-[22px]' : 'left-0.5'"
            />
          </button>
        </div>

        <p v-if="error" class="flex items-center gap-1.5 text-[13px] text-danger">
          <AlertCircle class="h-4 w-4 shrink-0" />
          {{ error }}
        </p>

        <div class="flex justify-end gap-2 border-t border-black/[0.06] pt-4">
          <button
            type="button"
            class="h-9 cursor-pointer rounded-md border border-black/10 px-4 text-[13px] text-ink transition-colors hover:bg-black/[0.03]"
            @click="drawerVisible = false"
          >
            取消
          </button>
          <button
            type="submit"
            :disabled="saving"
            class="flex h-9 cursor-pointer items-center gap-1.5 rounded-md bg-gradient-to-r from-brand to-brand-light px-4 text-[13px] font-medium text-white transition-all hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
          >
            <Loader2 v-if="saving" class="h-4 w-4 animate-spin" />
            {{ saving ? '保存中…' : '保存' }}
          </button>
        </div>
      </form>
    </t-drawer>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { DialogPlugin, MessagePlugin } from 'tdesign-vue-next'
import {
  AlertCircle,
  Download,
  ImageOff,
  Loader2,
  PackageOpen,
  Plus,
  Search,
  Trash2,
} from 'lucide-vue-next'

import StatusTag from '../components/StatusTag.vue'
import {
  createProduct,
  deleteProduct,
  listCategories,
  listProducts,
  updateProduct,
  updateProductStatus,
} from '../api/products'
import type { ProductPayload } from '../api/products'
import { exportProducts } from '../api/orders'
import type { Category, Product, ProductStatus } from '../api/types'

const rows = ref<Product[]>([])
const categories = ref<Category[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const loading = ref(false)

const filters = reactive<{ keyword: string; category_id?: number; status: string }>({
  keyword: '',
  category_id: undefined,
  status: '',
})

const columns = [
  { colKey: 'name', title: '商品信息', width: 280, cell: 'name' },
  { colKey: 'sku', title: 'SKU', width: 130, cell: 'sku' },
  { colKey: 'category_name', title: '分类', width: 110, cell: 'category' },
  { colKey: 'price', title: '单价', width: 150, cell: 'price' },
  { colKey: 'variant_count', title: '规格', width: 110, cell: 'variants' },
  { colKey: 'status', title: '状态', width: 105, cell: 'status' },
  { colKey: 'actions', title: '操作', width: 190, cell: 'actions' },
]

/** 规格名拼成一行放进 title，鼠标悬停即可看到具体规格，不占列宽。 */
function variantSummary(row: Product) {
  return (row.variants ?? []).map((item) => item.name).join('、')
}

const onSaleCount = computed(() => rows.value.filter((item) => item.status === 'on_sale').length)

const drawerVisible = ref(false)
const editing = ref<Product | null>(null)
const saving = ref(false)
const error = ref('')

/** 表单里的规格行：可选字段用空字符串而非 null，方便直接双向绑定到输入框。 */
interface VariantForm {
  name: string
  sku: string
  price: number
  image_url: string
  status: ProductStatus
}

const form = reactive({
  name: '',
  sku: '',
  category_id: null as number | null,
  price: 0,
  unit: '件',
  image_url: '',
  description: '',
  status: 'on_sale' as ProductStatus,
  variants: [] as VariantForm[],
})

const hasVariants = computed(() => form.variants.length > 0)

/** 起价口径与后端保持一致：优先取在售规格的最低价格。 */
const variantMinPrice = computed(() => {
  const onSale = form.variants.filter((item) => item.status === 'on_sale')
  const list = (onSale.length ? onSale : form.variants).map((item) => Number(item.price) || 0)
  return list.length ? Math.min(...list) : 0
})

function addVariant() {
  form.variants.push({ name: '', sku: '', price: 0, image_url: '', status: 'on_sale' })
}

function removeVariant(index: number) {
  form.variants.splice(index, 1)
}

/** 提交前逐行校验规格，错误信息能精确指到第几行，避免落到后端才报错。 */
function validateVariants() {
  if (!form.variants.length) return ''
  for (const [index, item] of form.variants.entries()) {
    if (!item.name) return `请填写第 ${index + 1} 个规格的名称`
    if (!item.price && item.price !== 0) return `请填写第 ${index + 1} 个规格的价格`
  }
  const names = form.variants.map((item) => item.name)
  if (new Set(names).size !== names.length) return '规格名称不能重复'
  const skus = form.variants.map((item) => item.sku).filter(Boolean)
  if (new Set(skus).size !== skus.length) return '规格 SKU 不能重复'
  return ''
}

async function load() {
  loading.value = true
  try {
    const result = await listProducts({
      keyword: filters.keyword || undefined,
      category_id: filters.category_id,
      status: filters.status || undefined,
      page: page.value,
      page_size: pageSize.value,
    })
    rows.value = result.items
    total.value = result.total
  } catch (err) {
    console.error('加载商品失败', err)
  } finally {
    loading.value = false
  }
}

async function loadCategories() {
  try {
    categories.value = await listCategories()
  } catch (err) {
    console.error('加载分类失败', err)
  }
}

function reload(target = 1) {
  page.value = target
  load()
}

function resetFilters() {
  filters.keyword = ''
  filters.category_id = undefined
  filters.status = ''
  reload(1)
}

function openCreate() {
  editing.value = null
  error.value = ''
  Object.assign(form, {
    name: '',
    sku: '',
    category_id: null,
    price: 0,
    unit: '件',
    image_url: '',
    description: '',
    status: 'on_sale' as ProductStatus,
    variants: [],
  })
  drawerVisible.value = true
}

function openEdit(row: Product) {
  editing.value = row
  error.value = ''
  Object.assign(form, {
    name: row.name,
    sku: row.sku ?? '',
    category_id: row.category_id ?? null,
    price: row.price,
    unit: row.unit || '件',
    image_url: row.image_url ?? '',
    description: row.description ?? '',
    status: row.status,
    variants: (row.variants ?? []).map((item) => ({
      name: item.name,
      sku: item.sku ?? '',
      price: item.price,
      image_url: item.image_url ?? '',
      status: item.status,
    })),
  })
  drawerVisible.value = true
}

async function save() {
  error.value = ''
  if (!form.name) {
    error.value = '请填写商品名称'
    return
  }
  // 有规格时单价由规格推导，不再要求手填
  if (!hasVariants.value && (!form.price || form.price <= 0)) {
    error.value = '请填写大于 0 的销售单价，或至少添加一个规格'
    return
  }
  const variantsError = validateVariants()
  if (variantsError) {
    error.value = variantsError
    return
  }

  saving.value = true
  const payload: ProductPayload = {
    name: form.name,
    sku: form.sku || null,
    category_id: form.category_id,
    price: Number(form.price) || 0,
    unit: form.unit || '件',
    image_url: form.image_url || null,
    description: form.description || null,
    status: form.status,
    // 整体替换语义：列表为空即清空该商品的规格
    variants: form.variants.map((item) => ({
      name: item.name,
      sku: item.sku || null,
      price: Number(item.price) || 0,
      image_url: item.image_url || null,
      status: item.status,
    })),
  }
  try {
    if (editing.value) {
      await updateProduct(editing.value.id, payload)
      MessagePlugin.success('商品已更新')
    } else {
      await createProduct(payload)
      MessagePlugin.success('商品已新增')
    }
    drawerVisible.value = false
    loadCategories()
    load()
  } catch (err) {
    console.error('保存商品失败', err)
    error.value = '保存失败，请检查填写内容后重试'
  } finally {
    saving.value = false
  }
}

async function toggleStatus(row: Product) {
  const next: ProductStatus = row.status === 'on_sale' ? 'off_shelf' : 'on_sale'
  try {
    await updateProductStatus(row.id, next)
    MessagePlugin.success(next === 'on_sale' ? '商品已上架' : '商品已下架')
    load()
  } catch (err) {
    console.error('切换商品状态失败', err)
  }
}

function remove(row: Product) {
  const dialog = DialogPlugin.confirm({
    header: '删除商品',
    body: `确认删除「${row.name}」及其全部规格？删除后该商品将从所有权限模板中移除，历史订单明细不受影响。`,
    theme: 'danger',
    confirmBtn: '确认删除',
    cancelBtn: '取消',
    onConfirm: async () => {
      dialog.destroy()
      try {
        await deleteProduct(row.id)
        MessagePlugin.success('商品已删除')
        loadCategories()
        load()
      } catch (err) {
        console.error('删除商品失败', err)
      }
    },
  })
}

async function exportExcel() {
  try {
    await exportProducts({
      keyword: filters.keyword || undefined,
      category_id: filters.category_id,
      status: filters.status || undefined,
    })
    MessagePlugin.success('导出任务已开始，请留意浏览器下载')
  } catch (err) {
    console.error('导出商品失败', err)
  }
}

onMounted(() => {
  loadCategories()
  load()
})
</script>

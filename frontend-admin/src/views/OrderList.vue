<template>
  <div class="space-y-4">
    <section class="admin-card admin-card-hover flex flex-wrap items-center justify-between gap-4 p-5">
      <div>
        <p class="page-title">订单管理</p>
        <p class="mt-1 text-[13px] leading-6 text-ink-muted">
          共 <span class="num font-medium text-brand">{{ total }}</span> 笔订单，
          待发货 <span class="num font-medium text-warning">{{ pendingCount }}</span> 笔需要处理。
        </p>
      </div>
      <button
        type="button"
        class="flex h-9 cursor-pointer items-center gap-1.5 rounded-md border border-black/10 px-3.5 text-[13px] text-ink transition-colors hover:border-brand/40 hover:bg-brand-soft/60 hover:text-brand"
        @click="exportExcel"
      >
        <Download class="h-4 w-4" />
        导出 Excel
      </button>
    </section>

    <section class="admin-card p-4">
      <div class="flex flex-wrap items-center gap-3">
        <div class="relative min-w-[220px] flex-1">
          <Search class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-muted/70" />
          <input
            v-model.trim="filters.keyword"
            type="text"
            placeholder="搜索订单号 / 客户姓名 / 电话"
            class="h-9 w-full rounded-md border border-black/10 bg-white pl-9 pr-3 text-[13px] outline-none transition-all placeholder:text-ink-muted/50 hover:border-brand/40 focus:border-brand focus:ring-4 focus:ring-brand/10"
            @keyup.enter="reload(1)"
          />
        </div>
        <select
          v-model="filters.link_id"
          class="h-9 min-w-[180px] max-w-[240px] cursor-pointer rounded-md border border-black/10 bg-white px-3 text-[13px] text-ink outline-none transition-all hover:border-brand/40 focus:border-brand"
        >
          <option :value="undefined">全部来源链接</option>
          <option v-for="item in linkOptions" :key="item.id" :value="item.id">{{ item.label }}</option>
        </select>
        <select
          v-model="filters.status"
          class="h-9 min-w-[130px] cursor-pointer rounded-md border border-black/10 bg-white px-3 text-[13px] text-ink outline-none transition-all hover:border-brand/40 focus:border-brand"
        >
          <option value="">全部状态</option>
          <option value="pending">待发货</option>
          <option value="shipped">已发货</option>
          <option value="completed">已完成</option>
          <option value="cancelled">已取消</option>
        </select>
        <input
          v-model="filters.start_time"
          type="date"
          class="h-9 cursor-pointer rounded-md border border-black/10 bg-white px-3 text-[13px] text-ink outline-none transition-all hover:border-brand/40 focus:border-brand"
        />
        <span class="text-[13px] text-ink-muted">至</span>
        <input
          v-model="filters.end_time"
          type="date"
          class="h-9 cursor-pointer rounded-md border border-black/10 bg-white px-3 text-[13px] text-ink outline-none transition-all hover:border-brand/40 focus:border-brand"
        />
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

    <section class="admin-card overflow-hidden">
      <t-table
        row-key="id"
        :data="rows"
        :columns="columns"
        :loading="loading"
        table-layout="fixed"
        size="medium"
      >
        <template #order_no="{ row }">
          <button
            type="button"
            class="num cursor-pointer text-[13px] font-medium text-brand transition-colors hover:underline"
            @click="openDetail(row)"
          >
            {{ row.order_no }}
          </button>
        </template>
        <template #link="{ row }">
          <span class="truncate text-[12px] text-ink-muted">{{ row.link_remark || '—' }}</span>
        </template>
        <template #customer="{ row }">
          <p class="truncate text-[13px] text-ink">{{ row.customer_name }}</p>
          <p class="num mt-0.5 truncate text-[12px] text-ink-muted">{{ maskPhone(row.customer_phone) }}</p>
        </template>
        <template #amount="{ row }">
          <span class="num text-[13px] font-medium text-ink">¥{{ row.total_amount.toFixed(2) }}</span>
          <p class="mt-0.5 text-[12px] text-ink-muted">{{ row.item_count }} 种商品</p>
        </template>
        <template #status="{ row }">
          <StatusTag kind="order" :value="row.status" :label="row.status_label" />
        </template>
        <template #created="{ row }">
          <span class="num text-[12px] text-ink-muted">{{ formatTime(row.created_at) }}</span>
        </template>
        <template #actions="{ row }">
          <button
            type="button"
            class="cursor-pointer rounded px-2 py-1 text-[13px] text-brand transition-colors hover:bg-brand-soft"
            @click="openDetail(row)"
          >
            查看详情
          </button>
        </template>
        <template #empty>
          <div class="flex flex-col items-center gap-2 py-14">
            <ClipboardList class="h-10 w-10 text-ink-muted/40" />
            <p class="text-[13px] text-ink-muted">当前筛选条件下没有订单</p>
          </div>
        </template>
      </t-table>

      <div class="flex items-center justify-between border-t border-black/[0.06] px-4 py-3">
        <span class="text-[13px] text-ink-muted">第 {{ page }} 页 · 共 {{ total }} 条记录</span>
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

    <!-- 订单详情抽屉 -->
    <t-drawer v-model:visible="drawerVisible" header="订单详情" size="560px" :footer="false">
      <div v-if="detail" class="space-y-4">
        <div class="rounded-lg border border-black/[0.06] bg-gradient-to-br from-brand-soft/70 to-white p-4">
          <div class="flex items-start justify-between gap-4">
            <div>
              <p class="num text-[15px] font-semibold text-ink">{{ detail.order_no }}</p>
              <p class="mt-1 text-[12px] text-ink-muted">下单时间：{{ formatTime(detail.created_at) }}</p>
              <p class="mt-0.5 text-[12px] text-ink-muted">来源链接：{{ detail.link_remark || '—' }}</p>
            </div>
            <StatusTag kind="order" :value="detail.status" :label="detail.status_label" />
          </div>
        </div>

        <div class="rounded-lg border border-black/[0.06] p-4">
          <p class="section-title mb-3 text-[15px]">收货信息</p>
          <dl class="space-y-2 text-[13px]">
            <div class="flex gap-3">
              <dt class="w-16 shrink-0 text-ink-muted">收货人</dt>
              <dd class="text-ink">{{ detail.customer_name }}</dd>
            </div>
            <div class="flex gap-3">
              <dt class="w-16 shrink-0 text-ink-muted">联系电话</dt>
              <dd class="num text-ink">{{ detail.customer_phone }}</dd>
            </div>
            <div class="flex gap-3">
              <dt class="w-16 shrink-0 text-ink-muted">收货地址</dt>
              <dd class="flex-1 leading-6 text-ink">{{ detail.customer_address }}</dd>
            </div>
            <div v-if="detail.remark" class="flex gap-3">
              <dt class="w-16 shrink-0 text-ink-muted">订单备注</dt>
              <dd class="flex-1 leading-6 text-ink">{{ detail.remark }}</dd>
            </div>
          </dl>
        </div>

        <div class="rounded-lg border border-black/[0.06] p-4">
          <p class="section-title mb-3 text-[15px]">商品明细</p>
          <table class="w-full text-[13px]">
            <thead>
              <tr class="text-[12px] text-ink-muted">
                <th class="pb-2 text-left font-normal">商品</th>
                <th class="pb-2 text-right font-normal">单价</th>
                <th class="pb-2 text-right font-normal">数量</th>
                <th class="pb-2 text-right font-normal">小计</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in detail.items" :key="item.id" class="border-t border-black/[0.06]">
                <td class="py-2.5 pr-2 text-ink">
                  {{ item.product_name }}
                  <span v-if="item.variant_name" class="text-ink-muted">· {{ item.variant_name }}</span>
                </td>
                <td class="num py-2.5 text-right text-ink-muted">¥{{ item.price.toFixed(2) }}</td>
                <td class="num py-2.5 text-right text-ink-muted">{{ item.quantity }}</td>
                <td class="num py-2.5 text-right font-medium text-ink">¥{{ item.subtotal.toFixed(2) }}</td>
              </tr>
            </tbody>
            <tfoot>
              <tr class="border-t border-black/[0.06]">
                <td colspan="3" class="pt-3 text-right text-[13px] text-ink-muted">订单总额</td>
                <td class="num pt-3 text-right text-[16px] font-semibold text-brand">
                  ¥{{ detail.total_amount.toFixed(2) }}
                </td>
              </tr>
            </tfoot>
          </table>
        </div>

        <div class="rounded-lg border border-black/[0.06] bg-[#FAFBFC] p-4">
          <p class="mb-3 text-[13px] font-medium text-ink">状态流转</p>
          <div class="flex flex-wrap gap-2">
            <button
              v-for="action in flowActions"
              :key="action.value"
              type="button"
              :disabled="!action.enabled || updating"
              class="h-9 rounded-md px-4 text-[13px] font-medium transition-all"
              :class="
                action.enabled && !updating
                  ? action.danger
                    ? 'cursor-pointer border border-danger/30 text-danger hover:bg-danger/10'
                    : 'cursor-pointer bg-gradient-to-r from-brand to-brand-light text-white hover:brightness-110'
                  : 'cursor-not-allowed border border-black/10 bg-black/[0.03] text-ink-muted/50'
              "
              @click="changeStatus(action)"
            >
              {{ action.label }}
            </button>
          </div>
          <p class="mt-3 text-[12px] leading-5 text-ink-muted">
            流转规则：待发货 → 已发货 → 已完成；任一进行中状态可取消，已完成或已取消不可回退。
          </p>
        </div>
      </div>
    </t-drawer>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { MessagePlugin } from 'tdesign-vue-next'
import { ClipboardList, Download, Search } from 'lucide-vue-next'

import StatusTag from '../components/StatusTag.vue'
import { exportOrders, getOrder, listOrders, updateOrderStatus } from '../api/orders'
import { listLinks } from '../api/links'
import type { Order, OrderStatus } from '../api/types'

const rows = ref<Order[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const loading = ref(false)
const updating = ref(false)

const drawerVisible = ref(false)
const detail = ref<Order | null>(null)

const linkOptions = ref<{ id: number; label: string }[]>([])

const filters = reactive<{
  keyword: string
  link_id?: number
  status: string
  start_time: string
  end_time: string
}>({
  keyword: '',
  link_id: undefined,
  status: '',
  start_time: '',
  end_time: '',
})

const columns = [
  { colKey: 'order_no', title: '订单号', width: 200, cell: 'order_no' },
  { colKey: 'link', title: '来源链接', width: 170, cell: 'link' },
  { colKey: 'customer', title: '客户', width: 150, cell: 'customer' },
  { colKey: 'amount', title: '金额', width: 130, cell: 'amount' },
  { colKey: 'status', title: '状态', width: 110, cell: 'status' },
  { colKey: 'created', title: '下单时间', width: 160, cell: 'created' },
  { colKey: 'actions', title: '操作', width: 120, cell: 'actions' },
]

const pendingCount = computed(() => rows.value.filter((item) => item.status === 'pending').length)

const flowActions = computed(() => {
  const status = detail.value?.status
  return [
    {
      value: 'shipped' as OrderStatus,
      label: '标记已发货',
      danger: false,
      enabled: status === 'pending',
    },
    {
      value: 'completed' as OrderStatus,
      label: '标记已完成',
      danger: false,
      enabled: status === 'shipped',
    },
    {
      value: 'cancelled' as OrderStatus,
      label: '取消订单',
      danger: true,
      enabled: status === 'pending' || status === 'shipped',
    },
  ]
})

function formatTime(value?: string | null) {
  if (!value) return '—'
  return new Date(value).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function maskPhone(phone: string) {
  return phone.length >= 7 ? `${phone.slice(0, 3)}****${phone.slice(-4)}` : phone
}

async function load() {
  loading.value = true
  try {
    const result = await listOrders({
      keyword: filters.keyword || undefined,
      link_id: filters.link_id,
      status: filters.status || undefined,
      start_time: filters.start_time || undefined,
      end_time: filters.end_time || undefined,
      page: page.value,
      page_size: pageSize.value,
    })
    rows.value = result.items
    total.value = result.total
  } catch (error) {
    console.error('加载订单失败', error)
  } finally {
    loading.value = false
  }
}

async function loadLinkOptions() {
  try {
    const result = await listLinks({ page: 1, page_size: 100 })
    linkOptions.value = result.items.map((item) => ({
      id: item.id,
      label: item.remark || `${item.token.slice(0, 8)}…`,
    }))
  } catch (error) {
    console.error('加载来源链接选项失败', error)
  }
}

function reload(target = 1) {
  page.value = target
  load()
}

function resetFilters() {
  filters.keyword = ''
  filters.link_id = undefined
  filters.status = ''
  filters.start_time = ''
  filters.end_time = ''
  reload(1)
}

async function openDetail(row: Order) {
  try {
    detail.value = await getOrder(row.id)
    drawerVisible.value = true
  } catch (error) {
    console.error('加载订单详情失败', error)
  }
}

async function changeStatus(action: { value: OrderStatus; label: string }) {
  if (!detail.value || !action.enabled) return
  updating.value = true
  try {
    detail.value = await updateOrderStatus(detail.value.id, action.value)
    MessagePlugin.success(`${action.label}成功`)
    load()
  } catch (error) {
    console.error('订单状态流转失败', error)
  } finally {
    updating.value = false
  }
}

async function exportExcel() {
  try {
    await exportOrders({
      keyword: filters.keyword || undefined,
      link_id: filters.link_id,
      status: filters.status || undefined,
      start_time: filters.start_time || undefined,
      end_time: filters.end_time || undefined,
    })
    MessagePlugin.success('导出任务已开始，请留意浏览器下载')
  } catch (error) {
    console.error('导出订单失败', error)
  }
}

onMounted(() => {
  loadLinkOptions()
  load()
})
</script>

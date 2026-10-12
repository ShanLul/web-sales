<template>
  <div class="space-y-4">
    <section class="admin-card admin-card-hover flex flex-wrap items-center justify-between gap-4 p-5">
      <div>
        <p class="page-title">临时链接</p>
        <p class="mt-1 text-[13px] leading-6 text-ink-muted">
          共 <span class="num font-medium text-brand">{{ total }}</span> 条链接。
          状态由有效期与可用次数实时推导，无需手动维护。
        </p>
      </div>
      <button
        type="button"
        class="flex h-9 cursor-pointer items-center gap-1.5 rounded-md bg-gradient-to-r from-brand to-brand-light px-3.5 text-[13px] font-medium text-white shadow-float transition-all hover:brightness-110 active:scale-[0.98]"
        @click="dialogVisible = true"
      >
        <Link2 class="h-4 w-4" />
        生成链接
      </button>
    </section>

    <section class="admin-card p-4">
      <div class="flex flex-wrap items-center gap-3">
        <div class="relative min-w-[240px] flex-1">
          <Search class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-muted/70" />
          <input
            v-model.trim="filters.keyword"
            type="text"
            placeholder="搜索备注或 token"
            class="h-9 w-full rounded-md border border-black/10 bg-white pl-9 pr-3 text-[13px] outline-none transition-all placeholder:text-ink-muted/50 hover:border-brand/40 focus:border-brand focus:ring-4 focus:ring-brand/10"
            @keyup.enter="reload(1)"
          />
        </div>
        <select
          v-model="filters.template_id"
          class="h-9 min-w-[170px] cursor-pointer rounded-md border border-black/10 bg-white px-3 text-[13px] text-ink outline-none transition-all hover:border-brand/40 focus:border-brand"
        >
          <option :value="undefined">全部模板</option>
          <option v-for="item in templates" :key="item.id" :value="item.id">{{ item.name }}</option>
        </select>
        <select
          v-model="filters.derived_status"
          class="h-9 min-w-[140px] cursor-pointer rounded-md border border-black/10 bg-white px-3 text-[13px] text-ink outline-none transition-all hover:border-brand/40 focus:border-brand"
        >
          <option value="">全部状态</option>
          <option v-for="item in statusOptions" :key="item.value" :value="item.value">
            {{ item.label }}
          </option>
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

    <section class="admin-card overflow-hidden">
      <t-table
        row-key="id"
        :data="rows"
        :columns="columns"
        :loading="loading"
        table-layout="fixed"
        size="medium"
      >
        <template #remark="{ row }">
          <div class="min-w-0">
            <p class="truncate text-[13px] font-medium text-ink">{{ row.remark || '未填写备注' }}</p>
            <p class="num mt-0.5 truncate text-[12px] text-ink-muted">{{ shortToken(row.token) }}</p>
          </div>
        </template>
        <template #template="{ row }">
          <span class="text-[13px] text-ink">{{ row.template_name || '—' }}</span>
        </template>
        <template #expire="{ row }">
          <span class="text-[12px] text-ink-muted">
            {{ row.expire_at ? formatTime(row.expire_at) : '永久有效' }}
          </span>
        </template>
        <template #remaining="{ row }">
          <span class="num text-[13px] text-ink">
            {{ row.max_uses === null ? '不限' : `${row.remaining_uses ?? 0} / ${row.max_uses}` }}
          </span>
          <span v-if="row.is_single_use" class="ml-1.5 rounded bg-warning/10 px-1.5 py-0.5 text-[11px] text-warning">
            一次性
          </span>
        </template>
        <template #status="{ row }">
          <StatusTag kind="link" :value="row.derived_status" :label="row.status_label" />
        </template>
        <template #used="{ row }">
          <span class="num text-[13px] text-ink-muted">{{ row.used_count }}</span>
        </template>
        <template #actions="{ row }">
          <div class="flex items-center gap-1">
            <button
              type="button"
              class="cursor-pointer rounded px-2 py-1 text-[13px] text-brand transition-colors hover:bg-brand-soft"
              @click="copyLink(row)"
            >
              复制
            </button>
            <button
              type="button"
              class="cursor-pointer rounded px-2 py-1 text-[13px] text-ink-muted transition-colors hover:bg-black/[0.04] hover:text-ink"
              @click="showQr(row)"
            >
              二维码
            </button>
            <button
              v-if="row.status === 'active'"
              type="button"
              class="cursor-pointer rounded px-2 py-1 text-[13px] text-ink-muted transition-colors hover:bg-black/[0.04] hover:text-ink"
              @click="switchStatus(row, 'disabled')"
            >
              禁用
            </button>
            <button
              v-else
              type="button"
              class="cursor-pointer rounded px-2 py-1 text-[13px] text-success transition-colors hover:bg-success/10"
              @click="switchStatus(row, 'active')"
            >
              启用
            </button>
            <button
              type="button"
              class="cursor-pointer rounded px-2 py-1 text-[13px] text-danger transition-colors hover:bg-danger/10"
              @click="voidLinkItem(row)"
            >
              作废
            </button>
          </div>
        </template>
        <template #empty>
          <div class="flex flex-col items-center gap-2 py-14">
            <Link2 class="h-10 w-10 text-ink-muted/40" />
            <p class="text-[13px] text-ink-muted">还没有临时链接，点击右上角「生成链接」创建第一条</p>
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

    <LinkGenerateDialog v-model:visible="dialogVisible" @created="reload(1)" />

    <!-- 二维码弹窗 -->
    <t-dialog v-model:visible="qrVisible" header="链接二维码" :footer="false" width="380px">
      <div class="flex flex-col items-center gap-4 py-2">
        <img v-if="qrCode" :src="qrCode" alt="链接二维码" class="h-52 w-52 rounded-lg" />
        <p class="break-all text-center text-[12px] leading-5 text-ink-muted">{{ qrTarget?.url }}</p>
        <button
          type="button"
          class="h-9 w-full cursor-pointer rounded-md bg-brand text-[13px] font-medium text-white transition-colors hover:bg-brand-light"
          @click="qrTarget && copyLink(qrTarget)"
        >
          复制链接
        </button>
      </div>
    </t-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { DialogPlugin, MessagePlugin } from 'tdesign-vue-next'
import { Link2, Search } from 'lucide-vue-next'
import QRCode from 'qrcode'

import LinkGenerateDialog from '../components/LinkGenerateDialog.vue'
import StatusTag from '../components/StatusTag.vue'
import { listLinks, updateLinkStatus, voidLink } from '../api/links'
import { listTemplateOptions } from '../api/permissions'
import type { TempLink, TemplateOption } from '../api/types'

const rows = ref<TempLink[]>([])
const templates = ref<TemplateOption[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const loading = ref(false)
const dialogVisible = ref(false)
const qrVisible = ref(false)
const qrCode = ref('')
const qrTarget = ref<TempLink | null>(null)

const filters = reactive<{ keyword: string; template_id?: number; derived_status: string }>({
  keyword: '',
  template_id: undefined,
  derived_status: '',
})

const statusOptions = [
  { value: 'unused', label: '未使用' },
  { value: 'in_use', label: '使用中' },
  { value: 'expired', label: '已过期' },
  { value: 'exhausted', label: '次数耗尽' },
  { value: 'disabled', label: '已禁用' },
  { value: 'voided', label: '已作废' },
]

const columns = [
  { colKey: 'remark', title: '备注 / 凭证', width: 230, cell: 'remark' },
  { colKey: 'template', title: '套用模板', width: 150, cell: 'template' },
  { colKey: 'expire', title: '有效期', width: 160, cell: 'expire' },
  { colKey: 'remaining', title: '剩余次数', width: 150, cell: 'remaining' },
  { colKey: 'status', title: '状态', width: 120, cell: 'status' },
  { colKey: 'used', title: '访问次数', width: 100, cell: 'used' },
  { colKey: 'actions', title: '操作', width: 260, cell: 'actions' },
]

function shortToken(token: string) {
  return `${token.slice(0, 10)}…${token.slice(-6)}`
}

function formatTime(value: string) {
  return new Date(value).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

async function load() {
  loading.value = true
  try {
    const result = await listLinks({
      keyword: filters.keyword || undefined,
      template_id: filters.template_id,
      derived_status: filters.derived_status || undefined,
      page: page.value,
      page_size: pageSize.value,
    })
    rows.value = result.items
    total.value = result.total
  } catch (error) {
    console.error('加载临时链接失败', error)
  } finally {
    loading.value = false
  }
}

async function loadTemplates() {
  try {
    templates.value = await listTemplateOptions()
  } catch (error) {
    console.error('加载模板选项失败', error)
  }
}

function reload(target = 1) {
  page.value = target
  load()
}

function resetFilters() {
  filters.keyword = ''
  filters.template_id = undefined
  filters.derived_status = ''
  reload(1)
}

async function copyLink(row: TempLink) {
  try {
    await navigator.clipboard.writeText(row.url)
    MessagePlugin.success('链接已复制到剪贴板')
  } catch (error) {
    console.error('复制失败', error)
    MessagePlugin.warning('浏览器未授权剪贴板，请手动选中复制')
  }
}

async function showQr(row: TempLink) {
  qrTarget.value = row
  qrCode.value = await QRCode.toDataURL(row.url, { width: 420, margin: 1 })
  qrVisible.value = true
}

async function switchStatus(row: TempLink, status: 'active' | 'disabled') {
  try {
    await updateLinkStatus(row.id, status)
    MessagePlugin.success(status === 'active' ? '链接已启用' : '链接已禁用')
    load()
  } catch (error) {
    console.error('切换链接状态失败', error)
  }
}

function voidLinkItem(row: TempLink) {
  const dialog = DialogPlugin.confirm({
    header: '作废链接',
    body: `确认作废「${row.remark || shortToken(row.token)}」？作废后客户访问将提示链接已失效，且不可再启用。`,
    theme: 'danger',
    confirmBtn: '确认作废',
    cancelBtn: '取消',
    onConfirm: async () => {
      dialog.destroy()
      try {
        await voidLink(row.id)
        MessagePlugin.success('链接已作废')
        load()
      } catch (error) {
        console.error('作废链接失败', error)
      }
    },
  })
}

onMounted(() => {
  loadTemplates()
  load()
})
</script>

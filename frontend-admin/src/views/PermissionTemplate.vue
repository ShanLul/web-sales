<template>
  <div class="space-y-4">
    <section class="admin-card admin-card-hover flex flex-wrap items-center justify-between gap-4 p-5">
      <div>
        <p class="page-title">权限模板</p>
        <p class="mt-1 text-[13px] leading-6 text-ink-muted">
          模板决定临时链接「能看到哪些商品」，是授权范围的唯一来源。共
          <span class="num font-medium text-brand">{{ templates.length }}</span> 个模板。
        </p>
      </div>
      <button
        type="button"
        class="flex h-9 cursor-pointer items-center gap-1.5 rounded-md bg-gradient-to-r from-brand to-brand-light px-3.5 text-[13px] font-medium text-white shadow-float transition-all hover:brightness-110 active:scale-[0.98]"
        @click="openCreate"
      >
        <Plus class="h-4 w-4" />
        新建模板
      </button>
    </section>

    <div class="grid gap-4 xl:grid-cols-[300px_1fr]">
      <!-- 模板列表 -->
      <aside class="admin-card flex max-h-[calc(100vh-220px)] flex-col overflow-hidden">
        <div class="border-b border-black/[0.06] px-4 py-3">
          <div class="relative">
            <Search class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-muted/70" />
            <input
              v-model.trim="keyword"
              type="text"
              placeholder="搜索模板名称"
              class="h-9 w-full rounded-md border border-black/10 bg-white pl-9 pr-3 text-[13px] outline-none transition-all placeholder:text-ink-muted/50 hover:border-brand/40 focus:border-brand focus:ring-4 focus:ring-brand/10"
            />
          </div>
        </div>

        <div class="flex-1 overflow-y-auto p-2">
          <p v-if="loadingList" class="flex items-center justify-center gap-2 py-12 text-[13px] text-ink-muted">
            <Loader2 class="h-4 w-4 animate-spin" />
            加载中…
          </p>
          <p v-else-if="!filteredTemplates.length" class="py-12 text-center text-[13px] text-ink-muted">
            暂无匹配的模板
          </p>
          <button
            v-for="item in filteredTemplates"
            v-else
            :key="item.id"
            type="button"
            class="mb-2 w-full cursor-pointer rounded-lg border p-3 text-left transition-all duration-200"
            :class="
              current?.id === item.id
                ? 'border-brand/40 bg-brand-soft shadow-sm'
                : 'border-black/[0.06] bg-white hover:-translate-y-0.5 hover:border-brand/30 hover:shadow-card'
            "
            @click="select(item.id)"
          >
            <div class="flex items-start justify-between gap-2">
              <p class="min-w-0 truncate text-[13px] font-medium text-ink">{{ item.name }}</p>
              <span
                class="shrink-0 rounded-full px-2 py-0.5 text-[11px] leading-4"
                :class="item.is_active ? 'bg-success/10 text-success' : 'bg-black/[0.05] text-ink-muted'"
              >
                {{ item.is_active ? '启用' : '停用' }}
              </span>
            </div>
            <p class="mt-1.5 line-clamp-2 text-[12px] leading-5 text-ink-muted">
              {{ item.description || '暂无说明' }}
            </p>
            <p class="mt-2 text-[12px] text-ink-muted">
              可见商品 <span class="num font-medium text-brand">{{ item.product_count }}</span> 个
            </p>
          </button>
        </div>
      </aside>

      <!-- 商品选择区 -->
      <section class="admin-card flex flex-col overflow-hidden">
        <template v-if="current">
          <div class="border-b border-black/[0.06] px-5 py-4">
            <div class="flex flex-wrap items-end gap-3">
              <div class="min-w-[200px] flex-1">
                <label class="mb-2 block text-[13px] font-medium text-ink" for="tpl-name">
                  模板名称 <span class="text-danger">*</span>
                </label>
                <input
                  id="tpl-name"
                  v-model.trim="form.name"
                  type="text"
                  maxlength="60"
                  placeholder="例如：华东区标准报价"
                  class="h-9 w-full rounded-md border border-black/10 px-3 text-[14px] outline-none transition-all placeholder:text-ink-muted/50 hover:border-brand/40 focus:border-brand focus:ring-4 focus:ring-brand/10"
                />
              </div>
              <div class="min-w-[220px] flex-[1.4]">
                <label class="mb-2 block text-[13px] font-medium text-ink" for="tpl-desc">模板说明</label>
                <input
                  id="tpl-desc"
                  v-model.trim="form.description"
                  type="text"
                  maxlength="200"
                  placeholder="例如：面向华东经销商，仅开放软装类目"
                  class="h-9 w-full rounded-md border border-black/10 px-3 text-[14px] outline-none transition-all placeholder:text-ink-muted/50 hover:border-brand/40 focus:border-brand focus:ring-4 focus:ring-brand/10"
                />
              </div>
              <div class="flex h-9 items-center gap-3 rounded-md border border-black/[0.06] bg-[#FAFBFC] px-3">
                <span class="text-[13px] text-ink">启用</span>
                <button
                  type="button"
                  role="switch"
                  :aria-checked="form.is_active"
                  class="relative h-6 w-11 shrink-0 cursor-pointer rounded-full transition-colors duration-200"
                  :class="form.is_active ? 'bg-brand' : 'bg-black/20'"
                  @click="form.is_active = !form.is_active"
                >
                  <span
                    class="absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-all duration-200"
                    :class="form.is_active ? 'left-[22px]' : 'left-0.5'"
                  />
                </button>
              </div>
            </div>
          </div>

          <div class="flex-1 overflow-y-auto p-4">
            <ProductPicker v-model="form.product_ids" />
          </div>

          <div class="flex flex-wrap items-center justify-between gap-3 border-t border-black/[0.06] bg-[#FAFBFC] px-5 py-3">
            <p class="text-[12px] leading-5 text-ink-muted">
              保存后立即生效：已生成的链接会按新范围展示商品
            </p>
            <div class="flex items-center gap-2">
              <button
                type="button"
                class="h-9 cursor-pointer rounded-md border border-black/10 px-3.5 text-[13px] text-danger transition-colors hover:border-danger/30 hover:bg-danger/5"
                @click="removeTemplate"
              >
                删除模板
              </button>
              <button
                type="button"
                class="h-9 cursor-pointer rounded-md border border-black/10 px-3.5 text-[13px] text-ink transition-colors hover:border-brand/40 hover:bg-brand-soft/60 hover:text-brand"
                @click="duplicate"
              >
                另存为副本
              </button>
              <button
                type="button"
                :disabled="saving"
                class="flex h-9 cursor-pointer items-center gap-1.5 rounded-md bg-gradient-to-r from-brand to-brand-light px-4 text-[13px] font-medium text-white transition-all hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
                @click="save"
              >
                <Loader2 v-if="saving" class="h-4 w-4 animate-spin" />
                {{ saving ? '保存中…' : '保存模板' }}
              </button>
            </div>
          </div>
        </template>

        <div v-else class="flex flex-1 flex-col items-center justify-center gap-3 py-24">
          <Layers class="h-12 w-12 text-ink-muted/35" />
          <p class="text-[15px] font-medium text-ink">请选择一个权限模板</p>
          <p class="max-w-md text-center text-[13px] leading-6 text-ink-muted">
            从左侧选择模板即可编辑其可见商品集合，也可以新建模板，按分类批量勾选商品后保存。
          </p>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { DialogPlugin, MessagePlugin } from 'tdesign-vue-next'
import { Layers, Loader2, Plus, Search } from 'lucide-vue-next'

import ProductPicker from '../components/ProductPicker.vue'
import {
  createTemplate,
  deleteTemplate,
  duplicateTemplate,
  getTemplate,
  listTemplates,
  updateTemplate,
} from '../api/permissions'
import type { PermissionTemplate } from '../api/types'

const templates = ref<PermissionTemplate[]>([])
const loadingList = ref(false)
const keyword = ref('')
const current = ref<PermissionTemplate | null>(null)
const saving = ref(false)

const form = reactive({
  name: '',
  description: '',
  is_active: true,
  product_ids: [] as number[],
})

const filteredTemplates = computed(() => {
  const text = keyword.value.toLowerCase()
  if (!text) return templates.value
  return templates.value.filter((item) => item.name.toLowerCase().includes(text))
})

async function loadTemplates(keepId?: number) {
  loadingList.value = true
  try {
    const result = await listTemplates({ page: 1, page_size: 100 })
    templates.value = result.items
    if (keepId) {
      const matched = result.items.find((item) => item.id === keepId)
      if (matched) applyTemplate(matched)
    } else if (!current.value && result.items.length) {
      applyTemplate(result.items[0])
    }
  } catch (error) {
    console.error('加载权限模板失败', error)
  } finally {
    loadingList.value = false
  }
}

function applyTemplate(item: PermissionTemplate) {
  current.value = item
  form.name = item.name
  form.description = item.description ?? ''
  form.is_active = item.is_active
  form.product_ids = [...item.product_ids]
}

async function select(id: number) {
  if (current.value && current.value.id === id) return
  try {
    // 取详情而非列表项：保证编辑时的可见商品集合是服务端最新值
    applyTemplate(await getTemplate(id))
  } catch (error) {
    console.error('加载模板详情失败', error)
  }
}

function openCreate() {
  const draft: PermissionTemplate = {
    id: 0,
    name: `新权限模板 ${templates.value.length + 1}`,
    description: '',
    is_active: true,
    product_count: 0,
    product_ids: [],
  }
  current.value = draft
  form.name = draft.name
  form.description = ''
  form.is_active = true
  form.product_ids = []
}

async function save() {
  if (!form.name) {
    MessagePlugin.warning('请填写模板名称')
    return
  }
  saving.value = true
  const payload = {
    name: form.name,
    description: form.description || null,
    is_active: form.is_active,
    product_ids: form.product_ids,
  }
  try {
    if (current.value?.id) {
      const updated = await updateTemplate(current.value.id, payload)
      MessagePlugin.success('模板已保存')
      await loadTemplates(updated.id)
    } else {
      const created = await createTemplate(payload)
      MessagePlugin.success('模板已创建')
      await loadTemplates(created.id)
    }
  } catch (error) {
    console.error('保存权限模板失败', error)
  } finally {
    saving.value = false
  }
}

function duplicate() {
  if (!current.value?.id) {
    MessagePlugin.warning('请先保存当前模板再复制')
    return
  }
  const dialog = DialogPlugin.confirm({
    header: '另存为副本',
    body: `将以「${form.name}」的可见商品集合复制出一个新模板，副本默认启用。`,
    confirmBtn: '确认复制',
    cancelBtn: '取消',
    onConfirm: async () => {
      dialog.destroy()
      try {
        const copy = await duplicateTemplate(current.value!.id, `${form.name} 副本`)
        MessagePlugin.success('副本已创建')
        await loadTemplates(copy.id)
      } catch (error) {
        console.error('复制模板失败', error)
      }
    },
  })
}

function removeTemplate() {
  if (!current.value?.id) {
    MessagePlugin.warning('该模板尚未保存，无需删除')
    return
  }
  const target = current.value
  const dialog = DialogPlugin.confirm({
    header: '删除权限模板',
    body: `确认删除「${target.name}」？已套用该模板的临时链接将失去可见商品范围，建议先停用。`,
    theme: 'danger',
    confirmBtn: '确认删除',
    cancelBtn: '取消',
    onConfirm: async () => {
      dialog.destroy()
      try {
        await deleteTemplate(target.id)
        MessagePlugin.success('模板已删除')
        current.value = null
        await loadTemplates()
      } catch (error) {
        console.error('删除模板失败', error)
      }
    },
  })
}

onMounted(() => loadTemplates())
</script>

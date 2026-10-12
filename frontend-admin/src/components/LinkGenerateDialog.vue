<template>
  <t-dialog
    v-model:visible="visible"
    :header="created ? '链接生成成功' : '生成临时链接'"
    :footer="false"
    width="600px"
    :close-on-overlay-click="false"
    @closed="reset"
  >
    <!-- 生成结果 -->
    <div v-if="created" class="space-y-5">
      <div class="flex items-start gap-3 rounded-lg border border-success/25 bg-success/[0.07] p-4">
        <CircleCheck class="mt-0.5 h-5 w-5 shrink-0 text-success" />
        <div class="min-w-0 text-[13px] leading-6 text-ink">
          <p class="font-medium">链接已生成，可直接发送给客户</p>
          <p class="text-ink-muted">
            套用模板「{{ created.template_name || '-' }}」，
            {{ created.max_uses ? `可用 ${created.max_uses} 次` : '不限次数' }}，
            {{ created.is_single_use ? '下单成功即失效' : '下单后仍可使用' }}
          </p>
        </div>
      </div>

      <div>
        <p class="mb-2 text-[13px] font-medium text-ink">访问链接</p>
        <div class="flex items-stretch gap-2">
          <input
            :value="created.url"
            readonly
            class="h-11 min-w-0 flex-1 rounded-lg border border-black/10 bg-[#FAFBFC] px-3 text-[13px] text-ink outline-none focus:border-brand"
          />
          <button
            type="button"
            class="flex h-11 shrink-0 cursor-pointer items-center gap-1.5 rounded-lg bg-gradient-to-r from-brand to-brand-light px-4 text-[13px] font-medium text-white transition-all hover:brightness-110 active:scale-[0.98]"
            @click="copy"
          >
            <Copy class="h-4 w-4" />
            复制
          </button>
        </div>
      </div>

      <div class="flex flex-col items-center gap-3 rounded-lg border border-black/[0.06] bg-white py-5">
        <img v-if="qrCode" :src="qrCode" alt="链接二维码" class="h-40 w-40 rounded-md" />
        <p class="text-[12px] leading-5 text-ink-muted">客户扫码即可在手机上打开下单页</p>
      </div>

      <div class="flex justify-end gap-2">
        <button
          type="button"
          class="h-9 cursor-pointer rounded-md border border-black/10 px-4 text-[13px] text-ink transition-colors hover:border-brand/40 hover:bg-brand-soft/60 hover:text-brand"
          @click="startOver"
        >
          再生成一条
        </button>
        <button
          type="button"
          class="h-9 cursor-pointer rounded-md bg-brand px-4 text-[13px] font-medium text-white transition-colors hover:bg-brand-light"
          @click="visible = false"
        >
          完成
        </button>
      </div>
    </div>

    <!-- 参数表单 -->
    <form v-else class="space-y-5" @submit.prevent="submit">
      <div>
        <label class="mb-2 block text-[13px] font-medium text-ink" for="link-template">
          套用权限模板 <span class="text-danger">*</span>
        </label>
        <select
          id="link-template"
          v-model.number="form.template_id"
          class="h-11 w-full cursor-pointer rounded-lg border border-black/10 bg-white px-3 text-[14px] text-ink outline-none transition-all hover:border-brand/40 focus:border-brand focus:ring-4 focus:ring-brand/10"
        >
          <option :value="0" disabled>请选择权限模板</option>
          <option v-for="item in templates" :key="item.id" :value="item.id">
            {{ item.name }}（{{ item.product_count }} 个商品）
          </option>
        </select>
        <p class="mt-1.5 text-[12px] leading-5 text-ink-muted">
          客户只能看到并购买该模板授权范围内的商品
        </p>
      </div>

      <div class="rounded-lg border border-black/[0.06] p-4">
        <p class="mb-3 text-[13px] font-medium text-ink">有效期</p>
        <div class="flex gap-2">
          <button
            v-for="option in expireModes"
            :key="option.value"
            type="button"
            class="h-9 flex-1 cursor-pointer rounded-md border text-[13px] transition-all"
            :class="
              form.expire_mode === option.value
                ? 'border-brand bg-brand-soft font-medium text-brand'
                : 'border-black/10 text-ink-muted hover:border-brand/40 hover:text-ink'
            "
            @click="form.expire_mode = option.value"
          >
            {{ option.label }}
          </button>
        </div>
        <div v-if="form.expire_mode === 'custom'" class="mt-3">
          <input
            v-model="form.expire_at"
            type="datetime-local"
            class="h-11 w-full rounded-lg border border-black/10 bg-white px-3 text-[14px] text-ink outline-none transition-all hover:border-brand/40 focus:border-brand focus:ring-4 focus:ring-brand/10"
          />
          <p class="mt-1.5 text-[12px] leading-5 text-ink-muted">到期后链接自动失效，无需手动处理</p>
        </div>
      </div>

      <div class="rounded-lg border border-black/[0.06] p-4">
        <p class="mb-3 text-[13px] font-medium text-ink">可用次数</p>
        <div class="flex gap-2">
          <button
            v-for="option in useModes"
            :key="option.value"
            type="button"
            class="h-9 flex-1 cursor-pointer rounded-md border text-[13px] transition-all"
            :class="
              form.use_mode === option.value
                ? 'border-brand bg-brand-soft font-medium text-brand'
                : 'border-black/10 text-ink-muted hover:border-brand/40 hover:text-ink'
            "
            @click="form.use_mode = option.value"
          >
            {{ option.label }}
          </button>
        </div>
        <div v-if="form.use_mode === 'limited'" class="mt-3">
          <input
            v-model.number="form.max_uses"
            type="number"
            min="1"
            max="100000"
            placeholder="请输入可用次数，例如 10"
            class="num h-11 w-full rounded-lg border border-black/10 bg-white px-3 text-[14px] text-ink outline-none transition-all placeholder:text-ink-muted/50 hover:border-brand/40 focus:border-brand focus:ring-4 focus:ring-brand/10"
          />
        </div>

        <div class="mt-4 flex items-start justify-between gap-4 border-t border-dashed border-black/10 pt-4">
          <div>
            <p class="text-[13px] font-medium text-ink">一次性链接</p>
            <p class="mt-0.5 text-[12px] leading-5 text-ink-muted">
              开启后客户下单成功即失效，适合单客户单次报价
            </p>
          </div>
          <button
            type="button"
            role="switch"
            :aria-checked="form.is_single_use"
            class="relative mt-0.5 h-6 w-11 shrink-0 cursor-pointer rounded-full transition-colors duration-200"
            :class="form.is_single_use ? 'bg-brand' : 'bg-black/20'"
            @click="form.is_single_use = !form.is_single_use"
          >
            <span
              class="absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-all duration-200"
              :class="form.is_single_use ? 'left-[22px]' : 'left-0.5'"
            />
          </button>
        </div>
      </div>

      <div>
        <label class="mb-2 block text-[13px] font-medium text-ink" for="link-remark">备注</label>
        <input
          id="link-remark"
          v-model.trim="form.remark"
          type="text"
          maxlength="200"
          placeholder="例如：华东区客户张经理 · 8 月报价"
          class="h-11 w-full rounded-lg border border-black/10 bg-white px-3 text-[14px] text-ink outline-none transition-all placeholder:text-ink-muted/50 hover:border-brand/40 focus:border-brand focus:ring-4 focus:ring-brand/10"
        />
        <p class="mt-1.5 text-[12px] leading-5 text-ink-muted">备注会显示在链接列表与订单来源中，便于对账</p>
      </div>

      <p v-if="error" class="flex items-center gap-1.5 text-[13px] leading-5 text-danger">
        <AlertCircle class="h-4 w-4 shrink-0" />
        {{ error }}
      </p>

      <div class="flex justify-end gap-2 border-t border-black/[0.06] pt-4">
        <button
          type="button"
          class="h-9 cursor-pointer rounded-md border border-black/10 px-4 text-[13px] text-ink transition-colors hover:bg-black/[0.03]"
          @click="visible = false"
        >
          取消
        </button>
        <button
          type="submit"
          :disabled="submitting"
          class="flex h-9 cursor-pointer items-center gap-1.5 rounded-md bg-gradient-to-r from-brand to-brand-light px-4 text-[13px] font-medium text-white transition-all hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
        >
          <Loader2 v-if="submitting" class="h-4 w-4 animate-spin" />
          {{ submitting ? '生成中…' : '生成链接' }}
        </button>
      </div>
    </form>
  </t-dialog>
</template>

<script setup lang="ts">
import { reactive, ref, watch } from 'vue'
import { MessagePlugin } from 'tdesign-vue-next'
import { AlertCircle, CircleCheck, Copy, Loader2 } from 'lucide-vue-next'
import QRCode from 'qrcode'

import { createLink } from '../api/links'
import { listTemplateOptions } from '../api/permissions'
import type { TempLink, TemplateOption } from '../api/types'

const visible = defineModel<boolean>('visible', { required: true })
const emit = defineEmits<{ (event: 'created'): void }>()

const templates = ref<TemplateOption[]>([])
const submitting = ref(false)
const error = ref('')
const created = ref<TempLink | null>(null)
const qrCode = ref('')

const expireModes = [
  { value: 'permanent' as const, label: '永久有效' },
  { value: 'custom' as const, label: '指定到期时间' },
]
const useModes = [
  { value: 'unlimited' as const, label: '不限次数' },
  { value: 'limited' as const, label: '指定次数' },
]

function defaultForm() {
  return {
    template_id: 0,
    remark: '',
    expire_mode: 'permanent' as 'permanent' | 'custom',
    expire_at: '',
    use_mode: 'unlimited' as 'unlimited' | 'limited',
    max_uses: 10 as number | null,
    is_single_use: false,
  }
}

const form = reactive(defaultForm())

async function loadTemplates() {
  try {
    templates.value = await listTemplateOptions()
  } catch (err) {
    console.error('加载权限模板失败', err)
  }
}

async function submit() {
  error.value = ''
  if (!form.template_id) {
    error.value = '请选择要套用的权限模板'
    return
  }
  if (form.expire_mode === 'custom') {
    if (!form.expire_at) {
      error.value = '请选择到期时间'
      return
    }
    if (new Date(form.expire_at).getTime() <= Date.now()) {
      error.value = '到期时间必须晚于当前时间'
      return
    }
  }
  if (form.use_mode === 'limited' && (!form.max_uses || form.max_uses < 1)) {
    error.value = '请输入大于 0 的可用次数'
    return
  }

  submitting.value = true
  try {
    const link = await createLink({
      template_id: form.template_id,
      remark: form.remark || null,
      expire_mode: form.expire_mode,
      expire_at: form.expire_mode === 'custom' ? form.expire_at : null,
      use_mode: form.use_mode,
      max_uses: form.use_mode === 'limited' ? Number(form.max_uses) : null,
      is_single_use: form.is_single_use,
    })
    created.value = link
    qrCode.value = await QRCode.toDataURL(link.url, { width: 320, margin: 1 })
    emit('created')
    MessagePlugin.success('临时链接生成成功')
  } catch (err) {
    console.error('生成链接失败', err)
    error.value = err instanceof Error && err.message ? err.message : '生成失败，请检查参数后重试'
  } finally {
    submitting.value = false
  }
}

async function copy() {
  if (!created.value) return
  try {
    await navigator.clipboard.writeText(created.value.url)
    MessagePlugin.success('链接已复制到剪贴板')
  } catch (err) {
    console.error('复制失败', err)
    MessagePlugin.warning('浏览器未授权剪贴板，请手动选中复制')
  }
}

function startOver() {
  created.value = null
  qrCode.value = ''
  Object.assign(form, defaultForm())
}

function reset() {
  startOver()
  error.value = ''
}

watch(visible, (value) => {
  if (value) {
    loadTemplates()
  }
})
</script>

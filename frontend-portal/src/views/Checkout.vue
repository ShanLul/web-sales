<template>
  <div class="flex min-h-screen flex-col">
    <header class="sticky top-0 z-20 flex h-14 items-center gap-2 border-b border-black/[0.06] bg-white px-2">
      <button
        type="button"
        aria-label="返回"
        class="flex h-11 w-11 cursor-pointer items-center justify-center rounded-full text-ink transition-colors active:bg-black/[0.05]"
        @click="router.back()"
      >
        <ChevronLeft class="h-5 w-5" />
      </button>
      <p class="flex-1 text-[16px] font-medium leading-6 text-ink">确认订单</p>
      <span class="pr-2 text-[12px] text-black/40">{{ store.totalCount }} 件商品</span>
    </header>

    <main class="flex-1 space-y-3 px-4 pb-[104px] pt-4">
      <!-- 商品清单 -->
      <section class="h5-card p-4">
        <div class="mb-3 flex items-center justify-between">
          <p class="text-[15px] font-medium text-ink">商品清单</p>
          <button
            type="button"
            class="cursor-pointer text-[13px] text-brand"
            @click="router.push({ name: 'order' })"
          >
            继续选购
          </button>
        </div>

        <div v-if="!store.lines.length" class="py-8 text-center text-[13px] text-black/45">
          还没有选择商品
        </div>

        <div
          v-for="line in store.lines"
          v-else
          :key="line.key"
          class="flex items-center gap-3 border-t border-black/[0.05] py-3 first:border-t-0 first:pt-0"
        >
          <img
            v-if="lineImage(line)"
            :src="lineImage(line)"
            :alt="line.product.name"
            class="h-14 w-14 shrink-0 rounded-lg border border-black/[0.06] object-cover"
            loading="lazy"
          />
          <div v-else class="h-14 w-14 shrink-0 rounded-lg bg-[#F3F3F3]" />
          <div class="min-w-0 flex-1">
            <!-- 规格必须跟着商品名一起展示，否则客户与业务都看不出选的是哪一款 -->
            <p class="line-clamp-2 text-[13px] leading-5 text-ink">
              {{ line.product.name }}
              <span v-if="line.variant" class="text-black/45">· {{ line.variant.name }}</span>
            </p>
            <p class="num mt-1 text-[12px] text-black/45">
              ¥{{ line.price.toFixed(2) }} × {{ line.quantity }}
            </p>
          </div>
          <p class="num shrink-0 text-[14px] font-medium text-ink">
            ¥{{ (line.price * line.quantity).toFixed(2) }}
          </p>
        </div>
      </section>

      <!-- 收货信息 -->
      <section class="h5-card p-4">
        <p class="mb-3 text-[15px] font-medium text-ink">收货信息</p>

        <div class="space-y-3">
          <div>
            <label class="mb-1.5 block text-[13px] text-black/55" for="c-name">
              收货人 <span class="text-danger">*</span>
            </label>
            <input
              id="c-name"
              v-model.trim="form.customer_name"
              type="text"
              maxlength="50"
              placeholder="请填写收货人姓名"
              class="h-11 w-full rounded-lg border bg-white px-3 text-[14px] text-ink outline-none transition-all placeholder:text-black/30 focus:ring-4"
              :class="
                errors.customer_name
                  ? 'border-danger focus:border-danger focus:ring-danger/10'
                  : 'border-black/[0.08] focus:border-brand focus:ring-brand/10'
              "
              @blur="touch('customer_name')"
            />
            <p v-if="errors.customer_name" class="mt-1 text-[12px] text-danger">{{ errors.customer_name }}</p>
          </div>

          <div>
            <label class="mb-1.5 block text-[13px] text-black/55" for="c-phone">
              手机号 <span class="text-danger">*</span>
            </label>
            <input
              id="c-phone"
              v-model.trim="form.customer_phone"
              type="tel"
              inputmode="numeric"
              maxlength="11"
              placeholder="用于配送联系，11 位手机号"
              class="num h-11 w-full rounded-lg border bg-white px-3 text-[14px] text-ink outline-none transition-all placeholder:text-black/30 focus:ring-4"
              :class="
                errors.customer_phone
                  ? 'border-danger focus:border-danger focus:ring-danger/10'
                  : 'border-black/[0.08] focus:border-brand focus:ring-brand/10'
              "
              @blur="touch('customer_phone')"
            />
            <p v-if="errors.customer_phone" class="mt-1 text-[12px] text-danger">
              {{ errors.customer_phone }}
            </p>
          </div>

          <div>
            <label class="mb-1.5 block text-[13px] text-black/55" for="c-address">
              详细地址 <span class="text-danger">*</span>
            </label>
            <textarea
              id="c-address"
              v-model.trim="form.customer_address"
              rows="3"
              maxlength="200"
              placeholder="省 / 市 / 区 + 街道门牌 + 楼栋房号"
              class="w-full resize-none rounded-lg border bg-white px-3 py-2.5 text-[14px] leading-6 text-ink outline-none transition-all placeholder:text-black/30 focus:ring-4"
              :class="
                errors.customer_address
                  ? 'border-danger focus:border-danger focus:ring-danger/10'
                  : 'border-black/[0.08] focus:border-brand focus:ring-brand/10'
              "
              @blur="touch('customer_address')"
            />
            <div class="mt-1 flex items-center justify-between">
              <p v-if="errors.customer_address" class="text-[12px] text-danger">
                {{ errors.customer_address }}
              </p>
              <span class="num ml-auto text-[11px] text-black/35">
                {{ form.customer_address.length }}/200
              </span>
            </div>
          </div>

          <div>
            <label class="mb-1.5 block text-[13px] text-black/55" for="c-remark">订单备注</label>
            <input
              id="c-remark"
              v-model.trim="form.remark"
              type="text"
              maxlength="200"
              placeholder="例如：工作日 9-18 点派送，需开增值税专票"
              class="h-11 w-full rounded-lg border border-black/[0.08] bg-white px-3 text-[14px] text-ink outline-none transition-all placeholder:text-black/30 focus:border-brand focus:ring-4 focus:ring-brand/10"
            />
          </div>
        </div>
      </section>

      <p v-if="submitError" class="flex items-start gap-2 rounded-lg border border-danger/20 bg-danger/[0.06] p-3 text-[13px] leading-5 text-danger">
        <AlertCircle class="mt-0.5 h-4 w-4 shrink-0" />
        {{ submitError }}
      </p>
    </main>

    <!-- 提交栏 -->
    <footer class="glass-bar fixed bottom-0 left-1/2 z-30 w-full max-w-[430px] -translate-x-1/2 border-t border-black/[0.06] px-4 pb-[calc(0.75rem+env(safe-area-inset-bottom))] pt-3">
      <div class="flex items-center justify-between gap-3">
        <div>
          <p class="text-[12px] leading-4 text-black/45">应付金额</p>
          <p class="num text-[18px] font-semibold leading-6 text-brand">
            ¥{{ store.totalAmount.toFixed(2) }}
          </p>
        </div>
        <button
          type="button"
          :disabled="submitting || !store.totalCount"
          class="flex h-11 cursor-pointer items-center gap-2 rounded-full bg-gradient-to-r from-brand to-brand-light px-7 text-[15px] font-medium text-white shadow-float transition-all active:scale-[0.98] disabled:cursor-not-allowed disabled:from-black/20 disabled:to-black/20 disabled:shadow-none"
          @click="submit"
        >
          <Loader2 v-if="submitting" class="h-4 w-4 animate-spin" />
          {{ submitting ? '提交中…' : '提交订单' }}
        </button>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
// 按需引入：走子路径可避免把整个 tdesign-mobile-vue 打进产物
import { ToastPlugin as Toast } from 'tdesign-mobile-vue/es/toast'
import { AlertCircle, ChevronLeft, Loader2 } from 'lucide-vue-next'

import { ApiError, LinkError } from '../api/client'
import type { CartLine } from '../api/types'
import { usePortalStore } from '../stores/portal'
import { readToken } from '../utils/token'

const router = useRouter()
const store = usePortalStore()

const submitting = ref(false)
const submitError = ref('')
const touched = reactive<Record<string, boolean>>({})

const form = reactive({
  customer_name: '',
  customer_phone: '',
  customer_address: '',
  remark: '',
})

const errors = reactive<Record<string, string>>({})

const PHONE_RE = /^1[3-9]\d{9}$/

/** 规格带图时优先用规格图，与选购页的视觉对应关系保持一致。 */
function lineImage(line: CartLine) {
  return line.variant?.image_url || line.product.image_url || ''
}

function validate() {
  errors.customer_name = form.customer_name ? '' : '请填写收货人姓名'
  if (!form.customer_phone) {
    errors.customer_phone = '请填写手机号'
  } else if (!PHONE_RE.test(form.customer_phone)) {
    errors.customer_phone = '手机号格式不正确，请填写 11 位有效号码'
  } else {
    errors.customer_phone = ''
  }
  if (!form.customer_address) {
    errors.customer_address = '请填写详细收货地址'
  } else if (form.customer_address.length < 5) {
    errors.customer_address = '地址太短，请补充到街道门牌'
  } else {
    errors.customer_address = ''
  }
  return !errors.customer_name && !errors.customer_phone && !errors.customer_address
}

function touch(field: string) {
  touched[field] = true
  validate()
}

async function submit() {
  submitError.value = ''
  Object.assign(touched, { customer_name: true, customer_phone: true, customer_address: true })
  if (!validate()) {
    submitError.value = '请先完善收货信息后再提交'
    Toast({ message: '请先完善收货信息', theme: 'warning' })
    return
  }
  if (!store.totalCount) {
    submitError.value = '请至少选择一件商品'
    Toast({ message: '请至少选择一件商品', theme: 'warning' })
    return
  }

  submitting.value = true
  try {
    const created = await store.submit({
      customer_name: form.customer_name,
      customer_phone: form.customer_phone,
      customer_address: form.customer_address,
      remark: form.remark || null,
    })
    router.replace({ name: 'result', query: { state: 'success', order_no: created.order_no } })
  } catch (error) {
    console.error('提交订单失败', error)
    if (error instanceof LinkError) {
      // 链接在填写过程中失效：记录原因后跳结果页统一提示
      store.setFailure(error.reason, error.message)
      router.replace({ name: 'result', query: { state: 'failure' } })
      return
    }
    // 其余业务失败（越权商品、过于频繁等）保留在当前页就地提示，避免打断用户
    submitError.value =
      error instanceof ApiError ? error.message : '提交失败，请检查网络后重试'
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  if (!readToken()) {
    router.replace({ name: 'order' })
    return
  }
  if (!store.lines.length) {
    router.replace({ name: 'order' })
  }
})
</script>

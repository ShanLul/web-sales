<template>
  <div class="flex min-h-screen flex-col">
    <!-- 下单成功 -->
    <template v-if="isSuccess">
      <div class="flex flex-1 flex-col items-center justify-center px-6 py-14">
        <div class="flex h-20 w-20 items-center justify-center rounded-full bg-success/10 animate-check-pop">
          <Check class="h-10 w-10 text-success" />
        </div>

        <h2 class="mt-6 text-[22px] font-semibold leading-8 text-ink">下单成功</h2>
        <p class="mt-2 text-[14px] leading-6 text-black/50">我们已收到您的订单，业务人员会尽快与您联系确认</p>

        <div class="mt-7 w-full rounded-2xl border border-black/[0.06] bg-white p-5 shadow-card">
          <dl class="space-y-3 text-[13px]">
            <div class="flex items-center justify-between">
              <dt class="text-black/45">订单号</dt>
              <dd class="num font-medium text-ink">{{ orderNo }}</dd>
            </div>
            <div v-if="store.lastOrder" class="flex items-center justify-between">
              <dt class="text-black/45">订单金额</dt>
              <dd class="num text-[16px] font-semibold text-brand">
                ¥{{ store.lastOrder.total_amount.toFixed(2) }}
              </dd>
            </div>
            <div v-if="store.lastOrder?.created_at" class="flex items-center justify-between">
              <dt class="text-black/45">提交时间</dt>
              <dd class="num text-ink">{{ formatTime(store.lastOrder.created_at) }}</dd>
            </div>
          </dl>
        </div>

        <div class="mt-6 w-full space-y-2 rounded-xl border border-brand/15 bg-brand-soft/60 p-4">
          <p class="flex items-center gap-2 text-[12px] leading-5 text-black/55">
            <Info class="h-3.5 w-3.5 shrink-0 text-brand" />
            请保持手机畅通，业务人员将联系您核对收货信息与开票需求。
          </p>
          <p v-if="store.linkInfo?.is_single_use" class="flex items-center gap-2 text-[12px] leading-5 text-black/55">
            <Info class="h-3.5 w-3.5 shrink-0 text-brand" />
            该链接为一次性链接，本次下单后已自动失效。
          </p>
        </div>

        <div class="mt-8 flex w-full flex-col gap-3">
          <button
            type="button"
            :disabled="!canReorder"
            class="h-11 w-full cursor-pointer rounded-full bg-gradient-to-r from-brand to-brand-light text-[15px] font-medium text-white shadow-float transition-all active:scale-[0.98] disabled:cursor-not-allowed disabled:from-black/20 disabled:to-black/20 disabled:shadow-none"
            @click="continueShopping"
          >
            {{ canReorder ? '继续选购' : '链接已失效，无法继续选购' }}
          </button>
        </div>
      </div>
    </template>

    <!-- 链接失效 -->
    <FailureCard
      v-else
      :reason="store.failure || 'UNKNOWN'"
      :message="store.failureMessage"
      @retry="reload"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Check, Info } from 'lucide-vue-next'

import FailureCard from '../components/FailureCard.vue'
import { usePortalStore } from '../stores/portal'
import { readToken } from '../utils/token'

const route = useRoute()
const router = useRouter()
const store = usePortalStore()

const isSuccess = computed(() => route.query.state === 'success')
const orderNo = computed(() => (route.query.order_no as string) || store.lastOrder?.order_no || '—')

/** 一次性链接下单后即失效，此时不再提供「继续选购」入口。 */
const canReorder = computed(
  () => Boolean(store.linkInfo) && !store.linkInfo?.is_single_use && store.linkInfo?.remaining_uses !== 0,
)

function formatTime(value: string) {
  return new Date(value).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

async function continueShopping() {
  if (!canReorder.value) return
  await store.init(readToken())
  router.replace({ name: 'order' })
}

async function reload() {
  store.resetFailure()
  await store.init(readToken())
  router.replace({ name: 'order' })
}
</script>

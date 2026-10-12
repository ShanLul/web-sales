/** 子系统共享状态：链接信息、授权商品、购物车与提交结果。 */
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { fetchCatalog, submitOrder, type SubmitOrderPayload } from '../api/portal'
import { ApiError, LinkError } from '../api/client'
import type { CatalogProduct, CartLine, FailureReason, LinkInfo, OrderCreated } from '../api/types'

export const usePortalStore = defineStore('portal', () => {
  const token = ref('')
  const linkInfo = ref<LinkInfo | null>(null)
  const products = ref<CatalogProduct[]>([])
  const loading = ref(false)
  const loaded = ref(false)

  /**
   * 购物车以 `商品id:规格id` 为键存储（无规格商品的规格位补 0），只存数量。
   * 商品与规格信息统一从 products 里取，避免同一份数据存两处导致对不上。
   */
  const cart = ref<Record<string, number>>({})

  const failure = ref<FailureReason | null>(null)
  const failureMessage = ref('')
  const lastOrder = ref<OrderCreated | null>(null)

  const NO_VARIANT = 0

  function cartKey(productId: number, variantId: number | null) {
    return `${productId}:${variantId ?? NO_VARIANT}`
  }

  const lines = computed<CartLine[]>(() => {
    const result: CartLine[] = []
    for (const [key, quantity] of Object.entries(cart.value)) {
      if (quantity <= 0) continue
      const [productId, variantId] = key.split(':').map(Number)
      const product = products.value.find((item) => item.id === productId)
      if (!product) continue
      const variant =
        variantId === NO_VARIANT
          ? null
          : ((product.variants ?? []).find((item) => item.id === variantId) ?? null)
      // 规格被删除或下架后该条目已不可售，直接从购物车视图里剔除
      if (variantId !== NO_VARIANT && !variant) continue
      result.push({
        key,
        product,
        variant,
        price: variant ? variant.price : product.price,
        quantity,
      })
    }
    return result
  })

  const totalAmount = computed(() =>
    lines.value.reduce((sum, line) => sum + line.price * line.quantity, 0),
  )

  const totalCount = computed(() => lines.value.reduce((sum, line) => sum + line.quantity, 0))

  const categories = computed(() => {
    const map = new Map<number, string>()
    products.value.forEach((item) => {
      if (item.category_id != null) {
        map.set(item.category_id, item.category_name || '其他')
      }
    })
    return [...map.entries()].map(([id, name]) => ({ id, name }))
  })

  function quantityOf(productId: number, variantId: number | null = null) {
    return cart.value[cartKey(productId, variantId)] ?? 0
  }

  /**
   * 商品卡片一次算齐所需的购物车状态：
   * - quantity：该商品所有规格的合计数量，用于封面角标
   * - activeVariantId：只有恰好好选中一个规格时才非空，此时卡片直接给步进器
   * - selectedCount：已选规格种类数，用于「已选 N 种」提示
   */
  function cardState(productId: number) {
    const selected = lines.value.filter((line) => line.product.id === productId)
    const single = selected.length === 1 ? selected[0].variant : null
    return {
      quantity: selected.reduce((sum, line) => sum + line.quantity, 0),
      activeVariantId: single?.id ?? null,
      activeQuantity: single?.quantity ?? 0,
      selectedCount: selected.length,
    }
  }

  function setQuantity(productId: number, variantId: number | null, quantity: number) {
    const key = cartKey(productId, variantId)
    const next = Math.max(0, Math.min(9999, Math.trunc(quantity) || 0))
    if (next === 0) {
      delete cart.value[key]
      return
    }
    cart.value[key] = next
  }

  function increase(productId: number, variantId: number | null = null) {
    setQuantity(productId, variantId, quantityOf(productId, variantId) + 1)
  }

  function decrease(productId: number, variantId: number | null = null) {
    setQuantity(productId, variantId, quantityOf(productId, variantId) - 1)
  }

  function clearCart() {
    cart.value = {}
  }

  function setFailure(reason: FailureReason, message: string) {
    failure.value = reason
    failureMessage.value = message
  }

  function resetFailure() {
    failure.value = null
    failureMessage.value = ''
  }

  /** 进入 H5 时初始化：token 变化则重新拉取目录，失败时记录失效原因。 */
  async function init(nextToken: string) {
    if (!nextToken) {
      setFailure('LINK_NOT_FOUND', '链接不完整，请向业务人员索取完整链接')
      return false
    }

    if (token.value === nextToken && loaded.value && !failure.value) {
      return true
    }

    // 切换到另一条链接时，清掉上一条链接的购物车与商品，避免越权数据残留。
    if (token.value !== nextToken) {
      cart.value = {}
      products.value = []
      linkInfo.value = null
      loaded.value = false
    }

    token.value = nextToken
    resetFailure()
    loading.value = true
    try {
      const result = await fetchCatalog(nextToken)
      linkInfo.value = result.link
      products.value = result.products
      loaded.value = true
      return true
    } catch (error) {
      console.error('加载授权商品失败', error)
      products.value = []
      linkInfo.value = null
      loaded.value = false
      if (error instanceof LinkError) {
        setFailure(error.reason, error.message)
      } else if (error instanceof ApiError) {
        setFailure('UNKNOWN', error.message)
      } else {
        setFailure('UNKNOWN', '网络异常，请检查网络后重新打开链接')
      }
      return false
    } finally {
      loading.value = false
    }
  }

  async function submit(
    payload: Omit<SubmitOrderPayload, 'token' | 'items'>,
  ): Promise<OrderCreated> {
    const created = await submitOrder({
      ...payload,
      token: token.value,
      items: lines.value.map((line) => ({
        product_id: line.product.id,
        variant_id: line.variant?.id ?? null,
        quantity: line.quantity,
      })),
    })
    lastOrder.value = created
    clearCart()
    return created
  }

  return {
    token,
    linkInfo,
    products,
    categories,
    loading,
    loaded,
    cart,
    lines,
    totalAmount,
    totalCount,
    failure,
    failureMessage,
    lastOrder,
    quantityOf,
    cardState,
    setQuantity,
    increase,
    decrease,
    clearCart,
    setFailure,
    resetFailure,
    init,
    submit,
  }
})

<template>
  <div class="flex items-center gap-1">
    <button
      v-if="quantity > 0"
      type="button"
      aria-label="减少数量"
      class="flex cursor-pointer items-center justify-center rounded-full border border-brand/25 bg-white text-brand transition-all active:scale-90"
      :class="buttonClass"
      @click.stop="emit('decrease')"
    >
      <Minus :class="iconClass" />
    </button>

    <input
      v-if="quantity > 0"
      :value="quantity"
      type="number"
      min="0"
      max="9999"
      inputmode="numeric"
      aria-label="商品数量"
      class="num rounded-md border border-black/10 bg-white text-center text-ink outline-none focus:border-brand"
      :class="inputClass"
      @click.stop
      @change="onInput"
    />

    <button
      type="button"
      :aria-label="quantity > 0 ? '增加数量' : '加入选购'"
      class="flex cursor-pointer items-center justify-center rounded-full bg-gradient-to-br from-brand to-brand-light text-white shadow-float transition-all active:scale-90"
      :class="buttonClass"
      @click.stop="emit('increase')"
    >
      <Plus :class="iconClass" />
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Minus, Plus } from 'lucide-vue-next'

/** compact 用于双列网格卡片，尺寸收紧以适配窄卡片。 */
const props = withDefaults(defineProps<{ quantity: number; compact?: boolean }>(), {
  compact: false,
})

const emit = defineEmits<{
  (event: 'increase'): void
  (event: 'decrease'): void
  (event: 'set', value: number): void
}>()

const buttonClass = computed(() => (props.compact ? 'h-7 w-7' : 'h-8 w-8'))
const iconClass = computed(() => (props.compact ? 'h-3.5 w-3.5' : 'h-4 w-4'))
const inputClass = computed(() =>
  props.compact ? 'h-7 w-9 text-[13px]' : 'h-8 w-12 text-[14px]',
)

function onInput(event: Event) {
  const target = event.target as HTMLInputElement
  emit('set', Number(target.value))
}
</script>

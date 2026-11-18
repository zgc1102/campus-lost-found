<script setup>
/**
 * 发布启事的类型切换。
 * 顺序按产品要求固定为「招领在左、寻物在右」，
 * 选中值的判断与提交逻辑仍由 PublishView 负责，本组件只做展示与回传。
 */
defineProps({
  modelValue: { type: String, default: 'lost' }
})
defineEmits(['update:modelValue'])

const options = [
  { value: 'found', label: '我要招领（捡到物品）' },
  { value: 'lost', label: '我要寻物（东西丢了）' }
]
</script>

<template>
  <div class="type-tab" style="margin-bottom:10px">
    <div
      v-for="option in options"
      :key="option.value"
      :class="{ active: modelValue === option.value }"
      @click="$emit('update:modelValue', option.value)"
    >{{ option.label }}</div>
  </div>
</template>

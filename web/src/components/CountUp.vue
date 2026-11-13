<script setup>
import { onUnmounted, ref, watch } from 'vue'

const props = defineProps({
  value: { type: Number, default: 0 },
  suffix: { type: String, default: '' },
  duration: { type: Number, default: 650 }
})
const display = ref(0)
let raf = 0
function animate(to) {
  cancelAnimationFrame(raf)
  const start = performance.now()
  const from = display.value
  const target = Number(to) || 0
  const tick = (now) => {
    const p = Math.min(1, (now - start) / props.duration)
    const eased = 1 - Math.pow(1 - p, 3)
    display.value = Math.round(from + (target - from) * eased)
    if (p < 1) raf = requestAnimationFrame(tick)
  }
  raf = requestAnimationFrame(tick)
}
watch(() => props.value, (v) => animate(v), { immediate: true })
onUnmounted(() => cancelAnimationFrame(raf))
</script>

<template><span class="count-up">{{ display }}{{ suffix }}</span></template>

<style scoped>
.count-up { font-variant-numeric: tabular-nums; }
</style>

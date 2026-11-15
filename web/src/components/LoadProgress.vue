<template>
  <div class="load-progress" :class="{ done: !loading }">
    <div class="lp-track"><i :style="{ width: pct + '%' }"></i></div>
    <div class="lp-meta"><span>{{ text }}</span><b>{{ pct }}%</b></div>
  </div>
</template>

<script setup>
import { onBeforeUnmount, ref, watch } from 'vue'

const props = defineProps({
  loading: { type: Boolean, default: true },
  text: { type: String, default: '正在读取…' }
})

const pct = ref(8)
let timer = null

function stop() {
  if (timer) { clearInterval(timer); timer = null }
}
function start() {
  stop()
  pct.value = Math.max(8, pct.value)
  timer = setInterval(() => {
    if (pct.value < 90) pct.value = Math.min(90, pct.value + Math.max(1, Math.round((90 - pct.value) / 8)))
  }, 420)
}
watch(() => props.loading, (v) => {
  if (v) start()
  else { stop(); pct.value = 100 }
}, { immediate: true })
onBeforeUnmount(stop)
</script>

<style scoped>
.load-progress { margin: 10px 0 12px; }
.lp-track { height: 5px; border-radius: 99px; background: #EEE7F7; overflow: hidden; }
.lp-track i { display: block; height: 100%; border-radius: 99px; background: linear-gradient(90deg,#7A4DB3,#C9A6E8); transition: width .35s ease; }
.lp-meta { display: flex; justify-content: space-between; margin-top: 5px; font-size: 9px; color: #9A8BAD; }
.lp-meta b { color: #5B2A91; font-weight: 600; }
.load-progress.done .lp-track i { background: #8FC9A6; }
</style>

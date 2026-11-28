<script setup>
import { onUnmounted, ref } from 'vue'

const props = defineProps({
  text: { type: String, default: '' },
  compact: { type: Boolean, default: false }
})

const phrases = [
  '正在翻找校园里的线索…',
  '正在把寻物和招领排排坐…',
  '正在核对这堆失物信息…',
  '正在问一问拾光里的老住户…',
  '马上就好，先别走开…'
]
const index = ref(0)
const timer = setInterval(() => {
  index.value = (index.value + 1) % phrases.length
}, 2600)
onUnmounted(() => clearInterval(timer))
</script>

<template>
  <div class="loading-state" :class="{ compact }" role="status" aria-live="polite">
    <span class="loading-spinner" aria-hidden="true"></span>
    <span class="loading-text">{{ text || phrases[index] }}</span>
  </div>
</template>

<style scoped>
.loading-state {
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  gap: 10px !important;
  width: fit-content !important;
  max-width: calc(100% - 24px);
  margin: 0 auto !important;
  padding: 28px 16px;
  color: #7a6a8d;
  font-size: 12px;
  line-height: 1.5;
  vertical-align: middle;
}
.loading-state .loading-text {
  flex: 0 0 auto !important;
  width: auto !important;
  max-width: calc(100vw - 86px);
  margin: 0 !important;
  text-align: left;
}
.loading-state.compact { padding: 12px 10px; font-size: 11px; display: inline-flex !important; }
.loading-spinner {
  flex: 0 0 auto !important;
  margin: 0 !important;
  width: 22px;
  height: 22px;
  border: 3px solid #e6d9f4;
  border-top-color: #5b2a91;
  border-radius: 50%;
  animation: loadingSpin .8s linear infinite;
  flex: none;
}
@keyframes loadingSpin { to { transform: rotate(360deg); } }
.loading-text { transition: opacity .2s; }
</style>

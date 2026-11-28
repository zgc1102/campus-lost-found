<script setup>
import { computed } from 'vue'

const props = defineProps({
  slide: { type: Object, required: true },
  index: { type: Number, required: true },
  total: { type: Number, required: true },
  placement: { type: String, default: 'center' }
})
const emit = defineEmits(['next', 'skip', 'demo'])

const progress = computed(() => ((props.index + 1) / props.total * 100) + '%')
const last = computed(() => props.index >= props.total - 1)
</script>

<template>
  <div class="tour-card guide-card" :class="'arrow-' + placement">
    <span v-if="placement !== 'center' && placement !== 'bottom'" class="guide-arrow"></span>
    <div class="tour-step">{{ index + 1 }} / {{ total }}</div>
    <div class="guide-icon-row">
      <div class="tour-emoji guide-emoji">{{ slide.e }}</div>
      <span v-if="slide.deepseek" class="deepseek-chip"><i>◈</i> DeepSeek</span>
    </div>
    <div class="tour-title">{{ slide.t }}</div>
    <div class="tour-body">{{ slide.b }}</div>
    <button v-if="slide.compareDemo" type="button" class="guide-demo-link" @click="emit('demo')">看看 AI 对比示例 →</button>
    <div class="tour-dots">
      <i v-for="i in total" :key="i" :class="{ on: i - 1 === index }"></i>
    </div>
    <div class="tour-progress"><i :style="{ width: progress }"></i></div>
    <div class="tour-acts">
      <button type="button" class="btn ghost" @click="emit('skip')">跳过</button>
      <button type="button" class="btn" @click="emit('next')">
        {{ slide.cta || (last ? '开始探索' : '下一步') }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.guide-card {
  position: relative !important;
  z-index: 1;
  width: 100%;
  max-width: none;
  max-height: calc(100vh - 28px);
  overflow-y: auto;
  box-sizing: border-box;
  scrollbar-width: none;
}
.guide-card::-webkit-scrollbar { display: none; width: 0; }
.guide-icon-row { display: flex; align-items: center; gap: 9px; position: relative; }
.guide-emoji { margin: 10px 0 4px; }
.deepseek-chip { display: inline-flex; align-items: center; gap: 4px; margin-top: 8px; border-radius: 99px; background: linear-gradient(135deg,#1d5fd1,#2f8cff); color: #fff; font-size: 10px; font-weight: 600; padding: 4px 9px; letter-spacing: .02em; }
.deepseek-chip i { font-style: normal; font-size: 11px; }
.guide-card .tour-title { font-size: 19px; }
.guide-card .tour-body { font-size: 13px; line-height: 1.75; }
.guide-card .tour-step { font-size: 11px; }
.guide-card .tour-acts .btn { font-size: 13px; }
.guide-arrow { position: absolute; z-index: -1; width: 14px; height: 14px; background: #fff; border: 1px solid #e2d6f7; }
.guide-card.arrow-left .guide-arrow { left: -8px; top: 54px; transform: rotate(45deg); border-right: 0; border-top: 0; }
.guide-card.arrow-right .guide-arrow { right: -8px; top: 54px; transform: rotate(225deg); border-right: 0; border-top: 0; }
.guide-card.arrow-below .guide-arrow { left: 50%; margin-left: -7px; top: -8px; transform: rotate(45deg); border-right: 0; border-bottom: 0; }
.guide-card.arrow-above .guide-arrow { left: 50%; margin-left: -7px; bottom: -8px; transform: rotate(225deg); border-left: 0; border-top: 0; }
@media (max-width: 720px) {
  .guide-card { max-height: 46vh; border-radius: 18px; }
  .guide-card .tour-title { font-size: 17px; }
  .guide-card .tour-body { font-size: 12px; line-height: 1.65; }
  .guide-card .tour-emoji { font-size: 34px; }
  .guide-card .tour-acts .btn { font-size: 12px; }
  .guide-arrow { display: none; }
}
</style>

<script setup>
import { computed, onMounted, ref } from 'vue'

const props = defineProps({
  type: { type: String, default: 'lost' }
})
const emit = defineEmits(['nav'])
const item = computed(() => {
  try { return JSON.parse(sessionStorage.getItem('sg:lastResult') || '{}') } catch (e) { return {} }
})
const approved = computed(() => item.value.status === 'approved')
const rejected = computed(() => item.value.status === 'rejected')
const pending = computed(() => !approved.value && !rejected.value)
const hasRadarPrevious = (() => {
  try { return !!sessionStorage.getItem('sg:radarPrevious') } catch (_) { return false }
})()
const step = ref(0)
const stepDone = ref(false)
const stepText = computed(() => {
  if (step.value < 2) return 'AI 正在审核文字和图片…'
  if (rejected.value) return 'AI 审核未通过'
  if (pending.value) return 'AI 正在自动审核，稍后自动上架'
  return 'AI 审核通过，已上架'
})
onMounted(() => {
  const timers = []
  timers.push(setTimeout(() => { step.value = 1 }, 350))
  timers.push(setTimeout(() => { step.value = 2 }, 900))
  if (approved.value) {
    timers.push(setTimeout(() => { step.value = 3; stepDone.value = true }, 1500))
  } else {
    timers.push(setTimeout(() => { stepDone.value = true }, 1300))
  }
  return () => timers.forEach(clearTimeout)
})
function askDetective() {
  try {
    sessionStorage.setItem('sg:radarSeed', JSON.stringify({
      title: item.value.title || '',
      place: item.value.place || '',
      cat: item.value.cat || 'other',
      lastSeen: item.value.eventTime || '',
      published: true
    }))
  } catch (_) {}
  emit('nav', 'radar')
}
function backToDetective() {
  try {
    const prev = sessionStorage.getItem('sg:radarPrevious')
    if (prev) sessionStorage.setItem('sg:radarRestore', prev)
    sessionStorage.removeItem('sg:radarPrevious')
  } catch (_) {}
  emit('nav', 'radar')
}
</script>

<template>
  <section class="screen active" id="screen-success">
    <div class="topbar">
      <div class="back" @click="$emit('nav', 'home')">‹</div>
      <div class="t">提交成功</div>
    </div>
    <div class="scroll">
      <div class="review-panel" :class="{ done: stepDone, bad: rejected }">
        <div class="review-ring" :class="{ done: stepDone, bad: rejected }"><span>{{ rejected && stepDone ? '!' : (stepDone ? '✓' : 'AI') }}</span></div>
        <div class="review-main">
          <b>{{ stepText }}</b>
          <div class="review-steps">
            <span :class="{ on: step >= 1 }">文字检查</span>
            <span :class="{ on: step >= 2 }">图片 / 特征检查</span>
            <span :class="{ on: step >= 3 }">{{ rejected ? '未通过' : '上架' }}</span>
          </div>
          <div v-if="item.ai" class="review-ai">
            AI 建议：{{ item.ai.decision === 'reject' ? '不建议上架' : item.ai.decision === 'review' ? '建议先上架，请自行核对' : '可以上架' }}
            <template v-if="item.ai.score !== undefined"> · 风险 {{ item.ai.score }}/100</template>
            <template v-if="item.ai.reviewNote"> · {{ item.ai.reviewNote }}</template>
          </div>
        </div>
      </div>
      <div v-if="stepDone" class="okpanel">
        <div class="big">✅</div>
        <h2>{{ approved ? '已发布成功' : '已提交，等待 AI 审核' }}</h2>
        <div class="okmeta">{{ item.title || '' }}</div>
        <p>{{ approved ? 'AI 审核已通过，其他同学已经可以在列表里看到这条信息。' : 'AI 正在自动审核，完成后会自动上架。' }}</p>
        <div v-if="item.typeSuggestion" class="type-suggest">
          AI 提示：这条内容更像「{{ item.typeSuggestion === 'found' ? '招领' : '寻物' }}」。如果类型写错了，可以返回修改，避免同学误解。
        </div>
        <p>你可以在「我的发布」里随时查看审核进度，也可以撤回删除。</p>
        <div class="okacts">
          <button v-if="hasRadarPrevious" class="btn" type="button" @click="backToDetective">返回刚才的侦探结果</button>
          <button v-else-if="type === 'lost' && approved" class="btn" type="button" @click="askDetective">让 AI 侦探帮我找下一步</button>
          <button class="btn ghost" type="button" @click="$emit('nav', 'mine')">查看我的发布</button>
          <button class="btn ghost" type="button" @click="$emit('nav', 'publish', type)">继续发布一条</button>
        </div>
      </div>
      <div v-if="stepDone" class="faq-note" style="margin-top:16px">💡 {{ approved ? '如需修改，可在「我的发布」里撤回后重新提交。' : '系统会自动审核；需要补充时会在「我的发布」里显示原因。' }}</div>
    </div>
  </section>
</template>

<style scoped>
.review-panel { display:flex; gap:12px; align-items:center; background:#FBF8FF; border:1px solid #EADFF5; border-radius:14px; padding:13px 14px; margin:10px 0 4px; }
.review-ring { width:42px; height:42px; flex:0 0 42px; border-radius:50%; border:3px solid #E8D8F5; border-top-color:#5B2A91; display:flex; align-items:center; justify-content:center; color:#5B2A91; font-size:11px; font-weight:700; animation:reviewSpin 1s linear infinite; }
.review-ring.done { animation:none; background:#EAF7EE; border-color:#BFE3CB; color:#2F7D46; font-size:19px; }
.review-ring.bad { background:#FDECEA; border-color:#F2C1BA; color:#C0392B; }
@keyframes reviewSpin { to { transform:rotate(360deg); } }
.review-main { min-width:0; }
.review-main > b { display:block; font-size:12px; color:#4B2B72; }
.review-steps { display:flex; gap:10px; margin-top:5px; flex-wrap:wrap; }
.review-steps span { font-size:9px; color:#B3A4C5; position:relative; padding-left:8px; }
.review-steps span::before { content:""; width:4px; height:4px; border-radius:50%; background:#D9CCE8; position:absolute; left:0; top:5px; }
.review-steps span.on { color:#5B2A91; }
.review-steps span.on::before { background:#5B2A91; }
.review-ai { margin-top:4px; font-size:9px; color:#8E7FA3; }
</style>

<style scoped>
.type-suggest { margin:8px 0; padding:8px 9px; border-radius:8px; background:#FFF8E8; border:1px solid #F0D6A8; color:#8A5A16; font-size:10px; line-height:1.6; }
</style>

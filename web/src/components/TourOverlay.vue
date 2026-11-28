<script setup>
import { nextTick, onMounted, onUnmounted, ref } from 'vue'

const KEY = 'sg:tour:v5'
const slides = [
  { icon: '👋', target: '', title: '欢迎来到清华校园拾光里', body: '一个智能系统全程把关的校园失物招领与爱心互助平台。\n先花 30 秒，带你逛一圈。', cta: '开始导览' },
  { icon: '🔎', target: '.entry-section.section-lost', title: '失物 · 寻物', body: '丢了东西点「寻物启事」，捡到东西点「失物招领」。\n点首页「发布」就能发布，类型选错会智能纠正。' },
  { icon: '🧭', target: '.guide-banner', title: '初入清华，先问一句', body: '游客、新生、家长都能用：访客怎么进校、校园卡丢了怎么办、食堂在哪。\n点这里，或直接问智能助手。' },
  { icon: '🤝', target: '.entry-section.section-help', title: '爱心 · 求助', body: '借用工具、代办跑腿、爱心捐赠、志愿帮忙。\n点「我来帮忙」就能对接，全程智能审核。' },
  { icon: '🔖', target: '.tag-entry', title: '拾光码：一码通用', body: '生成一张自己的拾光码，可以贴电脑、键盘、校园卡、充电器。\n捡到的人扫码后，可以只发通知，也可以直接看到你的电话。' },
  { icon: '🔔', target: '.bell', title: '智能匹配与通知', body: '发布后系统会自动配对相似招领 / 寻物，并在铃铛里提醒。\n点铃铛查看通知。' },
  { icon: '🔍', target: '.top-search', title: '搜索与智能问答', body: '找不到时先搜一搜，也可以直接问智能助手。\n校园卡、访客进校、食堂位置，都能问。' },
  { icon: '❓', target: '.help-btn', title: '随时重新打开这份引导', body: '点右上角的问号，或者首页底部的「使用引导」，\n都可以重新看一遍。' },
  { icon: '🚀', target: '', title: '开始你的拾光之旅', body: '右上角铃铛看通知，「我的」里管理发布和申请。\n遇到问题，随时找我们。', cta: '开始探索' }
]

const show = ref(false)
const index = ref(0)
const holeStyle = ref({ display: 'none' })
const cardStyle = ref({})
const placement = ref('center')
const cardRef = ref(null)

function isFirstVisit() {
  if (location.search.includes('tour=off')) return false
  if (new URLSearchParams(location.search).get('tour') === '1') return true
  try { return localStorage.getItem(KEY) !== '1' } catch (e) { return true }
}

function close() {
  show.value = false
  try { localStorage.setItem(KEY, '1') } catch (e) {}
}

function next() {
  if (index.value >= slides.length - 1) return close()
  index.value++
}

async function place() {
  if (!show.value) return
  await nextTick()
  const s = slides[index.value]
  const target = s.target ? document.querySelector(s.target) : null
  if (!target) {
    holeStyle.value = { display: 'none' }
    placement.value = 'center'
    cardStyle.value = { left: '50%', top: '50%', transform: 'translate(-50%, -50%)' }
    return
  }
  target.scrollIntoView({ block: 'center', inline: 'center', behavior: 'smooth' })
  setTimeout(() => {
    if (!show.value) return
    const r = target.getBoundingClientRect()
    const pad = 7
    holeStyle.value = {
      display: 'block',
      left: Math.max(6, r.left - pad) + 'px',
      top: Math.max(6, r.top - pad) + 'px',
      width: Math.max(16, r.width + pad * 2) + 'px',
      height: Math.max(16, r.height + pad * 2) + 'px'
    }
    const cardW = Math.min(346, window.innerWidth - 32)
    const below = r.bottom + 238 < window.innerHeight
    const top = below ? r.bottom + 16 : Math.max(16, r.top - 222)
    const left = Math.min(window.innerWidth - cardW - 14, Math.max(14, r.left + r.width / 2 - cardW / 2))
    placement.value = below ? 'below' : 'above'
    cardStyle.value = { left: left + 'px', top: top + 'px', width: cardW + 'px', transform: 'none' }
  }, 360)
}

function replay() {
  index.value = 0
  show.value = true
  place()
}

function onKey(e) {
  if (!show.value) return
  if (e.key === 'Escape') close()
  if (e.key === 'ArrowRight' || e.key === 'Enter') next()
}

onMounted(() => {
  window.addEventListener('sg:tour', replay)
  window.addEventListener('resize', place)
  document.addEventListener('keydown', onKey)
  if (isFirstVisit()) {
    show.value = true
    place()
  }
})
onUnmounted(() => {
  window.removeEventListener('sg:tour', replay)
  window.removeEventListener('resize', place)
  document.removeEventListener('keydown', onKey)
})
</script>

<template>
  <div v-if="show" class="guide-layer" :class="{ dim: !slides[index].target }">
    <div class="guide-blocker"></div>
    <div class="guide-hole" :style="holeStyle"></div>
    <div ref="cardRef" class="guide-card" :class="placement" :style="cardStyle">
      <div class="guide-top"><span class="guide-step">{{ index + 1 }} / {{ slides.length }}</span><button type="button" class="guide-close" @click="close">跳过</button></div>
      <div class="guide-icon">{{ slides[index].icon }}</div>
      <h3>{{ slides[index].title }}</h3>
      <p v-for="(line, i) in slides[index].body.split('\n')" :key="i">{{ line }}</p>
      <div class="guide-dots"><i v-for="(s, i) in slides" :key="i" :class="{ on: i <= index }" /></div>
      <button type="button" class="guide-next" @click="next">{{ slides[index].cta || (index === slides.length - 1 ? '开始探索' : '下一步') }} <span>›</span></button>
    </div>
  </div>
</template>

<style scoped>
.guide-layer { position: fixed; inset: 0; z-index: 9998; }
.guide-blocker { position: absolute; inset: 0; background: transparent; }
.guide-layer.dim .guide-blocker { background: rgba(7, 3, 12, .72); }
.guide-hole { position: fixed; z-index: 9999; border-radius: 14px; border: 2px solid #e8cd8e; box-shadow: 0 0 0 9999px rgba(7, 3, 12, .78), 0 0 24px rgba(232, 205, 142, .25); pointer-events: none; transition: left .3s ease, top .3s ease, width .3s ease, height .3s ease; }
.guide-card { position: fixed; z-index: 10000; box-sizing: border-box; padding: 16px 17px 14px; border: 1px solid rgba(232, 205, 142, .35); border-radius: 15px; background: rgba(25, 13, 39, .96); color: #fff; box-shadow: 0 20px 60px rgba(0, 0, 0, .4); font-family: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif; }
.guide-card.center { transform: translate(-50%, -50%); max-width: calc(100% - 28px); }
.guide-card.below::before, .guide-card.above::before { content: ''; position: absolute; left: 50%; margin-left: -7px; width: 12px; height: 12px; background: rgba(25, 13, 39, .96); border-left: 1px solid rgba(232, 205, 142, .35); border-top: 1px solid rgba(232, 205, 142, .35); transform: rotate(45deg); }
.guide-card.below::before { top: -7px; }
.guide-card.above::before { bottom: -7px; transform: rotate(225deg); }
.guide-top { display: flex; align-items: center; justify-content: space-between; }
.guide-step { color: rgba(232, 205, 142, .78); font-size: 10px; letter-spacing: .12em; }
.guide-close { border: 0; background: transparent; color: rgba(255, 255, 255, .45); font: inherit; font-size: 10px; cursor: pointer; padding: 0; }
.guide-icon { margin-top: 10px; font-size: 27px; line-height: 1; }
.guide-card h3 { margin: 7px 0 0; color: #fff8e8; font-size: 19px; line-height: 1.45; font-weight: 700; }
.guide-card p { margin: 7px 0 0; color: rgba(255, 255, 255, .62); font-size: 11px; line-height: 1.8; }
.guide-dots { display: flex; gap: 5px; margin-top: 13px; }
.guide-dots i { width: 5px; height: 5px; border-radius: 50%; background: rgba(255, 255, 255, .18); }
.guide-dots i.on { width: 16px; border-radius: 99px; background: #e8cd8e; }
.guide-next { width: 100%; margin-top: 13px; border: 1px solid rgba(232, 205, 142, .65); border-radius: 9px; background: #e8cd8e; color: #2b1645; padding: 9px 12px; font: inherit; font-size: 11px; font-weight: 700; cursor: pointer; }
.guide-next span { font-size: 16px; vertical-align: -1px; margin-left: 3px; }
@media (max-width: 560px) {
  .guide-card { padding: 14px 15px 13px; }
  .guide-card h3 { font-size: 17px; }
  .guide-card p { font-size: 10.5px; }
}
</style>

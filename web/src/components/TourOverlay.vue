<script setup>
import { onMounted, onUnmounted, ref } from 'vue'

const KEY = 'sg:tour:v3'
const slides = [
  { e: '👋', t: '欢迎来到清华校园拾光里', b: '一个智能系统全程把关的校园失物招领与爱心互助平台。\n先花 30 秒，带你逛一圈。' },
  { e: '🔎', t: '失物 · 寻物', b: '丢了东西点「寻物启事」，捡到东西点「失物招领」。\n点首页「发布」就能发布，类型选错会智能纠正。' },
  { e: '🧭', t: '初入清华，先问一句', b: '游客、新生、家长都能用：访客怎么进校、校园卡丢了怎么办、食堂在哪。\n点首页「初入清华园」，或直接问智能助手。' },
  { e: '🤝', t: '爱心 · 求助', b: '借用工具、代办跑腿、爱心捐赠、志愿帮忙。\n点「我来帮忙」就能对接，全程智能审核。' },
  { e: '🔖', t: '拾光码：一码通用', b: '生成一张自己的拾光码，可以贴电脑、键盘、校园卡、充电器。\n捡到的人扫码后，可以只发通知，也可以直接看到你的电话。' },
  { e: '🕵️', t: '寻物侦探：没发布也能用', b: '不用先发帖。填丢了什么、今天走过哪里、平时放口袋还是背包。\n智能助手会按校园地图和动作风险，给出下一步去哪找。' },
  { e: '🤖', t: '智能审核都在做什么', b: '发布：文字 + 图片双审，违规直接拦。\n拍照：自动识别物品并填写。\n认领：智能核验特征，支持多轮补充。\n问答：校园失物问题随时问。' },
  { e: '🚀', t: '开始你的拾光之旅', b: '右上角铃铛看通知，「我的」里管理发布和申请。\n遇到问题，随时找我们。' }
]
const index = ref(0)
const show = ref(localStorage.getItem(KEY) !== '1' && !location.search.includes('tour=off'))
function close() {
  show.value = false
  localStorage.setItem(KEY, '1')
}
function next() {
  if (index.value >= slides.length - 1) return close()
  index.value++
}
function replay() {
  index.value = 0
  show.value = true
}
onMounted(() => window.addEventListener('sg:tour', replay))
onUnmounted(() => window.removeEventListener('sg:tour', replay))
</script>

<template>
  <div v-if="show" class="tour show">
    <div class="tour-card">
      <div class="tour-step">{{ index + 1 }} / {{ slides.length }}</div>
      <div class="tour-emoji">{{ slides[index].e }}</div>
      <div class="tour-title">{{ slides[index].t }}</div>
      <div class="tour-body">{{ slides[index].b }}</div>
      <div class="tour-dots"><i v-for="(s, i) in slides" :key="i" :class="{ on: i === index }" /></div>
      <div class="tour-progress"><i :style="{ width: ((index + 1) / slides.length * 100) + '%' }" /></div>
      <div class="tour-acts">
        <button type="button" class="btn ghost" @click="close">跳过</button>
        <button type="button" class="btn" @click="next">{{ index === slides.length - 1 ? '开始使用' : '下一步' }}</button>
      </div>
    </div>
  </div>
</template>


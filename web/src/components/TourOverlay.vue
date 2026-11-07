<script setup>
import { ref } from 'vue'

const KEY = 'sg:vue:tour:v1'
const slides = [
  { e: '👋', t: '欢迎来到清华校园拾光里', b: '一个 AI 全程把关的校园失物招领与爱心互助平台。\n先花 30 秒，带你逛一圈。' },
  { e: '🔎', t: '失物 · 寻物', b: '丢了东西点「寻物启事」，捡到东西点「失物招领」。\n点右下角 ＋ 就能发布。' },
  { e: '🤝', t: '爱心 · 求助', b: '借用工具、代办跑腿、爱心捐赠、志愿帮忙。\n点「我来帮忙」就能对接。' },
  { e: '🔖', t: '拾光码：一码通用', b: '生成一张自己的拾光码，可以贴电脑、键盘、校园卡、充电器。\n捡到的人扫码后，可以只发通知，也可以直接看到你的电话。' },
  { e: '🕵️', t: '寻物侦探：没发布也能用', b: '不用先发帖。填丢了什么、今天走过哪里、平时放口袋还是背包。\nAI 会按校园地图和动作风险，给出下一步去哪找。' },
  { e: '🧭', t: '初入清华，先问一句', b: '访客怎么进校、校园卡丢了怎么办、食堂在哪。\n点「初入清华园」，或直接问 AI。' },
  { e: '🤖', t: 'AI 都在做什么', b: '发布：文字 + 图片双审。\n雷达：自动比对全站失物与招领。\n侦探：按路线推理下一步。' },
  { e: '🚀', t: '开始你的拾光之旅', b: '右上角看通知，「我的」里管理发布。\n遇到问题，随时找我们。' }
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
</script>

<template>
  <div v-if="show" class="vue-tour">
    <div class="vt-card">
      <div class="vt-step">{{ index + 1 }} / {{ slides.length }}</div>
      <div class="vt-emoji">{{ slides[index].e }}</div>
      <div class="vt-title">{{ slides[index].t }}</div>
      <div class="vt-body">{{ slides[index].b }}</div>
      <div class="vt-dots"><i v-for="(s, i) in slides" :key="i" :class="{ on: i === index }" /></div>
      <div class="vt-actions">
        <button type="button" class="vt-skip" @click="close">跳过</button>
        <button type="button" class="vt-next" @click="next">{{ index === slides.length - 1 ? '开始使用' : '下一步' }}</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.vue-tour {
  position: fixed;
  inset: 0;
  z-index: 400;
  background: rgba(20, 8, 32, .42);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}
.vt-card {
  width: min(330px, 88vw);
  background: #fff;
  border-radius: 22px;
  padding: 22px;
  box-shadow: 0 24px 60px rgba(20, 8, 32, .3);
}
.vt-step { font-size: 9px; letter-spacing: .12em; color: #A99BB9; }
.vt-emoji { font-size: 40px; margin: 14px 0 6px; }
.vt-title { font-size: 21px; font-weight: 700; color: #241C2E; }
.vt-body { font-size: 12px; line-height: 1.8; color: #6B607A; margin-top: 8px; white-space: pre-line; }
.vt-dots { display: flex; gap: 4px; margin: 16px 0 18px; }
.vt-dots i { width: 5px; height: 5px; border-radius: 50%; background: #DCCBF2; }
.vt-dots i.on { width: 16px; border-radius: 99px; background: #5B2A91; }
.vt-actions { display: flex; gap: 8px; }
.vt-skip, .vt-next { flex: 1; border-radius: 12px; padding: 11px; font-family: inherit; font-size: 12px; font-weight: 600; }
.vt-skip { border: 1px solid #ECE6F4; background: #fff; color: #6B607A; }
.vt-next { border: 0; background: linear-gradient(135deg, #5B2A91, #7A3CB0); color: #fff; }
</style>

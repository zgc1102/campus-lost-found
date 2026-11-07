<script setup>
import { ref } from 'vue'

const emit = defineEmits(['nav'])
const question = ref('')

function ask() {
  const q = question.value.trim()
  if (q) sessionStorage.setItem('sg:ask:q', q)
  emit('nav', 'ask')
}
</script>

<template>
  <section class="screen active" id="screen-guideHome">
    <div class="topbar">
      <div class="back" @click="$emit('nav', 'home')">‹</div>
      <div class="t">清华园指路</div>
    </div>
    <div class="scroll">
      <div class="hero" style="padding:18px;margin-bottom:12px">
        <h1>初入清华园，你想问什么？</h1>
        <p>游客、新生、家长都能用：一键问 AI，或让学长学姐为你指路。</p>
      </div>

      <div class="guide-ai">
        <div class="gai-t">问 AI · 进校、吃饭、丢东西，什么都能问</div>
        <div class="gai-row">
          <input v-model="question" maxlength="120" placeholder="例如：访客怎么进校？校园卡丢了怎么办？">
          <button type="button" class="btn" @click="ask">问 AI</button>
        </div>
        <div class="gai-chips">
          <span @click="question = '访客怎么进清华？'">访客进校</span>
          <span @click="question = '校园卡丢了怎么办？'">校园卡丢了</span>
          <span @click="question = '清华哪个食堂好吃？'">食堂推荐</span>
          <span @click="question = '校园里哪里可以借雨伞？'">借雨伞</span>
        </div>
      </div>

      <div class="sectitle" style="margin-top:14px">选择你想用的服务</div>
      <button type="button" class="g-card" @click="$emit('nav', 'map')">
        <div style="width:46px;height:46px;border-radius:13px;display:flex;align-items:center;justify-content:center;font-size:22px">🗺️</div>
        <div><div>清华大学全景地图</div><div class="sa">文旅图风格全景导览，地标一目了然</div></div>
        <div class="gb-arrow">›</div>
      </button>
      <button type="button" class="g-card" style="margin-top:8px" @click="$emit('nav', 'faq')">
        <div style="width:46px;height:46px;border-radius:13px;display:flex;align-items:center;justify-content:center;font-size:22px">❓</div>
        <div><div>来清华常问的问题</div><div class="sa">图文结合的答案，新生 / 访客必看</div></div>
        <div class="gb-arrow">›</div>
      </button>
      <button type="button" class="g-card" style="margin-top:8px" @click="$emit('nav', 'phones')">
        <div style="width:46px;height:46px;border-radius:13px;display:flex;align-items:center;justify-content:center;font-size:22px">☎️</div>
        <div><div>常用电话</div><div class="sa">校医院、保卫部、后勤、招生办</div></div>
        <div class="gb-arrow">›</div>
      </button>
      <div class="sa" style="text-align:center;padding:16px 0">免登录即可浏览地图与问答</div>
    </div>
  </section>
</template>

<style scoped>
.g-card {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  text-align: left;
}
.g-card > div:nth-child(2) {
  flex: 1;
  min-width: 0;
}
.g-card .gb-arrow {
  color: #5B2A91;
}
.guide-ai .gai-row {
  display: flex;
  gap: 6px;
}
.guide-ai .gai-row input {
  flex: 1;
  min-width: 0;
}
</style>

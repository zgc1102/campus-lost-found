<script setup>
import { computed } from 'vue'

const emit = defineEmits(['nav'])
const memo = computed(() => {
  try { return JSON.parse(sessionStorage.getItem('sg:memo') || '{}') } catch (e) { return {} }
})
</script>

<template>
  <section class="screen active mem-detail" id="screen-memorial">
    <div class="topbar">
      <div class="back" @click="$emit('nav', 'home')">‹</div>
      <div class="t">中央宣传窗</div>
    </div>
    <div class="scroll">
      <div class="mem-detail-hero">
        <div class="mdh-star">{{ memo.star || '📌' }}</div>
        <div class="mdh-name">{{ memo.name || '校园公告' }}</div>
        <div class="mdh-sub">{{ memo.sub || '清华校园拾光里' }}</div>
      </div>
      <div class="form-card" style="padding:16px">
        <p style="font-size:12px;line-height:1.9;color:var(--ink);white-space:pre-wrap">{{ memo.body || '这是中央宣传窗的公告详情。公告会同步到首页轮播；如果你看到的是失物招领点调整，请以现场指示为准。' }}</p>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'

const emit = defineEmits(['nav'])
const memo = computed(() => {
  try { return JSON.parse(sessionStorage.getItem('sg:memo') || '{}') } catch (e) { return {} }
})
const blocks = computed(() => {
  if (Array.isArray(memo.value.blocks) && memo.value.blocks.length) return memo.value.blocks
  return [{
    h: '公告内容',
    p: [memo.value.body || '这是中央宣传窗的公告详情。公告会同步到首页轮播；如果你看到的是失物招领点调整，请以现场指示为准。']
  }]
})
</script>

<template>
  <section class="screen active mem-detail" id="screen-memorial">
    <div class="topbar">
      <div class="back" @click="$emit('nav', 'home')">‹</div>
      <div class="t">{{ memo.name || '中央宣传窗' }}</div>
    </div>
    <div class="scroll">
      <div class="sectitle">{{ memo.name || '校园公告' }} · {{ memo.sub || '清华校园拾光里' }}</div>
      <div v-for="(b, i) in blocks" :key="i" class="blk">
        <h3>{{ b.h }}</h3>
        <p v-for="(p, j) in b.p" :key="j">{{ p }}</p>
      </div>
    </div>
  </section>
</template>

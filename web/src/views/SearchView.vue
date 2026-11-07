<script setup>
import { computed, onMounted, ref } from 'vue'
import { api } from '../api'

const emit = defineEmits(['nav'])
const q = ref('')
const items = ref([])
const loading = ref(true)
const imgMode = ref(false)
const imgCat = ref('')
const samples = [
  { cat: 'umbrella', e: '🌂', name: '雨伞' },
  { cat: 'card', e: '💳', name: '校园卡' },
  { cat: 'electronics', e: '🎧', name: '耳机' },
  { cat: 'bottle', e: '🥤', name: '水杯' },
  { cat: 'bag', e: '🎒', name: '书包' },
  { cat: 'keys', e: '🔑', name: '钥匙' }
]

onMounted(async () => {
  try {
    const list = await api.items()
    if (Array.isArray(list)) items.value = list
  } finally {
    loading.value = false
  }
})

const results = computed(() => {
  const text = q.value.trim().toLowerCase()
  if (!text && !imgCat.value) return []
  return items.value
    .filter((x) => ['approved', 'claimed', 'closed'].includes(x.status))
    .filter((x) => !text || ((x.title || '') + (x.desc || '') + (x.place || '')).toLowerCase().includes(text))
    .filter((x) => !imgCat.value || x.cat === imgCat.value)
    .slice(0, 30)
})
function chooseSample(s) {
  imgMode.value = true
  imgCat.value = s.cat
  q.value = ''
}
function label(x) {
  return x.type === 'help' ? '求助' : x.type === 'lost' ? '寻物' : '招领'
}
</script>

<template>
  <section class="screen active" id="screen-search">
    <div class="topbar">
      <div class="back" @click="$emit('nav', 'home')">‹</div>
      <div class="t">搜索</div>
    </div>
    <div class="scroll">
      <div class="page-bar">
        <div class="pb-search">
          <svg class="pb-mag" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><path d="M16.5 16.5 21 21"/></svg>
          <input v-model="q" placeholder="搜索失物、寻物、求助">
        </div>
      </div>
      <button type="button" class="btn ghost" style="width:100%;margin-bottom:6px" @click="imgMode = !imgMode">🖼️ 以图搜图（演示）</button>
      <div v-if="imgMode" class="imgsearch-grid" style="display:grid">
        <button v-for="s in samples" :key="s.cat" type="button" :class="{ on: imgCat === s.cat }" @click="chooseSample(s)">
          <span>{{ s.e }}</span><b>{{ s.name }}</b>
        </button>
      </div>
      <div v-if="imgMode" class="hintline">以图搜图演示：点选一张示例图，按类别标签匹配相似物品（离线纯前端，非真实 AI 识别）。</div>
      <div v-if="loading" class="empty">正在读取…</div>
      <div v-else-if="!q.trim() && !imgCat" class="empty">输入关键词，或点一张示例图搜全站</div>
      <div v-else-if="!results.length" class="empty">没有找到相关内容</div>
      <div v-else class="vue-list">
        <article v-for="it in results" :key="it.id" class="item" @click="$emit('nav', it.type === 'help' ? 'help' : (it.type === 'lost' ? 'found' : 'lost'))">
          <div class="thumb">{{ it.type === 'help' ? '🤝' : '📦' }}</div>
          <div class="body">
            <div class="tt"><span class="src-tag">{{ label(it) }}</span>{{ it.title }}</div>
            <div class="dd">{{ it.desc }}</div>
            <div class="row"><span class="meta">📍 {{ it.place || '未填写地点' }}</span></div>
          </div>
        </article>
      </div>
    </div>
  </section>
</template>

<style scoped>
.imgsearch-grid { grid-template-columns: repeat(3, 1fr); gap: 8px; margin-bottom: 8px; }
.imgsearch-grid button { border: 1px solid var(--line); border-radius: 12px; background: #fff; padding: 12px 4px; font-family: inherit; }
.imgsearch-grid button span { display: block; font-size: 24px; }
.imgsearch-grid button b { display: block; font-size: 9px; color: var(--sub); margin-top: 3px; }
.imgsearch-grid button.on { border-color: #5B2A91; background: #F4EEFB; }
</style>

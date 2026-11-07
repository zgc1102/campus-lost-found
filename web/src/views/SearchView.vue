<script setup>
import { computed, onMounted, ref } from 'vue'
import { api } from '../api'

const emit = defineEmits(['nav'])
const q = ref('')
const items = ref([])
const loading = ref(true)

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
  if (!text) return []
  return items.value
    .filter((x) => ['approved', 'claimed', 'closed'].includes(x.status))
    .filter((x) => ((x.title || '') + (x.desc || '') + (x.place || '')).toLowerCase().includes(text))
    .slice(0, 30)
})
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
      <div v-if="loading" class="empty">正在读取…</div>
      <div v-else-if="!q.trim()" class="empty">输入关键词，搜全站失物与求助</div>
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

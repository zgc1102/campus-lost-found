<script setup>
import { onMounted, ref } from 'vue'
import { api } from '../api'

const emit = defineEmits(['nav'])
const items = ref([])
const loading = ref(true)
const unread = ref(0)

onMounted(load)
async function load() {
  loading.value = true
  try {
    const data = await api.notices()
    items.value = data.items || []
    unread.value = data.unread || 0
  } finally {
    loading.value = false
  }
}
async function readAll() {
  await api.readNotices()
  items.value = items.value.map((x) => ({ ...x, read: true }))
  unread.value = 0
}
function fmt(ts) {
  if (!ts) return ''
  const d = new Date(ts)
  return `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}
</script>

<template>
  <section class="screen active" id="screen-notices">
    <div class="topbar">
      <div class="back" @click="$emit('nav', 'home')">‹</div>
      <div class="t">通知</div>
      <button type="button" class="btn" @click="readAll">全部已读</button>
    </div>
    <div class="scroll">
      <div class="list-meta"><b>{{ unread }}</b> 条未读 · 匹配、认领、拾光码提醒都在这里</div>
      <div v-if="loading" class="empty">正在读取通知…</div>
      <div v-else-if="!items.length" class="empty">还没有通知</div>
      <div v-else class="vue-list">
        <article v-for="n in items" :key="n.id" class="item" :style="n.read ? 'opacity:.7' : ''">
          <div class="thumb">{{ n.type === 'pickup' ? '🔖' : n.type === 'match' ? '🔍' : '📥' }}</div>
          <div class="body">
            <div class="tt">{{ n.text }}</div>
            <div class="row"><span class="meta">{{ fmt(n.at) }}</span></div>
          </div>
        </article>
      </div>
    </div>
  </section>
</template>

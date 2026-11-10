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
function typeLabel(t) {
  return ({
    match: '🔍 相似物品提醒',
    claim: '📥 收到认领申请',
    accepted: '✅ 申请已通过',
    rejected: '❌ 申请被拒',
    done: '🎉 已完成归还',
    pickup: '🔖 拾光码提醒'
  })[t] || '通知'
}
function openNotice(n) {
  if (!n.itemId) return
  sessionStorage.setItem('sg:focusItem', n.itemId)
  const t = n.itemType === 'help' ? 'help' : n.itemType === 'lost' ? 'lost' : 'found'
  emit('nav', t)
}
function fmt(ts) {
  if (!ts) return ''
  const d = new Date(ts)
  return `${d.getMonth() + 1}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}
</script>

<template>
  <section class="screen active" id="screen-notices">
    <div class="topbar">
      <div class="back" @click="$emit('nav', 'home')">‹</div>
      <div class="t">通知</div>
    </div>
    <div class="scroll">
      <div v-if="loading" class="empty">正在读取通知…</div>
      <div v-else-if="!items.length" class="empty">还没有通知</div>
      <template v-else>
        <div
          v-for="n in items"
          :key="n.id"
          class="mini"
          :style="n.read ? 'opacity:.7' : ''"
          @click="openNotice(n)"
        >
          <div class="mh">{{ typeLabel(n.type) }}</div>
          <div class="mmeta">{{ n.text }}</div>
          <div v-if="n.type === 'claim' && n.claimId" class="mmeta" style="color:var(--purple)">
            点这里查看对方填了什么，与自己那条对比 →
          </div>
          <div class="mmeta">{{ fmt(n.at) }}</div>
        </div>
      </template>
      <div class="adm-link" @click="readAll">全部标为已读</div>
    </div>
  </section>
</template>

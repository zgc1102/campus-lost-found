<script setup>
import { onMounted, ref } from 'vue'
import { api } from '../api'

const emit = defineEmits(['nav', 'publish'])
const items = ref([])
const loading = ref(true)

onMounted(async () => {
  try {
    const list = await api.mine()
    if (Array.isArray(list)) items.value = list
  } finally {
    loading.value = false
  }
})
function status(x) {
  return ({ pending: '审核中', approved: '已上架', rejected: '已驳回', closed: '已闭环', claimed: '已认领' })[x.status] || x.status
}
function fmt(ts) {
  if (!ts) return ''
  const d = new Date(ts)
  return `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}
</script>

<template>
  <section class="screen active" id="screen-mine">
    <div class="topbar">
      <div class="back" @click="$emit('nav', 'home')">‹</div>
      <div class="t">我的发布</div>
      <button type="button" class="btn" @click="$emit('publish', 'lost')">发布</button>
    </div>
    <div class="scroll">
      <div class="hintline">这台设备上发布的启事和求助。登录/换设备同步后续再接入。</div>
      <div v-if="loading" class="empty">正在读取…</div>
      <div v-else-if="!items.length" class="empty">还没有发布，点右上角「发布」写一条</div>
      <div v-else class="vue-list">
        <article v-for="it in items" :key="it.id" class="item">
          <div class="thumb">{{ it.type === 'help' ? '🤝' : (it.type === 'lost' ? '🔎' : '📦') }}</div>
          <div class="body">
            <div class="tt"><span class="src-tag">{{ it.type === 'help' ? '求助' : (it.type === 'lost' ? '寻物' : '招领') }}</span>{{ it.title }}</div>
            <div class="dd">{{ it.desc }}</div>
            <div class="row">
              <span class="meta">{{ status(it) }} · {{ fmt(it.createdAt) }}</span>
              <button type="button" class="btn" @click="$emit('publish', it.type === 'help' ? 'help' : it.type)">再发一条</button>
            </div>
          </div>
        </article>
      </div>
    </div>
  </section>
</template>

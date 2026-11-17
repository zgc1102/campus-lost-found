<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { api } from '../api'
const props = defineProps({
  claimId: { type: String, default: '' },
  closed: { type: Boolean, default: false }
})
const messages = ref([])
const text = ref('')
const loading = ref(false)
const error = ref('')
const outbox = ref([])
const side = ref('')
let refreshTimer = null
function key(m) {
  return m.id || m.clientMsgId || `${m.from}|${m.at}|${m.text}`
}
function timeOf(at) {
  const d = new Date(Number(at) || 0)
  if (!Number.isFinite(d.getTime())) return ''
  const now = new Date()
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const target = new Date(d.getFullYear(), d.getMonth(), d.getDate())
  const hm = `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
  if (target.getTime() === today.getTime()) return hm
  const yesterday = new Date(today.getTime() - 86400000)
  if (target.getTime() === yesterday.getTime()) return `昨天 ${hm}`
  return `${d.getMonth() + 1}-${String(d.getDate()).padStart(2, '0')} ${hm}`
}
const displayMessages = computed(() => {
  const rows = [
    ...messages.value.map((m) => ({ ...m, pending: false })),
    ...outbox.value.map((m) => ({ ...m, pending: true }))
  ]
  return rows.sort((a, b) => Number(a.at || 0) - Number(b.at || 0))
})
async function load(silent = false) {
  if (!props.claimId) return
  if (!silent) loading.value = true
  error.value = ''
  try {
    const r = await api.helpClaimMessages(props.claimId)
    side.value = r.side || side.value
    const merged = new Map()
    for (const m of messages.value) merged.set(key(m), m)
    for (const m of (r.messages || [])) merged.set(key(m), m)
    messages.value = [...merged.values()].sort((a, b) => Number(a.at || 0) - Number(b.at || 0))
    const ids = new Set(messages.value.map((m) => m.clientMsgId).filter(Boolean))
    outbox.value = outbox.value.filter((m) => !m.clientMsgId || !ids.has(m.clientMsgId))
  } catch (e) {
    error.value = e.message || '聊天记录加载失败'
  } finally {
    if (!silent) loading.value = false
  }
}
function scheduleRefresh() {
  if (refreshTimer) clearTimeout(refreshTimer)
  refreshTimer = setTimeout(() => load(true), 350)
}
function send() {
  const t = text.value.trim()
  if (!t || props.closed) return
  const item = {
    clientMsgId: 'hc_' + Date.now() + '_' + Math.random().toString(16).slice(2),
    text: t,
    at: Date.now(),
    status: 'queued'
  }
  outbox.value.push(item)
  text.value = ''
  deliver(item)
}
async function deliver(item) {
  if (!item || item.status === 'sending') return
  item.status = 'sending'
  item.error = ''
  try {
    const r = await api.helpClaimSend(props.claimId, item.text, item.clientMsgId)
    if (r?.message) {
      const k = key(r.message)
      if (!messages.value.some((m) => key(m) === k)) messages.value.push(r.message)
      messages.value = [...messages.value].sort((a, b) => Number(a.at || 0) - Number(b.at || 0))
      outbox.value = outbox.value.filter((x) => x.clientMsgId !== item.clientMsgId)
    }
    scheduleRefresh()
  } catch (e) {
    item.status = 'failed'
    item.error = e.message || '发送失败'
  }
}
onMounted(load)
watch(() => props.claimId, () => { messages.value = []; outbox.value = []; load() })
</script>

<template>
  <div class="hc-card">
    <div class="hc-title">爱心捐赠 · 匿名沟通</div>
    <div class="hc-hint">这里只用于沟通捐赠细节，不会自动公开手机号。</div>
    <div v-if="loading && !displayMessages.length" class="hc-empty">正在加载消息…</div>
    <div v-else-if="!displayMessages.length" class="hc-empty">还没有消息，可以先打个招呼。</div>
    <div v-for="m in displayMessages" :key="key(m)" class="hc-row" :class="{ mine: m.from ? m.from === side : true, pending: m.pending }">
      <span>
        <template v-if="m.status === 'failed'">! {{ m.text }}</template>
        <template v-else>{{ m.text }}</template>
        <em class="hc-time">{{ m.pending ? (m.status === 'failed' ? '发送失败，点击重试' : '正在发布中…') : timeOf(m.at) }}</em>
      </span>
      <button v-if="m.status === 'failed'" type="button" class="hc-retry" @click="deliver(m)">重试</button>
    </div>
    <div v-if="error" class="hc-error">{{ error }}</div>
    <div v-if="closed" class="hc-closed">这次沟通已经结束。</div>
    <div v-else class="hc-input">
      <input v-model="text" maxlength="200" placeholder="回复对方，不需要暴露手机号" @keyup.enter="send">
      <button type="button" :disabled="!text.trim()" @click="send">发送</button>
    </div>
    <button type="button" class="hc-refresh" :disabled="loading" @click="load">{{ loading ? '刷新中…' : '刷新消息' }}</button>
  </div>
</template>

<style scoped>
.hc-card { background:#fff; border:1px solid #EADFF5; border-radius:12px; padding:11px; margin-top:10px; }
.hc-title { font-size:11px; font-weight:600; color:#3B1D63; }
.hc-hint { font-size:8.5px; color:#8E7FA3; margin:4px 0 8px; line-height:1.6; }
.hc-empty { font-size:9px; color:#9A8CAB; padding:8px 0; }
.hc-row { display:flex; margin:5px 0; }
.hc-row span { max-width:82%; font-size:10px; line-height:1.6; padding:7px 9px; border-radius:10px; background:#F4EEFB; color:#4E445D; }
.hc-row.mine { justify-content:flex-end; }
.hc-row.mine span { background:#5B2A91; color:#fff; }
.hc-input { display:flex; gap:6px; margin-top:8px; }
.hc-input input { flex:1; min-width:0; background:#FAF7FE; border:1px solid #EADFF5; border-radius:9px; padding:8px; font-family:inherit; font-size:10.5px; }
.hc-input button { border:0; background:#5B2A91; color:#fff; border-radius:9px; padding:0 10px; font-family:inherit; font-size:10px; }
.hc-refresh { border:0; background:none; color:#7E6E92; font-size:8.5px; padding:6px 0 0; cursor:pointer; font-family:inherit; }
.hc-error { color:#C0392B; font-size:9px; margin-top:5px; }
.hc-closed { color:#7E6E92; background:#F3F0F7; border-radius:7px; padding:7px; font-size:9px; margin-top:7px; }
.hc-fail { display:block; font-style:normal; color:#FFD9D9; font-size:8px; margin-top:3px; }
</style>
<style scoped>
.hc-row.pending span { opacity:.7; }
.hc-time { display:block; margin-top:3px; font-style:normal; font-size:7.5px; opacity:.65; text-align:right; }
.hc-row.mine .hc-time { color:#F0E6FF; }
.hc-retry { margin-left:5px; align-self:center; border:1px solid #E7B9AE; background:#fff; color:#A23B2A; border-radius:7px; padding:3px 7px; font-family:inherit; font-size:8px; }
</style>

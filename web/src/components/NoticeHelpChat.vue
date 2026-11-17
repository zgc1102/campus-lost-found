<script setup>
import { onMounted, ref, watch } from 'vue'
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
function key(m) {
  return m.id || `${m.from}|${m.at}|${m.text}`
}
async function load() {
  if (!props.claimId) return
  loading.value = true
  error.value = ''
  try {
    const r = await api.helpClaimMessages(props.claimId)
    side.value = r.side || side.value
    const merged = new Map()
    for (const m of messages.value) merged.set(key(m), m)
    for (const m of (r.messages || [])) merged.set(key(m), m)
    messages.value = [...merged.values()].sort((a, b) => Number(a.at || 0) - Number(b.at || 0))
  } catch (e) {
    error.value = e.message || '聊天记录加载失败'
  } finally {
    loading.value = false
  }
}
function send() {
  const t = text.value.trim()
  if (!t || props.closed) return
  const item = { clientMsgId: 'hc_' + Date.now() + '_' + Math.random().toString(16).slice(2), text: t }
  outbox.value.push(item)
  text.value = ''
  deliver(item)
}
async function deliver(item) {
  try {
    await api.helpClaimSend(props.claimId, item.text, item.clientMsgId)
    outbox.value = outbox.value.filter((x) => x.clientMsgId !== item.clientMsgId)
    await load()
  } catch (e) {
    item.error = e.message || '发送失败'
  }
}
onMounted(load)
watch(() => props.claimId, load)
</script>

<template>
  <div class="hc-card">
    <div class="hc-title">爱心捐赠 · 匿名沟通</div>
    <div class="hc-hint">这里只用于沟通捐赠细节，不会自动公开手机号。</div>
    <div v-if="loading" class="hc-empty">正在加载消息…</div>
    <div v-else-if="!messages.length && !outbox.length" class="hc-empty">还没有消息，可以先打个招呼。</div>
    <div v-for="m in messages" :key="key(m)" class="hc-row" :class="{ mine: m.from === side }">
      <span>{{ m.text }}</span>
    </div>
    <div v-for="m in outbox" :key="m.clientMsgId" class="hc-row mine">
      <span>{{ m.text }}<i v-if="m.error" class="hc-fail" @click="deliver(m)">发送失败，点此重试</i></span>
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

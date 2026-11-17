<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { api } from '../api'

const props = defineProps({
  claimId: { type: String, default: '' },
  closed: { type: Boolean, default: false },
  placeholder: { type: String, default: '回复对方，不需要暴露手机号' }
})

const messages = ref([])
const outbox = ref([])
const text = ref('')
const loading = ref(false)
const error = ref('')
const side = ref('owner')
const blocked = ref(false)
const blockedBy = ref('')
let refreshTimer = null

function key(m) {
  return m.id || m.clientMsgId || `${m.from || ''}|${m.at || ''}|${m.text || ''}`
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
const display = computed(() => {
  const rows = [
    ...messages.value.map((m) => ({ ...m, pending: false })),
    ...outbox.value.map((m) => ({ ...m, pending: true }))
  ]
  return rows.sort((a, b) => Number(a.at || 0) - Number(b.at || 0))
})

async function load(incremental = false) {
  if (!props.claimId) return
  if (!incremental && !messages.value.length) loading.value = true
  error.value = ''
  try {
    const last = incremental && messages.value.length ? messages.value[messages.value.length - 1] : null
    const r = await api.claimMessages(props.claimId, last?.id || '', last?.at || 0)
    side.value = r.side || side.value
    if (r.blocked) {
      blocked.value = true
      blockedBy.value = r.blockedBy || ''
      messages.value = []
      outbox.value = []
      return
    }
    blocked.value = false
    const merged = new Map()
    for (const m of messages.value) merged.set(key(m), m)
    for (const m of (r.messages || [])) merged.set(key(m), m)
    messages.value = [...merged.values()].sort((a, b) => Number(a.at || 0) - Number(b.at || 0))
    const ids = new Set(messages.value.map((m) => m.clientMsgId).filter(Boolean))
    outbox.value = outbox.value.filter((m) => !m.clientMsgId || !ids.has(m.clientMsgId))
  } catch (e) {
    error.value = e.message || '聊天记录加载失败'
  } finally {
    loading.value = false
  }
}

function scheduleLoad() {
  if (refreshTimer) clearTimeout(refreshTimer)
  refreshTimer = setTimeout(() => load(true), 400)
}

function send() {
  const t = text.value.trim()
  if (!t || props.closed || blocked.value) return
  const item = {
    clientMsgId: 'cc_' + Date.now() + '_' + Math.random().toString(16).slice(2),
    text: t,
    at: Date.now(),
    from: side.value,
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
    const r = await api.claimSend(props.claimId, item.text, item.clientMsgId)
    if (r?.message) {
      const k = key(r.message)
      if (!messages.value.some((m) => key(m) === k)) messages.value.push(r.message)
      messages.value = [...messages.value].sort((a, b) => Number(a.at || 0) - Number(b.at || 0))
      outbox.value = outbox.value.filter((x) => x.clientMsgId !== item.clientMsgId)
    }
    scheduleLoad()
  } catch (e) {
    item.status = 'failed'
    item.error = e.message || '发送失败'
    if (e.body?.blocked) {
      blocked.value = true
      blockedBy.value = side.value === 'owner' ? 'claimer' : 'owner'
    }
  }
}

function retry(item) {
  if (!item || item.status === 'sending') return
  deliver(item)
}

onMounted(() => load(false))
watch(() => props.claimId, () => {
  messages.value = []
  outbox.value = []
  blocked.value = false
  load(false)
})
</script>

<template>
  <div class="cc-card">
    <div class="cc-title">匿名沟通</div>
    <div class="cc-safety">
      <b>安全提示</b>
      <span>平台不会索要验证码、支付密码，也不会要求转账、扫码付款或代付。对方若主动索要二维码、付款码、验证码，或让你先转账，请立即停止并举报。</span>
    </div>
    <div v-if="blocked" class="cc-blocked">
      <b>{{ blockedBy === side ? '你已屏蔽对方' : '对方已屏蔽你' }}</b>
      <span>双方都不能再看到对方的新消息，也不能再发送消息。</span>
    </div>
    <template v-else>
      <div v-if="error" class="cc-error">
        <span>聊天记录加载失败：{{ error }}</span>
        <button type="button" @click="load(false)">重试</button>
      </div>
      <div v-if="loading && !display.length" class="cc-empty">正在加载聊天记录…</div>
      <div v-else-if="!display.length" class="cc-empty">还没有消息，可以先回复对方。</div>
      <div v-for="m in display" :key="key(m)" class="cc-row" :class="{ mine: (m.from || side) === side, pending: m.pending }">
        <span>
          <template v-if="m.status === 'failed'">! {{ m.text }}</template>
          <template v-else>{{ m.text }}</template>
          <em class="cc-time">{{ m.pending ? (m.status === 'failed' ? '发送失败，点此重试' : '正在发布中…') : timeOf(m.at) }}</em>
        </span>
        <button v-if="m.status === 'failed'" type="button" class="cc-retry" @click="retry(m)">重试</button>
      </div>
      <div v-if="!closed" class="cc-input">
        <input v-model="text" maxlength="200" :placeholder="placeholder" @keyup.enter="send">
        <button type="button" :disabled="!text.trim()" @click="send">发送</button>
      </div>
      <div v-if="!closed" class="cc-foot">
        <button type="button" class="cc-refresh" :disabled="loading" @click="load(false)">{{ loading ? '刷新中…' : '刷新消息' }}</button>
        <span class="cc-hint">发送后会自动拉取对方的新消息（可能多条）；也可以点“刷新消息”手动获取。</span>
      </div>
      <div v-else class="cc-closed">这次沟通已经结束，不能再发送新消息。</div>
    </template>
  </div>
</template>

<style scoped>
.cc-card { background:#fff; border:1px solid #EFE7F7; border-radius:13px; padding:11px 12px; margin-top:10px; }
.cc-title { font-size:10px; font-weight:600; color:#5B2A91; margin-bottom:6px; }
.cc-safety { margin:7px 0 9px; padding:8px 9px; border-radius:9px; background:#FFF8E8; border:1px solid #F0D9A8; display:flex; flex-direction:column; gap:3px; }
.cc-safety b { font-size:9px; color:#9A6414; }
.cc-safety span { font-size:8.5px; line-height:1.6; color:#806A45; }
.cc-blocked { margin:8px 0; padding:9px 10px; border-radius:9px; background:#F3F0F7; border:1px solid #DED4EA; display:flex; flex-direction:column; gap:3px; }
.cc-blocked b { font-size:10px; color:#5B2A91; }
.cc-blocked span { font-size:8.5px; line-height:1.6; color:#7E6E92; }
.cc-row { display:flex; margin:5px 0; }
.cc-row span { max-width:82%; font-size:11px; line-height:1.6; padding:7px 9px; border-radius:10px; background:#F4EEFB; color:#4E445D; }
.cc-row.mine { justify-content:flex-end; }
.cc-row.mine span { background:#5B2A91; color:#fff; }
.cc-time { display:block; margin-top:3px; font-style:normal; font-size:7.5px; opacity:.62; text-align:right; }
.cc-row.pending span { opacity:.7; }
.cc-row .failed { background:#FFF1EE !important; color:#A23B2A !important; border:1px solid #F0C4B8; }
.cc-retry { margin-left:5px; align-self:center; border:1px solid #E7B9AE; background:#fff; color:#A23B2A; border-radius:7px; padding:3px 7px; font-family:inherit; font-size:8px; }
.cc-input { display:flex; gap:6px; margin-top:8px; }
.cc-input input { flex:1; min-width:0; background:#FAF7FE; border:1px solid #EADFF5; border-radius:9px; padding:8px; font-family:inherit; font-size:10.5px; }
.cc-input button { border:0; background:#5B2A91; color:#fff; border-radius:9px; padding:0 10px; font-family:inherit; font-size:10px; }
.cc-foot { display:flex; align-items:center; gap:8px; margin-top:7px; flex-wrap:wrap; }
.cc-refresh { border:1px solid #D9C8EE; background:#fff; color:#5B2A91; border-radius:7px; padding:4px 8px; font-family:inherit; font-size:8.5px; }
.cc-refresh:disabled { opacity:.5; }
.cc-hint { margin:0; flex:1; min-width:150px; font-size:8px; line-height:1.5; color:#8E7FA3; }
.cc-error { display:flex; align-items:center; justify-content:space-between; gap:6px; padding:7px 0; font-size:9px; color:#A23B2A; }
.cc-error button { border:1px solid #E7B9AE; background:#fff; color:#A23B2A; border-radius:7px; padding:3px 8px; font-family:inherit; font-size:9px; }
.cc-empty { font-size:9.5px; line-height:1.7; color:#6F607F; }
.cc-closed { margin-top:8px; padding:8px 9px; border-radius:8px; background:#F3F0F7; font-size:9px; color:#7E6E92; }
</style>

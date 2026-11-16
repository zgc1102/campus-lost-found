<script setup>
import { ref } from 'vue'

const props = defineProps({
  messages: { type: Array, default: () => [] },
  outbox: { type: Array, default: () => [] },
  side: { type: String, default: 'owner' },
  loading: { type: Boolean, default: false },
  error: { type: String, default: '' },
  blocked: { type: Boolean, default: false },
  blockedBy: { type: String, default: '' },
  placeholder: { type: String, default: '回复对方，不需要暴露手机号' }
})
const emit = defineEmits(['send', 'retry', 'refresh'])
const text = ref('')

function keyOf(m) {
  if (!m) return ''
  return m.id || `${m.from || ''}|${m.at || ''}|${m.text || ''}`
}
function timeOf(at) {
  const d = new Date(Number(at) || 0)
  if (!Number.isFinite(d.getTime())) return ''
  const now = new Date()
  const day = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const target = new Date(d.getFullYear(), d.getMonth(), d.getDate())
  const hm = `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
  if (target.getTime() === day.getTime()) return hm
  const y = new Date(day.getTime() - 86400000)
  if (target.getTime() === y.getTime()) return `昨天 ${hm}`
  return `${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${hm}`
}
function send() {
  const t = text.value.trim()
  if (!t || props.blocked) return
  emit('send', t)
  text.value = ''
}
</script>

<template>
  <div class="nd-card">
    <div class="nd-card-title">匿名沟通</div>
    <div class="nd-safety">
      <b>安全提示</b>
      <span>平台不会索要验证码、支付密码，也不会要求转账、扫码付款或代付。对方若主动索要二维码、付款码、验证码，或让你先转账，请立即停止并举报。官方拾光码只用于物品留言，不会要求付款；陌生人私发的二维码，一律不要扫。</span>
    </div>
    <div v-if="blocked" class="nd-blocked">
      <b>{{ blockedBy === side ? '你已屏蔽对方' : '对方已屏蔽你' }}</b>
      <span>双方都不能再看到对方的新消息，也不能再发送消息。</span>
    </div>
    <template v-else>
      <div v-if="error" class="nd-chat-error">
        <span>聊天记录加载失败：{{ error }}</span>
        <button type="button" @click="$emit('refresh')">重试</button>
      </div>
      <div v-if="loading && !messages.length" class="nd-message" style="color:#8E7FA3">正在加载聊天记录…</div>
      <template v-if="!loading || messages.length">
        <div v-if="!messages.length && !outbox.length" class="nd-message" style="color:#8E7FA3">还没有消息，可以先回复对方。</div>
        <div v-for="m in messages" :key="keyOf(m)" class="nd-chat" :class="m.from === side ? 'mine' : 'other'">
          <span>{{ m.text }}<em class="nd-chat-time">{{ timeOf(m.at) }}</em></span>
        </div>
        <div v-for="m in outbox" :key="m.clientMsgId" class="nd-chat" :class="m.from === side ? 'mine' : 'other'">
          <span class="pending" :class="{ failed: m.status === 'failed' }">
            <template v-if="m.status === 'failed'">! {{ m.text }}</template>
            <template v-else>{{ m.text }}</template>
            <em class="nd-chat-time">{{ m.status === 'failed' ? '发送失败，点击重试' : '发送中…' }}</em>
          </span>
          <button v-if="m.status === 'failed'" type="button" class="nd-retry" @click="$emit('retry', m)">重试</button>
        </div>
      </template>
      <div class="nd-chat-input">
        <input v-model="text" maxlength="200" :placeholder="placeholder" @keyup.enter="send">
        <button type="button" :disabled="!text.trim()" @click="send">发送</button>
      </div>
      <div class="nd-chat-foot">
        <button type="button" class="nd-chat-refresh" :disabled="loading" @click="$emit('refresh')">{{ loading ? '刷新中…' : '刷新消息' }}</button>
        <span class="nd-chat-help">对方新消息不会自动弹出，点“刷新消息”获取最新回复；发送失败的消息可点“重试”。</span>
      </div>
    </template>
  </div>
</template>

<style scoped>
.nd-safety { margin:7px 0 9px; padding:8px 9px; border-radius:9px; background:#FFF8E8; border:1px solid #F0D9A8; display:flex; flex-direction:column; gap:3px; }
.nd-safety b { font-size:9px; color:#9A6414; }
.nd-safety span { font-size:8.5px; line-height:1.6; color:#806A45; }
.nd-blocked { margin:8px 0; padding:9px 10px; border-radius:9px; background:#F3F0F7; border:1px solid #DED4EA; display:flex; flex-direction:column; gap:3px; }
.nd-blocked b { font-size:10px; color:#5B2A91; }
.nd-blocked span { font-size:8.5px; line-height:1.6; color:#7E6E92; }
.nd-chat { display:flex; margin:5px 0; }
.nd-chat span { max-width:82%; font-size:11px; line-height:1.6; padding:7px 9px; border-radius:10px; background:#F4EEFB; color:#4E445D; }
.nd-chat.mine { justify-content:flex-end; }
.nd-chat.mine span { background:#5B2A91; color:#fff; }
.nd-chat-time { display:block; margin-top:3px; font-style:normal; font-size:7.5px; opacity:.62; text-align:right; }
.nd-chat .pending { opacity:.62; }
.nd-chat .failed { background:#FFF1EE !important; color:#A23B2A !important; border:1px solid #F0C4B8; }
.nd-chat-input { display:flex; gap:6px; margin-top:8px; }
.nd-chat-input input { flex:1; min-width:0; background:#FAF7FE; border:1px solid #EADFF5; border-radius:9px; padding:8px; font-family:inherit; font-size:10.5px; }
.nd-chat-input button { border:0; background:#5B2A91; color:#fff; border-radius:9px; padding:0 10px; font-family:inherit; font-size:10px; }
.nd-chat-foot { display:flex; align-items:center; gap:8px; margin-top:7px; flex-wrap:wrap; }
.nd-chat-refresh { border:1px solid #D9C8EE; background:#fff; color:#5B2A91; border-radius:7px; padding:4px 8px; font-family:inherit; font-size:8.5px; }
.nd-chat-refresh:disabled { opacity:.5; }
.nd-chat-help { margin:0; flex:1; min-width:150px; font-size:8px; line-height:1.5; color:#8E7FA3; }
.nd-chat-error { display:flex; align-items:center; justify-content:space-between; gap:6px; padding:7px 0; font-size:9px; color:#A23B2A; }
.nd-chat-error button { border:1px solid #E7B9AE; background:#fff; color:#A23B2A; border-radius:7px; padding:3px 8px; font-family:inherit; font-size:9px; }
.nd-retry { margin-left:5px; align-self:center; border:1px solid #E7B9AE; background:#fff; color:#A23B2A; border-radius:7px; padding:3px 7px; font-family:inherit; font-size:8px; }
.nd-message { font-size:9.5px; line-height:1.7; color:#6F607F; }
.nd-card { background:#fff; border:1px solid #EFE7F7; border-radius:13px; padding:11px 12px; margin-top:10px; }
.nd-card-title { font-size:10px; font-weight:600; color:#5B2A91; margin-bottom:6px; }
</style>

<script setup>
import { ref } from 'vue'
import { api } from '../api'

const props = defineProps({
  kind: { type: String, required: true },
  targetId: { type: String, required: true },
  itemTitle: { type: String, default: '' },
  messageId: { type: String, default: '' }
})
const emit = defineEmits(['close', 'submitted'])
const reason = ref('言语骚扰')
const detail = ref('')
const scope = ref(props.messageId ? 'message' : 'chat')
const busy = ref(false)
const error = ref('')
const done = ref(false)

const reasons = [
  '言语骚扰',
  '辱骂威胁',
  '色情擦边',
  '诈骗/转账',
  '广告刷屏',
  '代考/作弊',
  '侵权/隐私',
  '其他'
]

async function submit() {
  if (busy.value) return
  if (!reason.value) {
    error.value = '请选择举报分类'
    return
  }
  busy.value = true
  error.value = ''
  try {
    await api.submitReport({
      kind: props.kind,
      targetId: props.targetId,
      reason: reason.value,
      detail: detail.value.trim(),
      scope: scope.value,
      messageId: props.messageId || ''
    })
    done.value = true
    emit('submitted')
  } catch (e) {
    error.value = e.message || '举报提交失败'
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <div class="rp-overlay" @click.self="emit('close')">
    <div class="rp-card">
      <button type="button" class="rp-x" @click="emit('close')">✕</button>
      <div class="rp-kicker">安全举报</div>
      <h3>{{ done ? '举报已提交' : '举报这次沟通' }}</h3>
      <p v-if="itemTitle" class="rp-item">《{{ itemTitle }}》</p>

      <template v-if="!done">
        <label class="rp-label">举报分类</label>
        <div class="rp-tags">
          <button v-for="r in reasons" :key="r" type="button" :class="{ on: reason === r }" @click="reason = r">{{ r }}</button>
        </div>

        <label class="rp-label">举报范围</label>
        <div class="rp-tags">
          <button type="button" :class="{ on: scope === 'message' }" @click="scope = 'message'">这一条消息</button>
          <button type="button" :class="{ on: scope === 'chat' }" @click="scope = 'chat'">整段聊天</button>
        </div>

        <label class="rp-label">补充说明（可选）</label>
        <textarea v-model="detail" maxlength="500" placeholder="请简单描述发生了什么，方便安全审核判断"></textarea>

        <p class="rp-note">举报后 AI 会审核相关聊天内容。审核期间请继续使用平台沟通。举报人身份不会展示给对方。</p>
        <div v-if="error" class="rp-error">{{ error }}</div>

        <div class="rp-actions">
          <button type="button" class="rp-primary" :disabled="busy" @click="submit">{{ busy ? '提交中…' : '提交举报' }}</button>
          <button type="button" class="rp-ghost" @click="emit('close')">取消</button>
        </div>
      </template>

      <template v-else>
        <p class="rp-done">AI 安全审核已介入。本次聊天内容仅用于安全判断，不会公开展示。</p>
        <p class="rp-done-sub">审核结果会记录在管理端。请你继续正常沟通，不要继续发送不当内容。</p>
        <div class="rp-actions">
          <button type="button" class="rp-primary" @click="emit('close')">知道了</button>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.rp-overlay { position:fixed; inset:0; z-index:1400; background:rgba(35,22,48,.55); display:flex; align-items:center; justify-content:center; padding:20px; }
.rp-card { width:min(460px,94vw); max-height:90vh; overflow:auto; background:#fff; border-radius:16px; padding:16px; box-shadow:0 18px 50px rgba(0,0,0,.25); position:relative; }
.rp-x { position:absolute; right:10px; top:9px; border:0; background:#F3EEFA; color:#5B2A91; width:25px; height:25px; border-radius:50%; }
.rp-kicker { font-size:9px; letter-spacing:.12em; color:#A99BB9; }
.rp-card h3 { margin:3px 0 8px; font-size:16px; color:#3B1D63; }
.rp-item { margin:0 0 10px; font-size:10px; color:#7E6E92; }
.rp-label { display:block; margin:9px 0 5px; font-size:9px; font-weight:600; color:#5B2A91; }
.rp-tags { display:flex; flex-wrap:wrap; gap:5px; }
.rp-tags button { border:1px solid #E6D8F3; background:#fff; color:#6F607F; border-radius:7px; padding:4px 7px; font-family:inherit; font-size:9px; }
.rp-tags button.on { background:#F1E8FB; border-color:#C9A9E8; color:#5B2A91; }
.rp-card textarea { width:100%; box-sizing:border-box; min-height:62px; background:#FAF7FE; border:1px solid #EADFF5; border-radius:9px; padding:8px; font-family:inherit; font-size:10px; }
.rp-note { margin:9px 0 0; font-size:8.5px; line-height:1.6; color:#8E7FA3; }
.rp-error { margin-top:7px; color:#A23B2A; font-size:9px; }
.rp-actions { display:flex; gap:7px; margin-top:12px; }
.rp-primary, .rp-ghost { flex:1; border-radius:8px; padding:8px; font-family:inherit; font-size:10px; }
.rp-primary { border:0; background:#5B2A91; color:#fff; }
.rp-primary:disabled { opacity:.55; }
.rp-ghost { border:1px solid #D9C8EE; background:#fff; color:#5B2A91; }
.rp-done { margin:5px 0 0; font-size:10.5px; line-height:1.7; color:#3B1D63; }
.rp-done-sub { margin:5px 0 0; font-size:9px; line-height:1.6; color:#7E6E92; }
</style>

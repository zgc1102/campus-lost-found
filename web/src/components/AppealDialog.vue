<script setup>
import { ref } from 'vue'
import { api } from '../api'

const props = defineProps({
  reportId: { type: String, required: true },
  kind: { type: String, default: '' },
  targetId: { type: String, default: '' }
})
const emit = defineEmits(['close', 'submitted'])
const reason = ref('')
const busy = ref(false)
const error = ref('')
const done = ref(false)

async function submit() {
  if (busy.value) return
  if (reason.value.trim().length < 5) {
    error.value = '请至少写 5 个字说明申诉理由'
    return
  }
  busy.value = true
  error.value = ''
  try {
    await api.submitAppeal({
      reportId: props.reportId,
      alertId: props.reportId,
      reason: reason.value.trim(),
      kind: props.kind,
      targetId: props.targetId
    })
    done.value = true
    emit('submitted')
  } catch (e) {
    error.value = e.message || '申诉提交失败'
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <div class="ap-overlay" @click.self="emit('close')">
    <div class="ap-card">
      <button type="button" class="ap-x" @click="emit('close')">✕</button>
      <div class="ap-kicker">申诉入口</div>
      <h3>{{ done ? '申诉已提交' : '对本次处理提出申诉' }}</h3>
      <template v-if="!done">
        <p class="ap-note">申诉会记录处理编号、你的说明和时间。审核期间原处理仍然有效。</p>
        <label>申诉理由</label>
        <textarea v-model="reason" maxlength="1000" placeholder="请说明你认为误判的原因，例如上下文被误解、对方先挑衅等"></textarea>
        <div v-if="error" class="ap-error">{{ error }}</div>
        <div class="ap-actions">
          <button type="button" class="ap-primary" :disabled="busy" @click="submit">{{ busy ? '提交中…' : '提交申诉' }}</button>
          <button type="button" class="ap-ghost" @click="emit('close')">取消</button>
        </div>
      </template>
      <template v-else>
        <p class="ap-note">申诉记录已保存。管理员复核后，如果通过，会解除对应的聊天暂停。</p>
        <button type="button" class="ap-primary" @click="emit('close')">知道了</button>
      </template>
    </div>
  </div>
</template>

<style scoped>
.ap-overlay { position:fixed; inset:0; z-index:1600; background:rgba(35,22,48,.58); display:flex; align-items:center; justify-content:center; padding:20px; }
.ap-card { width:min(440px,94vw); background:#fff; border-radius:15px; padding:16px; box-shadow:0 16px 45px rgba(0,0,0,.25); position:relative; }
.ap-x { position:absolute; right:10px; top:9px; border:0; background:#F3EEFA; color:#5B2A91; width:25px; height:25px; border-radius:50%; }
.ap-kicker { font-size:9px; letter-spacing:.12em; color:#A99BB9; }
.ap-card h3 { margin:3px 0 8px; font-size:15px; color:#3B1D63; }
.ap-note { margin:0 0 9px; font-size:9px; line-height:1.6; color:#8E7FA3; }
.ap-card label { display:block; margin:8px 0 5px; font-size:9px; font-weight:600; color:#5B2A91; }
.ap-card textarea { width:100%; box-sizing:border-box; min-height:90px; background:#FAF7FE; border:1px solid #EADFF5; border-radius:9px; padding:8px; font-family:inherit; font-size:10px; }
.ap-error { margin-top:6px; font-size:9px; color:#A23B2A; }
.ap-actions { display:flex; gap:7px; margin-top:11px; }
.ap-primary, .ap-ghost { flex:1; border-radius:8px; padding:8px; font-family:inherit; font-size:10px; }
.ap-primary { border:0; background:#5B2A91; color:#fff; }
.ap-primary:disabled { opacity:.55; }
.ap-ghost { border:1px solid #D9C8EE; background:#fff; color:#5B2A91; }
</style>

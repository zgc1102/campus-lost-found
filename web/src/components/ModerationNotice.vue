<script setup>
import { onMounted, onUnmounted, ref, watch } from 'vue'
import { api } from '../api'

const props = defineProps({
  kind: { type: String, required: true },
  targetId: { type: String, default: '' }
})

const active = ref(false)
const status = ref('')
const warning = ref('')
const counterpartNotice = ref('')
const reportId = ref('')
const showWarning = ref(false)
const showCounterpart = ref(false)
let timer = null

function seenKey(id) {
  return 'sg:moderation-warning:' + id
}
function apply(state) {
  active.value = Boolean(state?.active)
  status.value = state?.status || ''
  warning.value = state?.warning || ''
  counterpartNotice.value = state?.counterpartNotice || ''
  reportId.value = state?.reportId || ''
  if (warning.value && reportId.value) {
    let seen = ''
    try { seen = localStorage.getItem(seenKey(reportId.value)) || '' } catch (_) {}
    if (!seen) showWarning.value = true
  }
  if (counterpartNotice.value && reportId.value) {
    let seen = ''
    try { seen = localStorage.getItem('sg:moderation-counterpart:' + reportId.value) || '' } catch (_) {}
    if (!seen) showCounterpart.value = true
  }
}
async function load() {
  if (!props.targetId) return
  try {
    const r = await api.reportStatus(props.kind, props.targetId)
    apply(r?.state)
  } catch (_) {}
}
function closeWarning() {
  if (reportId.value) {
    try { localStorage.setItem(seenKey(reportId.value), '1') } catch (_) {}
  }
  showWarning.value = false
}
function closeCounterpart() {
  if (reportId.value) {
    try { localStorage.setItem('sg:moderation-counterpart:' + reportId.value, '1') } catch (_) {}
  }
  showCounterpart.value = false
}
onMounted(() => {
  load()
  timer = setInterval(load, 3000)
})
onUnmounted(() => { if (timer) clearInterval(timer) })
watch(() => [props.kind, props.targetId], () => {
  active.value = false
  warning.value = ''
  showWarning.value = false
  counterpartNotice.value = ''
  showCounterpart.value = false
  load()
})
</script>

<template>
  <div v-if="active" class="mn-banner">
    <b>安全审核</b>
    <span>检测到聊天异常，AI 安全审核已介入。审核期间聊天内容仅用于本次安全判断，不会公开展示。</span>
  </div>
  <div v-if="showWarning" class="mn-overlay" @click.self="closeWarning">
    <div class="mn-card">
      <div class="mn-kicker">AI 安全提醒</div>
      <h3>请立即停止不当言行</h3>
      <p>{{ warning }}</p>
      <p class="mn-sub">本次记录已保存到安全审核记录。如有异议，可通过平台申诉。</p>
      <button type="button" @click="closeWarning">我已知晓</button>
    </div>
  </div>
  <div v-if="showCounterpart" class="mn-overlay" @click.self="closeCounterpart">
    <div class="mn-card">
      <div class="mn-kicker">安全提醒</div>
      <h3>对方已被系统处理</h3>
      <p>{{ counterpartNotice }}</p>
      <p class="mn-sub">你不需要再回应对方的违规内容。如果有需要，可以结束这次沟通并重新选择。</p>
      <button type="button" @click="closeCounterpart">我已知晓</button>
    </div>
  </div>
</template>

<style scoped>
.mn-banner { margin:7px 0; padding:7px 9px; border-radius:8px; background:#FFF8E8; border:1px solid #F0D9A8; display:flex; flex-direction:column; gap:3px; }
.mn-banner b { font-size:9px; color:#9A6414; }
.mn-banner span { font-size:8.5px; line-height:1.6; color:#806A45; }
.mn-overlay { position:fixed; inset:0; z-index:1500; background:rgba(35,22,48,.58); display:flex; align-items:center; justify-content:center; padding:20px; }
.mn-card { width:min(400px,92vw); background:#fff; border-radius:15px; padding:16px; box-shadow:0 16px 42px rgba(0,0,0,.25); }
.mn-kicker { font-size:8.5px; letter-spacing:.1em; color:#A23B2A; }
.mn-card h3 { margin:3px 0 8px; font-size:15px; color:#3B1D63; }
.mn-card p { margin:0 0 7px; font-size:10px; line-height:1.7; color:#5C4B70; }
.mn-card .mn-sub { color:#8E7FA3; font-size:9px; }
.mn-card button { width:100%; margin-top:9px; border:0; background:#5B2A91; color:#fff; border-radius:8px; padding:8px; font-family:inherit; font-size:10px; }
</style>

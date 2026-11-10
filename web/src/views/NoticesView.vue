<script setup>
import { onMounted, ref } from 'vue'
import { api } from '../api'

const emit = defineEmits(['nav'])
const items = ref([])
const loading = ref(true)
const unread = ref(0)
const selected = ref(null)
const contact = ref('')
const actionMsg = ref('')

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
function typeLabel(t, itemType = '') {
  if (itemType === 'help') {
    return ({
      claim: '🤝 收到帮忙申请',
      accepted: '✅ 帮忙申请已通过',
      rejected: '❌ 帮忙申请被婉拒',
      need_more: '📝 帮忙申请待补充',
      done: '🎉 爱心帮助已完成'
    })[t] || '爱心求助提醒'
  }
  return ({
    match: '🔍 相似物品提醒',
    claim: '📥 收到认领申请',
    accepted: '✅ 申请已通过',
    rejected: '❌ 申请被拒',
    need_more: '📝 申请待补充',
    done: '🎉 已完成归还',
    pickup: '🔖 拾光码提醒'
  })[t] || '通知'
}
function openNotice(n) {
  selected.value = n
  contact.value = ''
  actionMsg.value = ''
}

function goItem() {
  if (!selected.value?.itemId) return
  sessionStorage.setItem('sg:focusItem', selected.value.itemId)
  const t = selected.value.itemType === 'help' ? 'help' : selected.value.itemType === 'lost' ? 'lost' : 'found'
  selected.value = null
  emit('nav', t)
}

async function revealContact() {
  try {
    const r = await api.noticeContact(selected.value.id)
    contact.value = r.contact || '对方没有留联系方式'
    actionMsg.value = '已标记为已读'
  } catch (e) { actionMsg.value = e.message || '读取失败' }
}

async function publishReport() {
  try {
    const r = await api.noticePublish(selected.value.id)
    selected.value.itemId = r.itemId
    selected.value.itemType = 'found'
    actionMsg.value = r.already ? '这条已经公开过了' : '已公开为招领，其他同学现在可以看见'
  } catch (e) { actionMsg.value = e.message || '公开失败' }
}

async function helpAction(status) {
  if (!selected.value?.claimId) return
  try {
    await api.claimAction(selected.value.claimId, { status })
    selected.value.claimStatus = status
    actionMsg.value = status === 'accepted' ? '已接受帮忙，完成后记得点「完成帮助」'
      : status === 'need_more' ? '已请对方补充说明'
      : '已婉拒这次帮忙'
  } catch (e) { actionMsg.value = e.message || '操作失败' }
}

async function completeHelp() {
  if (!selected.value?.claimId) return
  try {
    await api.claimComplete(selected.value.claimId, { code: '' })
    selected.value.claimStatus = 'completed'
    actionMsg.value = '已完成这次爱心帮助'
  } catch (e) { actionMsg.value = e.message || '确认失败' }
}

function ignoreNotice() {
  selected.value = null
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
          <div class="mh">{{ typeLabel(n.type, n.itemType) }}</div>
          <div class="mmeta">{{ n.text }}</div>
          <div v-if="n.type === 'claim' && n.claimId" class="mmeta" style="color:var(--purple)">
            点这里查看对方填了什么，与自己那条对比 →
          </div>
          <div class="mmeta">{{ fmt(n.at) }}</div>
        </div>
      </template>
      <div class="adm-link" @click="readAll">全部标为已读</div>
    </div>

    <div v-if="selected" class="sheet vue-sheet show notice-detail">
      <button type="button" class="sheet-x" @click="selected = null">收起</button>
      <div class="nd-kicker">{{ typeLabel(selected.type, selected.itemType) }}</div>
      <h2>{{ selected.report?.itemName || selected.itemTitle || '通知详情' }}</h2>
      <div class="nd-text">{{ selected.report?.message || selected.text }}</div>
      <div v-if="selected.report?.tagItem" class="nd-meta">拾光码物品：{{ selected.report.tagItem }}</div>
      <div v-if="selected.report?.at" class="nd-meta">上报时间：{{ fmt(selected.report.at) }}</div>
      <div v-if="contact" class="nd-contact">联系方式：{{ contact }}</div>
      <div v-if="actionMsg" class="nd-msg">{{ actionMsg }}</div>
      <div v-if="selected.itemType === 'help'" class="nd-claim">
        <div class="nd-meta">帮忙说明：{{ selected.claimMessage || selected.report?.message || selected.text }}</div>
        <div v-if="selected.claimContact" class="nd-contact">对方联系方式：{{ selected.claimContact }}</div>
        <div class="nd-actions">
          <template v-if="selected.claimId && selected.claimStatus === 'pending'">
            <button type="button" class="btn" @click="helpAction('accepted')">接受帮忙</button>
            <button type="button" class="btn ghost" @click="helpAction('need_more')">请补充</button>
            <button type="button" class="btn ghost" @click="helpAction('rejected')">婉拒</button>
          </template>
          <button v-if="selected.claimId && selected.claimStatus === 'accepted'" type="button" class="btn" @click="completeHelp">完成帮助</button>
          <button type="button" class="btn ghost" @click="goItem">查看求助详情</button>
          <button type="button" class="btn ghost" @click="ignoreNotice">忽略</button>
        </div>
      </div>
      <div v-else class="nd-actions">
        <template v-if="selected.type === 'pickup' && selected.report">
          <button type="button" class="btn" @click="revealContact">联系捡到的人</button>
          <button type="button" class="btn ghost" @click="publishReport">公开为招领</button>
        </template>
        <button v-if="selected.itemId" type="button" class="btn ghost" @click="goItem">查看对应内容</button>
        <button type="button" class="btn ghost" @click="ignoreNotice">不是我的 / 忽略</button>
      </div>
    </div>
  </section>
</template>

<style scoped>
.notice-detail { padding-bottom: 92px; }
.nd-kicker { font-size: 10px; color: var(--sub); letter-spacing: .08em; }
.notice-detail h2 { margin: 7px 0 8px; font-size: 17px; color: var(--ink); }
.nd-text { font-size: 12px; line-height: 1.8; color: #4E445D; white-space: pre-wrap; }
.nd-meta { margin-top: 7px; font-size: 10.5px; color: #8E7FA3; }
.nd-contact { margin-top: 10px; padding: 8px 10px; border-radius: 9px; background: #F1E8FB; color: #3B1D63; font-size: 12px; }
.nd-msg { margin-top: 8px; font-size: 10.5px; color: #A97A00; }
.nd-actions { display: flex; flex-wrap: wrap; gap: 7px; margin-top: 14px; }
.nd-actions .btn { flex: 1; min-width: 130px; }
</style>


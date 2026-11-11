<script setup>
import { computed, onMounted, ref } from 'vue'
import { api } from '../api'

const emit = defineEmits(['nav'])
const items = ref([])
const loading = ref(true)
const unread = ref(0)
const tab = ref('all')
const selected = ref(null)
const contact = ref('')
const actionMsg = ref('')
const groups = [
  ['all', '全部'],
  ['lost', '失物'],
  ['help', '求助'],
  ['tag', '拾光码'],
  ['system', '系统']
]
function groupOf(n) {
  if (n.type === 'pickup' || n.report) return 'tag'
  if (n.itemType === 'help') return 'help'
  if (n.itemType === 'lost' || n.itemType === 'found' || ['match', 'claim', 'accepted', 'rejected', 'done'].includes(n.type)) return 'lost'
  return 'system'
}
const visibleItems = computed(() => tab.value === 'all' ? items.value : items.value.filter((n) => groupOf(n) === tab.value))
function groupUnread(id) {
  return items.value.filter((n) => !n.read && (id === 'all' || groupOf(n) === id)).length
}

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
  if (!n.read) {
    n.read = true
    unread.value = Math.max(0, unread.value - 1)
    api.readNotice(n.id).catch(() => {})
  }
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
    const rid = selected.value.report?.id
    const r = rid ? await api.reportContact(rid) : await api.noticeContact(selected.value.id)
    contact.value = r.contact || '对方没有留联系方式'
    if (selected.value.report) selected.value.report.status = r.status || 'contacted'
    actionMsg.value = '已标记为已读'
  } catch (e) { actionMsg.value = e.message || '读取失败' }
}

async function publishReport() {
  try {
    const rid = selected.value.report?.id
    const r = rid ? await api.reportPublish(rid) : await api.noticePublish(selected.value.id)
    selected.value.itemId = r.itemId
    selected.value.itemType = 'found'
    if (selected.value.report) selected.value.report.status = 'published'
    actionMsg.value = r.already ? '这条已经公开过了' : '已公开为招领，其他同学现在可以看见'
  } catch (e) { actionMsg.value = e.message || '公开失败' }
}

async function closeReport() {
  try {
    const rid = selected.value.report?.id
    if (!rid) return
    await api.reportClose(rid)
    selected.value.report.status = 'closed'
    actionMsg.value = '已标记为找回 / 关闭'
  } catch (e) { actionMsg.value = e.message || '关闭失败' }
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
  <section v-if="!selected" class="screen active" id="screen-notices">
    <div class="topbar">
      <div class="back" @click="$emit('nav', 'home')">‹</div>
      <div class="t">通知</div>
    </div>
    <div class="notice-tabs">
      <button v-for="[id, label] in groups" :key="id" type="button" :class="{ on: tab === id }" @click="tab = id">
        {{ label }}<i v-if="groupUnread(id)">{{ groupUnread(id) }}</i>
      </button>
    </div>
    <div class="scroll">
      <div v-if="loading" class="empty">正在读取通知…</div>
      <div v-else-if="!visibleItems.length" class="empty">这个分类还没有通知</div>
      <template v-else>
        <div
          v-for="n in visibleItems"
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
  </section>

  <section v-else class="screen active notice-detail-screen">
    <div class="topbar">
      <div class="back" @click="selected = null">‹</div>
      <div class="t">通知详情</div>
    </div>
    <div class="scroll nd-scroll">
      <div class="nd-hero" :class="'nd-hero-' + (selected.type || 'system')">
        <div class="nd-hero-icon">{{ selected.type === 'pickup' ? '🔖' : selected.itemType === 'help' ? '🤝' : '🔔' }}</div>
        <div class="nd-hero-main">
          <div class="nd-kicker">{{ typeLabel(selected.type, selected.itemType) }}</div>
          <h2>{{ selected.report?.itemName || selected.itemTitle || '通知详情' }}</h2>
          <div class="nd-time">{{ fmt(selected.at) }}</div>
        </div>
        <div v-if="selected.report" class="nd-state">{{ ({pending:'待确认', contacted:'已联系', published:'已公开', closed:'已找回'})[selected.report.status] || selected.report.status }}</div>
      </div>

      <div v-if="selected.report" class="nd-card">
        <div class="nd-card-title">捡到上报</div>
        <div class="nd-kv"><span>捡到物品</span><b>{{ selected.report.itemName || '捡到物品' }}</b></div>
        <div class="nd-kv"><span>拾光码物品</span><b>{{ selected.report.tagItem || '我的物品' }}</b></div>
        <div class="nd-kv"><span>上报时间</span><b>{{ fmt(selected.report.at) }}</b></div>
        <div class="nd-message">{{ selected.report.message }}</div>
      </div>

      <div v-else class="nd-card">
        <div class="nd-card-title">通知内容</div>
        <div class="nd-message">{{ selected.text }}</div>
        <div v-if="!selected.itemId" class="nd-legacy">这条是旧版通知，只保留了文字记录，没有可操作的上报详情。</div>
      </div>

      <div v-if="selected.itemType === 'help'" class="nd-card nd-help-card">
        <div class="nd-card-title">帮忙说明</div>
        <div class="nd-message">{{ selected.claimMessage || selected.report?.message || selected.text }}</div>
        <div v-if="selected.claimContact" class="nd-contact">对方联系方式：{{ selected.claimContact }}</div>
        <div v-if="selected.claimStatus" class="nd-state" style="margin-top:8px">{{ ({pending:'待处理', accepted:'进行中', completed:'已完成', rejected:'已婉拒', need_more:'待补充'})[selected.claimStatus] || selected.claimStatus }}</div>
      </div>

      <div v-if="contact" class="nd-contact">联系方式：{{ contact }}</div>
      <div v-if="actionMsg" class="nd-msg">{{ actionMsg }}</div>

      <div class="nd-actions">
        <template v-if="selected.type === 'pickup' && selected.report">
          <button type="button" class="btn" @click="revealContact">联系捡到的人</button>
          <button v-if="selected.report.status !== 'published' && selected.report.status !== 'closed'" type="button" class="btn ghost" @click="publishReport">公开为招领</button>
          <button v-if="selected.report.status !== 'closed'" type="button" class="btn ghost" @click="closeReport">已找回 / 关闭</button>
          <button type="button" class="btn ghost" @click="ignoreNotice">不是我的 / 忽略</button>
        </template>
        <template v-else-if="selected.itemType === 'help'">
          <template v-if="selected.claimId && selected.claimStatus === 'pending'">
            <button type="button" class="btn" @click="helpAction('accepted')">接受帮忙</button>
            <button type="button" class="btn ghost" @click="helpAction('need_more')">请补充</button>
            <button type="button" class="btn ghost" @click="helpAction('rejected')">婉拒</button>
          </template>
          <button v-if="selected.claimId && selected.claimStatus === 'accepted'" type="button" class="btn" @click="completeHelp">完成帮助</button>
          <button type="button" class="btn ghost" @click="goItem">查看求助详情</button>
          <button type="button" class="btn ghost" @click="ignoreNotice">忽略</button>
        </template>
        <template v-else>
          <button v-if="selected.itemId && selected.type !== 'pickup'" type="button" class="btn ghost" @click="goItem">查看对应内容</button>
          <button type="button" class="btn ghost" @click="ignoreNotice">忽略</button>
        </template>
      </div>
    </div>
  </section>
</template>

<style scoped>
.notice-detail-screen { background: var(--bg); }
.nd-kicker { font-size: 10px; color: var(--sub); letter-spacing: .08em; }
.notice-detail-screen h2 { margin: 7px 0 8px; font-size: 17px; color: var(--ink); }
.nd-text { font-size: 12px; line-height: 1.8; color: #4E445D; white-space: pre-wrap; }
.nd-meta { margin-top: 7px; font-size: 10.5px; color: #8E7FA3; }
.nd-contact { margin-top: 10px; padding: 8px 10px; border-radius: 9px; background: #F1E8FB; color: #3B1D63; font-size: 12px; }
.nd-msg { margin-top: 8px; font-size: 10.5px; color: #A97A00; }
.nd-actions { display: flex; flex-wrap: wrap; gap: 7px; margin-top: 14px; }
.nd-actions .btn { flex: 1; min-width: 130px; }
</style>


<style scoped>
.nd-status { margin-top: 8px; display:inline-block; font-size:10px; color:#5B2A91; background:#F1E8FB; border-radius:99px; padding:4px 8px; }
</style>



<style scoped>
.notice-tabs { display:flex; gap:6px; overflow-x:auto; padding:8px 10px 0; background:#fff; border-bottom:1px solid var(--line); flex-shrink:0; }
.notice-tabs button { border:0; background:transparent; color:#8E7FA3; font-family:inherit; font-size:11px; padding:6px 8px 8px; border-bottom:2px solid transparent; white-space:nowrap; }
.notice-tabs button.on { color:var(--primary); border-bottom-color:var(--primary); font-weight:600; }
.notice-tabs button i { font-style:normal; font-size:8px; color:#fff; background:#B45A5A; border-radius:99px; padding:1px 4px; margin-left:3px; }
</style>


<style scoped>
.nd-scroll { padding:12px 12px 28px; }
.nd-hero { display:flex; align-items:flex-start; gap:10px; background:#fff; border:1px solid #EADFF5; border-radius:16px; padding:14px; margin-bottom:10px; }
.nd-hero-icon { width:38px; height:38px; flex:0 0 38px; border-radius:12px; background:linear-gradient(145deg,#6D3BA6,#3B1D63); display:flex; align-items:center; justify-content:center; font-size:18px; }
.nd-hero-main { flex:1; min-width:0; }
.nd-hero-main h2 { margin:4px 0 3px; font-size:17px; line-height:1.35; color:var(--ink); }
.nd-time { font-size:9.5px; color:#A99BB9; }
.nd-state { flex:0 0 auto; font-size:9px; color:#5B2A91; background:#F1E8FB; border-radius:99px; padding:4px 7px; }
.nd-card { background:#fff; border:1px solid #EADFF5; border-radius:14px; padding:12px 13px; margin-bottom:10px; }
.nd-card-title { font-size:11px; font-weight:600; color:#3B1D63; margin-bottom:8px; }
.nd-kv { display:flex; justify-content:space-between; gap:10px; font-size:10.5px; padding:4px 0; border-bottom:1px dashed #F1EBF7; }
.nd-kv span { color:#8E7FA3; }
.nd-kv b { color:#3B1D63; font-weight:500; text-align:right; }
.nd-message { margin-top:9px; background:#FAF7FE; border-radius:9px; padding:9px 10px; font-size:12px; line-height:1.8; color:#4E445D; white-space:pre-wrap; }
.nd-legacy { margin-top:8px; font-size:9.5px; color:#A97A00; line-height:1.6; }
.nd-contact { margin:8px 0; padding:8px 10px; border-radius:9px; background:#F1E8FB; color:#3B1D63; font-size:11px; }
.nd-msg { margin:8px 0; font-size:10.5px; color:#A97A00; }
.nd-actions { display:flex; flex-wrap:wrap; gap:7px; margin-top:12px; }
.nd-actions .btn { flex:1; min-width:120px; }
.nd-help-card { border-color:#D8E8DD; background:#FBFEFC; }
</style>


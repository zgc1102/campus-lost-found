<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { api, clearApiCache } from '../api'
import CountUp from '../components/CountUp.vue'
import NoticeChat from '../components/NoticeChat.vue'
import NoticePickup from '../components/NoticePickup.vue'
import NoticeClaim from '../components/NoticeClaim.vue'
import NoticeHelp from '../components/NoticeHelp.vue'
import NoticeSystem from '../components/NoticeSystem.vue'

const emit = defineEmits(['nav'])
const items = ref([])
const loading = ref(true)
const unread = ref(0)
const tab = ref('all')
const selected = ref(null)
const contact = ref('')
const actionMsg = ref('')
const chat = ref([])
const chatText = ref('')
const chatLoading = ref(false)
const chatError = ref('')
const outbox = ref([])
const chatSide = ref('owner')
const chatKind = ref('report')
const chatTargetId = ref('')
const chatBlocked = ref(false)
const blockedBy = ref('')
const claimPhoneInput = ref('')
const claimPhoneSaving = ref(false)
const claimPhoneMsg = ref('')
const revealOpen = ref(false)
const revealTarget = ref('')
const revealing = ref(false)
const revealMsg = ref('')
const revealPhoneInput = ref('')
const helpSupplement = ref('')
const helpSupplementing = ref(false)
const helpSupplementMsg = ref('')
const claimPhonePromptOpen = ref(false)
const claimPhonePrompt = ref('')
const claimPhonePromptError = ref('')
const claimPhonePromptBusy = ref(false)
const claimImageBusy = ref(false)
const claimImageError = ref('')
const compareOpen = ref(false)
const targetOpen = ref(false)
const myItems = ref([])
const branch = computed(() => {
  const s = selected.value
  if (!s) return 'system'
  if (s.type === 'pickup' && s.report) return 'pickup'
  if (s.itemType === 'help') return 'help'
  if (s.claimId && (s.itemType === 'lost' || s.itemType === 'found')) return 'claim'
  return 'system'
})
const chatClosed = computed(() => {
  const s = selected.value
  if (!s) return false
  if (s.type === 'pickup') return s.report?.status === 'closed'
  if (s.claimId) return ['completed', 'closed', 'rejected'].includes(s.claimStatus)
  return false
})

function grams(s) {
  const x = String(s || '').replace(/\s+/g, '')
  const set = new Set()
  for (let i = 0; i < Math.max(0, x.length - 1); i++) set.add(x.slice(i, i + 2))
  return set
}
function pairScore(a, b) {
  if (!a || !b) return 0
  const ga = grams((a.title || '') + (a.desc || ''))
  const gb = grams((b.title || '') + (b.desc || ''))
  const union = new Set([...ga, ...gb])
  let pct = union.size ? Math.round(([...ga].filter((x) => gb.has(x)).length / union.size) * 100) : 0
  if (a.cat && a.cat === b.cat) pct += 10
  if (a.place && b.place && (String(a.place).includes(String(b.place)) || String(b.place).includes(String(a.place)))) pct += 10
  return Math.min(99, pct)
}
const matchSystemScore = computed(() => {
  const raw = selected.value?.matchScore
  if (raw !== null && raw !== undefined && raw !== '' && Number.isFinite(Number(raw))) return Number(raw)
  const m = String(selected.value?.text || '').match(/(\d+)\s*%/)
  return m ? Number(m[1]) : 0
})
const matchSource = computed(() => selected.value?.matchSourceItem || selected.value?.item || null)
const matchTarget = computed(() => selected.value?.matchTargetItem || matchItem.value)
const matchItem = computed(() => {
  if (!selected.value?.item) return null
  const want = selected.value.item.type === 'lost' ? 'found' : 'lost'
  const candidates = myItems.value.filter((x) => x.type === want)
  return candidates.sort((a, b) => pairScore(selected.value.item, b) - pairScore(selected.value.item, a))[0] || null
})
const matchLocalScore = computed(() => {
  if (!matchSource.value || !matchTarget.value) return null
  return pairScore(matchSource.value, matchTarget.value)
})
const matchBothMine = computed(() => !!(matchSource.value?.isMine && matchTarget.value?.isMine))
async function loadMyItems() {
  try {
    const list = await api.mine()
    if (Array.isArray(list)) myItems.value = list
  } catch (_) { myItems.value = [] }
}
function currentSimilarity() {
  const it = selected.value?.item
  if (!it) return 0
  const a = grams((it.title || '') + (it.desc || ''))
  const b = grams((selected.value?.claimMessage || selected.value?.text || selected.value?.report?.message || ''))
  const union = new Set([...a, ...b])
  if (!union.size) return 0
  return Math.round(([...a].filter((x) => b.has(x)).length / union.size) * 100)
}
const groups = [
  ['all', '全部'],
  ['lost', '失物'],
  ['help', '求助'],
  ['tag', '拾光码'],
  ['system', '系统']
]
function groupOf(n) {
  if (n.itemType === 'help') return 'help'
  // 失物/招领优先归到“失物”，即使它来自拾光码或带有 report 字段
  if (n.itemType === 'lost' || n.itemType === 'found' || ['match', 'claim', 'accepted', 'rejected', 'done'].includes(n.type)) return 'lost'
  if (n.type === 'pickup' || n.report) return 'tag'
  return 'system'
}
const visibleItems = computed(() => tab.value === 'all' ? items.value : items.value.filter((n) => groupOf(n) === tab.value))
function groupUnread(id) {
  return items.value.filter((n) => !n.read && (id === 'all' || groupOf(n) === id)).length
}
function groupCount(id) {
  return items.value.filter((n) => id === 'all' || groupOf(n) === id).length
}

onMounted(load)
let lastNoticeLoad = 0
async function load() {
  loading.value = true
  try {
    const data = await api.notices()
    items.value = data.items || []
    unread.value = data.unread || 0
    lastNoticeLoad = Date.now()
    applyMineFocus()
  } finally {
    loading.value = false
  }
}
function applyMineFocus() {
  const nid = sessionStorage.getItem('sg:focusNotice')
  const cid = sessionStorage.getItem('sg:focusClaim')
  if (!nid && !cid) return
  let target = nid ? items.value.find((n) => n.id === nid) : null
  if (!target && cid) target = items.value.find((n) => n.claimId === cid)
  sessionStorage.removeItem('sg:focusNotice')
  sessionStorage.removeItem('sg:focusClaim')
  if (target) openNotice(target)
}
function refreshWhenVisible() {
  if (document.hidden) return
  if (Date.now() - lastNoticeLoad > 15000) load()
}
async function refreshSelected() {
  const id = selected.value?.id
  if (!id) return
  clearApiCache()
  await load()
  const fresh = items.value.find((x) => x.id === id)
  if (fresh) {
    selected.value = fresh
    hydrateNoticeImages(fresh)
  }
}
onMounted(() => {
  document.addEventListener('visibilitychange', refreshWhenVisible)
  window.addEventListener('focus', refreshWhenVisible)
})
onUnmounted(() => {
  document.removeEventListener('visibilitychange', refreshWhenVisible)
  window.removeEventListener('focus', refreshWhenVisible)
})
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
      done: '🎉 爱心帮助已完成',
      help_withdraw: '↩️ 帮忙人已撤回申请',
      help_removed: '🚪 发布者已结束沟通',
      help_accepted: '✅ 帮忙申请已通过',
      help_rejected: '❌ 帮忙申请被婉拒',
      help_need_more: '📝 帮忙申请待补充',
      help_supplement: '💬 帮忙人补充了说明',
      help_done: '🎉 爱心帮助已完成'
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
  chat.value = []
  chatText.value = ''
  chatError.value = ''
  outbox.value = []
  chatBlocked.value = false
  blockedBy.value = ''
  claimPhoneInput.value = ''
  claimPhoneMsg.value = ''
  revealOpen.value = false
  revealTarget.value = ''
  revealMsg.value = ''
  revealPhoneInput.value = ''
  helpSupplement.value = ''
  helpSupplementMsg.value = ''
  claimPhonePromptOpen.value = false
  claimPhonePrompt.value = ''
  claimPhonePromptError.value = ''
  claimImageError.value = ''
  compareOpen.value = false
  targetOpen.value = false
  const _reportId = n.reportId || n.report?.id
  const _ct = (n.type === 'pickup' && _reportId)
    ? { id: _reportId, kind: 'report' }
    : (n.claimId && n.itemType !== 'help')
      ? { id: n.claimId, kind: 'claim' }
      : (_reportId ? { id: _reportId, kind: 'report' } : null)
  chatKind.value = _ct?.kind || 'report'
  chatTargetId.value = _ct?.id || ''
  if (_ct) openChatForNotice(n, _ct)
  if (n.type === 'match') loadMyItems()
  if (!n.read) {
    n.read = true
    unread.value = Math.max(0, unread.value - 1)
    api.readNotice(n.id).catch(() => {})
  }
  hydrateNoticeImages(n)
}
async function hydrateNoticeImages(n) {
  if (n.hasClaimImage && n.claimId) {
    try {
      const r = await api.claimImage(n.claimId)
      if (selected.value?.id === n.id && r?.image) selected.value.claimImage = r.image
    } catch (_) {}
  }
  if (n.hasReportPhoto && n.report?.id) {
    try {
      const r = await api.reportImage(n.report.id)
      if (selected.value?.id === n.id && r?.image) selected.value.report.photo = r.image
    } catch (_) {}
  }
}

function currentChatTarget() {
  const s = selected.value
  if (!s) return null
  // 拾光码上报的聊天必须走 report，不能因为带 claimId 就串到认领聊天
  if (s.type === 'pickup' && s.report?.id) return { id: s.report.id, kind: 'report' }
  if (s.claimId && s.itemType !== 'help') return { id: s.claimId, kind: 'claim' }
  if (s.report?.id) return { id: s.report.id, kind: 'report' }
  return null
}
async function openChatForNotice(n, target) {
  await loadChat(target.id, target.kind)
  // 兼容旧数据：以前的聊天可能存在 report 里，claim 还没有 messages
  if (target.kind === 'claim' && !chatError.value && !chat.length && (n.reportId || n.report?.id)) {
    await loadChat(n.reportId || n.report.id, 'report')
  }
}
async function loadChat(rid, kind = 'report') {
  chatLoading.value = true
  chatError.value = ''
  chatKind.value = kind
  chatTargetId.value = rid
  try {
    const r = kind === 'claim' ? await api.claimMessages(rid) : await api.reportMessages(rid)
    chatSide.value = r.side || 'owner'
    if (r.blocked) {
      chatBlocked.value = true
      blockedBy.value = r.blockedBy || 'owner'
      chat.value = []
      outbox.value = []
      return
    }
    chatBlocked.value = false
    const incoming = Array.isArray(r.messages) ? r.messages : []
    const merged = new Map()
    for (const m of chat.value) merged.set(chatKey(m), m)
    for (const m of incoming) merged.set(chatKey(m), m)
    chat.value = [...merged.values()].sort((a, b) => Number(a.at || 0) - Number(b.at || 0))
  } catch (e) {
    chatError.value = e.message || '聊天记录加载失败'
  } finally {
    chatLoading.value = false
  }
}
function chatKey(m) {
  if (!m) return ''
  return m.id || `${m.from || ''}|${m.at || ''}|${m.text || ''}`
}
function appendChat(m) {
  if (!m) return
  const k = chatKey(m)
  if (k && chat.value.some((x) => chatKey(x) === k)) return
  chat.value.push(m)
}
function chatTime(at) {
  const d = new Date(Number(at) || 0)
  if (!Number.isFinite(d.getTime())) return ''
  const now = new Date()
  const y = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const target = new Date(d.getFullYear(), d.getMonth(), d.getDate())
  const hm = `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
  if (target.getTime() === y.getTime()) return hm
  const yesterday = new Date(y.getTime() - 86400000)
  if (target.getTime() === yesterday.getTime()) return `昨天 ${hm}`
  return `${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${hm}`
}
function makeClientMsgId() {
  try {
    if (globalThis.crypto?.randomUUID) return `c_${globalThis.crypto.randomUUID()}`
  } catch (_) {}
  return `c_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`
}
function sendChat(textInput) {
  const text = String(textInput || chatText.value || '').trim()
  const target = chatTargetId.value ? { id: chatTargetId.value, kind: chatKind.value } : null
  if (!text || !target || chatBlocked.value) return
  const item = {
    clientMsgId: makeClientMsgId(),
    text,
    from: chatSide.value,
    at: Date.now(),
    status: 'queued',
    error: ''
  }
  outbox.value.push(item)
  chatText.value = ''
  sendOutbox(item)
}
async function sendOutbox(item) {
  if (!item || item.status === 'sending') return
  item.status = 'sending'
  item.error = ''
  const target = chatTargetId.value ? { id: chatTargetId.value, kind: chatKind.value } : null
  const rid = target?.id
  const kind = target?.kind || chatKind.value
  if (!rid) {
    item.status = 'failed'
    item.error = '聊天已关闭'
    return
  }
  try {
    const r = kind === 'claim'
      ? await api.claimSend(rid, item.text, item.clientMsgId)
      : await api.reportSend(rid, item.text, item.clientMsgId)
    if (r?.message) {
      if ((selected.value?.report?.id || selected.value?.claimId) === rid) appendChat(r.message)
      outbox.value = outbox.value.filter((x) => x.clientMsgId !== item.clientMsgId)
    } else {
      item.status = 'failed'
      item.error = '已发送，但未收到回执'
    }
  } catch (e) {
    item.status = 'failed'
    item.error = e.message || '发送失败'
    if (e.body?.blocked) {
      chatBlocked.value = true
      blockedBy.value = chatSide.value === 'owner' ? 'owner' : 'finder'
      item.error = '对方已屏蔽你，消息发送失败'
    }
  }
}
function retryOutbox(item) {
  if (!item || item.status === 'sending') return
  sendOutbox(item)
}
function refreshChat() {
  if (chatLoading.value || !chatTargetId.value) return
  loadChat(chatTargetId.value, chatKind.value)
}

function goItem() {
  if (!selected.value?.itemId) return
  if (!selected.value.item || ['removed', 'hidden'].includes(selected.value.item.status)) {
    actionMsg.value = '此物品已下架，没有更多信息了'
    return
  }
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
    actionMsg.value = '已标记为找回 / 关闭，拾光码已自动停用'
  } catch (e) { actionMsg.value = e.message || '关闭失败' }
}

function askRevealPhone(target) {
  revealTarget.value = target
  revealMsg.value = ''
  revealOpen.value = true
}
async function doRevealPhone() {
  if (revealing.value) return
  revealing.value = true
  revealMsg.value = ''
  try {
    if (revealTarget.value === 'claim') {
      const r = await api.claimRevealPhone(selected.value.claimId)
      selected.value.claimPhoneRevealed = true
      selected.value.ownerContact = r.ownerContact || ''
      selected.value.claimContact = r.claimContact || selected.value.claimContact
    } else {
      const r = await api.reportRevealPhone(selected.value.report.id, revealPhoneInput.value.trim())
      selected.value.report.phoneRevealed = true
      selected.value.report.ownerContact = r.ownerContact || ''
      selected.value.report.contact = r.finderContact || selected.value.report.contact
    }
    revealOpen.value = false
    actionMsg.value = '已公布双方手机号，双方现在可以互相看到'
  } catch (e) {
    revealMsg.value = e.message || '公布失败'
  } finally {
    revealing.value = false
  }
}
async function generatePickupCode() {
  const rid = selected.value?.claimId
  if (!rid) return
  try {
    const r = await api.claimPickupCode(rid)
    actionMsg.value = r.already ? '取件码已存在' : '取件码已生成，请双方核对'
    await refreshSelected()
  } catch (e) {
    actionMsg.value = e.message || '取件码生成失败'
  }
}
async function supplementClaimImage(image) {
  const rid = selected.value?.claimId
  if (!rid || !image || claimImageBusy.value) return
  claimImageBusy.value = true
  claimImageError.value = ''
  try {
    await api.claimSupplementImage(rid, image)
    if (selected.value?.claimId === rid) selected.value.claimImage = image
    actionMsg.value = '图片已通过审核并上传，等待发布者查看'
    await refreshSelected()
    if (selected.value?.claimId === rid && !selected.value.claimImage) selected.value.claimImage = image
  } catch (e) {
    claimImageError.value = e.message || '图片上传失败'
    actionMsg.value = claimImageError.value
  } finally {
    claimImageBusy.value = false
  }
}
async function supplementClaim(textInput) {
  const rid = selected.value?.claimId
  const text = String(textInput || '').trim()
  if (!rid || text.length < 2) return
  try {
    await api.supplement(rid, { message: text, contact: '' })
    actionMsg.value = '已补充，等待发布者再看'
    await refreshSelected()
  } catch (e) {
    actionMsg.value = e.message || '补充失败'
  }
}
async function supplementHelp(textInput) {
  if (!selected.value?.claimId || helpSupplementing.value) return
  const text = String(textInput || helpSupplement.value || '').trim()
  if (text.length < 2) { helpSupplementMsg.value = '请写一点补充说明'; return }
  helpSupplementing.value = true
  helpSupplementMsg.value = ''
  try {
    await api.helpClaimSupplement(selected.value.claimId, { message: text, contact: selected.value.claimContact || '' })
    selected.value.claimMessage = (selected.value.claimMessage || '') + '\n补充：' + text
    selected.value.claimStatus = 'pending'
    helpSupplement.value = ''
    helpSupplementMsg.value = '已补充，等待发布者再看'
    await refreshSelected()
  } catch (e) {
    helpSupplementMsg.value = e.message || '补充失败'
  } finally {
    helpSupplementing.value = false
  }
}
async function saveClaimPhone(phoneInput) {
  const rid = selected.value?.claimId
  if (!rid || claimPhoneSaving.value) return
  const phone = String(phoneInput || claimPhoneInput.value || '').trim()
  if (!phone) { claimPhoneMsg.value = '请先填写手机号'; return }
  claimPhoneSaving.value = true
  claimPhoneMsg.value = ''
  try {
    const r = selected.value.itemType === 'help'
      ? await api.helpClaimContact(rid, phone)
      : await api.claimContact(rid, phone)
    selected.value.ownerContact = r.ownerContact || ''
    if (selected.value.item?.isMine) selected.value.claimContact = r.claimContact || selected.value.claimContact
    else selected.value.claimContact = r.claimContact || phone
    claimPhoneInput.value = ''
    claimPhoneMsg.value = r.accepted ? '手机号已补充，双方已可互相联系' : '手机号已补充，对方通过后自动交换'
    await refreshSelected()
  } catch (e) {
    claimPhoneMsg.value = e.message || '手机号保存失败'
  } finally {
    claimPhoneSaving.value = false
  }
}
async function blockReport() {  const rid = selected.value.report?.id
  if (!rid) return
  if (!confirm('屏蔽这个人？屏蔽后双方都看不到对方的新消息，也不能再互发。')) return
  try {
    await api.reportBlock(rid)
    selected.value.report.status = 'closed'
    selected.value.report.blocked = true
    chatBlocked.value = true
    blockedBy.value = 'owner'
    chat.value = []
    outbox.value = []
    actionMsg.value = '已屏蔽对方，双方都不能再发送消息'
  } catch (e) { actionMsg.value = e.message || '屏蔽失败' }
}

async function blockClaim() {
  const rid = selected.value?.claimId
  if (!rid) return
  if (!confirm('屏蔽对方？屏蔽后双方不能再互发消息，也不能再查看对方手机号。')) return
  try {
    if (selected.value.itemType === 'help') await api.helpClaimBlock(rid)
    else await api.claimBlock(rid)
    selected.value.claimBlocked = true
    selected.value.claimStatus = 'closed'
    chatBlocked.value = true
    blockedBy.value = 'owner'
    chat.value = []
    outbox.value = []
    actionMsg.value = '已屏蔽对方，双方不能再互发消息'
    await refreshSelected()
  } catch (e) { actionMsg.value = e.message || '屏蔽失败' }
}
async function helpAction(status) {
  if (!selected.value?.claimId) return
  try {
    await api.helpClaimAction(selected.value.claimId, { status })
    selected.value.claimStatus = status
    actionMsg.value = status === 'accepted' ? '已接受帮忙，完成后记得点「完成帮助」'
      : status === 'need_more' ? '已请对方补充说明'
      : '已婉拒这次帮忙'
    await refreshSelected()
  } catch (e) { actionMsg.value = e.message || '操作失败' }
}
async function claimAction(status, needImage = false) {
  if (!selected.value?.claimId) return
  try {
    await api.claimAction(selected.value.claimId, { status, image: !!needImage })
    selected.value.claimStatus = status
    actionMsg.value = status === 'accepted' ? '已通过认领，双方手机号可以交换'
      : status === 'need_more' ? '已请对方补充线索'
      : '已拒绝这次认领'
    await refreshSelected()
  } catch (e) {
    actionMsg.value = e.message || '操作失败'
    if (status === 'accepted' && selected.value?.item?.isMine && String(e.message || '').includes('请先补充你的手机号')) {
      claimPhonePrompt.value = ''
      claimPhonePromptError.value = e.message || ''
      claimPhonePromptOpen.value = true
    }
  }
}
async function submitClaimPhonePrompt() {
  const phone = claimPhonePrompt.value.trim()
  if (!phone) { claimPhonePromptError.value = '请输入你的手机号'; return }
  if (claimPhonePromptBusy.value) return
  claimPhonePromptBusy.value = true
  claimPhonePromptError.value = ''
  try {
    await api.claimContact(selected.value.claimId, phone)
    claimPhonePromptOpen.value = false
    await claimAction('accepted')
  } catch (e) {
    claimPhonePromptError.value = e.message || '手机号保存失败'
  } finally {
    claimPhonePromptBusy.value = false
  }
}

async function withdrawHelpClaim() {
  const rid = selected.value?.claimId
  if (!rid) return
  try {
    await api.helpClaimWithdraw(rid)
    actionMsg.value = '已撤回申请，名额已经空出'
    await refreshSelected()
  } catch (e) {
    actionMsg.value = e.message || '撤回失败'
  }
}
async function removeHelpClaim() {
  const rid = selected.value?.claimId
  if (!rid) return
  try {
    await api.helpClaimRemove(rid)
    actionMsg.value = '已结束与对方的沟通，名额已经空出'
    await refreshSelected()
  } catch (e) {
    actionMsg.value = e.message || '操作失败'
  }
}
async function completeHelp() {
  if (!selected.value?.claimId) return
  try {
    await api.helpClaimComplete(selected.value.claimId)
    selected.value.claimStatus = 'completed'
    actionMsg.value = '已完成这次爱心帮助'
    await refreshSelected()
  } catch (e) { actionMsg.value = e.message || '确认失败' }
}

async function copyCompare() {
  const s = selected.value
  if (!s) return
  const main = s.type === 'match' ? matchSource.value : s.item
  const other = s.type === 'match' ? matchTarget.value : null
  const lines = s.type === 'match'
    ? ['匹配报告', '系统匹配：' + (main?.title || '—'), '系统匹配分：' + matchSystemScore.value + '%', '对方发布：' + (other?.title || '—'), '当前重算分：' + (matchLocalScore.value === null ? '—' : matchLocalScore.value + '%'), '口径：系统分为发布时评分，当前重算分为两条文本重算，仅供推荐，不代表归属。']
    : ['匹配对比报告', '发布物品：' + (main?.title || '—'), '信息对比度：' + (s.claimAi?.confidence ?? '—') + '%', '当前文本相似度：' + currentSimilarity() + '%', '说明：仅供参考，最终请自行认真核对。']
  try {
    await navigator.clipboard.writeText(lines.join('\n'))
    actionMsg.value = '已复制结论，不包含手机号等隐私'
  } catch (_) {
    actionMsg.value = '复制失败，请手动选择文字'
  }
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
      <button v-for="[id, label] in groups" :key="id" type="button" :class="{ on: tab === id }" :title="groupUnread(id) + ' 条未读'" @click="tab = id">
        {{ label }}<i v-if="groupCount(id)">{{ groupCount(id) }}</i>
      </button>
      <span class="unread-sum">共 {{ loading ? '—' : items.length }} 条 · 未读 {{ loading ? '—' : unread }}</span>
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
            {{ n.itemType === 'help' ? '看看对方能怎么帮你 →' : '点这里查看对方填了什么，与自己那条对比 →' }}
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
        <div v-if="selected.report && selected.itemType !== 'help'" class="nd-state">{{ ({pending:'待确认', contacted:'已联系', published:'已公开', closed:'已找回'})[selected.report.status] || selected.report.status }}</div>
      </div>

      <NoticePickup v-if="branch === 'pickup'" :notice="selected" @reveal="askRevealPhone('report')" @publish="publishReport" @block="blockReport" @close="closeReport" @ignore="ignoreNotice">
        <template #chat>
          <NoticeChat :messages="chat" :outbox="outbox" :side="chatSide" :loading="chatLoading" :error="chatError" :blocked="chatBlocked" :blocked-by="blockedBy" :closed="chatClosed" placeholder="回复捡到者，不需要暴露手机号" @send="sendChat" @retry="retryOutbox" @refresh="refreshChat" />
        </template>
      </NoticePickup>

      <NoticeClaim v-else-if="branch === 'claim'" :notice="selected" :image-busy="claimImageBusy" :image-error="claimImageError" @claim-action="claimAction" @reveal="askRevealPhone('claim')" @block="blockClaim" @compare="compareOpen = true" @ignore="ignoreNotice" @supplement="supplementClaim" @supplement-image="supplementClaimImage" @pickup-code="generatePickupCode">
        <template #chat>
          <NoticeChat :messages="chat" :outbox="outbox" :side="chatSide" :loading="chatLoading" :error="chatError" :blocked="chatBlocked" :blocked-by="blockedBy" :closed="chatClosed" placeholder="回复对方，不需要暴露手机号" @send="sendChat" @retry="retryOutbox" @refresh="refreshChat" />
        </template>
      </NoticeClaim>

      <NoticeHelp v-else-if="branch === 'help'" :notice="selected" :supplementing="helpSupplementing" :phone-saving="claimPhoneSaving" :supplement-msg="helpSupplementMsg" :phone-msg="claimPhoneMsg" @supplement="supplementHelp" @save-phone="saveClaimPhone" @help-action="helpAction" @complete="completeHelp" @block="blockClaim" @compare="compareOpen = true" @ignore="ignoreNotice" @withdraw="withdrawHelpClaim" @remove="removeHelpClaim" />

      <NoticeSystem v-else :notice="selected" @compare="compareOpen = true" @ignore="ignoreNotice" />

      <div v-if="contact" class="nd-contact">联系方式：{{ contact }}</div>
      <div v-if="actionMsg" class="nd-msg">{{ actionMsg }}</div>
    </div>

    <div v-if="claimPhonePromptOpen" class="reveal-overlay" @click.self="claimPhonePromptOpen = false">
      <div class="reveal-card">
        <div class="compare-kicker">通过认领前确认</div>
        <h3>请先补充你的手机号</h3>
        <p>通过认领后，双方手机号会同时公布。你还没有留手机号，请先填写。</p>
        <div class="nd-phone-row" style="margin-top:10px">
          <input v-model="claimPhonePrompt" maxlength="20" placeholder="输入你的手机号">
        </div>
        <div v-if="claimPhonePromptError" class="nd-send-error">{{ claimPhonePromptError }}</div>
        <div class="reveal-actions">
          <button type="button" class="btn" :disabled="claimPhonePromptBusy" @click="submitClaimPhonePrompt">{{ claimPhonePromptBusy ? '保存中…' : '保存并公布' }}</button>
          <button type="button" class="btn ghost" :disabled="claimPhonePromptBusy" @click="claimPhonePromptOpen = false">取消</button>
        </div>
      </div>
    </div>

    <div v-if="revealOpen" class="reveal-overlay" @click.self="revealOpen = false">
      <div class="reveal-card">
        <div class="compare-kicker">公布手机号</div>
        <h3>确认公布双方手机号？</h3>
        <p>公布后，你和对方都能看到彼此的完整手机号，方便直接联系。请确认对方身份后再公布。</p>
        <div v-if="revealTarget === 'claim'" class="reveal-phones">
          <div><span>你的手机号</span><b>{{ selected.item?.isMine ? (selected.ownerContact || selected.item?.contact?.phone || '尚未留') : (selected.claimContact || '尚未留') }}</b></div>
          <div><span>对方手机号</span><b>{{ selected.item?.isMine ? (selected.claimContact || '尚未留') : (selected.ownerContact || selected.item?.contact?.phone || '尚未留') }}</b></div>
        </div>
        <div v-else-if="revealTarget === 'report'" class="reveal-phones">
          <div><span>你的手机号</span><b>{{ selected.report?.ownerContact || '尚未留' }}</b></div>
          <div><span>捡到者手机号</span><b>{{ selected.report?.contact || '尚未留' }}</b></div>
        </div>
        <div v-if="revealTarget === 'report' && !selected.report?.ownerContact" class="nd-phone-row" style="margin-top:9px">
          <input v-model="revealPhoneInput" maxlength="20" placeholder="你还没有留手机号，请先填写">
        </div>
        <div v-if="revealMsg" class="nd-send-error">{{ revealMsg }}</div>
        <div class="reveal-actions">
          <button type="button" class="btn" :disabled="revealing" @click="doRevealPhone">{{ revealing ? '公布中…' : '确认公布' }}</button>
          <button type="button" class="btn ghost" :disabled="revealing" @click="revealOpen = false">取消</button>
        </div>
      </div>
    </div>

    <div v-if="compareOpen && selected.item" class="compare-overlay" @click.self="compareOpen = false">
      <div class="compare-card">
        <button type="button" class="compare-x" @click="compareOpen = false; targetOpen = false">✕</button>
        <div class="compare-kicker">匹配对比报告</div>
        <h2>{{ selected.item.title || '对应物品' }}</h2>
        <div v-if="selected.claimId" class="cc-claim-detail">
          <div class="cc-tag">认领详情</div>
          <p class="cc-claim-msg">{{ selected.claimMessage || selected.text }}</p>
          <div class="nd-kv"><span>发布者手机号</span><b>{{ selected.ownerContact || (selected.item?.contact?.phone ? '已留手机号（通过后显示完整）' : '还没留手机号') }}</b></div>
          <div class="nd-kv"><span>认领人手机号</span><b>{{ selected.item?.isMine ? (selected.claimContact || '还没留手机号') : (selected.claimContact ? '已留手机号' : '还没留手机号') }}</b></div>
          <div v-if="selected.item?.isMine && !selected.ownerContact && !selected.item?.contact?.phone" class="nd-phone-fill">
            <p>你是发布者。留手机号后，你通过认领时，双方才能互相联系。</p>
            <div class="nd-phone-row">
              <input v-model="claimPhoneInput" maxlength="20" placeholder="补充你的手机号">
              <button type="button" :disabled="claimPhoneSaving" @click="saveClaimPhone">{{ claimPhoneSaving ? '保存中…' : '补充手机号' }}</button>
            </div>
          </div>
          <div v-else-if="!selected.item?.isMine && !selected.claimContact" class="nd-phone-fill">
            <p>你还没有留手机号。补充后，发布者通过申请时才能联系你。</p>
            <div class="nd-phone-row">
              <input v-model="claimPhoneInput" maxlength="20" placeholder="补充你的手机号">
              <button type="button" :disabled="claimPhoneSaving" @click="saveClaimPhone">{{ claimPhoneSaving ? '保存中…' : '补充手机号' }}</button>
            </div>
          </div>
          <div v-if="selected.claimStatus === 'accepted' || selected.claimStatus === 'completed'" class="nd-exchange-ok">双方手机号已交换，可以直接联系。</div>
          <div v-else class="nd-exchange-tip">发布者确认通过后，双方手机号才会交换；未通过前只显示打码号码。</div>
          <div v-if="claimPhoneMsg" class="nd-phone-msg">{{ claimPhoneMsg }}</div>
        </div>
        <div v-if="matchBothMine" class="compare-note" style="background:#FFF4E5;border-color:#F0D6A8">
          这两条都是你自己发布的，不需要再和“自己”对比。你可以直接查看原通知，或等另一位同学发布相关内容。
        </div>
        <div class="compare-grid">
          <div class="compare-col">
            <div class="cc-tag">{{ selected.type === 'match' ? '系统匹配' : '发布物品' }}</div>
            <div class="cc-title">{{ (selected.type === 'match' ? matchSource : selected.item)?.title || '未命名' }}</div>
            <div class="cc-meta">{{ (selected.type === 'match' ? matchSource : selected.item)?.place || '未填写地点' }} · {{ fmt((selected.type === 'match' ? matchSource : selected.item)?.createdAt) }}</div>
            <p>{{ (selected.type === 'match' ? matchSource : selected.item)?.desc || '暂无描述' }}</p>
            <div v-if="selected.type === 'match'" class="cc-score">本次匹配 <CountUp :value="matchSystemScore" suffix="%" /></div>
          </div>
          <div class="compare-col">
            <template v-if="selected.type === 'match'">
              <div class="cc-tag other">对方发布</div>
              <div class="cc-title">{{ matchTarget ? matchTarget.title : '对方没有发布内容' }}</div>
              <div class="cc-meta">{{ matchTarget ? (matchTarget.place || '未填写地点') + ' · ' + fmt(matchTarget.createdAt) : '这条提醒只有你这一侧的内容' }}</div>
              <p>{{ matchTarget ? matchTarget.desc : '对方可能只是刷到了相似物品，并没有单独发布内容，无法展示对方详情。' }}</p>
              <div v-if="matchTarget" class="cc-score other-score">当前重算 <CountUp v-if="matchLocalScore !== null" :value="matchLocalScore" suffix="%" /><template v-else>—</template></div>
            </template>
            <template v-else>
              <div class="cc-tag other">{{ selected.itemType === 'help' ? '帮忙申请' : (selected.item.type === 'lost' ? '提供线索' : '认领留言') }}</div>
              <div class="cc-title">{{ selected.claimMessage || selected.report?.message || selected.text }}</div>
              <div class="cc-meta">{{ selected.claimAi ? '申请时已做 AI 核验' : '未做 AI 核验' }}</div>
              <p>{{ selected.claimAi?.reason || '可以打开原物品详情，对照描述后自行判断。' }}</p>
            </template>
          </div>
        </div>
        <div class="compare-scores">
          <template v-if="selected.type === 'match'">
            <div><b><CountUp :value="matchSystemScore" suffix="%" /></b><span>发布时系统分</span></div>
            <div><b><CountUp v-if="matchLocalScore !== null" :value="matchLocalScore" suffix="%" /><template v-else>—</template></b><span>按当前描述重算</span></div>
          </template>
          <template v-else>
            <div><b>{{ selected.claimAi ? selected.claimAi.confidence + '%' : '—' }}</b><span>信息对比度</span></div>
            <div><b>{{ currentSimilarity() }}%</b><span>当前文本相似度</span></div>
          </template>
        </div>
        <div v-if="selected.claimId" class="score-explain">
          <p><b>一句话：分数越高只代表“越像”，不代表“越真”；分数低也不代表一定是假的。</b></p>
          <p><b>信息对比度</b>：AI 对申请说明和物品描述的语义接近程度。高 = 意思更像，但可能只是同类物品；低 = 描述差异大或证据不足，需要补充。</p>
          <p><b>当前文本相似度</b>：只按字面重合计算。很高（例如 80% 以上）要警惕直接复述公开描述、照抄线索；很低也不代表假，可能只是换了说法。</p>
          <p class="score-warn" v-if="currentSimilarity() >= 80">这条字面相似度很高，可能复述了公开描述，不能当作独有证据。</p>
          <p><b>真正要看</b>：颜色、型号、划痕、贴纸、挂件、丢失地点、时间、照片；最终由发布者判断。</p>
        </div>
        <div class="compare-note">
          {{ selected.type === 'match'
            ? '两个分数口径不同：系统分是发布时算法给出的，当前重算分是按两条文本重新计算的；缺少数据时显示 —，不当作 0。只用于推荐，不代表归属。'
            : '两个分数都不是证据，只用于帮助失主判断；最终请自行认真核对物品特征。' }}
        </div>
        <div class="compare-actions">
          <button type="button" class="btn ghost" @click="copyCompare">复制结论</button>
          <button type="button" class="btn ghost" :disabled="!matchTarget || matchBothMine" @click="targetOpen = !targetOpen">
            {{ !matchTarget ? '对方没有发布内容' : (matchBothMine ? '两条都是你的发布' : (targetOpen ? '收起对方内容' : '查看对方发布的内容')) }}
          </button>
        </div>
        <div v-if="targetOpen && matchTarget" class="cc-target">
          <div class="cc-tag">对方发布的完整内容</div>
          <div class="cc-title">{{ matchTarget.title }}</div>
          <div class="cc-meta">{{ matchTarget.place || '未填写地点' }} · {{ fmt(matchTarget.createdAt) }}</div>
          <p>{{ matchTarget.desc || '对方没有写详细描述' }}</p>
        </div>
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


<style scoped>
.nd-chat { display:flex; margin:5px 0; }
.nd-chat span { max-width:82%; font-size:11px; line-height:1.6; padding:7px 9px; border-radius:10px; background:#F4EEFB; color:#4E445D; }
.nd-chat.mine { justify-content:flex-end; }
.nd-chat.mine span { background:#5B2A91; color:#fff; }
.nd-chat-input { display:flex; gap:6px; margin-top:8px; }
.nd-chat-input input { flex:1; min-width:0; background:#FAF7FE; border:1px solid #EADFF5; border-radius:9px; padding:8px; font-family:inherit; font-size:10.5px; }
.nd-chat-input button { border:0; background:#5B2A91; color:#fff; border-radius:9px; padding:0 10px; font-family:inherit; font-size:10px; }
</style>


<style scoped>
.unread-sum { margin-left:auto; align-self:center; font-size:9px; color:#8E7FA3; white-space:nowrap; padding-right:4px; }
</style>


<style scoped>
.nd-ai-check { margin-top:8px; padding:9px; border-radius:9px; background:#FBF8FF; border:1px solid #EADFF7; }
.nd-ai-check b { display:block; font-size:10.5px; color:#5B2A91; }
.nd-ai-check > span { font-size:9px; color:#A97A00; }
.nd-ai-check p { margin:3px 0; font-size:10px; line-height:1.6; color:#6E607F; }
.nd-ai-points { display:flex; flex-wrap:wrap; gap:4px; margin-top:4px; }
.nd-ai-points i { font-style:normal; font-size:9px; color:#5B2A91; background:#F1E8FB; border-radius:5px; padding:2px 5px; }
</style>


<style scoped>
.compare-overlay { position:fixed;inset:0;z-index:400;background:rgba(20,8,34,.48);display:flex;align-items:center;justify-content:center;padding:14px; }
.compare-card { position:relative;width:min(760px,94vw);max-height:88vh;overflow-y:auto;background:#fff;border-radius:18px;padding:16px; }
.compare-x { position:absolute;right:10px;top:10px;border:0;background:#F3EEFA;color:#5B2A91;width:26px;height:26px;border-radius:50%; }
.compare-kicker { font-size:9px;color:#A99BB9;letter-spacing:.1em; }
.compare-card h2 { margin:3px 0 10px;font-size:17px;color:#3B1D63;padding-right:26px; }
.compare-grid { display:grid;grid-template-columns:1fr 1fr;gap:9px; }
.compare-col { border:1px solid #EADFF5;border-radius:12px;padding:9px;background:#FCFAFF; }
.cc-tag { display:inline-block;font-size:8.5px;color:#5B2A91;background:#F1E8FB;border-radius:4px;padding:1px 4px; }
.cc-tag.other { color:#2F5FA8;background:#EEF4FF; }
.cc-title { margin-top:5px;font-size:12px;font-weight:600;color:#3B1D63; }
.cc-meta { font-size:9px;color:#8E7FA3;margin-top:3px; }
.compare-col p { margin:5px 0 0;font-size:9.5px;line-height:1.6;color:#6E607F; }
.compare-scores { display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:9px; }
.compare-scores div { background:#FBF8FF;border:1px solid #EADFF5;border-radius:10px;padding:8px;text-align:center; }
.compare-scores b { display:block;font-size:18px;color:#5B2A91; }
.compare-scores span { font-size:9px;color:#8E7FA3; }
.compare-note { margin-top:7px;font-size:9px;line-height:1.6;color:#A97A00; }
.compare-actions { display:flex;gap:8px;margin-top:10px; }
.compare-actions .btn { flex:1; }
@media (max-width:600px) { .compare-grid { grid-template-columns:1fr; } }
</style>




<style scoped>
.cc-score { margin-top:6px; display:inline-block; font-size:9px; color:#5B2A91; background:#F1E8FB; border-radius:5px; padding:2px 6px; }
.cc-score.other-score { color:#2F5FA8; background:#EEF4FF; }
</style>



<style scoped>
.nd-legacy { display:block; flex:0 0 100%; width:100%; margin:10px 0 12px; font-size:12px; line-height:1.6; color:#A97A00; }
.nd-actions { display:flex; flex:0 0 100%; width:100%; gap:8px; justify-content:flex-end; flex-wrap:wrap; }
</style>






<style scoped>
.nd-safety { margin:7px 0 9px; padding:8px 9px; border-radius:9px; background:#FFF8E8; border:1px solid #F0D9A8; display:flex; flex-direction:column; gap:3px; }
.nd-safety b { font-size:9px; color:#9A6414; }
.nd-safety span { font-size:8.5px; line-height:1.6; color:#806A45; }
.nd-chat-time { display:block; margin-top:3px; font-style:normal; font-size:7.5px; opacity:.62; text-align:right; }
.nd-chat .pending { opacity:.62; }
.nd-chat-error { display:flex; align-items:center; justify-content:space-between; gap:6px; padding:7px 0; font-size:9px; color:#A23B2A; }
.nd-chat-error button { border:1px solid #E7B9AE; background:#fff; color:#A23B2A; border-radius:7px; padding:3px 8px; font-family:inherit; font-size:9px; }
.nd-send-error { margin-top:5px; font-size:8.5px; color:#A23B2A; }
.nd-chat-input button:disabled, .nd-chat-input input:disabled { opacity:.55; }
</style>

<style scoped>
.nd-chat-head { display:flex; align-items:center; justify-content:space-between; gap:8px; }
.nd-chat-refresh { border:1px solid #D9C8EE; background:#fff; color:#5B2A91; border-radius:7px; padding:4px 8px; font-family:inherit; font-size:8.5px; }
.nd-chat-refresh:disabled { opacity:.5; }
.nd-chat-help { margin:5px 0 7px; font-size:8px; line-height:1.5; color:#8E7FA3; }
.nd-chat .failed { background:#FFF1EE !important; color:#A23B2A !important; border:1px solid #F0C4B8; }
.nd-retry { margin-left:5px; align-self:center; border:1px solid #E7B9AE; background:#fff; color:#A23B2A; border-radius:7px; padding:3px 7px; font-family:inherit; font-size:8px; }
</style>

<style scoped>
.nd-chat-foot { display:flex; align-items:center; gap:8px; margin-top:7px; flex-wrap:wrap; }
.nd-chat-foot .nd-chat-help { margin:0; flex:1; min-width:150px; }
.nd-chat-foot .nd-chat-refresh { flex:0 0 auto; }
</style>

<style scoped>
.nd-blocked { margin:8px 0; padding:9px 10px; border-radius:9px; background:#F3F0F7; border:1px solid #DED4EA; display:flex; flex-direction:column; gap:3px; }
.nd-blocked b { font-size:10px; color:#5B2A91; }
.nd-blocked span { font-size:8.5px; line-height:1.6; color:#7E6E92; }
</style>

<style scoped>
.cc-target { margin-top:10px; padding:10px; border:1px solid #E7DCF4; border-radius:10px; background:#FBF8FF; }
.cc-target .cc-title { margin-top:5px; }
.cc-target p { margin:4px 0 0; font-size:9.5px; line-height:1.7; color:#6F607F; }
</style>



<style scoped>
.nd-phone-fill { margin-top:7px; padding:8px; border-radius:9px; background:#FBF7FF; border:1px solid #EADFF5; }
.nd-phone-fill p { margin:0 0 6px; font-size:9px; line-height:1.6; color:#7C6A8E; }
.nd-phone-row { display:flex; gap:6px; }
.nd-phone-row input { flex:1; min-width:0; background:#fff; border:1px solid #E4D6F2; border-radius:8px; padding:7px; font-family:inherit; font-size:9.5px; }
.nd-phone-row button { border:0; background:#5B2A91; color:#fff; border-radius:8px; padding:0 9px; font-family:inherit; font-size:9px; }
.nd-exchange-ok { margin-top:7px; font-size:9px; color:#2F7D46; }
.nd-exchange-tip { margin-top:7px; font-size:8.5px; line-height:1.6; color:#8E7FA3; }
.nd-phone-msg { margin-top:5px; font-size:8.5px; color:#5B2A91; }
</style>

<style scoped>
.reveal-overlay { position:fixed; inset:0; z-index:10000; background:rgba(28,18,42,.62); display:flex; align-items:center; justify-content:center; padding:18px; }
.reveal-card { width:min(400px,100%); background:#fff; border-radius:14px; padding:16px; box-shadow:0 18px 50px rgba(20,10,35,.3); }
.reveal-card h3 { margin:6px 0 7px; font-size:15px; color:#3B1D63; }
.reveal-card p { margin:0; font-size:10px; line-height:1.7; color:#6F607F; }
.reveal-actions { display:flex; flex-direction:column; gap:7px; margin-top:12px; }
.reveal-actions .btn { width:100%; }
</style>

<style scoped>
.cc-claim-detail { margin:8px 0 10px; padding:9px; border:1px solid #E7DCF4; border-radius:10px; background:#FBF8FF; }
.cc-claim-msg { margin:5px 0 7px; font-size:9.5px; line-height:1.7; color:#5F4E72; }
</style>

<style scoped>
.help-supplement { margin-top:9px; padding:9px; border:1px solid #E7DCF4; border-radius:9px; background:#FBF8FF; }
.help-supplement p { margin:0 0 6px; font-size:9px; line-height:1.6; color:#7C6A8E; }
.help-supplement textarea { width:100%; box-sizing:border-box; min-height:60px; background:#fff; border:1px solid #E4D6F2; border-radius:8px; padding:8px; font-family:inherit; font-size:9.5px; }
.help-supplement button { margin-top:6px; width:100%; border:0; background:#5B2A91; color:#fff; border-radius:8px; padding:8px; font-family:inherit; font-size:9.5px; }
</style>

<style scoped>
.reveal-phones { margin-top:9px; border:1px solid #E7DCF4; border-radius:9px; background:#FBF8FF; padding:7px 9px; }
.reveal-phones > div { display:flex; justify-content:space-between; gap:12px; padding:4px 0; font-size:9px; color:#7C6A8E; }
.reveal-phones b { color:#3B1D63; font-weight:600; text-align:right; }
</style>
<style scoped>
.score-explain { margin-top:7px; padding:7px 9px; border-radius:8px; background:#FBF8FF; border:1px solid #EFE7F7; }
.score-explain p { margin:3px 0; font-size:8.5px; line-height:1.6; color:#7C6A8E; }
.score-explain b { color:#5B2A91; }
</style>
<style scoped>
.score-warn { margin:4px 0; padding:5px 7px; border-radius:6px; background:#FFF8E8; border:1px solid #F0D9A8; color:#8A5A12 !important; }
</style>

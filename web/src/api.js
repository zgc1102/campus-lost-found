const API_BASE = '/api'
const USER_KEY = 'sg:user:v1'

function owner() {
  const account = localStorage.getItem('sg:account:v1')
  if (account) return account
  let id = localStorage.getItem(USER_KEY)
  if (!id) {
    id = 'u_' + Math.random().toString(36).slice(2, 9)
    localStorage.setItem(USER_KEY, id)
  }
  return id
}

const GET_CACHE = new Map()
const INFLIGHT = new Map()
const LS_PREFIX = 'sg:api-cache:v1:'
function cloneData(data) {
  try { return structuredClone(data) } catch (_) { return JSON.parse(JSON.stringify(data)) }
}
function lsKey(path) { return LS_PREFIX + owner() + '|' + path }
function readLocal(path) {
  try {
    const raw = localStorage.getItem(lsKey(path))
    if (!raw) return null
    const hit = JSON.parse(raw)
    if (!hit || !hit.at || !hit.data) return null
    if (Date.now() - hit.at > 24 * 3600 * 1000) return null
    return hit
  } catch (_) { return null }
}
function writeLocal(path, data) {
  try { localStorage.setItem(lsKey(path), JSON.stringify({ at: Date.now(), data })) } catch (_) {}
}
export function clearApiCache() {
  GET_CACHE.clear()
  INFLIGHT.clear()
  try {
    const keys = []
    for (let i = 0; i < localStorage.length; i++) {
      const k = localStorage.key(i)
      if (k && k.startsWith(LS_PREFIX)) keys.push(k)
    }
    keys.forEach((k) => localStorage.removeItem(k))
  } catch (_) {}
}
async function cachedGet(path, ttl = 30000) {
  const key = owner() + '|' + path
  const local = readLocal(path)
  if (local) {
    if (Date.now() - local.at > ttl) {
      // 先在后台刷新，界面先显示上次数据
      call(path).then((data) => { writeLocal(path, data); GET_CACHE.set(key, { at: Date.now(), data }) }).catch(() => {})
    }
    return cloneData(local.data)
  }
  const hit = GET_CACHE.get(key)
  if (hit && Date.now() - hit.at < ttl) return cloneData(hit.data)
  if (INFLIGHT.has(key)) return cloneData(await INFLIGHT.get(key))
  const task = call(path).then((data) => {
    GET_CACHE.set(key, { at: Date.now(), data })
    writeLocal(path, data)
    INFLIGHT.delete(key)
    return data
  }).catch((e) => {
    INFLIGHT.delete(key)
    throw e
  })
  INFLIGHT.set(key, task)
  return cloneData(await task)
}

async function call(path, options = {}) {
  const { skipCacheClear, timeout: _timeout, ...fetchOptions } = options
  if (!skipCacheClear && (fetchOptions.method || 'GET').toUpperCase() !== 'GET') clearApiCache()
  const headers = {
    'Content-Type': 'application/json',
    'X-Owner': owner(),
    ...(options.headers || {})
  }
  const timeout = options.timeout || 20000
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeout)
  let res
  try {
    res = await fetch(API_BASE + path, { ...fetchOptions, headers, signal: controller.signal })
  } catch (e) {
    if (e && e.name === 'AbortError') throw new Error('读取超时，请检查网络后重试')
    throw e
  } finally {
    clearTimeout(timer)
  }
  if (!res.ok) {
    let message = 'HTTP ' + res.status
    let body = null
    try {
      body = await res.json()
      if (body && body.error) message = body.error
    } catch (_) {}
    const err = new Error(message)
    err.body = body
    err.status = res.status
    throw err
  }
  const text = await res.text()
  return text ? JSON.parse(text) : null
}

export const api = {
  items(includeClosed = false) {
    return call('/items' + (includeClosed ? '?include_closed=1' : ''))
  },
  announcements() {
    return call('/announcements').catch(() => [])
  },
  create(item) {
    return call('/items', { method: 'POST', body: JSON.stringify(item) })
  },
  precheck(item) {
    return call('/precheck', { method: 'POST', body: JSON.stringify(item), skipCacheClear: true })
  },
  claim(id, body) {
    return call('/items/' + encodeURIComponent(id) + '/claims', { method: 'POST', body: JSON.stringify(body || {}) })
  },
  claimCheck(id, message) {
    return call('/items/' + encodeURIComponent(id) + '/claim-check', { method: 'POST', body: JSON.stringify({ message }), skipCacheClear: true })
  },
  compareAI(id, otherId) {
    return call('/items/' + encodeURIComponent(id) + '/compare-ai', { method: 'POST', body: JSON.stringify({ otherId }), timeout: 60000, skipCacheClear: true })
  },
  report(id) {
    return call('/items/' + encodeURIComponent(id) + '/report', { method: 'POST' })
  },
  claims() {
    return call('/claims')
  },
  claimAction(id, body) {
    return call('/claims/' + encodeURIComponent(id), { method: 'PATCH', body: JSON.stringify(body || {}) })
  },
  claimComplete(id, body) {
    return call('/claims/' + encodeURIComponent(id) + '/complete', { method: 'POST', body: JSON.stringify(body || {}) })
  },
  supplement(id, body) {
    return call('/claims/' + encodeURIComponent(id) + '/supplement', { method: 'POST', body: JSON.stringify(body || {}) })
  },
  mine() {
    return call('/mine')
  },
  accountLogin(body) {
    return call('/account/login', { method: 'POST', body: JSON.stringify(body) })
  },
  remove(id) {
    return call('/items/' + encodeURIComponent(id), { method: 'DELETE' })
  },
  update(id, item) {
    return call('/items/' + encodeURIComponent(id), { method: 'PATCH', body: JSON.stringify(item) })
  },
  ask(question) {
    return call('/ask', { method: 'POST', body: JSON.stringify({ question }), skipCacheClear: true })
  },
  async askStream(question, onDelta) {
    const res = await fetch('/api/ask/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Owner': owner() },
      body: JSON.stringify({ question })
    })
    if (!res.ok) {
      let msg = '问答服务暂时不可用'
      try { msg = (await res.json()).error || msg } catch (_) {}
      throw new Error(msg)
    }
    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    let final = null
    while (true) {
      const { value, done } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const parts = buffer.split('\n\n')
      buffer = parts.pop() || ''
      for (const part of parts) {
        const lines = part.split('\n')
        const ev = (lines.find((x) => x.startsWith('event:')) || '').slice(6).trim()
        const raw = lines.find((x) => x.startsWith('data:'))
        if (!raw) continue
        let data = {}
        try { data = JSON.parse(raw.slice(5).trim()) } catch (_) { continue }
        if (ev === 'delta' && onDelta) onDelta(data.text || '')
        if (ev === 'done') final = data
      }
    }
    return final || {}
  },
  vision(image) {
    return call('/vision/analyze', { method: 'POST', body: JSON.stringify({ image, mime: 'image/jpeg' }), skipCacheClear: true })
  },
  format(title, desc, place) {
    return call('/format', { method: 'POST', body: JSON.stringify({ title, desc, place }), skipCacheClear: true })
  },
  notices() {
    return call('/notices')
  },
  readNotices() {
    return call('/notices/read', { method: 'POST', skipCacheClear: true })
  },
  readNotice(id) {
    return call('/notices/' + encodeURIComponent(id) + '/read', { method: 'POST', skipCacheClear: true })
  },
  noticeContact(id) {
    return call('/notices/' + encodeURIComponent(id) + '/contact', { method: 'POST' })
  },
  noticePublish(id) {
    return call('/notices/' + encodeURIComponent(id) + '/publish', { method: 'POST' })
  },
  reportContact(id) {
    return call('/reports/' + encodeURIComponent(id) + '/contact', { method: 'POST' })
  },
  reportPublish(id) {
    return call('/reports/' + encodeURIComponent(id) + '/publish', { method: 'POST' })
  },
  reportClose(id) {
    return call('/reports/' + encodeURIComponent(id) + '/close', { method: 'POST' })
  },
  reportBlock(id) {
    return call('/reports/' + encodeURIComponent(id) + '/block', { method: 'POST' })
  },
  reportMessages(id) {
    return call('/reports/' + encodeURIComponent(id) + '/messages/list', { method: 'POST', skipCacheClear: true })
  },
  reportSend(id, text, clientMsgId) {
    return call('/reports/' + encodeURIComponent(id) + '/messages/send', { method: 'POST', body: JSON.stringify({ text, clientMsgId }), skipCacheClear: true })
  },
  helpClaimAction(id, body) {
    return call('/help-claims/' + encodeURIComponent(id) + '/action', { method: 'PATCH', body: JSON.stringify(body || {}), skipCacheClear: true })
  },
  helpClaimComplete(id) {
    return call('/help-claims/' + encodeURIComponent(id) + '/complete', { method: 'POST', body: '{}', skipCacheClear: true })
  },
  helpClaimContact(id, phone) {
    return call('/help-claims/' + encodeURIComponent(id) + '/contact', { method: 'POST', body: JSON.stringify({ phone }), skipCacheClear: true })
  },
  helpClaimSupplement(id, body) {
    return call('/help-claims/' + encodeURIComponent(id) + '/supplement', { method: 'POST', body: JSON.stringify(body || {}), skipCacheClear: true })
  },
  helpClaimBlock(id) {
    return call('/help-claims/' + encodeURIComponent(id) + '/block', { method: 'POST', body: '{}', skipCacheClear: true })
  },
  helpClaimWithdraw(id) {
    return call('/help-claims/' + encodeURIComponent(id) + '/withdraw', { method: 'PATCH', body: '{}', skipCacheClear: true })
  },
  helpClaimRemove(id) {
    return call('/help-claims/' + encodeURIComponent(id) + '/remove', { method: 'PATCH', body: '{}', skipCacheClear: true })
  },
  claimRestore(id) {
    return call('/claims/' + encodeURIComponent(id) + '/restore', { method: 'PATCH', body: '{}', skipCacheClear: true })
  },
  helpClaimRestore(id) {
    return call('/help-claims/' + encodeURIComponent(id) + '/restore', { method: 'PATCH', body: '{}', skipCacheClear: true })
  },
  requestReportPhoto(id) {
    return call('/reports/' + encodeURIComponent(id) + '/request-photo', { method: 'POST', body: '{}', skipCacheClear: true })
  },
  supplementReportPhoto(id, image) {
    return call('/reports/' + encodeURIComponent(id) + '/supplement-photo', { method: 'POST', body: JSON.stringify({ image }), skipCacheClear: true })
  },
  reopenReport(id) {
    return call('/reports/' + encodeURIComponent(id) + '/reopen', { method: 'POST', body: '{}', skipCacheClear: true })
  },
  claimCancel(id) {
    return call('/claims/' + encodeURIComponent(id) + '/cancel', { method: 'POST', body: '{}', skipCacheClear: true })
  },
  claimImage(id) {
    return call('/claims/' + encodeURIComponent(id) + '/image')
  },
  reportImage(id) {
    return call('/reports/' + encodeURIComponent(id) + '/image')
  },
  claimPickupCode(id) {
    return call('/claims/' + encodeURIComponent(id) + '/pickup-code', { method: 'POST', body: '{}', skipCacheClear: true })
  },
  claimSupplementImage(id, image) {
    return call('/claims/' + encodeURIComponent(id) + '/supplement-image', { method: 'POST', body: JSON.stringify({ image }), skipCacheClear: true })
  },
  claimContact(id, phone) {
    return call('/claims/' + encodeURIComponent(id) + '/contact', { method: 'POST', body: JSON.stringify({ phone }), skipCacheClear: true })
  },
  claimRevealPhone(id) {
    return call('/claims/' + encodeURIComponent(id) + '/reveal-phone', { method: 'POST', body: '{}', skipCacheClear: true })
  },
  claimBlock(id) {
    return call('/claims/' + encodeURIComponent(id) + '/block', { method: 'POST', body: '{}', skipCacheClear: true })
  },
  reportRevealPhone(id, phone) {
    return call('/reports/' + encodeURIComponent(id) + '/reveal-phone', { method: 'POST', body: JSON.stringify({ phone: phone || '' }), skipCacheClear: true })
  },
  claimMessages(id, after, afterAt) {
    return call('/claims/' + encodeURIComponent(id) + '/messages/list', {
      method: 'POST',
      body: JSON.stringify({ after: after || '', afterAt: afterAt || 0 }),
      skipCacheClear: true
    })
  },
  claimSend(id, text, clientMsgId) {
    return call('/claims/' + encodeURIComponent(id) + '/messages/send', { method: 'POST', body: JSON.stringify({ text, clientMsgId }), skipCacheClear: true })
  },
  adminLogin(password) {
    return call('/login', { method: 'POST', body: JSON.stringify({ password }) })
  },
  adminItems(token) {
    return call('/admin/items', { headers: { 'X-Admin-Token': token } })
  },
  adminStats(token) {
    return call('/admin/stats', { headers: { 'X-Admin-Token': token } })
  },
  adminConfig(token) {
    return call('/admin/ai/config', { headers: { 'X-Admin-Token': token } })
  },
  adminSaveConfig(body, token) {
    return call('/admin/ai/config', { method: 'POST', headers: { 'X-Admin-Token': token }, body: JSON.stringify(body) })
  },
  adminAccounts(token) {
    return call('/admin/accounts', { headers: { 'X-Admin-Token': token } })
  },
  adminBanAccount(id, banned, token) {
    return call('/admin/accounts/' + encodeURIComponent(id) + '/ban', { method: 'POST', headers: { 'X-Admin-Token': token }, body: JSON.stringify({ banned }) })
  },
  adminSpecialNumbers(token) {
    return call('/admin/special-numbers', { headers: { 'X-Admin-Token': token } })
  },
  adminSpecialSave(phone, remove, token) {
    return call('/admin/special-numbers', { method: 'POST', headers: { 'X-Admin-Token': token }, body: JSON.stringify({ phone, remove }) })
  },
  adminReset(token) {
    return call('/admin/reset', { method: 'POST', headers: { 'X-Admin-Token': token } })
  },
  adminAiTest(body, token) {
    return call('/admin/ai/test', { method: 'POST', headers: { 'X-Admin-Token': token }, body: JSON.stringify(body) })
  },
  adminPhoneApprove(id, token) {
    return call('/admin/items/' + encodeURIComponent(id) + '/phone-approve', { method: 'POST', headers: { 'X-Admin-Token': token } })
  },
  adminAiReview(id, token) {
    return call('/admin/ai/review/' + encodeURIComponent(id), { method: 'POST', headers: { 'X-Admin-Token': token } })
  },
  adminAiReviewAll(token) {
    return call('/admin/ai/review-all', { method: 'POST', headers: { 'X-Admin-Token': token } })
  },
  adminAnnouncements(token) {
    return call('/admin/announcements', { headers: { 'X-Admin-Token': token } })
  },
  adminCreateAnnouncement(body, token) {
    return call('/admin/announcements', { method: 'POST', headers: { 'X-Admin-Token': token }, body: JSON.stringify(body) })
  },
  adminPatchAnnouncement(id, body, token) {
    return call('/admin/announcements/' + encodeURIComponent(id), { method: 'PATCH', headers: { 'X-Admin-Token': token }, body: JSON.stringify(body) })
  },
  adminDeleteAnnouncement(id, token) {
    return call('/admin/announcements/' + encodeURIComponent(id), { method: 'DELETE', headers: { 'X-Admin-Token': token } })
  },
  adminDeploy(token) {
    return call('/admin/deploy', { method: 'POST', headers: { 'X-Admin-Token': token } })
  },
  adminDeployLog(token) {
    return call('/admin/deploy-log', { headers: { 'X-Admin-Token': token } })
  },
  adminPatch(id, body, token) {
    return call('/admin/items/' + encodeURIComponent(id), { method: 'PATCH', headers: { 'X-Admin-Token': token }, body: JSON.stringify(body) })
  },
  radar(body) {
    return call('/agent/radar', { method: 'POST', body: JSON.stringify(body) })
  },
  similar(id) {
    return call('/items/' + encodeURIComponent(id) + '/similar')
  },
  detective(body) {
    return call('/agent/detective', { method: 'POST', body: JSON.stringify(body) })
  },
  createTag(body) {
    return call('/tags', { method: 'POST', body: JSON.stringify(body) })
  },
  myTags() {
    return call('/tags/mine')
  },
  tag(code) {
    return call('/tags/' + encodeURIComponent(code))
  },
  notifyTag(code, body) {
    return call('/tags/' + encodeURIComponent(code) + '/notify', { method: 'POST', body: JSON.stringify(body) })
  },
  deleteTag() {
    return call('/tags/mine/delete', { method: 'POST' })
  },
  tag(code) {
    return call('/tags/' + encodeURIComponent(code))
  }
}

export function oldUrl(screen = 'home', extra = '') {
  const base = location.port === '5173'
    ? 'http://127.0.0.1:8000/用户端.html'
    : '/用户端.html'
  return base + '?' + extra + '#' + screen
}




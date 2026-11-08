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

async function call(path, options = {}) {
  const headers = {
    'Content-Type': 'application/json',
    'X-Owner': owner(),
    ...(options.headers || {})
  }
  const res = await fetch(API_BASE + path, { ...options, headers })
  if (!res.ok) {
    let message = 'HTTP ' + res.status
    let body = null
    try {
      body = await res.json()
      if (body && body.error) message = body.error
    } catch (_) {}
    const err = new Error(message)
    err.body = body
    throw err
  }
  const text = await res.text()
  return text ? JSON.parse(text) : null
}

export const api = {
  items() {
    return call('/items')
  },
  announcements() {
    return call('/announcements').catch(() => [])
  },
  create(item) {
    return call('/items', { method: 'POST', body: JSON.stringify(item) })
  },
  claim(id, body) {
    return call('/items/' + encodeURIComponent(id) + '/claims', { method: 'POST', body: JSON.stringify(body || {}) })
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
  ask(question) {
    return call('/ask', { method: 'POST', body: JSON.stringify({ question }) })
  },
  vision(image) {
    return call('/vision/analyze', { method: 'POST', body: JSON.stringify({ image, mime: 'image/jpeg' }) })
  },
  format(title, desc, place) {
    return call('/format', { method: 'POST', body: JSON.stringify({ title, desc, place }) })
  },
  notices() {
    return call('/notices')
  },
  readNotices() {
    return call('/notices/read', { method: 'POST' })
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
  adminPhoneApprove(id, token) {
    return call('/admin/items/' + encodeURIComponent(id) + '/phone-approve', { method: 'POST', headers: { 'X-Admin-Token': token } })
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
  detective(body) {
    return call('/agent/detective', { method: 'POST', body: JSON.stringify(body) })
  },
  createTag(body) {
    return call('/tags', { method: 'POST', body: JSON.stringify(body) })
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

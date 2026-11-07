const API_BASE = '/api'
const USER_KEY = 'sg:user:v1'

function owner() {
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
    try {
      const body = await res.json()
      if (body && body.error) message = body.error
    } catch (_) {}
    throw new Error(message)
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
  mine() {
    return call('/mine')
  },
  ask(question) {
    return call('/ask', { method: 'POST', body: JSON.stringify({ question }) })
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

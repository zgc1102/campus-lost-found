<script setup>
import { computed, onMounted, ref } from 'vue'
import { api } from '../api'

const TOKEN_KEY = 'sg:admin:token'
const token = ref(sessionStorage.getItem(TOKEN_KEY) || '')
// 旧版本曾经把 token 存在 localStorage，迁移时清掉，避免无密码直接进后台
localStorage.removeItem(TOKEN_KEY)
const password = ref('')
const loading = ref(false)
const error = ref('')
const tab = ref('all')
const search = ref('')

const stats = ref(null)
const items = ref([])
const accounts = ref([])
const announcements = ref([])
const specials = ref([])
const config = ref(null)
const deployLog = ref([])

const annTitle = ref('')
const annBody = ref('')
const apiKey = ref('')
const rejectTarget = ref(null)
const rejectReason = ref('')

const tabs = [
  ['pending', '待审核'],
  ['approved', '已上架'],
  ['rejected', '已驳回'],
  ['all', '全部'],
  ['overview', '概览'],
  ['users', '注册用户'],
  ['phone', '号码白名单'],
  ['announce', '公告'],
  ['ai', 'AI 配置'],
  ['deploy', '部署日志']
]

const filteredItems = computed(() => {
  const q = search.value.trim().toLowerCase()
  return items.value
    .filter((x) => tab.value === 'all' || (tab.value !== 'overview' && tab.value !== 'users' && tab.value !== 'announce' && tab.value !== 'ai' && tab.value !== 'deploy' && tab.value !== 'phone' ? x.status === tab.value : true))
    .filter((x) => !q || ((x.title || '') + (x.desc || '') + (x.place || '')).toLowerCase().includes(q))
    .sort((a, b) => (b.createdAt || 0) - (a.createdAt || 0))
})

onMounted(() => { if (token.value) loadAll() })

async function loadAll() {
  if (!token.value) return
  loading.value = true
  error.value = ''
  try {
    const [s, list, accs, anns, sp, cfg, dep] = await Promise.all([
      api.adminStats(token.value),
      api.adminItems(token.value),
      api.adminAccounts(token.value),
      api.adminAnnouncements(token.value),
      api.adminSpecialNumbers(token.value),
      api.adminConfig(token.value),
      api.adminDeployLog(token.value)
    ])
    stats.value = s
    items.value = Array.isArray(list) ? list : []
    accounts.value = Array.isArray(accs) ? accs : []
    announcements.value = Array.isArray(anns) ? anns : []
    specials.value = Array.isArray(sp) ? sp : []
    config.value = cfg
    deployLog.value = Array.isArray(dep) ? dep : (dep.log ? String(dep.log).split('\n').filter(Boolean).map((x) => ({ text: x })) : (dep.items || dep.logs || []))
  } catch (e) {
    error.value = e.message || '读取失败'
    if (String(e.message).includes('登录') || String(e.message).includes('401')) logout()
  } finally {
    loading.value = false
  }
}

async function login() {
  error.value = ''
  loading.value = true
  try {
    const r = await api.adminLogin(password.value)
    token.value = r.token
    sessionStorage.setItem(TOKEN_KEY, r.token)
    password.value = ''
    await loadAll()
  } catch (e) {
    error.value = e.message || '登录失败'
  } finally {
    loading.value = false
  }
}

function logout() {
  token.value = ''
  sessionStorage.removeItem(TOKEN_KEY)
}

async function review(it, status) {
  if (status === 'rejected') {
    rejectTarget.value = it
    rejectReason.value = ''
    return
  }
  try {
    await api.adminPatch(it.id, { status, rejectReason: '' }, token.value)
    await loadAll()
  } catch (e) { error.value = e.message || '操作失败' }
}

async function confirmReject() {
  if (!rejectTarget.value) return
  if (rejectReason.value.trim().length < 2) {
    error.value = '请写一下驳回理由'
    return
  }
  try {
    await api.adminPatch(rejectTarget.value.id, {
      status: 'rejected',
      rejectReason: rejectReason.value.trim()
    }, token.value)
    rejectTarget.value = null
    rejectReason.value = ''
    await loadAll()
  } catch (e) { error.value = e.message || '驳回失败' }
}

async function approvePhone(it) {
  try {
    await api.adminPhoneApprove(it.id, token.value)
    await loadAll()
  } catch (e) { error.value = e.message || '操作失败' }
}

async function toggleBan(a) {
  try {
    await api.adminBanAccount(a.id, !a.banned, token.value)
    await loadAll()
  } catch (e) { error.value = e.message || '操作失败' }
}

async function deployCode() {
  try {
    const r = await api.adminDeploy(token.value)
    error.value = r.msg || '已触发更新'
    setTimeout(() => window.location.reload(), 15000)
  } catch (e) { error.value = e.message || '更新失败' }
}

async function saveConfig() {
  if (!config.value) return
  try {
    const body = {
      enabled: !!config.value.enabled,
      base_url: config.value.base_url || '',
      model: config.value.model || '',
      auto_approve: !!config.value.auto_approve,
      approve_threshold: Number(config.value.approve_threshold || 0),
      auto_reject: !!config.value.auto_reject,
      reject_threshold: Number(config.value.reject_threshold || 0)
    }
    if (apiKey.value) body.api_key = apiKey.value
    await api.adminSaveConfig(body, token.value)
    apiKey.value = ''
    await loadAll()
  } catch (e) { error.value = e.message || '保存失败' }
}

async function createAnnouncement() {
  if (annTitle.value.trim().length < 2 || annBody.value.trim().length < 5) {
    error.value = '标题或正文太短'
    return
  }
  try {
    await api.adminCreateAnnouncement({ title: annTitle.value.trim(), body: annBody.value.trim(), publish: true }, token.value)
    annTitle.value = ''
    annBody.value = ''
    await loadAll()
  } catch (e) { error.value = e.message || '发布失败' }
}

async function setAnnouncement(a, status) {
  try {
    await api.adminPatchAnnouncement(a.id, { status }, token.value)
    await loadAll()
  } catch (e) { error.value = e.message || '操作失败' }
}

async function removeAnnouncement(a) {
  if (!confirm('确定删除公告「' + a.title + '」？')) return
  try {
    await api.adminDeleteAnnouncement(a.id, token.value)
    await loadAll()
  } catch (e) { error.value = e.message || '删除失败' }
}

function fmt(ts) {
  if (!ts) return ''
  const d = new Date(ts)
  const p = (n) => String(n).padStart(2, '0')
  return `${d.getMonth() + 1}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`
}
function specialName(s) {
  if (typeof s === 'string') return s
  return s.phone || s.number || s.id || JSON.stringify(s)
}
function statusText(s) {
  return ({ pending: '待审核', approved: '已上架', rejected: '已驳回', claimed: '已认领', closed: '已闭环', removed: '已下架' })[s] || s
}
function statusClass(s) {
  return 'st-' + s
}
</script>

<template>
  <div class="admin-shell">
    <header class="admin-header">
      <div class="admin-wrap">
        <div class="brand">
          <div class="brand-mark">拾</div>
          <div>
            <h1>管理后台 · 清华校园拾光里</h1>
            <p>仅管理员可见 · 审核发布内容 · 管理公告与用户</p>
          </div>
        </div>
        <div class="header-actions" v-if="token">
          <button type="button" @click="loadAll">刷新</button>
          <button type="button" @click="deployCode">更新代码</button>
          <button type="button" @click="logout">退出登录</button>
        </div>
      </div>
    </header>

    <main class="admin-main">
      <div class="admin-wrap">
        <div v-if="!token" class="login-card">
          <h2>管理员登录</h2>
          <p>密码在服务器文件夹的「管理员密码.txt」里</p>
          <input v-model="password" type="password" placeholder="输入管理员密码" @keyup.enter="login">
          <button type="button" class="primary" :disabled="loading" @click="login">{{ loading ? '登录中…' : '登录' }}</button>
          <div v-if="error" class="error">{{ error }}</div>
          <div class="login-foot">登录后可审核待发布内容、下架违规信息。</div>
        </div>

        <template v-else>
          <div v-if="error" class="error top-error">{{ error }}</div>

          <div class="overview-strip">
            <div class="ov-item"><b>{{ stats?.items ?? '—' }}</b><span>全部内容</span></div>
            <div class="ov-item"><b>{{ stats?.byStatus?.pending ?? '—' }}</b><span>待审核</span></div>
            <div class="ov-item"><b>{{ stats?.byStatus?.approved ?? '—' }}</b><span>已上架</span></div>
            <div class="ov-item"><b>{{ stats?.accounts ?? '—' }}</b><span>注册用户</span></div>
            <div class="ov-item"><b>{{ stats?.claims ?? '—' }}</b><span>认领申请</span></div>
            <div class="ov-item"><b>{{ stats?.announcements ?? '—' }}</b><span>已发布公告</span></div>
          </div>
          <div class="ai-status">
            <span :class="['dot', config?.enabled ? 'on' : 'off']"></span>
            <template v-if="config?.enabled">
              AI 审核已启用 · 模型：<b>{{ config.model || '未填写模型' }}</b> · 自动审核中
            </template>
            <template v-else>暂未启用 AI 大模型审核</template>
          </div>

          <div class="admin-tabs">
            <button v-for="[id, name] in tabs" :key="id" type="button" :class="{ on: tab === id }" @click="tab = id">{{ name }}</button>
          </div>

          <div v-if="tab === 'overview'" class="panel-grid">
            <div class="panel">
              <h3>内容分布</h3>
              <div class="bar-row" v-for="(n, k) in (stats?.byStatus || {})" :key="k">
                <span>{{ statusText(k) }}</span><i><b :style="{ width: Math.max(3, (n / (stats.items || 1)) * 100) + '%' }" /></i><em>{{ n }}</em>
              </div>
            </div>
            <div class="panel">
              <h3>类型统计</h3>
              <div class="type-stats">
                <div><b>{{ stats?.lost ?? 0 }}</b><span>寻物</span></div>
                <div><b>{{ stats?.found ?? 0 }}</b><span>招领</span></div>
                <div><b>{{ stats?.help ?? 0 }}</b><span>求助</span></div>
              </div>
              <h3 style="margin-top:18px">近 7 天发布</h3>
              <div class="days"><span v-for="d in (stats?.days || [])" :key="d.day"><i :style="{ height: Math.max(4, d.count * 2) + 'px' }" /><em>{{ d.day }}</em></span></div>
            </div>
          </div>

          <template v-else-if="tab === 'users'">
            <div class="panel">
              <h3>注册用户 · {{ accounts.length }}</h3>
              <div class="user-row" v-for="a in accounts" :key="a.id">
                <div><b>{{ a.phone }}</b><span>{{ fmt(a.createdAt) }} 注册 · {{ a.banned ? '已停用' : '正常' }}</span></div>
                <button type="button" class="ghost" @click="toggleBan(a)">{{ a.banned ? '解封' : '封禁' }}</button>
              </div>
            </div>
          </template>

          <template v-else-if="tab === 'phone'">
            <div class="panel">
              <h3>号码白名单 · {{ specials.length }}</h3>
              <div class="user-row" v-for="s in specials" :key="specialName(s)">
                <div><b>{{ specialName(s) }}</b><span>{{ s.reason || s.note || '特殊号码' }}</span></div>
              </div>
            </div>
          </template>

          <template v-else-if="tab === 'announce'">
            <div class="panel">
              <h3>发布公告</h3>
              <input v-model="annTitle" class="field" maxlength="60" placeholder="公告标题">
              <textarea v-model="annBody" class="field" maxlength="2000" placeholder="公告正文"></textarea>
              <button type="button" class="primary" @click="createAnnouncement">发布公告</button>
              <h3 style="margin-top:22px">公告列表 · {{ announcements.length }}</h3>
              <div class="ann-row" v-for="a in announcements" :key="a.id">
                <div><b>{{ a.title }}</b><span>{{ a.body }}</span><em>{{ a.status }}</em></div>
                <div class="row-actions">
                  <button type="button" class="ghost" @click="setAnnouncement(a, a.status === 'published' ? 'draft' : 'published')">{{ a.status === 'published' ? '下架' : '发布' }}</button>
                  <button type="button" class="danger" @click="removeAnnouncement(a)">删除</button>
                </div>
              </div>
            </div>
          </template>

          <template v-else-if="tab === 'ai'">
            <div class="panel" v-if="config">
              <h3>AI 配置</h3>
              <label class="check"><input v-model="config.enabled" type="checkbox"> 启用 AI 审核</label>
              <div class="form-grid">
                <label><span>Base URL</span><input v-model="config.base_url" class="field"></label>
                <label><span>模型</span><input v-model="config.model" class="field"></label>
                <label><span>API Key（留空不修改）</span><input v-model="apiKey" type="password" class="field"></label>
                <label><span>自动通过阈值</span><input v-model.number="config.approve_threshold" type="number" class="field"></label>
                <label><span>自动驳回阈值</span><input v-model.number="config.reject_threshold" type="number" class="field"></label>
              </div>
              <button type="button" class="primary" @click="saveConfig">保存 AI 配置</button>
            </div>
          </template>

          <template v-else-if="tab === 'deploy'">
            <div class="panel">
              <h3>部署日志</h3>
              <div class="log-row" v-for="(l, i) in deployLog" :key="i">{{ l.time || l.at || '' }} {{ l.text || l.msg || JSON.stringify(l) }}</div>
              <div v-if="!deployLog.length" class="empty">暂无日志</div>
            </div>
          </template>

          <template v-else>
            <div class="toolbar">
              <input v-model="search" placeholder="搜索标题 / 地点 / 描述">
              <span>{{ filteredItems.length }} 条</span>
            </div>
            <div v-if="loading" class="empty">正在读取…</div>
            <div v-else-if="!filteredItems.length" class="empty">暂无内容</div>
            <div v-else class="item-list">
              <article v-for="it in filteredItems" :key="it.id" class="admin-item">
                <div class="ai-head">
                  <span class="tag" :class="it.type === 'lost' ? 'tag-lost' : 'tag-found'">{{ it.type === 'lost' ? '寻物' : '招领' }}</span>
                  <span class="status" :class="statusClass(it.status)">{{ statusText(it.status) }}</span>
                  <span v-if="it.autoApproved" class="status ai-ok">AI 自动通过</span>
                  <span v-if="it.autoRejected" class="status ai-no">AI 自动拦截</span>
                  <b class="ai-title">{{ it.title }}</b>
                </div>
                <div class="ai-meta">{{ it.place || '未填写地点' }} · {{ fmt(it.createdAt) }}</div>
                <div class="ai-desc">{{ it.desc }}</div>
                <div v-if="it.secret" class="ai-secret">🔒 核验特征：{{ it.secret }}</div>
                <div v-if="it.rejectReason" class="ai-secret" style="border-color:#F3CFCF;color:#A12F2F;background:#FDF2F2">驳回理由：{{ it.rejectReason }}</div>
                <img v-if="it.photoUrl" :src="it.photoUrl" class="ai-photo" alt="">
                <div v-if="it.contact && it.contact.phone" class="ai-phone">📞 联系电话：{{ it.contact.phone }}</div>
                <div class="ai-actions">
                  <button v-if="it.status === 'pending'" type="button" class="primary" @click="review(it, 'approved')">通过并上架</button>
                  <button v-if="it.status === 'pending'" type="button" class="danger" @click="review(it, 'rejected')">驳回</button>
                  <button v-if="it.status === 'approved' || it.status === 'claimed'" type="button" class="ghost" @click="review(it, 'removed')">下架</button>
                  <button v-if="it.status === 'rejected'" type="button" class="primary" @click="review(it, 'approved')">改为通过</button>
                  <button v-if="it.phoneStatus === 'yellow' && !it.phoneVerified" type="button" class="ghost" @click="approvePhone(it)">通过号码</button>
                </div>
              </article>
            </div>
          </template>
        </template>
      </div>
      <div v-if="rejectTarget" class="admin-modal">
        <div class="modal-card">
          <h3>驳回「{{ rejectTarget.title }}」</h3>
          <p>请填写驳回理由，发布者会在「我的发布」里看到。</p>
          <textarea v-model="rejectReason" maxlength="200" placeholder="例如：描述过于模糊，请补充物品颜色/划痕等独有特征"></textarea>
          <div class="modal-actions">
            <button type="button" class="ghost" @click="rejectTarget = null">取消</button>
            <button type="button" class="danger" @click="confirmReject">确认驳回</button>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.admin-shell { width: 100%; min-width: 0; min-height: 100vh; background: #F3EEFA; color: #241C2E; font-family: inherit; }
.admin-header { background: linear-gradient(135deg, #3B1D63, #5B2A91 60%, #7A3CB0); color: #fff; padding: 22px 0 20px; box-shadow: 0 8px 24px rgba(59,29,99,.16); }
.admin-wrap { width: min(1120px, calc(100% - 48px)); margin: 0 auto; }
.brand { display: flex; align-items: center; gap: 12px; }
.brand-mark { width: 42px; height: 42px; border-radius: 13px; background: rgba(255,255,255,.15); display: flex; align-items: center; justify-content: center; font-size: 19px; font-weight: 700; }
.brand h1 { margin: 0; font-size: 20px; font-weight: 700; letter-spacing: .03em; }
.brand p { margin: 5px 0 0; font-size: 11px; color: #D9CCEC; }
.header-actions { float: right; margin-top: -42px; display: flex; gap: 8px; }
.header-actions button { background: rgba(255,255,255,.12); border: 1px solid rgba(255,255,255,.24); color: #fff; border-radius: 9px; padding: 8px 14px; font-family: inherit; font-size: 11px; }
.admin-main { padding: 22px 0 50px; }
.login-card { width: min(420px, 100%); margin: 70px auto; background: #fff; border: 1px solid #E7DDF4; border-radius: 18px; padding: 28px; box-shadow: 0 16px 44px rgba(59,29,99,.1); text-align: center; }
.login-card h2 { margin: 0 0 8px; font-size: 20px; }
.login-card p { margin: 0 0 18px; font-size: 11px; color: #8E7FA3; }
.login-card input { width: 100%; box-sizing: border-box; background: #F8F4FD; border: 1px solid #EDE3F8; border-radius: 10px; padding: 11px; font-family: inherit; font-size: 13px; margin-bottom: 10px; }
.primary { background: linear-gradient(135deg,#5B2A91,#7A3CB0); color: #fff; border: 0; border-radius: 9px; padding: 9px 15px; font-family: inherit; font-size: 12px; font-weight: 600; cursor: pointer; }
.login-card .primary { width: 100%; padding: 11px; }
.ghost { background: #fff; border: 1px solid #E4D8F1; color: #5B2A91; border-radius: 9px; padding: 8px 12px; font-family: inherit; font-size: 11px; cursor: pointer; }
.danger { background: #fff; border: 1px solid #F3CFCF; color: #C0392B; border-radius: 9px; padding: 8px 12px; font-family: inherit; font-size: 11px; cursor: pointer; }
.error { color: #C0392B; font-size: 11px; margin-top: 10px; }
.top-error { background: #FDEAEA; border: 1px solid #F3CFCF; border-radius: 9px; padding: 9px 12px; margin-bottom: 12px; }
.overview-strip { display: grid; grid-template-columns: repeat(6, 1fr); gap: 10px; margin-bottom: 14px; }
.ov-item { background: #fff; border: 1px solid #E9DFF5; border-radius: 13px; padding: 12px 14px; }
.ov-item b { display: block; font-size: 22px; color: #5B2A91; line-height: 1.1; }
.ov-item span { display: block; font-size: 10px; color: #8E7FA3; margin-top: 4px; }
.admin-tabs { display: flex; gap: 4px; background: #fff; border: 1px solid #E9DFF5; border-radius: 12px; padding: 4px; margin-bottom: 14px; overflow-x: auto; }
.admin-tabs button { flex: 1; white-space: nowrap; border: 0; background: transparent; border-radius: 8px; padding: 9px 8px; font-family: inherit; font-size: 11.5px; color: #7A6C8E; cursor: pointer; }
.admin-tabs button.on { background: #5B2A91; color: #fff; font-weight: 600; }
.panel { background: #fff; border: 1px solid #E9DFF5; border-radius: 15px; padding: 18px; }
.panel-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.panel h3 { margin: 0 0 12px; font-size: 14px; }
.bar-row { display: flex; align-items: center; gap: 10px; margin: 9px 0; font-size: 11px; color: #6E607F; }
.bar-row span { width: 66px; }
.bar-row i { flex: 1; height: 6px; background: #F0E8FA; border-radius: 99px; overflow: hidden; }
.bar-row i b { display: block; height: 100%; background: linear-gradient(90deg,#8A52C7,#C9A7F0); }
.bar-row em { font-style: normal; width: 28px; text-align: right; color: #5B2A91; }
.type-stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
.type-stats div { background: #F8F4FD; border-radius: 11px; padding: 12px; text-align: center; }
.type-stats b { display: block; font-size: 22px; color: #5B2A91; }
.type-stats span { font-size: 10px; color: #8E7FA3; }
.days { display: flex; align-items: flex-end; gap: 8px; height: 80px; padding-top: 6px; }
.days span { flex: 1; text-align: center; font-size: 8px; color: #A99BB9; }
.days i { display: block; width: 100%; background: linear-gradient(180deg,#C9A7F0,#8A52C7); border-radius: 4px 4px 0 0; }
.days em { font-style: normal; display: block; margin-top: 4px; }
.toolbar { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
.toolbar input { flex: 1; background: #fff; border: 1px solid #E9DFF5; border-radius: 10px; padding: 10px 12px; font-family: inherit; font-size: 12px; }
.toolbar span { font-size: 11px; color: #8E7FA3; }
.item-list { display: grid; gap: 10px; }
.admin-item { background: #fff; border: 1px solid #E9DFF5; border-radius: 13px; padding: 14px; }
.ai-head { display: flex; align-items: center; gap: 7px; flex-wrap: wrap; }
.tag { font-size: 10px; padding: 2px 7px; border-radius: 5px; background: #F4EEFB; color: #5B2A91; }
.tag-lost { background: #E8F0FE; color: #2F5FA8; }
.status { font-size: 9.5px; padding: 2px 7px; border-radius: 5px; background: #F4EEFB; color: #6D3AB0; }
.st-pending { background: #FFF4D6; color: #A97A00; }
.st-approved { background: #E6F4EA; color: #2F7D46; }
.st-rejected { background: #FDEAEA; color: #A12F2F; }
.ai-ok { background: #E6F4EA; color: #2F7D46; }
.ai-no { background: #FDEAEA; color: #A12F2F; }
.ai-title { font-size: 14px; margin-left: 2px; }
.ai-meta { font-size: 10.5px; color: #8E7FA3; margin-top: 6px; }
.ai-desc { font-size: 12px; line-height: 1.7; color: #4E445D; margin-top: 5px; }
.ai-secret { font-size: 11px; color: #5B2A91; background: #F7F0FF; border-radius: 8px; padding: 7px 9px; margin-top: 7px; }
.ai-photo { display: block; max-width: 220px; max-height: 220px; border-radius: 10px; margin-top: 9px; border: 1px solid #EDE3F8; object-fit: cover; }
.ai-phone { display: inline-block; font-size: 11px; color: #2F7D46; background: #E6F4EA; border-radius: 7px; padding: 6px 9px; margin-top: 8px; }
.ai-actions { display: flex; gap: 7px; flex-wrap: wrap; margin-top: 10px; }
.user-row, .ann-row { display: flex; justify-content: space-between; align-items: center; gap: 12px; padding: 11px 0; border-bottom: 1px solid #F0EAF7; }
.user-row b, .ann-row b { display: block; font-size: 12px; }
.user-row span, .ann-row span { display: block; font-size: 10px; color: #8E7FA3; margin-top: 3px; }
.ann-row em { font-style: normal; font-size: 9px; color: #A97A00; }
.row-actions { display: flex; gap: 6px; }
.field { width: 100%; box-sizing: border-box; background: #F8F4FD; border: 1px solid #EDE3F8; border-radius: 9px; padding: 9px 10px; font-family: inherit; font-size: 12px; margin-bottom: 8px; }
textarea.field { min-height: 78px; resize: vertical; }
.check { display: flex; align-items: center; gap: 7px; font-size: 11px; margin: 6px 0 12px; }
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.form-grid span { display: block; font-size: 10px; color: #8E7FA3; margin-bottom: 4px; }
.log-row { font-size: 10.5px; color: #6E607F; padding: 7px 0; border-bottom: 1px solid #F0EAF7; word-break: break-all; }
.empty { text-align: center; color: #A99BB9; font-size: 11px; padding: 26px 0; }
@media (max-width: 760px) {
  .admin-wrap { width: calc(100% - 24px); }
  .overview-strip { grid-template-columns: repeat(3, 1fr); }
  .panel-grid { grid-template-columns: 1fr; }
  .admin-tabs { flex-wrap: nowrap; }
  .admin-tabs button { flex: 0 0 auto; }
  .header-actions { float: none; margin-top: 12px; }
  .form-grid { grid-template-columns: 1fr; }
  .brand h1 { font-size: 16px; }
}
</style>

<style scoped>
.admin-modal { position: fixed; inset: 0; background: rgba(20,8,32,.42); z-index: 500; display: flex; align-items: center; justify-content: center; padding: 20px; }
.modal-card { width: min(440px, 100%); background: #fff; border-radius: 16px; padding: 20px; box-shadow: 0 20px 60px rgba(20,8,32,.25); }
.modal-card h3 { margin: 0 0 6px; font-size: 15px; }
.modal-card p { margin: 0 0 10px; font-size: 11px; color: #8E7FA3; }
.modal-card textarea { width: 100%; box-sizing: border-box; min-height: 84px; background: #F8F4FD; border: 1px solid #EDE3F8; border-radius: 10px; padding: 10px; font-family: inherit; font-size: 12px; resize: vertical; }
.modal-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 12px; }
</style>


<style scoped>
.ai-status { display:flex; align-items:center; gap:7px; background:#fff; border:1px solid #E9DFF5; border-radius:11px; padding:9px 12px; margin:-4px 0 12px; font-size:11px; color:#6E607F; }
.ai-status b { color:#2F7D46; }
.ai-status .dot { width:7px; height:7px; border-radius:50%; background:#A99BB9; }
.ai-status .dot.on { background:#2F7D46; box-shadow:0 0 0 3px rgba(47,125,70,.12); }
</style>



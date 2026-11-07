<script setup>
import { onMounted, ref } from 'vue'
import { api } from '../api'

const TOKEN_KEY = 'sg:admin:token'
const token = ref(localStorage.getItem(TOKEN_KEY) || '')
const password = ref('')
const stats = ref(null)
const items = ref([])
const loading = ref(false)
const error = ref('')
const tab = ref('pending')
const config = ref(null)
const accounts = ref([])
const announcements = ref([])
const deployLog = ref([])
const annTitle = ref('')
const annBody = ref('')
const apiKey = ref('')

onMounted(() => { if (token.value) load() })

async function login() {
  error.value = ''
  loading.value = true
  try {
    const data = await api.adminLogin(password.value)
    token.value = data.token
    localStorage.setItem(TOKEN_KEY, token.value)
    password.value = ''
    await load()
  } catch (e) {
    error.value = e.message || '登录失败'
  } finally {
    loading.value = false
  }
}

async function load() {
  if (!token.value) return
  loading.value = true
  try {
    const [s, list] = await Promise.all([api.adminStats(token.value), api.adminItems(token.value)])
    stats.value = s
    items.value = Array.isArray(list) ? list : []
  } catch (e) {
    error.value = e.message || '读取失败'
  } finally {
    loading.value = false
  }
}

async function review(it, status) {
  try {
    await api.adminPatch(it.id, { status, rejectReason: status === 'rejected' ? '管理员驳回' : '' }, token.value)
    await load()
  } catch (e) {
    error.value = e.message || '操作失败'
  }
}

async function switchTab(t) {
  tab.value = t
  if (!token.value) return
  if (t === 'config') {
    try { config.value = await api.adminConfig(token.value) } catch (e) { error.value = e.message }
  }
  if (t === 'accounts') {
    try { accounts.value = await api.adminAccounts(token.value) } catch (e) { error.value = e.message }
  }
  if (t === 'announcements') {
    try { announcements.value = await api.adminAnnouncements(token.value) } catch (e) { error.value = e.message }
  }
  if (t === 'deploy') {
    try {
      const d = await api.adminDeployLog(token.value)
      deployLog.value = Array.isArray(d) ? d : (d.items || d.logs || [])
    } catch (e) { error.value = e.message }
  }
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
    await switchTab('config')
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
    await switchTab('announcements')
  } catch (e) {
    error.value = e.message || '发布失败'
  }
}

async function setAnnouncement(a, status) {
  try {
    await api.adminPatchAnnouncement(a.id, { status }, token.value)
    await switchTab('announcements')
  } catch (e) { error.value = e.message || '操作失败' }
}

async function removeAnnouncement(a) {
  if (!confirm('确定删除公告「' + a.title + '」？')) return
  try {
    await api.adminDeleteAnnouncement(a.id, token.value)
    await switchTab('announcements')
  } catch (e) { error.value = e.message || '删除失败' }
}

async function toggleBan(a) {
  try {
    await api.adminBanAccount(a.id, !a.banned, token.value)
    await switchTab('accounts')
  } catch (e) { error.value = e.message || '操作失败' }
}
</script>

<template>
  <section class="screen active" id="screen-admin">
    <div class="topbar">
      <div class="t">拾光里 · 管理端</div>
      <button v-if="token" type="button" class="btn" @click="token=''; localStorage.removeItem('sg:admin:token')">退出</button>
    </div>
    <div class="scroll">
      <div v-if="!token" class="form-card">
        <div class="fc-title">管理员登录</div>
        <div class="form-item">
          <label>管理密码</label>
          <input v-model="password" type="password" placeholder="输入管理密码" @keyup.enter="login">
        </div>
        <button type="button" class="submit-btn" :disabled="loading" @click="login">{{ loading ? '登录中…' : '登录' }}</button>
        <div v-if="error" class="warn-box" style="margin-top:10px">{{ error }}</div>
      </div>

      <template v-else>
        <div class="home-stats" style="margin-bottom:12px">
          <div><b>{{ stats ? (stats.items ?? stats.total ?? '—') : '—' }}</b><span>全部</span></div>
          <div><b>{{ stats && stats.byStatus ? (stats.byStatus.pending || 0) : '—' }}</b><span>待审核</span></div>
          <div><b>{{ stats && stats.byStatus ? (stats.byStatus.approved || 0) : '—' }}</b><span>已上架</span></div>
        </div>
        <div class="lf-tabs" style="padding:0 0 10px">
          <button type="button" :class="{ on: tab === 'pending' }" @click="switchTab('pending')">待审核</button>
          <button type="button" :class="{ on: tab === 'all' }" @click="switchTab('all')">全部</button>
          <button type="button" :class="{ on: tab === 'config' }" @click="switchTab('config')">AI</button>
          <button type="button" :class="{ on: tab === 'accounts' }" @click="switchTab('accounts')">账号</button>
          <button type="button" :class="{ on: tab === 'announcements' }" @click="switchTab('announcements')">公告</button>
          <button type="button" :class="{ on: tab === 'deploy' }" @click="switchTab('deploy')">部署</button>
        </div>
        <div v-if="tab === 'config' && config" class="form-card">
          <div class="fc-title">AI 配置</div>
          <label style="display:flex;gap:6px;align-items:center;font-size:11px;margin:8px 0">
            <input v-model="config.enabled" type="checkbox" style="width:auto"> 启用 AI 审核
          </label>
          <div class="sa">Base URL</div>
          <input v-model="config.base_url" style="width:100%;box-sizing:border-box;background:#F8F4FD;border:1px solid #EDE3F8;border-radius:9px;padding:8px;margin:4px 0 8px;font-family:inherit;font-size:11px">
          <div class="sa">模型</div>
          <input v-model="config.model" style="width:100%;box-sizing:border-box;background:#F8F4FD;border:1px solid #EDE3F8;border-radius:9px;padding:8px;margin:4px 0 8px;font-family:inherit;font-size:11px">
          <div class="sa">API Key（留空不修改）</div>
          <input v-model="apiKey" type="password" style="width:100%;box-sizing:border-box;background:#F8F4FD;border:1px solid #EDE3F8;border-radius:9px;padding:8px;margin:4px 0 8px;font-family:inherit;font-size:11px">
          <div class="sa">自动通过阈值 / 自动驳回阈值</div>
          <div style="display:flex;gap:6px">
            <input v-model.number="config.approve_threshold" type="number" min="0" max="100" style="flex:1;background:#F8F4FD;border:1px solid #EDE3F8;border-radius:9px;padding:8px;font-family:inherit;font-size:11px">
            <input v-model.number="config.reject_threshold" type="number" min="0" max="100" style="flex:1;background:#F8F4FD;border:1px solid #EDE3F8;border-radius:9px;padding:8px;font-family:inherit;font-size:11px">
          </div>
          <button type="button" class="btn" style="width:100%;margin-top:10px" @click="saveConfig">保存 AI 配置</button>
        </div>
        <div v-else-if="tab === 'accounts'" class="form-card">
          <div class="fc-title">账号</div>
          <div v-for="a in accounts" :key="a.id" class="sa" style="padding:7px 0;border-bottom:1px solid var(--line)">
            {{ a.phone }} · {{ a.banned ? '封禁' : '正常' }}
            <button type="button" class="btn ghost" style="margin-left:6px" @click="toggleBan(a)">{{ a.banned ? '解封' : '封禁' }}</button>
          </div>
        </div>
        <div v-else-if="tab === 'announcements'" class="form-card">
          <div class="fc-title">公告</div>
          <input v-model="annTitle" maxlength="60" placeholder="公告标题" style="width:100%;box-sizing:border-box;background:#F8F4FD;border:1px solid #EDE3F8;border-radius:10px;padding:9px;margin:7px 0;font-family:inherit;font-size:11px">
          <textarea v-model="annBody" maxlength="2000" placeholder="公告正文" style="width:100%;box-sizing:border-box;background:#F8F4FD;border:1px solid #EDE3F8;border-radius:10px;padding:9px;margin-bottom:7px;font-family:inherit;font-size:11px;min-height:70px"></textarea>
          <button type="button" class="btn" style="width:100%;margin-bottom:10px" @click="createAnnouncement">发布公告</button>
          <div v-for="a in announcements" :key="a.id || a.title" class="sa" style="padding:7px 0;border-bottom:1px solid var(--line)">
            <b>{{ a.title }}</b><br>{{ a.body || a.text || '' }}
            <div style="display:flex;gap:5px;margin-top:6px">
              <button type="button" class="btn" @click="setAnnouncement(a, a.status === 'published' ? 'draft' : 'published')">{{ a.status === 'published' ? '下架' : '发布' }}</button>
              <button type="button" class="btn ghost" @click="removeAnnouncement(a)">删除</button>
            </div>
          </div>
        </div>
        <div v-else-if="tab === 'deploy'" class="form-card">
          <div class="fc-title" style="display:flex;justify-content:space-between;align-items:center">部署日志 <button type="button" class="btn ghost" @click="switchTab('deploy')">刷新</button></div>
          <div v-for="(l, i) in deployLog" :key="i" class="sa" style="padding:6px 0;border-bottom:1px solid var(--line)">
            {{ l.time || l.at || '' }} {{ l.text || l.msg || JSON.stringify(l) }}
          </div>
          <div v-if="!deployLog.length" class="sa">暂无日志</div>
        </div>
        <template v-else>
          <div v-if="loading" class="empty">正在读取…</div>
          <div v-else class="vue-list">
            <article v-for="it in items.filter(x => tab === 'all' || x.status === 'pending')" :key="it.id" class="item">
              <div class="thumb">{{ it.photoUrl ? '🖼️' : '📦' }}</div>
              <div class="body">
                <div class="tt"><span class="src-tag">{{ it.status }}</span>{{ it.title }}</div>
                <div class="dd">{{ it.desc }}</div>
                <div class="row">
                  <span class="meta">📍 {{ it.place }} · {{ it.ownerId ? it.ownerId.slice(0, 8) : '' }}</span>
                  <span style="display:flex;gap:4px">
                    <button type="button" class="btn" @click="review(it, 'approved')">通过</button>
                    <button type="button" class="btn ghost" @click="review(it, 'rejected')">驳回</button>
                  </span>
                </div>
              </div>
            </article>
          </div>
        </template>
      </template>
    </div>
  </section>
</template>

<style scoped>
.form-card .form-item input { width:100%; box-sizing:border-box; background:#F8F4FD; border:1px solid #EDE3F8; border-radius:10px; padding:10px; font-family:inherit; font-size:12px; }
.lf-tabs button { flex:1; }
</style>

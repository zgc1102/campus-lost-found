<script setup>
import { onMounted, ref } from 'vue'
import { api } from '../api'

const emit = defineEmits(['nav', 'publish'])
const items = ref([])
const claims = ref([])
const tab = ref('mine')
const loading = ref(true)
const phone = ref('')
const password = ref('')
const authMsg = ref('')
const account = ref(localStorage.getItem('sg:account:v1') || '')

onMounted(load)
async function load() {
  loading.value = true
  try {
    const [list, cs] = await Promise.all([api.mine(), api.claims()])
    if (Array.isArray(list)) items.value = list
    claims.value = cs.received || []
  } finally {
    loading.value = false
  }
}
async function login() {
  authMsg.value = ''
  try {
    const r = await api.accountLogin({ phone: phone.value.trim(), password: password.value })
    localStorage.setItem('sg:account:v1', r.accountId)
    account.value = r.accountId
    password.value = ''
    await load()
  } catch (e) {
    authMsg.value = e.message || '登录失败'
  }
}
function logout() {
  localStorage.removeItem('sg:account:v1')
  account.value = ''
  load()
}
async function withdraw(it) {
  if (!confirm('确定撤回删除「' + it.title + '」？')) return
  try {
    await api.remove(it.id)
    await load()
  } catch (e) {
    authMsg.value = e.message || '撤回失败'
  }
}
async function actClaim(c, status) {
  try {
    await api.claimAction(c.id, { status })
    await load()
  } catch (e) {
    authMsg.value = e.message || '操作失败'
  }
}
function status(x) {
  return ({ pending: '审核中', approved: '已上架', rejected: '已驳回', closed: '已闭环', claimed: '已认领' })[x.status] || x.status
}
function fmt(ts) {
  if (!ts) return ''
  const d = new Date(ts)
  return `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}
</script>

<template>
  <section class="screen active" id="screen-mine">
    <div class="topbar">
      <div class="back" @click="$emit('nav', 'home')">‹</div>
      <div class="t">我的发布</div>
      <button type="button" class="btn" @click="$emit('publish', 'lost')">发布</button>
    </div>
    <div class="scroll">
      <div class="form-card" style="padding:14px;margin-bottom:10px">
        <div class="fc-title">账号</div>
        <div v-if="account" style="padding-top:10px;font-size:11px;color:var(--sub)">
          已登录 · {{ account.slice(0, 10) }}
          <button type="button" class="btn ghost" style="margin-left:8px" @click="logout">退出</button>
        </div>
        <template v-else>
          <div class="form-item" style="margin:8px 0">
            <input v-model="phone" maxlength="11" placeholder="手机号">
          </div>
          <div class="form-item" style="margin:8px 0">
            <input v-model="password" type="password" placeholder="密码（至少 4 位）">
          </div>
          <button type="button" class="btn" style="width:100%" @click="login">登录 / 注册</button>
          <div v-if="authMsg" class="sa" style="margin-top:6px">{{ authMsg }}</div>
        </template>
      </div>
      <div class="lf-tabs" style="padding:0 0 10px">
        <button type="button" :class="{ on: tab === 'mine' }" @click="tab = 'mine'">我的发布</button>
        <button type="button" :class="{ on: tab === 'claims' }" @click="tab = 'claims'">认领申请 {{ claims.length ? '(' + claims.length + ')' : '' }}</button>
      </div>
      <div class="hintline">这台设备上发布的启事和求助。登录后换设备也能看到「我的发布」。</div>
      <template v-if="tab === 'mine'">
        <div v-if="loading" class="empty">正在读取…</div>
        <div v-else-if="!items.length" class="empty">还没有发布，点右上角「发布」写一条</div>
        <div v-else class="vue-list">
          <article v-for="it in items" :key="it.id" class="item">
            <div class="thumb">{{ it.type === 'help' ? '🤝' : (it.type === 'lost' ? '🔎' : '📦') }}</div>
            <div class="body">
              <div class="tt"><span class="src-tag">{{ it.type === 'help' ? '求助' : (it.type === 'lost' ? '寻物' : '招领') }}</span>{{ it.title }}</div>
              <div class="dd">{{ it.desc }}</div>
              <div class="row">
                <span class="meta">{{ status(it) }} · {{ fmt(it.createdAt) }}</span>
                <span style="display:flex;gap:5px">
                  <button type="button" class="btn" @click="$emit('publish', it.type === 'help' ? 'help' : it.type)">再发一条</button>
                  <button type="button" class="btn ghost" @click="withdraw(it)">撤回删除</button>
                </span>
              </div>
            </div>
          </article>
        </div>
      </template>
      <template v-else>
        <div v-if="loading" class="empty">正在读取…</div>
        <div v-else-if="!claims.length" class="empty">还没有人申请</div>
        <div v-else class="vue-list">
          <article v-for="c in claims" :key="c.id" class="item">
            <div class="thumb">🙋</div>
            <div class="body">
              <div class="tt"><span class="src-tag">{{ c.status }}</span>{{ c.itemTitle }}</div>
              <div class="dd">{{ c.message }}</div>
              <div v-if="c.itemSecret" class="dd" style="color:#8A52C7">核对特征：{{ c.itemSecret }}</div>
              <div class="row">
                <span class="meta">{{ fmt(c.createdAt) }}</span>
                <span style="display:flex;gap:4px">
                  <button type="button" class="btn" @click="actClaim(c, 'accepted')">通过</button>
                  <button type="button" class="btn ghost" @click="actClaim(c, 'need_more')">补充</button>
                  <button type="button" class="btn ghost" @click="actClaim(c, 'rejected')">拒绝</button>
                </span>
              </div>
            </div>
          </article>
        </div>
      </template>
    </div>
  </section>
</template>

<style scoped>
.form-item input {
  width: 100%;
  box-sizing: border-box;
  background: #F8F4FD;
  border: 1px solid #EDE3F8;
  border-radius: 10px;
  padding: 9px 10px;
  font-family: inherit;
  font-size: 11px;
  color: var(--ink);
}
</style>

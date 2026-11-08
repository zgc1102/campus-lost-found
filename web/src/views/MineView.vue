<script setup>
import { onMounted, ref } from 'vue'
import { api } from '../api'

const emit = defineEmits(['nav', 'publish', 'edit'])
const items = ref([])
const claims = ref([])
const sentClaims = ref([])
const tab = ref('mine')
const loading = ref(true)
const phone = ref('')
const password = ref('')
const authMsg = ref('')
const account = ref(localStorage.getItem('sg:account:v1') || '')
const accountPhone = ref(localStorage.getItem('sg:account:phone') || '')
const origin = location.origin
const myTag = ref(null)

onMounted(() => load())
async function load(silent = false) {
  if (!silent) loading.value = true
  try {
    const [list, cs, tags] = await Promise.all([api.mine(), api.claims(), api.myTags()])
    if (Array.isArray(list)) items.value = list
    claims.value = cs.received || []
    sentClaims.value = cs.sent || []
    myTag.value = Array.isArray(tags) && tags.length ? tags[0] : null
  } finally {
    if (!silent) loading.value = false
  }
}
async function login() {
  authMsg.value = ''
  try {
    const r = await api.accountLogin({ phone: phone.value.trim(), password: password.value })
    localStorage.setItem('sg:account:v1', r.accountId)
    localStorage.setItem('sg:account:phone', r.phone || phone.value.trim())
    account.value = r.accountId
    accountPhone.value = r.phone || phone.value.trim()
    password.value = ''
    await load(true)
  } catch (e) {
    authMsg.value = e.message || '登录失败'
  }
}
function logout() {
  localStorage.removeItem('sg:account:v1')
  localStorage.removeItem('sg:account:phone')
  account.value = ''
  accountPhone.value = ''
  load(true)
}
function maskPhone(p) {
  const s = String(p || '')
  if (s.length < 7) return s
  return s.slice(0, 3) + '****' + s.slice(-4)
}
async function withdraw(it) {
  if (!confirm('确定撤回删除「' + it.title + '」？')) return
  try {
    await api.remove(it.id)
    await load(true)
  } catch (e) {
    authMsg.value = e.message || '撤回失败'
  }
}
async function cancelMyTag() {
  if (!confirm('确定注销拾光码？注销后别人扫码会显示此码已注销，不能再给你发消息。')) return
  try {
    await api.deleteTag()
    myTag.value = null
  } catch (e) {
    authMsg.value = e.message || '注销失败'
  }
}

async function actClaim(c, status) {
  try {
    await api.claimAction(c.id, { status })
    await load(true)
  } catch (e) {
    authMsg.value = e.message || '操作失败'
  }
}

async function completeClaim(c) {
  const code = prompt('请输入对方提供的 6 位取件码')
  if (!code) return
  try {
    await api.claimComplete(c.id, { code: code.trim() })
    await load(true)
  } catch (e) {
    authMsg.value = e.message || '确认失败'
  }
}
function status(x) {
  return ({ pending: '审核中', approved: '已上架', rejected: '已驳回', closed: '已闭环', claimed: '已认领', removed: '已下架' })[x.status] || x.status
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
      <div class="netbadge on">🌐 已连接服务器：{{ origin }}（其他同学也能看到）</div>

      <div v-if="myTag" class="tag-mine">
        <div class="tm-head"><b>我的拾光码</b><span class="tm-dot">长期有效</span></div>
        <div class="tm-code">{{ myTag.code }}</div>
        <div class="tm-meta">{{ myTag.itemName || '我的物品' }} · 注册于 {{ new Date(myTag.createdAt).toLocaleDateString('zh-CN') }}</div>
        <div class="tm-warn">此码长期有效，不随版本更新失效。如果不再使用，建议及时注销，避免被他人反复扫码打扰。</div>
        <button type="button" class="tm-cancel" @click="cancelMyTag">注销此码</button>
      </div>
      <div v-else class="tag-mine empty-tag">
        <div class="tm-meta">还没有拾光码。给物品贴一张码，捡到的人扫码就能联系你。</div>
        <button type="button" class="tm-create" @click="$emit('nav', 'tag')">去生成拾光码</button>
      </div>

      <div class="accbox">
        <div v-if="account" class="acc-line">
          ✅ 已登录：{{ maskPhone(accountPhone) }}
          <a href="javascript:void(0)" @click="logout">退出</a>
        </div>
        <template v-else>
          <div class="acc-title">登录后，换设备或换网址也能看到「我的发布」<br>第一次输入手机号 + 密码就是注册</div>
          <div class="acc-row">
            <input v-model="phone" inputmode="numeric" maxlength="20" placeholder="手机号">
            <input v-model="password" type="password" maxlength="30" placeholder="密码（至少 4 位）">
          </div>
          <button type="button" class="btn" style="width:100%;margin-top:8px" @click="login">登录 / 注册</button>
          <div v-if="authMsg" class="tip-small" style="margin-top:6px;color:#c0392b">{{ authMsg }}</div>
        </template>
      </div>

      <div v-if="claims.length" style="margin:12px 0">
        <div class="sectitle">认领申请</div>
        <div v-for="c in claims" :key="c.id" class="mini">
          <div class="mh">{{ c.itemTitle }}<span class="st">{{ c.status }}</span></div>
          <div class="mmeta">{{ c.message }}</div>
          <div class="mact">
            <template v-if="c.status === 'accepted'">
              <button type="button" class="btn" @click="completeClaim(c)">确认归还</button>
            </template>
            <template v-else>
              <button type="button" class="btn" @click="actClaim(c, 'accepted')">通过</button>
              <button type="button" class="btn ghost" @click="actClaim(c, 'need_more')">补充</button>
              <button type="button" class="btn ghost" @click="actClaim(c, 'rejected')">拒绝</button>
            </template>
          </div>
        </div>
        <div v-if="sentClaims.length" class="sectitle" style="margin-top:10px">我发出的认领</div>
        <div v-for="c in sentClaims" :key="'s'+c.id" class="mini">
          <div class="mh">{{ c.itemTitle }}<span class="st">{{ c.status }}</span></div>
          <div class="mmeta">{{ c.message }}</div>
          <div v-if="c.status === 'accepted'" class="mmeta">取件码：{{ c.returnCode || '向对方索取' }}</div>
          <div v-if="c.status === 'accepted'" class="mact">
            <button type="button" class="btn" @click="completeClaim(c)">确认归还</button>
          </div>
        </div>
      </div>

      <div class="hintline">{{ items.length ? '共 ' + items.length + ' 条发布，只有「已上架」的才会出现在公共列表里。' : '你还没有发布过内容。提交后会先进入审核，通过后才上架。' }}</div>

      <div v-if="loading" class="empty">正在读取…</div>
      <div v-else-if="!items.length" class="empty">
        还没有发布记录<br><br>
        <button type="button" class="btn" @click="$emit('publish', 'lost')">发布寻物</button>
        <button type="button" class="btn ghost" style="margin-left:5px" @click="$emit('publish', 'found')">发布招领</button>
      </div>
      <div v-else>
        <div v-for="it in items" :key="it.id" class="mini">
          <div class="mh">
            {{ it.type === 'help' ? '🤝' : (it.type === 'lost' ? '🔎' : '📦') }} {{ it.title }}
            <span class="st" :class="'st-' + it.status">{{ status(it) }}</span>
          </div>
          <div class="mmeta">{{ it.type === 'help' ? '爱心求助' : (it.type === 'lost' ? '寻物启事' : '招领启事') }} · {{ it.place || '' }} · {{ fmt(it.createdAt) }}</div>
          <div v-if="it.status === 'rejected' || it.status === 'removed'" class="reason" style="color:#c0392b;font-size:11px;margin-top:4px">{{ it.status === 'removed' ? '下架理由' : '驳回理由' }}：{{ it.rejectReason || '未填写' }}</div>
          <div class="mact">
            <button type="button" class="btn ghost" @click="$emit('edit', it)">查看</button>
            <button v-if="it.status === 'rejected'" type="button" class="btn" @click="$emit('edit', it)">修改并重新提交</button>
            <button v-else type="button" class="btn" @click="$emit('publish', it.type === 'help' ? 'help' : it.type)">再发一次</button>
            <button type="button" class="btn danger" @click="withdraw(it)">撤回删除</button>
          </div>
        </div>
      </div>
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


<style scoped>
.tag-mine { background:#fff; border:1px solid #EADFF5; border-radius:12px; padding:10px 12px; margin-bottom:10px; }
.tm-head { display:flex; align-items:center; justify-content:space-between; }
.tm-head b { font-size:12px; color:#3B1D63; }
.tm-dot { font-size:9px; color:#2F7D46; background:#EAF7EE; border-radius:99px; padding:3px 6px; }
.tm-code { font-size:18px; font-weight:700; letter-spacing:.12em; color:#5B2A91; margin:5px 0 2px; }
.tm-meta { font-size:10.5px; color:#6E607F; line-height:1.6; }
.tm-warn { font-size:9.5px; color:#A97A00; background:#FFF8E8; border-radius:7px; padding:6px 7px; margin-top:7px; line-height:1.6; }
.tm-cancel { width:100%; margin-top:7px; border:1px solid #F3CFCF; background:#FDF2F2; color:#A12F2F; border-radius:8px; padding:7px; font-family:inherit; font-size:10px; }
.tm-create { margin-top:7px; border:0; background:linear-gradient(135deg,#5B2A91,#7A3CB0); color:#fff; border-radius:8px; padding:8px 12px; font-family:inherit; font-size:10.5px; }
.empty-tag .tm-meta { margin-bottom:2px; }
</style>


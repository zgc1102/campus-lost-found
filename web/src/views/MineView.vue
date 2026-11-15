<script setup>
import { computed, onMounted, ref } from 'vue'
import { api } from '../api'

const emit = defineEmits(['nav', 'publish', 'edit'])
const items = ref([])
const claims = ref([])
const sentClaims = ref([])
const lostClaims = computed(() => claims.value.filter((c) => c.itemType !== 'help'))
const helpClaims = computed(() => claims.value.filter((c) => c.itemType === 'help'))
const tab = ref('mine')
const loading = ref(true)
const phone = ref('')
const password = ref('')
const authMsg = ref('')
const codeFor = ref(null)
const codeInput = ref('')
const codeError = ref('')
const codeBusy = ref(false)
const successMsg = ref('')
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
  phone.value = ''
  password.value = ''
  authMsg.value = ''
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
  successMsg.value = ''
  if (c.itemType === 'help') {
    try {
      await api.claimComplete(c.id, { code: '' })
      successMsg.value = '已完成帮助'
      await load(true)
    } catch (e) {
      authMsg.value = e.message || '确认失败'
    }
    return
  }
  codeFor.value = c
  codeInput.value = ''
  codeError.value = ''
}

async function submitCode() {
  if (!codeFor.value) return
  if (!/^\d{4,6}$/.test(codeInput.value.trim())) {
    codeError.value = '请输入 4~6 位取件码'
    return
  }
  codeBusy.value = true
  codeError.value = ''
  try {
    const done = codeFor.value
    await api.claimComplete(done.id, { code: codeInput.value.trim() })
    done.status = 'completed'
    if (done.itemId) {
      const item = items.value.find((x) => x.id === done.itemId)
      if (item) item.status = 'closed'
    }
    successMsg.value = '已确认归还，该招领已结束'
    codeFor.value = null
    codeInput.value = ''
    codeError.value = ''
    await load(true)
  } catch (e) {
    codeError.value = e.message || '取件码不正确'
  } finally {
    codeBusy.value = false
  }
}

function claimStatus(s) {
  return ({ pending: '待确认', accepted: '已通过', completed: '已完成', rejected: '已拒绝', need_more: '待补充', closed: '已结束' })[s] || s
}
function claimVerdict(c) {
  const n = Number(c?.confidence)
  if (!Number.isFinite(n) || n <= 0) return '暂无参考'
  if (n >= 80) return '相似度较高'
  if (n >= 60) return '有一些相似'
  return '相似度较低'
}
function status(x) {
  return ({ pending: '审核中', approved: '进行中', rejected: '未通过', closed: '已结束', claimed: '进行中', removed: '已下架' })[x.status] || x.status
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
      <div v-if="!account" class="tip-small">登录后可以查看自己的发布和申请。</div>

      <div v-if="myTag" class="tag-mine">
        <div class="tm-head"><b>我的拾光码</b><span class="tm-dot">长期有效</span></div>
        <img v-if="myTag.qrData" :src="myTag.qrData" class="tm-qr" alt="拾光码二维码">
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
            <input v-model="phone" inputmode="numeric" maxlength="20" placeholder="手机号" autocomplete="off">
            <input v-model="password" type="password" maxlength="30" placeholder="密码（至少 4 位）" autocomplete="new-password">
          </div>
          <button type="button" class="btn" style="width:100%;margin-top:8px" @click="login">登录 / 注册</button>
          <div v-if="authMsg" class="tip-small" style="margin-top:6px;color:#c0392b">{{ authMsg }}</div>
        </template>
      </div>

      <div v-if="successMsg" class="success-line">{{ successMsg }}</div>

      <div v-if="lostClaims.length" style="margin:12px 0">
        <div class="sectitle">认领申请</div>
        <div v-for="c in lostClaims" :key="c.id" class="mini">
          <div class="mh">{{ c.itemTitle }}<span class="st">{{ claimStatus(c.status) }}</span></div>
          <div class="mmeta">{{ c.message }}</div>
          <div v-if="c.aiCheck" class="claim-ai-line">信息对比度 {{ c.aiCheck.confidence }}% · {{ claimVerdict(c.aiCheck) }}</div>
          <div v-if="c.aiCheck?.reason" class="tip-small">依据：{{ c.aiCheck.reason }}</div>
          <div v-if="c.hint" class="claim-hint" :class="'hint-' + c.hint.type">{{ c.hint.text }}<template v-if="c.hint.type === 'strong'"> 对比度 {{ c.hint.score }}%，地点和描述有相近项。</template></div>
          <div v-if="c.status === 'accepted'" class="mact">
            <button type="button" class="btn" @click="completeClaim(c)">归还</button>
          </div>
          <div v-else-if="c.status === 'pending'" class="mact">
            <button type="button" class="btn" @click="actClaim(c, 'accepted')">通过</button>
            <button type="button" class="btn ghost" @click="actClaim(c, 'need_more')">补充</button>
            <button type="button" class="btn ghost" @click="actClaim(c, 'rejected')">拒绝</button>
          </div>
          <div v-else-if="c.status === 'need_more'" class="mact">
            <button type="button" class="btn" @click="actClaim(c, 'accepted')">通过</button>
            <button type="button" class="btn ghost" @click="actClaim(c, 'rejected')">拒绝</button>
            <button type="button" class="btn ghost" @click="actClaim(c, 'need_more')">再次提醒补充</button>
          </div>
          <div v-if="codeFor && codeFor.id === c.id" class="code-box">
            <input v-model="codeInput" inputmode="numeric" maxlength="6" placeholder="输入对方提供的 4~6 位取件码">
            <button type="button" class="btn" :disabled="codeBusy" @click="submitCode">{{ codeBusy ? '确认中…' : '确认归还' }}</button>
            <button type="button" class="btn ghost" @click="codeFor = null">取消</button>
            <div v-if="codeError" class="tip-small" style="color:#c0392b">{{ codeError }}</div>
          </div>
        </div>
      </div>

      <div v-if="helpClaims.length" style="margin:12px 0">
        <div class="sectitle">帮忙申请</div>
        <div v-for="c in helpClaims" :key="c.id" class="mini">
          <div class="mh">{{ c.itemTitle }}<span class="st">{{ claimStatus(c.status) }}</span></div>
          <div class="mmeta">{{ c.message }}</div>
          <div v-if="c.status === 'accepted'" class="mact">
            <button type="button" class="btn" @click="completeClaim(c)">完成帮助</button>
          </div>
          <div v-else-if="c.status === 'pending'" class="mact">
            <button type="button" class="btn" @click="actClaim(c, 'accepted')">接受帮忙</button>
            <button type="button" class="btn ghost" @click="actClaim(c, 'need_more')">请补充</button>
            <button type="button" class="btn ghost" @click="actClaim(c, 'rejected')">婉拒</button>
          </div>
          <div v-else-if="c.status === 'need_more'" class="mact">
            <button type="button" class="btn" @click="actClaim(c, 'accepted')">接受帮忙</button>
            <button type="button" class="btn ghost" @click="actClaim(c, 'rejected')">婉拒</button>
          </div>
        </div>
      </div>

      <div v-if="sentClaims.length" style="margin:12px 0">
        <div class="sectitle">我发出的认领 / 帮忙</div>
        <div v-for="c in sentClaims" :key="'s'+c.id" class="mini">
          <div class="mh">{{ c.itemTitle }}<span class="st">{{ claimStatus(c.status) }}</span></div>
          <div class="mmeta">{{ c.message }}</div>
          <div v-if="c.aiCheck && c.itemType !== 'help'" class="claim-ai-line">信息对比度 {{ c.aiCheck.confidence }}% · {{ claimVerdict(c.aiCheck) }}</div>
          <div v-if="c.status === 'accepted' && c.itemType !== 'help'" class="mmeta">取件码：{{ c.returnCode || '向对方索取' }}</div>
        </div>
      </div>

      <div class="hintline">{{ items.length ? '共 ' + items.length + ' 条发布，只有「进行中」的才会出现在公共列表里。' : '你还没有发布过内容。发布后 AI 会自动审核，通过后自动上架。' }}</div>

      <div v-if="claims.length" class="tip-small" style="margin:4px 0 8px">信息对比度只作提示，不自动通过、不自动拒绝、不改变排序。最终由发布者决定。</div>

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



<style scoped>
.tm-qr { width:112px; height:112px; display:block; margin:8px auto 4px; border-radius:8px; }
</style>


<style scoped>
.code-box { margin-top:7px; padding:8px; background:#FBF8FF; border:1px solid #EADFF5; border-radius:9px; display:flex; flex-wrap:wrap; gap:6px; }
.code-box input { flex:1; min-width:140px; border:1px solid #E4D4F7; border-radius:8px; padding:8px; font-family:inherit; font-size:11px; }
.code-box .btn { width:auto; flex:0 0 auto; padding:8px 10px; }
</style>


<style scoped>
.claim-ai-line { margin-top:3px; font-size:9.5px; color:#5B2A91; background:#F7F0FF; border-radius:5px; padding:3px 5px; display:inline-block; }
</style>





<style scoped>
.success-line { margin:10px 0; padding:8px 10px; background:#EAF7EE; border:1px solid #CFE8D6; color:#2F7D46; border-radius:8px; font-size:11px; }
</style>


<style scoped>
.claim-hint { margin-top:5px; padding:6px 8px; border-radius:7px; font-size:9px; line-height:1.6; }
.claim-hint.hint-strong { background:#EEF8F1; border:1px solid #CFE8D7; color:#2F6B45; }
.claim-hint.hint-weak { background:#F8F6FB; border:1px solid #E5DEEC; color:#8B7A9B; }
</style>

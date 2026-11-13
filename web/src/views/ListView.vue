<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { api } from '../api'

const props = defineProps({
  type: { type: String, default: 'lost' }
})
const emit = defineEmits(['nav', 'publish'])

const items = ref([])
const loading = ref(true)
const query = ref('')
const selected = ref(null)
const claimMsg = ref('')
const claimPhone = ref('')
const claimState = ref('')
const claiming = ref(false)
const reportState = ref('')
const claimOpen = ref(false)
const claimCheck = ref(null)
const claimChecking = ref(false)
const claimCheckError = ref('')
const photoOpen = ref(false)
const showClosed = ref(false)
const aiPhotoInput = ref(null)
const aiPhotoState = ref('')

async function openDetail(it) {
  selected.value = it
  claimMsg.value = ''
  claimPhone.value = ''
  claimState.value = ''
  claimOpen.value = false
  photoOpen.value = false
  claimCheck.value = null
  claimCheckError.value = ''
}

function openAiPhoto() {
  aiPhotoInput.value?.click()
}

function onAiPhoto(e) {
  const file = e.target.files && e.target.files[0]
  if (!file) return
  aiPhotoState.value = '智能识别照片中…'
  const reader = new FileReader()
  reader.onload = () => {
    const img = new Image()
    img.onload = async () => {
      const max = 720
      const scale = Math.min(1, max / Math.max(img.width, img.height))
      const canvas = document.createElement('canvas')
      canvas.width = Math.round(img.width * scale)
      canvas.height = Math.round(img.height * scale)
      canvas.getContext('2d').drawImage(img, 0, 0, canvas.width, canvas.height)
      const photo = canvas.toDataURL('image/jpeg', 0.75)
      let info = { photo }
      try {
        const d = await api.vision(photo)
        if (d && d.ok !== false) {
          info = { ...info, category: d.category, color: d.color, brand: d.brand, features: d.features, desc: d.desc }
        }
      } catch (_) {}
      sessionStorage.setItem('sg:aiPhoto', JSON.stringify(info))
      aiPhotoState.value = ''
      emit('nav', 'publish')
    }
    img.src = reader.result
  }
  reader.readAsDataURL(file)
  e.target.value = ''
}
async function submitClaim() {
  if (!selected.value) return
  if (claimMsg.value.trim().length < 2) { claimState.value = selected.value.type === 'lost' ? '写一下你是在哪里捡到的' : '写一下只有失主知道的细节'; return }
  claiming.value = true
  claimState.value = ''
  try {
    if (selected.value.myClaim === 'need_more' && selected.value.myClaimId) {
      await api.supplement(selected.value.myClaimId, { message: claimMsg.value.trim(), contact: claimPhone.value.trim() })
      claimState.value = '已补充，等对方再看'
    } else {
      await api.claim(selected.value.id, { message: claimMsg.value.trim(), contact: claimPhone.value.trim() })
      claimState.value = '已发送，等对方确认'
    }
  } catch (e) {
    claimState.value = e.message || '发送失败'
  } finally {
    claiming.value = false
  }
}

async function runClaimCheck() {
  if (!selected.value) return
  if (claimMsg.value.trim().length < 2) {
    claimCheckError.value = '先写下你记得的物品特征，再做核验'
    return
  }
  claimChecking.value = true
  claimCheckError.value = ''
  claimCheck.value = null
  try {
    const r = await api.claimCheck(selected.value.id, claimMsg.value.trim())
    if (r && r.ok && r.check) claimCheck.value = r.check
    else claimCheckError.value = r?.error || 'AI 核验暂时不可用，可以直接提交'
  } catch (e) {
    claimCheckError.value = e.message || 'AI 核验暂时不可用，可以直接提交'
  } finally {
    claimChecking.value = false
  }
}

function aiVerdict(v) {
  return v === 'match' ? '特征吻合' : v === 'mismatch' ? '特征不一致' : '需要人工核对'
}

async function reportItem() {
  if (!selected.value || !confirm('确认举报这条信息？')) return
  try {
    await api.report(selected.value.id)
    reportState.value = '已举报，管理员会核实'
  } catch (e) {
    reportState.value = e.message || '举报失败'
  }
}

const copy = computed(() => props.type === 'lost'
  ? {
      title: '失物招领', kicker: '失物招领', hint: '捡到的东西在这里等主人', other: '寻物启事', publish: '发布启事',
      warning: '⚠️ 认领提示：认领物品前，请务必核对物品独有特征，请勿仅凭照片认领，谨防冒领。<br>交接请选择公共场所，不要前往偏僻地点，谨慎公开手机号、微信等私人联系方式。'
    }
  : {
      title: '寻物启事', kicker: '失物招领', hint: '看到的同学可以帮一把', other: '失物招领', publish: '发布启事',
      warning: '⚠️ 防骗提示：主动联系你并提供“验证码 / 转账 / 付费解锁”的，基本都是骗子。<br>真实认领请当面核对物品细节，平台不会收取任何费用。'
    })

const visible = computed(() => {
  const target = props.type === 'lost' ? 'found' : 'lost'
  const q = query.value.trim().toLowerCase()
  return items.value
    .filter((x) => x.type === target && ['approved', 'claimed', 'closed'].includes(x.status))
    .filter((x) => showClosed.value || x.status !== 'closed')
    .filter((x) => !q || ((x.title || '') + (x.desc || '') + (x.place || '')).toLowerCase().includes(q))
    .sort((a, b) => (b.createdAt || 0) - (a.createdAt || 0))
})

onMounted(load)
watch(() => props.type, () => { query.value = '' })
watch(showClosed, () => load())

async function load() {
  loading.value = true
  try {
    const list = await api.items(showClosed.value)
    if (Array.isArray(list)) items.value = list
    const focus = sessionStorage.getItem('sg:focusItem')
    if (focus) {
      sessionStorage.removeItem('sg:focusItem')
      const hit = items.value.find((x) => x.id === focus)
      if (hit) openDetail(hit)
    }
  } catch (_) {
    items.value = []
  } finally {
    loading.value = false
  }
}

function fmt(ts) {
  if (!ts) return ''
  const d = new Date(ts)
  return `${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}
function label(x) {
  return x.type === 'found' ? '招领' : '寻物'
}
function thumbText(x) {
  return ({
    bag: '🎒', card: '🪪', watch: '⌚', electronics: '🎧', umbrella: '☂️',
    key: '🔑', keys: '🔑', book: '📚', sports: '🏀', cup: '🥤', bottle: '🥤',
    charger: '🔋', repair: '🛠️', life: '🏠', office: '🖨️', outdoor: '⛺',
    cloth: '🧥', other: '📦'
  })[x.cat] || '📦'
}
function chipText(x) {
  if (!x.fields) return []
  return Object.values(x.fields).filter(Boolean).slice(0, 3)
}
function actionLabel(x) {
  if (x.isMine) return '你发布的'
  if (x.status === 'closed') return '已结束'
  if (x.status === 'claimed') return '进行中'
  if (x.status !== 'approved') return '暂不可操作'
  if (x.type === 'lost') return '提供线索'
  if (x.myClaim === 'pending') return '已申请'
  if (x.myClaim === 'accepted' || x.myClaim === 'completed') return '已通过'
  if (x.myClaim === 'need_more') return '补充信息'
  if (x.myClaim === 'rejected') return '重新申请'
  if (x.act) return x.act
  return x.type === 'lost' ? '提供线索' : '认领'
}
function statusChip(x) {
  const map = { claimed: '进行中', closed: '已结束', pending: '审核中', rejected: '未通过', removed: '已下架' }
  return map[x.status] || ''
}
function canClaim(x) {
  return !x.isMine && x.status === 'approved' && !['pending', 'accepted', 'completed'].includes(x.myClaim)
}
function openOldPublish() {
  emit('publish', props.type)
}
function openOldRadar() {
  emit('nav', 'radar')
}
function openOldHelp() {
  emit('nav', 'help')
}
</script>

<style>
.vue-sheet {
  max-height: 88vh;
  overflow-y: auto;
  z-index: 210;
}
.vue-sheet .big-thumb {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 52px;
  color: #5B2A91;
  overflow: hidden;
}
.scroll > .tip-box {
  margin-top: 10px;
  margin-bottom: 14px;
}
.item .sum {
  font-size: 12.5px;
  line-height: 1.55;
}
.item .dd {
  font-size: 12px;
  line-height: 1.6;
}
.item .meta {
  font-size: 10.5px;
}
.item .chips .chip {
  font-size: 10px;
}
</style>

<template>
  <section class="screen active" :id="'screen-' + type">
    <div class="topbar">
      <div class="back" @click="$emit('nav', 'home')">‹</div>
      <div class="t">{{ copy.title }}</div>
      <button class="btn" type="button" @click="openOldPublish">{{ copy.publish }}</button>
    </div>

    <div class="lf-tabs">
      <button type="button" :class="{ on: type === 'lost' }" @click="$emit('nav', 'lost')">失物招领</button>
      <button type="button" :class="{ on: type === 'found' }" @click="$emit('nav', 'found')">寻物启事</button>
    </div>

    <div class="scroll">
      <div class="tip-box" v-html="copy.warning"></div>

      <button type="button" class="ai-photo-entry" @click="openAiPhoto">
        <span class="ape-ico">📷</span>
        <span class="ape-copy"><b>智能拍照识别</b><i>拍一张，自动识别物品、颜色和特征</i></span>
        <span class="ape-go">→</span>
      </button>
      <input ref="aiPhotoInput" type="file" accept="image/*" capture="environment" style="display:none" @change="onAiPhoto">
      <div v-if="aiPhotoState" class="ai-photo-state">{{ aiPhotoState }}</div>

      <div class="list-meta">
        <b>{{ visible.length }}</b> 条{{ type === 'lost' ? '招领' : '寻物' }} · {{ copy.hint }}
        <button type="button" class="closed-toggle" @click="showClosed = !showClosed">{{ showClosed ? '隐藏已结束' : '显示已结束' }}</button>
      </div>

      <button type="button" class="match-entry" @click="$emit('nav', 'match')">
        <span class="me-badge">配对</span>
        <span class="me-copy"><b>智能匹配报告</b><i>把寻物和招领放在一起，看文本、类别、地点、时间四项依据</i></span>
        <span class="re-go">查看 →</span>
      </button>

      <button type="button" class="radar-entry" @click="openOldRadar">
        <span class="re-badge">智能</span>
        <span class="re-copy"><b>{{ type === 'lost' ? '寻物雷达' : '招领雷达' }}</b><i>自动比对全站{{ type === 'lost' ? '招领' : '寻物' }}</i></span>
        <span class="re-go">扫描 →</span>
      </button>

      <div class="page-bar">
        <div class="pb-search">
          <svg class="pb-mag" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><path d="M16.5 16.5 21 21"/></svg>
          <input v-model="query" :placeholder="'搜索' + copy.title">
        </div>
        <button type="button" class="pb-ico primary" title="发布" @click="openOldPublish">＋</button>
        <button type="button" class="pb-ico" title="拍照发布" @click="openOldPublish">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3 7h4l1.6-2h6.8L17 7h4v12H3z"/><circle cx="12" cy="13" r="3.4"/></svg>
        </button>
        <button type="button" class="pb-ico" title="问一问" @click="openOldHelp">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M21 12a8 8 0 0 1-8 8H7l-4 3v-6a8 8 0 1 1 18-5z"/></svg>
        </button>
      </div>

      <div v-if="loading" class="empty">正在读取校园数据…</div>
      <div v-else-if="!visible.length" class="empty">暂时没有{{ type === 'lost' ? '招领' : '寻物' }}，换个关键词试试</div>
      <div v-else class="vue-list">
        <article v-for="it in visible" :key="it.id" class="item" @click="openDetail(it)">
          <div class="thumb" :style="it.photoUrl ? 'padding:0;overflow:hidden' : ''" @click.stop="it.photoUrl && (selected = it, photoOpen = true)">
            <img v-if="it.photoUrl" :src="it.photoUrl" alt="" loading="lazy">
            <span v-else>{{ thumbText(it) }}</span>
          </div>
          <div class="body">
            <div class="tt">
              <span class="src-tag">{{ label(it) }}</span>{{ it.title || '未命名物品' }}<span v-if="statusChip(it)" class="st" :class="'st-' + it.status">{{ statusChip(it) }}</span>
            </div>
            <div class="dd">{{ it.desc || '暂无描述' }}</div>
            <div v-if="it.fields && chipText(it)" class="chips">
              <span v-for="c in chipText(it)" :key="c" class="chip">{{ c }}</span>
            </div>
            <div class="row">
              <span class="meta">📍 {{ it.place || '未填写地点' }} · {{ fmt(it.createdAt) }}</span>
              <button class="btn" type="button" :disabled="!canClaim(it)" @click.stop="openDetail(it)">{{ actionLabel(it) }}</button>
            </div>
          </div>
        </article>
      </div>
    </div>

    <div v-if="selected" class="modal-backdrop" @click="selected = null"></div>
    <div v-if="selected" class="sheet vue-sheet show item-detail-modal">
      <button type="button" class="sheet-x" aria-label="关闭" @click="selected = null">✕</button>
      <div class="detail-modal-grid">
      <div class="dm-left">
      <div class="big-thumb" @click="selected.photoUrl && (photoOpen = true)">
        <img v-if="selected.photoUrl" :src="selected.photoUrl" alt="" style="width:100%;height:100%;object-fit:cover;border-radius:16px">
        <span v-else>{{ thumbText(selected) }}</span>
      </div>
      </div>
      <div class="dm-right">
      <div class="sh">{{ selected.title || '未命名物品' }}</div>
      <div v-if="selected.isMine" class="sa" style="margin-top:6px;color:var(--purple)">这是你自己发布的内容，不能认领自己的发布。</div>
      <div class="sa">{{ selected.desc || '暂无描述' }}</div>
      <div v-if="selected.ai" class="pub-ai" :class="'pub-ai-' + (selected.ai.decision || 'review')">
        <b>🤖 智能审核 {{ ({approve:'建议通过', reject:'建议驳回', review:'建议复核'})[selected.ai.decision] || '已分析' }}</b>
        <span>风险 {{ selected.ai.score ?? '—' }}/100</span>
        <p>{{ selected.ai.reason || '智能审核已完成内容分析' }}</p>
      </div>
      <div class="sa" style="margin-top:8px">📍 {{ selected.place || '未填写地点' }} · {{ fmt(selected.createdAt) }}</div>
      <div class="sa" style="margin-top:8px">联系方式：{{ (selected.contact && selected.contact.phone) || '认领时由发布者确认' }}</div>
      <template v-if="selected.status === 'approved'">
        <button v-if="!claimOpen" type="button" class="btn" style="width:100%;margin-top:14px" :disabled="!canClaim(selected)" @click="canClaim(selected) && (claimOpen = true)">{{ actionLabel(selected) }}</button>
        <div v-if="claimOpen" class="claimbox">
        <div class="tip-small" style="margin:0 0 8px">{{ selected.type === 'lost' ? '写下你是在哪里、什么时候捡到的，方便失主核对' : '写下只有失主知道的细节，对方核对后才会通过' }}</div>
        <div class="ai-check-help">
          <b>AI 核验线索是干什么的？</b>
          <span>把你写的线索和失主描述做一次对比，看看地点、时间和物品特征是否对得上。它只是给你和失主一个参考，不会自动拒绝，也不影响你正常提交。</span>
        </div>
        <button type="button" class="ai-check-btn" :disabled="claimChecking" @click="runClaimCheck">{{ claimChecking ? 'AI 正在比对…' : (selected.type === 'lost' ? '✨ 帮我核对一下线索' : '✨ AI 核验吻合度') }}</button>
        <div v-if="claimCheck" class="claim-ai">
          <div class="ca-head"><b>{{ aiVerdict(claimCheck.verdict) }}</b><span>{{ claimCheck.confidence }}% 吻合</span></div>
          <div class="ca-bar"><i :style="{ width: claimCheck.confidence + '%' }"></i></div>
          <p v-if="claimCheck.reason">{{ claimCheck.reason }}</p>
          <div v-if="claimCheck.points?.length" class="ca-points">
            <span v-for="p in claimCheck.points" :key="p">{{ p }}</span>
          </div>
          <div class="ca-advice">
            {{ selected.type === 'lost'
              ? (claimCheck.confidence >= 60
                ? '线索里已经包含了一些关键特征，但最终仍要由失主当面核对。'
                : '目前线索可能只覆盖了地点或时间。建议再补充：颜色、外观、划痕、包装等特征，失主更容易判断。')
              : 'AI 只做辅助比对，最终是否通过仍由失主决定。' }}
          </div>
        </div>
        <div v-if="claimCheckError" class="tip-small" style="color:#A97A00">{{ claimCheckError }}</div>
        <textarea v-model="claimMsg" maxlength="200" :placeholder="selected.type === 'lost' ? '例如：今天下午在图书馆三楼靠窗座位捡到，伞柄有白色划痕' : '例如：伞骨内侧缠过胶带，伞柄上有一张卡通贴纸'" style="width:100%;box-sizing:border-box;background:#F8F4FD;border:1px solid #EDE3F8;border-radius:11px;padding:10px;font-family:inherit;font-size:11px;min-height:70px"></textarea>
        <input v-model="claimPhone" maxlength="30" :placeholder="selected.type === 'lost' ? '你的联系方式（方便失主联系你）' : '你的联系方式（手机号 / 微信号）'" style="width:100%;box-sizing:border-box;margin-top:7px;background:#F8F4FD;border:1px solid #EDE3F8;border-radius:11px;padding:10px;font-family:inherit;font-size:11px">
        <div v-if="claimState" class="sa" style="margin-top:6px">{{ claimState }}</div>
        <button type="button" class="btn" style="width:100%;margin-top:10px" :disabled="claiming" @click="submitClaim">{{ claiming ? '发送中…' : (selected.type === 'lost' ? '发送线索' : '发送认领申请') }}</button>
        <div class="close" @click="claimOpen = false">取消</div>
        </div>
      </template>
      <div v-else class="sa" style="margin-top:12px;color:#8E7FA3">
        {{ selected.status === 'closed' ? '这条信息已经结束，不能再认领。' : '当前状态暂不可认领。' }}
      </div>
      <div v-if="reportState" class="sa" style="margin-top:6px">{{ reportState }}</div>
      <div class="close" @click="reportItem">🚩 举报这条信息</div>
      </div>
      </div>

    </div>
    <div v-if="photoOpen && selected && selected.photoUrl" class="img-viewer" style="display:flex" @click="photoOpen = false">
      <img :src="selected.photoUrl" alt="">
      <div class="img-viewer-close">✕</div>
    </div>
  </section>
</template>

<style scoped>
.pub-ai { margin-top:9px; border-radius:9px; padding:8px 9px; background:#F7F0FF; border:1px solid #EADDF7; font-size:10px; line-height:1.6; }
.pub-ai b { color:#5B2A91; margin-right:6px; }
.pub-ai span { color:#8E7FA3; font-size:9px; }
.pub-ai p { margin:3px 0 0; color:#6E607F; }
.pub-ai-reject { background:#FDF2F2; border-color:#F3CFCF; }
.similar-box { margin-top:10px; border-top:1px dashed #EADDF7; padding-top:9px; }
.similar-title { font-size:10px; color:#8E7FA3; margin-bottom:5px; }
.similar-row { display:flex; flex-direction:column; gap:2px; background:#FAF7FE; border-radius:8px; padding:7px 8px; margin-bottom:5px; }
.similar-row b { font-size:10.5px; color:#3B1D63; }
.similar-row span { font-size:9px; color:#8E7FA3; }
</style>


<style scoped>
.similar-pct { margin-left:6px; font-style:normal; color:#5B2A91; background:#F1E8FB; border-radius:99px; padding:2px 5px; }
</style>


<style scoped>
.similar-why { display:flex; flex-wrap:wrap; gap:4px; margin-top:3px; }
.similar-why i { font-style:normal; font-size:8.5px; color:#7A5AA8; background:#F7F0FF; border-radius:4px; padding:2px 4px; }
</style>


<style scoped>
.closed-toggle { float:right; border:0; background:transparent; color:#8E7FA3; font-family:inherit; font-size:9.5px; text-decoration:underline; padding:0; }
</style>


<style scoped>
.similar-verdict { font-size:9px; color:#A97A00; margin-top:2px; }
</style>


<style scoped>
.ai-photo-entry { width:100%; display:flex; align-items:center; gap:9px; border:1px solid #E4D4F7; background:linear-gradient(135deg,#FBF8FF,#F4ECFC); border-radius:13px; padding:10px 12px; margin-top:9px; font-family:inherit; text-align:left; }
.ape-ico { width:32px; height:32px; flex:0 0 32px; border-radius:10px; background:linear-gradient(145deg,#6D3BA6,#3B1D63); display:flex; align-items:center; justify-content:center; font-size:15px; }
.ape-copy { flex:1; display:flex; flex-direction:column; gap:2px; }
.ape-copy b { font-size:12px; color:#3B1D63; }
.ape-copy i { font-style:normal; font-size:9.5px; color:#8E7FA3; }
.ape-go { color:#7A3CB0; font-size:18px; }
.ai-photo-state { margin-top:6px; font-size:10px; color:#7A3CB0; }
</style>






<style scoped>
.ai-check-btn { width:100%; border:1px solid #D8C8EE; background:#F7F0FF; color:#5B2A91; border-radius:9px; padding:8px; font-family:inherit; font-size:11px; margin-bottom:7px; }
.claim-ai { background:#FBF8FF; border:1px solid #EADFF7; border-radius:10px; padding:9px; margin-bottom:8px; }
.ca-head { display:flex; justify-content:space-between; align-items:center; font-size:11px; color:#3B1D63; }
.ca-head b { color:#5B2A91; }
.ca-head span { font-size:10px; color:#7A5AA8; }
.ca-bar { height:5px; background:#EDE4F8; border-radius:99px; overflow:hidden; margin:6px 0; }
.ca-bar i { display:block; height:100%; background:linear-gradient(90deg,#8A52C7,#5B2A91); border-radius:99px; }
.claim-ai p { margin:4px 0; font-size:10px; line-height:1.6; color:#6E607F; }
.ca-points { display:flex; flex-wrap:wrap; gap:4px; }
.ca-points span { font-size:9px; background:#F1E8FB; color:#5B2A91; border-radius:5px; padding:2px 5px; }
</style>



<style scoped>
.match-entry { display:flex;align-items:center;gap:9px;width:100%;border:1px solid #D8C8EE;background:linear-gradient(135deg,#F8F2FF,#EEF5FF);border-radius:12px;padding:9px 10px;margin-bottom:8px;font-family:inherit;text-align:left; }
.me-badge { flex:0 0 auto;font-size:9px;color:#fff;background:#5B2A91;border-radius:5px;padding:3px 5px; }
.me-copy { flex:1;min-width:0;display:flex;flex-direction:column;gap:2px; }
.me-copy b { font-size:11px;color:#3B1D63; }
.me-copy i { font-style:normal;font-size:9px;color:#8E7FA3;line-height:1.5; }
</style>



<style scoped>
.item-detail-modal { width:min(820px,94vw) !important; max-width:94vw !important; max-height:88vh; overflow-y:auto; }
.detail-modal-grid { display:grid; grid-template-columns:0.9fr 1.1fr; gap:14px; align-items:start; }
.dm-left .big-thumb { height:100%; min-height:260px; margin:0; }
.dm-right { min-width:0; }
.dm-right .sh { margin-top:0; }
@media (max-width:640px) { .detail-modal-grid { grid-template-columns:1fr; } .dm-left .big-thumb { min-height:180px; height:180px; } }
</style>


<style scoped>
.modal-backdrop { position:fixed; inset:0; z-index:150; background:rgba(10,5,20,.62); }
.sheet.item-detail-modal { z-index:160; width:min(820px,94vw) !important; max-width:94vw !important; }
.dm-right .sh { padding-right:26px; overflow-wrap:anywhere; line-height:1.35; }
</style>


<style scoped>
.sheet.item-detail-modal { box-shadow:0 26px 70px rgba(12,6,22,.38) !important; clip-path:none !important; }
</style>


<style scoped>
.ai-check-help { background:#F7F2FD; border:1px solid #EADFF5; border-radius:9px; padding:8px 9px; margin-bottom:7px; }
.ai-check-help b { display:block; font-size:10.5px; color:#5B2A91; margin-bottom:2px; }
.ai-check-help span { display:block; font-size:10px; line-height:1.65; color:#7A6B8E; }
.ca-advice { margin-top:6px; font-size:9.5px; line-height:1.6; color:#8E6A00; }
.sheet.item-detail-modal { width:min(960px,94vw) !important; max-width:94vw !important; padding:22px !important; }
.detail-modal-grid { gap:20px; }
.dm-left .big-thumb { min-height:360px; }
.dm-right .sh { font-size:20px; }
.dm-right .sa { font-size:13px; line-height:1.75; }
.dm-right .claimbox { padding:12px; }
.dm-right .claimbox textarea, .dm-right .claimbox input { font-size:13px !important; padding:12px !important; }
@media (max-width:640px) { .sheet.item-detail-modal { width:94vw !important; padding:16px !important; } .dm-left .big-thumb { min-height:200px; } }
</style>


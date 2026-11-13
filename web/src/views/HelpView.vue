<script setup>
import { computed, onMounted, ref } from 'vue'
import { api } from '../api'

const emit = defineEmits(['nav', 'publish'])
const props = defineProps({
  initialCat: { type: String, default: 'help_borrow' }
})

const items = ref([])
const loading = ref(true)
const query = ref('')
const active = ref(props.initialCat)
const selected = ref(null)
const goMsg = ref('')
const goPhone = ref('')
const goState = ref('')
const going = ref(false)
const photoOpen = ref(false)
const photoSrc = ref('')

const cats = [
  { id: 'help_borrow', title: '借用工具', sub: '借伞 / 充电宝', art: art('<path d="M4 12a8 8 0 0 1 16 0H4Z"/><path d="M12 12v7a2 2 0 0 0 4 0"/><path d="M9 12V9a3 3 0 0 1 6 0v3"/>') },
  { id: 'help_errand', title: '代办跑腿', sub: '帮取 / 帮带', art: art('<path d="M5 18c4 0 4-6 8-6s4-6 7-6"/><circle cx="5" cy="18" r="2"/><path d="M18 3l3 3-3 3"/>') },
  { id: 'help_donate', title: '爱心捐赠', sub: '闲置送人', art: art('<path d="M4 10h16v10H4z"/><path d="M12 10v10"/><path d="M4 10l2-4h12l2 4"/><path d="M12 6c-2-4-6-2-4 1M12 6c2-4 6-2 4 1"/>') },
  { id: 'help_volunteer', title: '志愿帮忙', sub: '找人搭把手', art: art('<path d="M12 20s-7-4.3-7-9a4 4 0 0 1 7-2 4 4 0 0 1 7 2c0 4.7-7 9-7 9Z"/><path d="M8 20l-3 2M16 20l3 2"/>') }
]

function art(body) {
  return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">' + body + '</svg>'
}
function fmt(ts) {
  if (!ts) return ''
  const d = new Date(ts)
  return `${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}
function thumb(x) {
  if (x.photoUrl) return null
  return ({ help_borrow: '🛠️', help_errand: '🏃', help_donate: '🎁', help_volunteer: '🤝' })[x.cat] || '🤝'
}
function chips(x) {
  return x.fields ? Object.values(x.fields).filter(Boolean).slice(0, 3) : []
}

const visible = computed(() => {
  const q = query.value.trim().toLowerCase()
  return items.value
    .filter((x) => x.type === 'help' && ['approved', 'claimed', 'closed'].includes(x.status))
    .filter((x) => !active.value || x.cat === active.value)
    .filter((x) => !q || ((x.title || '') + (x.desc || '') + (x.place || '')).toLowerCase().includes(q))
    .sort((a, b) => (b.createdAt || 0) - (a.createdAt || 0))
})

onMounted(async () => {
  await load()
  const id = sessionStorage.getItem('sg:focusItem')
  if (id) {
    const target = items.value.find((x) => x.id === id)
    if (target) selected.value = target
    sessionStorage.removeItem('sg:focusItem')
  }
})
async function load() {
  loading.value = true
  try {
    const list = await api.items()
    if (Array.isArray(list)) items.value = list
  } finally {
    loading.value = false
  }
}
function openDetail(it) {
  selected.value = it
  goMsg.value = ''
  goPhone.value = ''
  goState.value = ''
}
function aiLabel(d) {
  return d === 'approve' ? '建议通过' : d === 'reject' ? '建议驳回' : '建议复核'
}
async function submitHelp() {
  if (!selected.value) return
  if (goMsg.value.trim().length < 2) { goState.value = '说一句你能怎么帮'; return }
  going.value = true
  goState.value = ''
  try {
    await api.claim(selected.value.id, { message: goMsg.value.trim(), contact: goPhone.value.trim() })
    goState.value = '已告诉对方，等 TA 确认'
  } catch (e) {
    goState.value = e.message || '发送失败'
  } finally {
    going.value = false
  }
}
</script>

<template>
  <section class="screen active" id="screen-help">
    <div class="topbar">
      <div class="back" @click="$emit('nav', 'home')">‹</div>
      <div class="t">爱心求助</div>
      <button class="btn" type="button" @click="$emit('publish', 'help', active)">发布</button>
    </div>

    <div class="scroll">
      <div class="hintline">同学之间互相搭把手：借个东西、帮取快递、闲置送人、找人帮忙。</div>

      <div class="help-cats">
        <button
          v-for="c in cats"
          :key="c.id"
          type="button"
          :class="{ on: active === c.id }"
          @click="active = c.id"
        >
          <span class="hc-ic" v-html="c.art" />
          <div><b>{{ c.title }}</b><span>{{ c.sub }}</span></div>
        </button>
      </div>

      <div class="page-bar">
        <div class="pb-search">
          <svg class="pb-mag" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><path d="M16.5 16.5 21 21"/></svg>
          <input v-model="query" placeholder="搜索爱心求助">
        </div>
        <button type="button" class="pb-ico primary" title="发布求助" @click="$emit('publish', 'help', active)">＋</button>
        <button type="button" class="pb-ico" title="问一问" @click="$emit('nav', 'ask')">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M21 12a8 8 0 0 1-8 8H7l-4 3v-6a8 8 0 1 1 18-5z"/></svg>
        </button>
      </div>

      <div v-if="loading" class="empty">正在读取求助…</div>
      <div v-else-if="!visible.length" class="empty">这个方向暂时没有求助</div>
      <div v-else class="vue-list">
        <article v-for="it in visible" :key="it.id" class="item" @click="openDetail(it)">
          <div class="thumb" :style="it.photoUrl ? 'padding:0;overflow:hidden' : ''" @click.stop="it.photoUrl && (photoSrc = it.photoUrl, photoOpen = true)">
            <img v-if="it.photoUrl" :src="it.photoUrl" alt="" loading="lazy">
            <span v-else>{{ thumb(it) }}</span>
          </div>
          <div class="body">
            <div class="tt"><span class="src-tag">求助</span>{{ it.title }}<span v-if="it.status === 'closed'" class="help-done">已结束</span></div>
            <div class="dd">{{ it.desc }}</div>
            <div v-if="it.ai" class="help-ai-line">🤖 智能审核 {{ aiLabel(it.ai.decision) }} · 风险 {{ it.ai.score ?? '—' }}/100</div>
            <div v-if="chips(it).length" class="chips"><span v-for="c in chips(it)" :key="c" class="chip">{{ c }}</span></div>
            <div class="row">
              <span class="meta">📍 {{ it.place || '未填写地点' }} · {{ fmt(it.createdAt) }}</span>
              <button v-if="it.status === 'approved'" type="button" class="btn" @click.stop="openDetail(it)">我来帮忙</button>
              <span v-else class="help-state">{{ it.status === 'closed' ? '已结束' : '进行中' }}</span>
            </div>
          </div>
        </article>
      </div>
    </div>

    <div v-if="selected" class="sheet vue-sheet show">
      <button type="button" class="sheet-x" @click="selected = null">收起</button>
      <div class="big-thumb" @click="selected.photoUrl && (photoSrc = selected.photoUrl, photoOpen = true)">
        <img v-if="selected.photoUrl" :src="selected.photoUrl" alt="" style="width:100%;height:100%;object-fit:cover;border-radius:16px">
        <span v-else>{{ thumb(selected) }}</span>
      </div>
      <div class="sh">{{ selected.title }}</div>
      <div class="sa">{{ selected.desc }}</div>
      <div v-if="selected.ai" class="help-ai-box">
        <b>🤖 智能审核 {{ aiLabel(selected.ai.decision) }} · 风险 {{ selected.ai.score ?? '—' }}/100</b>
        <p>{{ selected.ai.reason || '智能审核已完成内容分析' }}</p>
      </div>
      <div class="sa" style="margin-top:8px">📍 {{ selected.place || '未填写地点' }}</div>
      <div class="sa" style="margin-top:8px">联系方式：{{ (selected.contact && selected.contact.phone) || '对方确认后可见' }}</div>
      <div v-if="selected.status !== 'approved'" class="sa" style="margin-top:10px;color:var(--sub)">
        这条求助{{ selected.status === 'closed' ? '已经结束' : '已经有人帮忙，正在进行中' }}。
      </div>
      <template v-else>
        <textarea v-model="goMsg" maxlength="120" placeholder="说一句你能怎么帮，例如：我明天上午可以带过去" style="width:100%;box-sizing:border-box;margin-top:10px;background:#F8F4FD;border:1px solid #EDE3F8;border-radius:11px;padding:10px;font-family:inherit;font-size:11px;min-height:64px"></textarea>
        <input v-model="goPhone" maxlength="20" placeholder="你的联系方式（对方确认后可见）" style="width:100%;box-sizing:border-box;margin-top:7px;background:#F8F4FD;border:1px solid #EDE3F8;border-radius:11px;padding:10px;font-family:inherit;font-size:11px">
        <div v-if="goState" class="sa" style="margin-top:6px">{{ goState }}</div>
        <button type="button" class="btn" style="width:100%;margin-top:12px" :disabled="going" @click="submitHelp">{{ going ? '发送中…' : '发送' }}</button>
      </template>
      <div class="close" @click="selected = null">收起</div>
    </div>
    <div v-if="photoOpen" class="help-photo-viewer" @click="photoOpen = false">
      <img :src="photoSrc" alt="查看大图">
      <button type="button" @click.stop="photoOpen = false">✕</button>
    </div>
  </section>
</template>

<style>
.vue-list .item .thumb {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}
.help-cats button.on {
  border-color: #5B2A91;
  background: #5B2A91;
}
.help-cats button.on b,
.help-cats button.on span {
  color: #fff;
}
.help-cats button.on .hc-ic {
  background: rgba(255,255,255,.16) !important;
  border-color: transparent !important;
  color: #fff !important;
}
</style>


<style>
.help-photo-viewer { position:fixed; inset:0; z-index:800; background:rgba(12,5,20,.88); display:flex; align-items:center; justify-content:center; padding:24px; }
.help-photo-viewer img { max-width:94vw; max-height:88vh; border-radius:12px; }
.help-photo-viewer button { position:absolute; top:18px; right:20px; width:38px; height:38px; border:0; border-radius:50%; background:rgba(255,255,255,.16); color:#fff; font-size:16px; }
</style>


<style scoped>
.help-done { margin-left:5px; font-size:9px; color:#8E7FA3; background:#F0EDF5; border-radius:99px; padding:2px 5px; vertical-align:middle; }
.help-state { font-size:10px; color:#8E7FA3; white-space:nowrap; }
</style>


<style scoped>
.help-ai-line { margin-top:5px; font-size:9px; color:#7A5AA8; background:#F7F0FF; border-radius:5px; padding:3px 5px; display:inline-block; }
.help-ai-box { margin-top:9px; padding:8px 9px; border-radius:9px; background:#F7F0FF; border:1px solid #EADDF7; }
.help-ai-box b { font-size:10px; color:#5B2A91; }
.help-ai-box p { margin:3px 0 0; font-size:10px; line-height:1.6; color:#6E607F; }
</style>



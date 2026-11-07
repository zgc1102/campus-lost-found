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
const photoOpen = ref(false)

function openDetail(it) {
  selected.value = it
  claimMsg.value = ''
  claimPhone.value = ''
  claimState.value = ''
  claimOpen.value = false
  photoOpen.value = false
}
async function submitClaim() {
  if (!selected.value) return
  if (claimMsg.value.trim().length < 2) { claimState.value = '写一下只有失主知道的细节'; return }
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
  ? { title: '失物招领', kicker: 'LOST & FOUND', hint: '捡到的东西在这里等主人', other: '寻物启事', publish: '发布启事' }
  : { title: '寻物启事', kicker: 'LOST & FOUND', hint: '看到的同学可以帮一把', other: '失物招领', publish: '发布启事' })

const visible = computed(() => {
  const target = props.type === 'lost' ? 'found' : 'lost'
  const q = query.value.trim().toLowerCase()
  return items.value
    .filter((x) => x.type === target && ['approved', 'claimed', 'closed'].includes(x.status))
    .filter((x) => !q || ((x.title || '') + (x.desc || '') + (x.place || '')).toLowerCase().includes(q))
    .sort((a, b) => (b.createdAt || 0) - (a.createdAt || 0))
})

onMounted(load)
watch(() => props.type, () => { query.value = '' })

async function load() {
  loading.value = true
  try {
    const list = await api.items()
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
  const text = (x.title || '') + (x.cat || '')
  if (text.includes('伞')) return '🌂'
  if (text.includes('卡')) return '💳'
  if (text.includes('钥匙')) return '🔑'
  if (text.includes('电脑') || text.includes('键盘')) return '💻'
  if (text.includes('耳机')) return '🎧'
  if (text.includes('杯')) return '🥤'
  if (text.includes('包')) return '🎒'
  return '📦'
}
function chipText(x) {
  if (!x.fields) return []
  return Object.values(x.fields).filter(Boolean).slice(0, 3)
}
function actionLabel(x) {
  if (x.myClaim === 'pending') return '已申请'
  if (x.myClaim === 'accepted' || x.myClaim === 'completed') return '已通过'
  if (x.myClaim === 'need_more') return '补充信息'
  if (x.myClaim === 'rejected') return '重新申请'
  return '认领'
}
function canClaim(x) {
  return x.status === 'approved' && !['pending', 'accepted', 'completed'].includes(x.myClaim)
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
      <div class="tip-box">
        ⚠️ 认领提示：认领物品前，请务必核对物品独有特征，请勿仅凭照片认领，谨防冒领。<br>
        交接请选择公共场所，不要前往偏僻地点，谨慎公开手机号、微信等私人联系方式。
      </div>

      <div class="list-meta">
        <b>{{ visible.length }}</b> 条{{ type === 'lost' ? '招领' : '寻物' }} · {{ copy.hint }}
      </div>

      <button type="button" class="radar-entry" @click="openOldRadar">
        <span class="re-badge">AI</span>
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
          <div class="thumb" :style="it.photoUrl ? 'padding:0;overflow:hidden' : ''">
            <img v-if="it.photoUrl" :src="it.photoUrl" alt="" loading="lazy">
            <span v-else>{{ thumbText(it) }}</span>
          </div>
          <div class="body">
            <div class="tt">
              <span class="src-tag">{{ label(it) }}</span>{{ it.title || '未命名物品' }}
            </div>
            <div v-if="it.summary" class="sum">{{ it.summary }}</div>
            <div class="dd">{{ it.desc || '暂无描述' }}</div>
            <div v-if="it.fields && chipText(it)" class="chips">
              <span v-for="c in chipText(it)" :key="c" class="chip">{{ c }}</span>
            </div>
            <div class="row">
              <span class="meta">📍 {{ it.place || '未填写地点' }} · {{ fmt(it.createdAt) }}</span>
              <button class="btn" type="button" @click.stop="openDetail(it)">{{ actionLabel(it) }}</button>
            </div>
          </div>
        </article>
      </div>
    </div>

    <div v-if="selected" class="sheet vue-sheet show">
      <button type="button" class="sheet-x" @click="selected = null">收起</button>
      <div class="big-thumb" @click="selected.photoUrl && (photoOpen = true)">
        <img v-if="selected.photoUrl" :src="selected.photoUrl" alt="" style="width:100%;height:100%;object-fit:cover;border-radius:16px">
        <span v-else>{{ thumbText(selected) }}</span>
      </div>
      <div class="sh">{{ selected.title || '未命名物品' }}</div>
      <div class="sa">{{ selected.desc || '暂无描述' }}</div>
      <div class="sa" style="margin-top:8px">📍 {{ selected.place || '未填写地点' }} · {{ fmt(selected.createdAt) }}</div>
      <div class="sa" style="margin-top:8px">联系方式：{{ (selected.contact && selected.contact.phone) || '认领时由发布者确认' }}</div>
      <button v-if="!claimOpen" type="button" class="btn" style="width:100%;margin-top:14px" :disabled="!canClaim(selected)" @click="canClaim(selected) && (claimOpen = true)">{{ actionLabel(selected) }}</button>
      <div v-if="claimOpen" class="claimbox">
        <div class="tip-small" style="margin:0 0 8px">写下只有失主知道的细节，对方核对后才会通过</div>
        <textarea v-model="claimMsg" maxlength="200" placeholder="例如：伞骨内侧缠过胶带，伞柄上有一张卡通贴纸" style="width:100%;box-sizing:border-box;background:#F8F4FD;border:1px solid #EDE3F8;border-radius:11px;padding:10px;font-family:inherit;font-size:11px;min-height:70px"></textarea>
        <input v-model="claimPhone" maxlength="30" placeholder="你的联系方式（手机号 / 微信号）" style="width:100%;box-sizing:border-box;margin-top:7px;background:#F8F4FD;border:1px solid #EDE3F8;border-radius:11px;padding:10px;font-family:inherit;font-size:11px">
        <div v-if="claimState" class="sa" style="margin-top:6px">{{ claimState }}</div>
        <button type="button" class="btn" style="width:100%;margin-top:10px" :disabled="claiming" @click="submitClaim">{{ claiming ? '发送中…' : '发送认领申请' }}</button>
        <div class="close" @click="claimOpen = false">取消</div>
      </div>
      <div v-if="reportState" class="sa" style="margin-top:6px">{{ reportState }}</div>
      <div class="close" @click="reportItem">🚩 举报这条信息</div>
      <div class="close" @click="selected = null">收起</div>
    </div>
    <div v-if="photoOpen && selected && selected.photoUrl" class="img-viewer" style="display:flex" @click="photoOpen = false">
      <img :src="selected.photoUrl" alt="">
      <div class="img-viewer-close">✕</div>
    </div>
  </section>
</template>

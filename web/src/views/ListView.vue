<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { api, oldUrl } from '../api'

const props = defineProps({
  type: { type: String, default: 'lost' }
})
const emit = defineEmits(['nav'])

const items = ref([])
const loading = ref(true)
const query = ref('')
const selected = ref(null)

const copy = computed(() => props.type === 'lost'
  ? { title: '失物招领', kicker: 'LOST & FOUND', hint: '捡到的东西在这里等主人', other: '寻物启事', publish: '发布招领' }
  : { title: '寻物启事', kicker: 'LOST & FOUND', hint: '看到的同学可以帮一把', other: '失物招领', publish: '发布寻物' })

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
function openOldPublish() {
  location.href = oldUrl('home', 'open=publish&type=' + props.type)
}
function openOldRadar() {
  location.href = oldUrl('lost')
}
function openOldHelp() {
  location.href = oldUrl('help')
}
</script>

<style scoped>
.vue-list .item {
  position: relative;
  padding-bottom: 40px;
}
.vue-list .item .btn {
  position: absolute;
  right: 11px;
  bottom: 10px;
  width: 38px;
  height: 38px;
  min-width: 38px;
  padding: 0;
  border-radius: 50% !important;
  font-size: 9px;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}
.vue-list .item .thumb {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: #5B2A91;
  flex: 0 0 78px;
}
.vue-list .item .thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
</style>

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
        <button type="button" class="pb-ico" title="问一问" @click="openOldHelp">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M21 12a8 8 0 0 1-8 8H7l-4 3v-6a8 8 0 1 1 18-5z"/></svg>
        </button>
      </div>

      <div v-if="loading" class="empty">正在读取校园数据…</div>
      <div v-else-if="!visible.length" class="empty">暂时没有{{ type === 'lost' ? '招领' : '寻物' }}，换个关键词试试</div>
      <div v-else class="vue-list">
        <article v-for="it in visible" :key="it.id" class="item" @click="selected = it">
          <div class="thumb" :style="it.photoUrl ? 'padding:0;overflow:hidden' : ''">
            <img v-if="it.photoUrl" :src="it.photoUrl" alt="" loading="lazy">
            <span v-else>{{ (it.title || '物').slice(0, 1) }}</span>
          </div>
          <div style="flex:1;min-width:0">
            <div class="tt">{{ it.title || '未命名物品' }}</div>
            <div class="dd">{{ it.desc || '暂无描述' }}</div>
            <div class="chips">
              <span class="chip">{{ label(it) }}</span>
              <span class="chip">{{ it.place || '未填写地点' }}</span>
            </div>
            <div class="meta">📍 {{ it.place || '未填写地点' }} · {{ fmt(it.createdAt) }}</div>
          </div>
          <button class="btn" type="button" @click.stop="selected = it">认领</button>
        </article>
      </div>
    </div>

    <div v-if="selected" class="sheet vue-sheet show">
      <button type="button" class="sheet-x" @click="selected = null">收起</button>
      <div class="big-thumb">
        <img v-if="selected.photoUrl" :src="selected.photoUrl" alt="" style="width:100%;height:100%;object-fit:cover;border-radius:16px">
        <span v-else>{{ (selected.title || '物').slice(0, 1) }}</span>
      </div>
      <div class="sh">{{ selected.title || '未命名物品' }}</div>
      <div class="sa">{{ selected.desc || '暂无描述' }}</div>
      <div class="sa" style="margin-top:8px">📍 {{ selected.place || '未填写地点' }} · {{ fmt(selected.createdAt) }}</div>
      <div class="sa" style="margin-top:8px">联系方式：{{ (selected.contact && selected.contact.phone) || '认领时由发布者确认' }}</div>
      <button type="button" class="btn" style="width:100%;margin-top:12px" @click="selected = null">关闭</button>
      <div class="close" @click="selected = null">收起</div>
    </div>
  </section>
</template>

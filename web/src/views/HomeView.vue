<script setup>
import { computed, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { api } from '../api'

const emit = defineEmits(['nav'])

const items = ref([])
const loading = ref(true)
const slideIndex = ref(0)
const defaultSlides = [
  { star: '📌', name: '失物招领点调整通知', sub: '校园公告 · 11-01 02:34' },
  { star: '📢', name: '校园失物招领与爱心互助', sub: '清华校园 · 公益项目' },
  { star: '🔖', name: '拾光码：给失物一张身份证', sub: '一码通用 · 可打印' },
  { star: '🔎', name: '失物雷达：主动匹配', sub: '寻物与招领自动配对' },
  { star: '🕵️', name: '寻物侦探：按路线推理', sub: '没发布也能用' }
]
const slides = ref(defaultSlides.slice())
let timer = null

const stats = computed(() => {
  const pub = items.value.filter((x) => ['approved', 'claimed', 'closed'].includes(x.status))
  const closed = items.value.filter((x) => x.status === 'closed')
  const start = new Date()
  start.setHours(0, 0, 0, 0)
  const today = pub.filter((x) => (x.createdAt || 0) >= start.getTime())
  return { total: pub.length, closed: closed.length, today: today.length }
})

const shown = reactive({ total: 0, closed: 0, today: 0 })
let countFrame = null
watch(stats, (val) => {
  cancelAnimationFrame(countFrame)
  const from = { ...shown }
  const start = performance.now()
  const step = (now) => {
    const p = Math.min(1, (now - start) / 650)
    const ease = 1 - Math.pow(1 - p, 3)
    shown.total = Math.round(from.total + (val.total - from.total) * ease)
    shown.closed = Math.round(from.closed + (val.closed - from.closed) * ease)
    shown.today = Math.round(from.today + (val.today - from.today) * ease)
    if (p < 1) countFrame = requestAnimationFrame(step)
  }
  countFrame = requestAnimationFrame(step)
}, { immediate: true })

const helpEntries = [
  { cat: 'help_borrow', title: '借用工具', sub: '借伞 · 充电宝', tone: 'tone-lilac', art: artUmbrella() },
  { cat: 'help_errand', title: '代办跑腿', sub: '帮取 · 帮带', tone: 'tone-peach', art: artErrand() },
  { cat: 'help_donate', title: '爱心捐赠', sub: '闲置送人', tone: 'tone-gold', art: artGift() },
  { cat: 'help_volunteer', title: '志愿帮忙', sub: '找人搭把手', tone: 'tone-slate', art: artHands() }
]

const lostEntries = [
  { target: 'lost', title: '失物招领', sub: '捡到的东西', tone: 'tone-violet', art: artSearch() },
  { target: 'found', title: '寻物启事', sub: '丢了的东西', tone: 'tone-blue', art: artMegaphone() }
]

function artUmbrella() {
  return '<svg viewBox="0 0 80 80" fill="none"><path d="M12 40a28 28 0 0 1 56 0H12Z" fill="#8A52C7"/><path d="M12 40c8-8 14-8 20 0 6-8 12-8 20 0 6-8 12-8 16 0" stroke="#C8A96A" stroke-width="3" stroke-linecap="round"/><path d="M40 40v20a8 8 0 0 0 16 0" stroke="#3B1D63" stroke-width="4" stroke-linecap="round"/><circle cx="24" cy="62" r="5" fill="#E8DCF7"/></svg>'
}
function artErrand() {
  return '<svg viewBox="0 0 80 80" fill="none"><rect x="18" y="28" width="32" height="32" rx="6" fill="#E8B4A0"/><path d="M24 28v-6h20v6" stroke="#8A4A33" stroke-width="4" stroke-linecap="round"/><path d="M50 38h9l7 10v10H52V38Z" fill="#C8A96A"/><circle cx="26" cy="64" r="5" fill="#5B2A91"/><circle cx="54" cy="64" r="5" fill="#5B2A91"/><path d="M26 48h14M26 54h9" stroke="#8A4A33" stroke-width="2.5" stroke-linecap="round"/></svg>'
}
function artGift() {
  return '<svg viewBox="0 0 80 80" fill="none"><rect x="16" y="30" width="48" height="34" rx="5" fill="#E8B4A0"/><rect x="16" y="24" width="48" height="12" rx="4" fill="#C8A96A"/><rect x="36" y="24" width="8" height="40" fill="#FFF4E8"/><path d="M40 50s-9-5.4-9-10a5 5 0 0 1 9-2 5 5 0 0 1 9 2c0 4.6-9 10-9 10Z" fill="#B85A3C"/></svg>'
}
function artHands() {
  return '<svg viewBox="0 0 80 80" fill="none"><path d="M14 54c0-12 12-20 26-20s26 8 26 20" fill="#C9A7F0"/><path d="M40 46s-11-6.5-11-12a6 6 0 0 1 11-2 6 6 0 0 1 11 2c0 5.5-11 12-11 12Z" fill="#8A52C7"/><path d="M18 58l-8 10M62 58l8 10" stroke="#5B2A91" stroke-width="4" stroke-linecap="round"/></svg>'
}
function artSearch() {
  return '<svg viewBox="0 0 80 80" fill="none"><circle cx="34" cy="34" r="18" fill="#F1E6FA" stroke="#5B2A91" stroke-width="5"/><circle cx="34" cy="34" r="10" fill="#C9A7F0"/><path d="M48 48 64 64" stroke="#3B1D63" stroke-width="7" stroke-linecap="round"/><rect x="40" y="18" width="17" height="21" rx="3" fill="#fff" stroke="#8A52C7" stroke-width="2"/></svg>'
}
function artMegaphone() {
  return '<svg viewBox="0 0 80 80" fill="none"><path d="M16 36v12l34 14V22L16 36Z" fill="#8A52C7"/><path d="M50 30h8a10 10 0 0 1 0 20h-8" fill="#C9A7F0"/><path d="M26 50v14" stroke="#3B1D63" stroke-width="5" stroke-linecap="round"/><path d="M56 20l6-6M62 30h9M56 62l6 6" stroke="#C8A96A" stroke-width="3" stroke-linecap="round"/></svg>'
}

function restartTimer() {
  clearTimeout(timer)
  timer = setTimeout(() => {
    if (document.hidden) return restartTimer()
    slideIndex.value = (slideIndex.value + 1) % slides.value.length
    restartTimer()
  }, 6500)
}
function goSlide(i) {
  slideIndex.value = (i + slides.value.length) % slides.value.length
  restartTimer()
}

async function load() {
  loading.value = true
  try {
    const [list, anns] = await Promise.all([api.items(), api.announcements()])
    if (Array.isArray(list)) items.value = list
    if (Array.isArray(anns) && anns.length) {
      const annSlides = anns.slice(0, 2).map((a) => ({
        star: a.pinned ? '📌' : '📢',
        name: a.title,
        sub: '校园公告 · ' + new Date(a.publishedAt).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }),
        body: a.body || ''
      }))
      slides.value = annSlides.concat(defaultSlides).slice(0, 5)
      slideIndex.value = 0
    }
  } catch (_) {
    items.value = []
  } finally {
    loading.value = false
    restartTimer()
  }
}

onMounted(load)
onUnmounted(() => { clearTimeout(timer); if (countFrame) cancelAnimationFrame(countFrame) })
function replayTour() {
  window.dispatchEvent(new Event('sg:tour'))
}
function openMemo(s) {
  sessionStorage.setItem('sg:memo', JSON.stringify(s))
  emit('nav', 'memorial')
}
</script>

<template>
  <section class="screen active" id="screen-home">
    <div class="ticker">
      <div class="ticker-track">
        <span>绿色能源 · 智慧矿山 · 红色引领 · 爱国爱岗 · 孝道 · 清华校园拾光里 · 有温度的服务</span>
        <span>绿色能源 · 智慧矿山 · 红色引领 · 爱国爱岗 · 孝道 · 清华校园拾光里 · 有温度的服务</span>
      </div>
    </div>

    <div class="topbar">
      <button type="button" class="top-search" title="搜索" @click="$emit('nav', 'search')">
        <svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="#fff" stroke-width="2.2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="M16.5 16.5 21 21"/></svg>
      </button>
      <div class="t">清华校园拾光里</div>
      <button type="button" class="help-btn" title="使用引导" @click="replayTour">?</button>
      <div class="bell" title="通知" @click="$emit('nav', 'notices')">🔔</div>
      <div class="login" title="我的发布" @click="$emit('nav', 'mine')">
        <svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="1.8" width="18" height="18"><circle cx="12" cy="8" r="4"/><path d="M4 21c0-4 4-6 8-6s8 2 8 6"/></svg>
      </div>
    </div>

    <div class="scroll">
      <div class="mem-win">
        <span class="mw-tag" style="cursor:pointer" @click="$emit('nav', 'notices')">公告通知 · 左右滑动</span>
        <div class="mem-track">
          <div class="mem-slide" @click="openMemo(slides[slideIndex])">
            <div class="mem-star">{{ slides[slideIndex].star }}</div>
            <div><div class="mn">{{ slides[slideIndex].name }}</div><div class="ms">{{ slides[slideIndex].sub }}</div></div>
          </div>
        </div>
        <button type="button" class="mw-nav prev" aria-label="上一条" @click="goSlide(slideIndex - 1)">‹</button>
        <button type="button" class="mw-nav next" aria-label="下一条" @click="goSlide(slideIndex + 1)">›</button>
        <div class="mw-dots">
          <i v-for="(s, i) in slides" :key="i" :class="{ on: i === slideIndex }" />
        </div>
      </div>

      <div class="entry-split">
        <div class="entry-section section-help">
          <div class="entry-head">
            <div><span class="eh-kicker">MUTUAL AID</span><h2>爱心 · 求助</h2></div>
            <span class="eh-count">4 个入口</span>
          </div>
          <div class="entry-list">
            <button
              v-for="(item, i) in helpEntries"
              :key="item.cat"
              type="button"
              class="entry-card"
              :class="item.tone"
              @click="$emit('nav', 'help', item.cat)"
            >
              <span class="entry-art" v-html="item.art" />
              <span class="entry-copy"><b>{{ item.title }}</b><i>{{ item.sub }}</i></span>
              <span class="entry-arrow">↗</span>
            </button>
          </div>
        </div>

        <div class="entry-section section-lost">
          <div class="entry-head">
            <div><span class="eh-kicker">LOST &amp; FOUND</span><h2>失物 · 寻物</h2></div>
            <span class="eh-count">2 个入口</span>
          </div>
          <div class="entry-list">
            <button
              v-for="item in lostEntries"
              :key="item.target"
              type="button"
              class="entry-card"
              :class="item.tone"
              @click="$emit('nav', item.target)"
            >
              <span class="entry-art" v-html="item.art" />
              <span class="entry-copy"><b>{{ item.title }}</b><i>{{ item.sub }}</i></span>
              <span class="entry-arrow">↗</span>
            </button>
          </div>
          <button type="button" class="tag-entry tag-inline" @click="$emit('nav', 'tag')">
            <span class="tag-badge">码</span>
            <span class="tag-copy"><b>拾光码</b><i>给失物一张身份证</i></span>
            <span class="tag-go">→</span>
          </button>
          <button type="button" class="lost-cta detective-cta" @click="$emit('nav', 'detective')">
            <span class="lc-kicker">LOST DETECTIVE</span>
            <b>寻物侦探</b>
            <i>按时间线推测下一步去哪找</i>
            <span class="lc-plus">→</span>
          </button>
        </div>
      </div>

      <div class="sectitle">给初来清华的人 · 游客 / 新生 / 家长</div>
      <div class="guide-banner" @click="$emit('nav', 'guide')">
        <div class="gb-text">
          <div class="gb-t1">初入清华园，你想问什么？</div>
          <div class="gb-t2">访客怎么进校？校园卡丢了怎么办？食堂在哪？一键问 AI 或学长学姐。</div>
        </div>
        <div class="gb-arrow">›</div>
      </div>
      <div class="guide-quick">
        <span @click="$emit('nav', 'ask')">访客进校</span>
        <span @click="$emit('nav', 'ask')">校园卡丢了</span>
        <span @click="$emit('nav', 'ask')">食堂推荐</span>
        <span @click="$emit('nav', 'ask')">借雨伞</span>
      </div>

      <div class="home-stats">
        <div><b>{{ loading ? '—' : shown.total }}</b><span>已发布</span></div>
        <div><b>{{ loading ? '—' : shown.closed }}</b><span>已找回</span></div>
        <div><b>{{ loading ? '—' : shown.today }}</b><span>今日新增</span></div>
      </div>

      <div class="foot-b">
        <div class="flinks">
          <span @click="$emit('nav', 'mine')">我的发布</span>
          <span @click="$emit('nav', 'legacy', 'about')">平台简介</span>
          <span @click="replayTour">使用引导</span>
          <span @click="$emit('nav', 'legacy', 'contact')">联系方式</span>
          <span @click="$emit('nav', 'legacy', 'legal')">法律声明</span>
          <span @click="$emit('nav', 'legacy', 'privacy')">隐私权保护</span>
        </div>
        <div class="flic">测试版 · 暂未备案 · 仅用于校园公益</div>
        <div class="fcopy">Copyright © 2025-2026 清城牧羊 版权所有</div>
        <div class="ver">v3.2 · 2026-10-26 · 本机 / 同 Wi-Fi / 公网 三种模式自动切换</div>
      </div>
    </div>
    <button class="fab-pub" type="button" aria-label="发布启事" @click="$emit('nav', 'publish')">＋</button>
  </section>
</template>



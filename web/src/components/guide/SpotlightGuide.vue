<script setup>
import { nextTick, onMounted, onUnmounted, ref } from 'vue'
import GuideCard from './GuideCard.vue'
import { guideSteps } from './guideSteps'

const KEY = 'sg:tour:v6'
const show = ref(false)
const index = ref(0)
const holeStyle = ref({ display: 'none' })
const cardStyle = ref({})
const placement = ref('center')
const layerClass = ref('')

function isFirstVisit() {
  if (location.search.includes('tour=off')) return false
  if (new URLSearchParams(location.search).get('tour') === '1') return true
  try { return localStorage.getItem(KEY) !== '1' } catch (e) { return true }
}

function close() {
  show.value = false
  try { localStorage.setItem(KEY, '1') } catch (e) {}
}

function next() {
  if (index.value >= guideSteps.length - 1) return close()
  index.value++
  place()
}

function centerCard() {
  placement.value = 'center'
  layerClass.value = 'dim'
  holeStyle.value = { display: 'none' }
  cardStyle.value = {
    left: '50%',
    top: '50%',
    transform: 'translate(-50%, -50%)',
    width: 'min(360px, calc(100vw - 28px))'
  }
}

async function place() {
  if (!show.value) return
  await nextTick()
  const slide = guideSteps[index.value]
  const target = slide.target ? document.querySelector(slide.target) : null
  if (!target) {
    centerCard()
    return
  }
  target.scrollIntoView({ block: 'center', inline: 'center', behavior: 'smooth' })
  setTimeout(() => {
    if (!show.value) return
    const r = target.getBoundingClientRect()
    const pad = 7
    holeStyle.value = {
      display: 'block',
      left: Math.max(7, r.left - pad) + 'px',
      top: Math.max(7, r.top - pad) + 'px',
      width: Math.max(18, r.width + pad * 2) + 'px',
      height: Math.max(18, r.height + pad * 2) + 'px'
    }
    layerClass.value = 'spot'
    const margin = 16
    const width = Math.min(360, window.innerWidth - margin * 2)
    if (window.innerWidth <= 720) {
      placement.value = 'bottom'
      cardStyle.value = {
        left: margin + 'px',
        right: margin + 'px',
        bottom: margin + 'px',
        top: 'auto',
        width: 'auto',
        transform: 'none'
      }
      return
    }
    const gap = 22
    let left = r.left > window.innerWidth / 2 ? r.left - width - gap : r.right + gap
    if (left < margin || left + width > window.innerWidth - margin) {
      left = Math.min(window.innerWidth - width - margin, Math.max(margin, r.left + r.width / 2 - width / 2))
    }
    const cardHeight = 350
    const top = Math.min(window.innerHeight - cardHeight - margin, Math.max(margin, r.top + r.height / 2 - cardHeight / 2))
    placement.value = left < r.left ? 'right' : 'left'
    cardStyle.value = { left: left + 'px', top: top + 'px', width: width + 'px', transform: 'none' }
  }, 380)
}

function replay() {
  index.value = 0
  show.value = true
  centerCard()
  place()
}

function onKey(e) {
  if (!show.value) return
  if (e.key === 'Escape') close()
  if (e.key === 'ArrowRight' || e.key === 'Enter') next()
}

onMounted(() => {
  window.addEventListener('sg:tour', replay)
  window.addEventListener('resize', place)
  document.addEventListener('keydown', onKey)
  if (isFirstVisit()) {
    show.value = true
    centerCard()
    place()
  }
})
onUnmounted(() => {
  window.removeEventListener('sg:tour', replay)
  window.removeEventListener('resize', place)
  document.removeEventListener('keydown', onKey)
})
</script>

<template>
  <div v-if="show" class="guide-layer" :class="layerClass">
    <div class="guide-blocker"></div>
    <div class="guide-hole" :style="holeStyle"></div>
    <GuideCard
      :slide="guideSteps[index]"
      :index="index"
      :total="guideSteps.length"
      :placement="placement"
      :style="cardStyle"
      @next="next"
      @skip="close"
    />
  </div>
</template>

<style scoped>
.guide-layer { position: fixed; inset: 0; z-index: 9998; }
.guide-blocker { position: absolute; inset: 0; background: transparent; }
.guide-layer.dim .guide-blocker { background: rgba(7, 3, 12, .72); }
.guide-hole { position: fixed; z-index: 9999; border-radius: 14px; border: 2px solid #e8cd8e; box-shadow: 0 0 0 9999px rgba(7, 3, 12, .78), 0 0 24px rgba(232, 205, 142, .25); pointer-events: none; transition: left .3s ease, top .3s ease, width .3s ease, height .3s ease; }
</style>

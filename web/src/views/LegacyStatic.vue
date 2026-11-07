<script setup>
import { computed } from 'vue'
import { legacyScreens } from '../data/legacyScreens'

const props = defineProps({
  name: { type: String, default: 'about' }
})
const emit = defineEmits(['nav'])

const html = computed(() => {
  const raw = legacyScreens[props.name] || '<section class="screen active" id="screen-info"><div class="topbar"><div class="t">暂无内容</div></div></section>'
  return raw.replace('class="screen', 'class="screen active')
})

function onClick(e) {
  const back = e.target.closest('[data-back]')
  if (back) { emit('nav', 'home'); return }
  const nav = e.target.closest('[data-nav]')
  if (nav) {
    const t = nav.getAttribute('data-nav')
    const map = { mine: 'mine', about: 'about', contact: 'contact', legal: 'legal', privacy: 'privacy', guideHome: 'guide' }
    emit('nav', map[t] || 'home')
  }
}
</script>

<template>
  <div class="legacy-static" @click="onClick" v-html="html" />
</template>

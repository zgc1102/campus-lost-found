<script setup>
import HomeView from './views/HomeView.vue'
import BottomNav from './components/BottomNav.vue'
import { oldUrl } from './api'

function go(target) {
  const map = {
    home: 'home',
    lost: 'lost',
    found: 'found',
    help: 'help',
    mine: 'mine',
    notices: 'notices',
    tag: 'tag',
    detective: 'detective',
    ask: 'ask',
    guide: 'guideHome'
  }
  if (target === 'home') return
  const screen = map[target] || 'home'
  const extra = target === 'tag' ? 'open=tag' : target === 'detective' ? 'open=detective' : ''
  location.href = oldUrl(screen, extra)
}
</script>

<template>
  <div class="phone">
    <HomeView @nav="go" />
    <BottomNav @nav="go" />
  </div>
</template>

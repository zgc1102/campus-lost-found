<script setup>
import { ref } from 'vue'
import HomeView from './views/HomeView.vue'
import ListView from './views/ListView.vue'
import BottomNav from './components/BottomNav.vue'
import { oldUrl } from './api'

const params = new URLSearchParams(location.search)
const initial = params.get('view')
const view = ref(initial === 'lost' || initial === 'found' ? initial : 'home')

function go(target) {
  if (target === 'home') {
    view.value = 'home'
    history.replaceState({}, '', location.pathname)
    return
  }
  if (target === 'lost' || target === 'found') {
    view.value = target
    history.replaceState({}, '', location.pathname + '?view=' + target)
    return
  }
  const map = {
    help: 'help',
    mine: 'mine',
    notices: 'notices',
    tag: 'tag',
    detective: 'detective',
    ask: 'ask',
    guide: 'guideHome'
  }
  const screen = map[target] || 'home'
  const extra = target === 'tag' ? 'open=tag' : target === 'detective' ? 'open=detective' : ''
  location.href = oldUrl(screen, extra)
}
</script>

<template>
  <div class="phone">
    <HomeView v-if="view === 'home'" @nav="go" />
    <ListView v-else :type="view" @nav="go" />
    <BottomNav :active="view" @nav="go" />
  </div>
</template>

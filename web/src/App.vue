<script setup>
import { ref } from 'vue'
import HomeView from './views/HomeView.vue'
import ListView from './views/ListView.vue'
import HelpView from './views/HelpView.vue'
import PublishView from './views/PublishView.vue'
import RadarView from './views/RadarView.vue'
import TagView from './views/TagView.vue'
import MineView from './views/MineView.vue'
import BottomNav from './components/BottomNav.vue'
import { oldUrl } from './api'

const params = new URLSearchParams(location.search)
const initial = params.get('view')
const initialView = ['lost', 'found', 'help', 'publish', 'radar', 'tag', 'mine'].includes(initial) ? initial : 'home'
const view = ref(initialView)
const publishType = ref(params.get('type') || 'lost')
const helpCat = ref(params.get('cat') || 'help_borrow')

function go(target) {
  if (target === 'home') {
    view.value = 'home'
    history.replaceState({}, '', location.pathname)
    return
  }
  if (target === 'lost' || target === 'found' || target === 'help') {
    view.value = target
    history.replaceState({}, '', location.pathname + '?view=' + target)
    return
  }
  if (target === 'mine' || target === 'tag' || target === 'radar' || target === 'detective') {
    view.value = target === 'detective' ? 'radar' : target
    history.replaceState({}, '', location.pathname + '?view=' + (target === 'detective' ? 'radar' : target))
    return
  }
  const map = {
    notices: 'notices',
    ask: 'ask',
    guide: 'guideHome'
  }
  const screen = map[target] || 'home'
  location.href = oldUrl(screen)
}

function publish(type, cat) {
  publishType.value = type
  helpCat.value = cat || helpCat.value
  view.value = 'publish'
  history.replaceState({}, '', location.pathname + '?view=publish&type=' + encodeURIComponent(type))
}
</script>

<template>
  <div class="phone">
    <HomeView v-if="view === 'home'" @nav="go" />
    <ListView v-else-if="view === 'lost' || view === 'found'" :type="view" @nav="go" @publish="publish" />
    <HelpView v-else-if="view === 'help'" @nav="go" @publish="publish" />
    <PublishView v-else-if="view === 'publish'" :type="publishType" :help-cat="helpCat" @nav="go" />
    <RadarView v-else-if="view === 'radar'" @nav="go" />
    <TagView v-else-if="view === 'tag'" @nav="go" />
    <MineView v-else-if="view === 'mine'" @nav="go" @publish="publish" />
    <BottomNav :active="view === 'publish' ? (publishType === 'help' ? 'help' : publishType) : view" @nav="go" />
  </div>
</template>

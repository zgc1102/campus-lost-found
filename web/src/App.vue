<script setup>
import { ref } from 'vue'
import HomeView from './views/HomeView.vue'
import ListView from './views/ListView.vue'
import HelpView from './views/HelpView.vue'
import PublishView from './views/PublishView.vue'
import RadarView from './views/RadarView.vue'
import TagView from './views/TagView.vue'
import MineView from './views/MineView.vue'
import GuideView from './views/GuideView.vue'
import MapView from './views/MapView.vue'
import AskView from './views/AskView.vue'
import NoticesView from './views/NoticesView.vue'
import SearchView from './views/SearchView.vue'
import InfoView from './views/InfoView.vue'
import AdminView from './views/AdminView.vue'
import BottomNav from './components/BottomNav.vue'
import TourOverlay from './components/TourOverlay.vue'

const params = new URLSearchParams(location.search)
const initial = params.get('view')
const isAdmin = location.pathname.replace(/\/+$/, '') === '/admin'
const initialView = isAdmin ? 'admin' : ['lost', 'found', 'help', 'publish', 'radar', 'tag', 'mine', 'guide', 'map', 'ask', 'notices', 'info', 'search', 'admin'].includes(initial) ? initial : 'home'
const view = ref(initialView)
const publishType = ref(params.get('type') || 'lost')
const helpCat = ref(params.get('cat') || 'help_borrow')
const infoKey = ref(params.get('info') || 'about')

function go(target, arg) {
  if (target === 'home') {
    view.value = 'home'
    history.replaceState({}, '', location.pathname)
    return
  }
  if (target === 'info') {
    infoKey.value = arg || 'about'
    view.value = 'info'
    history.replaceState({}, '', location.pathname + '?view=info&info=' + infoKey.value)
    return
  }
  if (target === 'publish') {
    publish('lost')
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
  if (target === 'guide' || target === 'map' || target === 'ask' || target === 'notices' || target === 'search') {
    view.value = target
    history.replaceState({}, '', location.pathname + '?view=' + target)
    return
  }
  view.value = 'home'
  history.replaceState({}, '', location.pathname)
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
    <GuideView v-else-if="view === 'guide'" @nav="go" />
    <MapView v-else-if="view === 'map'" @nav="go" />
    <AskView v-else-if="view === 'ask'" @nav="go" />
    <NoticesView v-else-if="view === 'notices'" @nav="go" />
    <InfoView v-else-if="view === 'info'" :info-key="infoKey" @nav="go" />
    <SearchView v-else-if="view === 'search'" @nav="go" />
    <AdminView v-else-if="view === 'admin'" />
    <BottomNav v-if="view !== 'admin' && view !== 'map' && view !== 'ask'" :active="view === 'publish' ? (publishType === 'help' ? 'help' : publishType) : view" @nav="go" />
    <TourOverlay />
  </div>
</template>

<script setup>
import { computed, defineAsyncComponent, onMounted, onUnmounted, ref } from 'vue'
import HomeView from './views/HomeView.vue'
import ListView from './views/ListView.vue'
import LoadingState from './components/LoadingState.vue'
import BottomNav from './components/BottomNav.vue'
import TourOverlay from './components/TourOverlay.vue'

const asyncView = (loader) => defineAsyncComponent({
  loader,
  loadingComponent: LoadingState,
  delay: 120
})

const HelpView = asyncView(() => import('./views/HelpView.vue'))
const HelpPublishView = asyncView(() => import('./views/HelpPublishView.vue'))
const PublishView = asyncView(() => import('./views/PublishView.vue'))
const RadarView = asyncView(() => import('./views/RadarView.vue'))
const MatchView = asyncView(() => import('./views/MatchView.vue'))
const TagView = asyncView(() => import('./views/TagView.vue'))
const TagScanView = asyncView(() => import('./views/TagScanView.vue'))
const MineView = asyncView(() => import('./views/MineView.vue'))
const GuideView = asyncView(() => import('./views/GuideView.vue'))
const MapView = asyncView(() => import('./views/MapView.vue'))
const AskView = asyncView(() => import('./views/AskView.vue'))
const NoticesView = asyncView(() => import('./views/NoticesView.vue'))
const SearchView = asyncView(() => import('./views/SearchView.vue'))
const StaticInfoView = asyncView(() => import('./views/StaticInfoView.vue'))
const SuccessView = asyncView(() => import('./views/SuccessView.vue'))
const ToolsView = asyncView(() => import('./views/ToolsView.vue'))
const MemorialView = asyncView(() => import('./views/MemorialView.vue'))
const FaqView = asyncView(() => import('./views/FaqView.vue'))
const PhonesView = asyncView(() => import('./views/PhonesView.vue'))
const InfoView = asyncView(() => import('./views/InfoView.vue'))
const AdminView = asyncView(() => import('./views/AdminView.vue'))
const params = new URLSearchParams(location.search)
const initial = params.get('view')
const tagCode = ref(params.get('tag') || params.get('code') || '')
const isAdmin = location.pathname.replace(/\/+$/, '') === '/admin'
const initialView = isAdmin ? 'admin' : (tagCode.value ? 'tag-scan' : ['lost', 'found', 'help', 'publish', 'help-publish', 'radar', 'match', 'tag', 'mine', 'guide', 'map', 'ask', 'notices', 'info', 'search', 'admin', 'legacy', 'success', 'lend', 'borrow', 'memorial', 'faq', 'phones'].includes(initial) ? initial : 'home')
const view = ref(initialView)
const publishType = ref(params.get('type') || 'lost')
const helpCat = ref(params.get('cat') || 'help_borrow')
const helpPublishCat = ref('help_borrow')
const editingItem = ref(null)
const infoKey = ref(params.get('info') || 'about')
const legacyName = ref(params.get('screen') || 'about')

function go(target, arg) {
  if (target === 'home') {
    tagCode.value = ''
    view.value = 'home'
    history.pushState({}, '', location.pathname)
    return
  }
  if (target === 'legacy') {
    legacyName.value = arg || 'about'
    view.value = 'legacy'
    history.pushState({}, '', location.pathname + '?view=legacy&screen=' + legacyName.value)
    return
  }
  if (target === 'info') {
    infoKey.value = arg || 'about'
    view.value = 'info'
    history.pushState({}, '', location.pathname + '?view=info&info=' + infoKey.value)
    return
  }
  if (target === 'publish') {
    publish(arg === 'help' ? 'help' : 'lost')
    return
  }
  if (target === 'lost' || target === 'found' || target === 'help' || target === 'lend' || target === 'borrow') {
    if (target === 'help' && arg) helpCat.value = arg
    view.value = target
    history.pushState({}, '', location.pathname + '?view=' + target + (target === 'help' ? '&cat=' + helpCat.value : ''))
    return
  }
  if (target === 'mine' || target === 'tag' || target === 'radar' || target === 'detective') {
    view.value = target === 'detective' ? 'radar' : target
    history.pushState({}, '', location.pathname + '?view=' + (target === 'detective' ? 'radar' : target))
    return
  }
  if (target === 'guide' || target === 'map' || target === 'ask' || target === 'notices' || target === 'search' || target === 'success' || target === 'memorial' || target === 'faq' || target === 'phones') {
    view.value = target
    history.pushState({}, '', location.pathname + '?view=' + target)
    return
  }
  view.value = 'home'
  history.pushState({}, '', location.pathname)
}

const viewKey = computed(() => [view.value, publishType.value, helpCat.value, editingItem.value?.id || '', infoKey.value, legacyName.value, tagCode.value].join('|'))

function syncFromUrl() {
  const p = new URLSearchParams(location.search)
  const v = p.get('view')
  const allowed = ['home','lost','found','help','publish','help-publish','radar','match','tag','tag-scan','mine','guide','map','ask','notices','info','search','legacy','success','lend','borrow','memorial','faq','phones']
  tagCode.value = p.get('tag') || p.get('code') || ''
  if (tagCode.value) { view.value = 'tag-scan'; return }
  publishType.value = p.get('type') || 'lost'
  helpCat.value = p.get('cat') || 'help_borrow'
  infoKey.value = p.get('info') || 'about'
  legacyName.value = p.get('screen') || 'about'
  view.value = allowed.includes(v) ? v : 'home'
}

function goBack() {
  if (isAdmin) return
  if (history.length > 1) history.back()
  else go('home')
}

let touchStart = null
function onTouchStart(e) {
  const t = e.touches && e.touches[0]
  if (!t || t.clientX > 40 || view.value === 'map') return
  touchStart = { x: t.clientX, y: t.clientY, at: Date.now() }
}
function onTouchEnd(e) {
  if (!touchStart) return
  const t = e.changedTouches && e.changedTouches[0]
  const start = touchStart
  touchStart = null
  if (!t) return
  const dx = t.clientX - start.x
  const dy = Math.abs(t.clientY - start.y)
  if (dx > 72 && dy < 70 && Date.now() - start.at < 700) goBack()
}

onMounted(() => window.addEventListener('popstate', syncFromUrl))
onUnmounted(() => window.removeEventListener('popstate', syncFromUrl))

function publish(type, cat) {
  editingItem.value = null
  if (type === 'help') {
    publishType.value = 'help'
    helpPublishCat.value = cat || 'help_borrow'
    view.value = 'help-publish'
    history.pushState({}, '', location.pathname + '?view=help-publish')
    return
  }
  publishType.value = type
  helpCat.value = cat || helpCat.value
  view.value = 'publish'
  history.pushState({}, '', location.pathname + '?view=publish&type=' + encodeURIComponent(type))
}

function editItem(item) {
  editingItem.value = item
  if (item.type === 'help') {
    publishType.value = 'help'
    helpPublishCat.value = item.cat || item.helpCat || 'help_borrow'
    view.value = 'help-publish'
    history.pushState({}, '', location.pathname + '?view=help-publish&cat=' + helpPublishCat.value)
    return
  }
  publishType.value = item.type === 'found' ? 'found' : 'lost'
  view.value = 'publish'
  history.pushState({}, '', location.pathname + '?view=publish&type=' + publishType.value)
}
</script>

<template>
  <div v-if="view === 'admin'" class="admin-route">
    <AdminView />
  </div>
  <div v-else class="phone" @touchstart.passive="onTouchStart" @touchend.passive="onTouchEnd">
    <nav v-if="view !== 'map' && view !== 'ask' && view !== 'tag-scan'" class="desktop-nav" aria-label="桌面导航">
      <button type="button" :class="{ on: view === 'home' }" @click="go('home')">首页</button>
      <button type="button" :class="{ on: view === 'lost' || view === 'found' }" @click="go('lost')">失物招领</button>
      <button type="button" :class="{ on: view === 'help' }" @click="go('help')">爱心互助</button>
      <button type="button" :class="{ on: view === 'mine' }" @click="go('mine')">我的</button>
    </nav>
    <Transition name="page" mode="out-in">
      <div :key="viewKey" class="page-view">
    <HomeView v-if="view === 'home'" @nav="go" />
    <ListView v-else-if="view === 'lost' || view === 'found'" :type="view" @nav="go" @publish="publish" />
    <HelpView v-else-if="view === 'help'" :key="helpCat" :initial-cat="helpCat" @nav="go" @publish="publish" />
    <HelpPublishView v-else-if="view === 'help-publish'" :key="editingItem ? editingItem.id : 'new-' + helpPublishCat" :help-cat="helpPublishCat" :edit-item="editingItem" @nav="go" />
    <PublishView v-else-if="view === 'publish'" :key="publishType + '-' + helpCat + '-' + (editingItem ? editingItem.id : 'new')" :type="publishType" :help-cat="helpCat" :edit-item="editingItem" @nav="go" />
    <RadarView v-else-if="view === 'radar'" @nav="go" />
    <MatchView v-else-if="view === 'match'" @nav="go" />
    <TagScanView v-else-if="view === 'tag-scan'" :code="tagCode" @nav="go" />
    <TagView v-else-if="view === 'tag'" @nav="go" />
    <MineView v-else-if="view === 'mine'" @nav="go" @publish="publish" @edit="editItem" />
    <GuideView v-else-if="view === 'guide'" @nav="go" />
    <MapView v-else-if="view === 'map'" @nav="go" />
    <AskView v-else-if="view === 'ask'" @nav="go" />
    <NoticesView v-else-if="view === 'notices'" @nav="go" />
    <InfoView v-else-if="view === 'info'" :info-key="infoKey" @nav="go" />
    <SearchView v-else-if="view === 'search'" @nav="go" />
    <StaticInfoView v-else-if="view === 'legacy'" :name="legacyName" @nav="go" />
    <SuccessView v-else-if="view === 'success'" :type="publishType" @nav="go" />
    <ToolsView v-else-if="view === 'lend' || view === 'borrow'" :mode="view" @nav="go" />
    <MemorialView v-else-if="view === 'memorial'" @nav="go" />
    <FaqView v-else-if="view === 'faq'" @nav="go" />
    <PhonesView v-else-if="view === 'phones'" @nav="go" />
      </div>
    </Transition>
    <BottomNav v-if="view !== 'map' && view !== 'ask' && view !== 'tag-scan'" :active="view === 'publish' ? (publishType === 'help' ? 'help' : publishType) : view" @nav="go" />
    <TourOverlay v-if="view !== 'tag-scan'" />
  </div>
</template>

<style>
html {
  scrollbar-gutter: stable;
}
body {
  min-height: 100vh;
}
.admin-route {
  position: fixed;
  inset: 0;
  width: 100vw;
  height: 100vh;
  overflow-y: auto;
  overflow-x: hidden;
  scrollbar-gutter: stable;
  background: #F3EEFA;
  overscroll-behavior: contain;
}
.page-view { min-height: 100%; }
.page-enter-active, .page-leave-active { transition: opacity .18s ease, transform .18s ease; }
.page-enter-from { opacity: 0; transform: translateX(14px); }
.page-leave-to { opacity: 0; transform: translateX(-10px); }
@media (max-width: 759px) {
  html, body, #app {
    width: 100%;
    overflow-x: hidden;
  }
  body {
    display: block;
  }
  .phone {
    width: 390px;
    max-width: 100%;
    margin: 0 auto;
    border-radius: 0;
    box-shadow: none;
  }
  .bottom-nav {
    position: fixed;
    left: 50%;
    width: 390px;
    max-width: 100%;
    transform: translateX(-50%);
  }
}
</style>

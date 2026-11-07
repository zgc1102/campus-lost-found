<script setup>
defineProps({
  active: { type: String, default: 'home' }
})
defineEmits(['nav'])
</script>

<template>
  <nav class="bottom-nav" aria-label="底部导航">
    <button type="button" :class="{ on: active === 'home' }" data-nav="home" @click="$emit('nav', 'home')">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><path d="M3 11l9-8 9 8"/><path d="M5 10v10h14V10"/></svg><span>首页</span>
    </button>
    <button type="button" :class="{ on: active === 'lost' || active === 'found' }" data-nav="lost" @click="$emit('nav', 'lost')">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><circle cx="11" cy="11" r="7"/><path d="M16.5 16.5 21 21"/></svg><span>失物</span>
    </button>
    <button type="button" :class="{ on: active === 'help' }" data-nav="help" @click="$emit('nav', 'help')">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><path d="M12 20s-7-4.3-7-9a4 4 0 0 1 7-2 4 4 0 0 1 7 2c0 4.7-7 9-7 9Z"/></svg><span>互助</span>
    </button>
    <button type="button" :class="{ on: active === 'mine' }" data-nav="mine" @click="$emit('nav', 'mine')">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><circle cx="12" cy="8" r="4"/><path d="M4 21c0-4 4-6 8-6s8 2 8 6"/></svg><span>我的</span>
    </button>
  </nav>
</template>

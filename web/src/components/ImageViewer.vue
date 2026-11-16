<script setup>
defineProps({ src: { type: String, default: '' } })
defineEmits(['close'])
</script>

<template>
  <div v-if="src" class="img-viewer" @click.self="$emit('close')">
    <img :src="src" alt="查看大图">
    <button type="button" @click="$emit('close')">关闭</button>
  </div>
</template>

<style scoped>
.img-viewer { position:fixed; inset:0; z-index:9999; background:rgba(20,12,30,.82); display:flex; align-items:center; justify-content:center; padding:24px; }
.img-viewer img { max-width:92vw; max-height:82vh; border-radius:10px; box-shadow:0 12px 40px rgba(0,0,0,.45); }
.img-viewer button { position:absolute; top:18px; right:18px; border:0; border-radius:8px; padding:8px 14px; background:#fff; color:#3B1D63; font-family:inherit; font-size:11px; cursor:pointer; }
</style>

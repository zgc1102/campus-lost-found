<script setup>
import { onMounted } from 'vue'

onMounted(() => {
  location.replace('/admin')
})
</script>

<template>
  <div style="min-height:100vh;display:flex;align-items:center;justify-content:center;font-family:inherit;color:#5B2A91">
    正在进入管理端…
  </div>
</template>

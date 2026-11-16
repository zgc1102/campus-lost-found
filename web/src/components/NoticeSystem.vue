<script setup>
const props = defineProps({ notice: { type: Object, required: true } })
defineEmits(['compare', 'ignore'])
</script>

<template>
  <div class="nd-card">
    <div class="nd-card-title">通知内容</div>
    <div class="nd-message">{{ notice.text }}</div>
    <div v-if="!notice.itemId" class="nd-legacy">这条是旧版通知，只保留了文字记录，没有可操作的上报详情。</div>
  </div>
  <div v-if="!notice.report && !notice.item && notice.itemId" class="nd-legacy">原物品已删除或数据不完整，无法生成匹配报告。</div>
  <div class="nd-actions">
    <button v-if="notice.item" type="button" class="btn ghost" @click="$emit('compare')">查看匹配报告</button>
    <button type="button" class="btn ghost" @click="$emit('ignore')">忽略</button>
  </div>
</template>

<style src="../styles/notice-branch.css"></style>

<script setup>
const props = defineProps({ notice: { type: Object, required: true } })
defineEmits(['reveal', 'publish', 'block', 'close', 'ignore'])
function time(ts) {
  if (!ts) return ''
  const d = new Date(Number(ts) || 0)
  if (!Number.isFinite(d.getTime())) return ''
  return `${d.getMonth() + 1}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}
function openPhoto() {
  if (props.notice.report?.photo) window.open(props.notice.report.photo, '_blank', 'noopener')
}
</script>

<template>
  <div class="nd-card">
    <div class="nd-card-title">捡到上报</div>
    <div class="nd-kv"><span>捡到物品</span><b>{{ notice.report?.itemName || '捡到物品' }}</b></div>
    <div class="nd-kv"><span>拾光码物品</span><b>{{ notice.report?.tagItem || '我的物品' }}</b></div>
    <div class="nd-kv"><span>上报时间</span><b>{{ time(notice.report?.at) }}</b></div>
    <div class="nd-message">{{ notice.report?.message }}</div>
    <div v-if="notice.report?.photo" style="margin-top:8px">
      <img :src="notice.report.photo" alt="物品照片" title="双击查看大图" style="max-width:100%;max-height:220px;border-radius:9px;border:1px solid #EADFF5;cursor:zoom-in" @dblclick="openPhoto">
    </div>
    <div v-if="notice.report?.phoneRevealed" class="nd-kv"><span>我的手机号</span><b>{{ notice.report?.ownerContact || '未留手机号' }}</b></div>
    <div v-if="notice.report?.phoneRevealed" class="nd-kv"><span>捡到者手机号</span><b>{{ notice.report?.contact || '未留手机号' }}</b></div>
  </div>
  <slot name="chat" />
  <div class="nd-actions">
    <template v-if="notice.isReportOwner">
      <button v-if="!notice.report?.phoneRevealed" type="button" class="btn" @click="$emit('reveal')">公布双方手机号并联系</button>
      <button type="button" class="btn ghost" @click="$emit('block')">屏蔽</button>
      <button v-if="notice.report?.status !== 'closed'" type="button" class="btn ghost" @click="$emit('close')">关闭</button>
    </template>
    <button type="button" class="btn ghost" @click="$emit('ignore')">忽略</button>
  </div>
</template>

<style src="../styles/notice-branch.css"></style>

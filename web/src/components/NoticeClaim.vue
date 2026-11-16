<script setup>
const props = defineProps({ notice: { type: Object, required: true } })
defineEmits(['claim-action', 'reveal', 'block', 'compare', 'ignore'])
function time(ts) {
  if (!ts) return ''
  const d = new Date(Number(ts) || 0)
  if (!Number.isFinite(d.getTime())) return ''
  return `${d.getMonth() + 1}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}
function statusText(s) {
  return ({ pending: '待处理', accepted: '已通过', completed: '已完成', rejected: '已拒绝', need_more: '待补充' })[s] || s || ''
}
</script>

<template>
  <div class="nd-card">
    <div class="nd-card-title">认领申请</div>
    <div class="nd-message">{{ notice.claimMessage || notice.text }}</div>
    <div class="nd-kv"><span>发布者手机号</span><b>{{ notice.ownerContact || (notice.item?.contact?.phone ? '已留手机号（通过后显示完整）' : '还没留手机号') }}</b></div>
    <div class="nd-kv"><span>认领人手机号</span><b>{{ notice.item?.isMine ? (notice.claimContact || '还没留手机号') : (notice.claimContact ? '已留手机号' : '还没留手机号') }}</b></div>
    <div v-if="notice.claimStatus" class="nd-state">{{ statusText(notice.claimStatus) }}</div>
    <div v-if="notice.claimAi" class="nd-ai-check">
      <b>信息对比度：{{ notice.claimAi.confidence }}%</b>
      <span>仅供发布者参考</span>
      <p v-if="notice.claimAi.reason">{{ notice.claimAi.reason }}</p>
      <div v-if="notice.claimAi.points?.length" class="nd-ai-points"><i v-for="p in notice.claimAi.points" :key="p">{{ p }}</i></div>
    </div>
  </div>
  <slot name="chat" />
  <div class="nd-actions">
    <template v-if="(notice.isPublisher || notice.item?.isMine) && notice.claimId && (!notice.claimStatus || ['pending','need_more'].includes(notice.claimStatus))">
      <button type="button" class="btn" @click="$emit('claim-action', 'accepted')">通过认领</button>
      <button type="button" class="btn ghost" @click="$emit('claim-action', 'need_more')">请补充</button>
      <button type="button" class="btn ghost" @click="$emit('claim-action', 'rejected')">拒绝</button>
      <button v-if="notice.canBlockClaim" type="button" class="btn ghost" @click="$emit('block')">屏蔽对方</button>
    </template>
    <button v-if="notice.claimId && notice.canRevealPhone && !notice.claimPhoneRevealed && !['accepted','completed'].includes(notice.claimStatus)" type="button" class="btn ghost" @click="$emit('reveal')">公布双方手机号</button>
    <button v-if="notice.item" type="button" class="btn ghost" @click="$emit('compare')">查看匹配报告</button>
    <button type="button" class="btn ghost" @click="$emit('ignore')">忽略</button>
  </div>
</template>

<style src="../styles/notice-branch.css"></style>

<script setup>
import { ref } from 'vue'
const props = defineProps({
  notice: { type: Object, required: true },
  supplementing: { type: Boolean, default: false },
  phoneSaving: { type: Boolean, default: false },
  supplementMsg: { type: String, default: '' },
  phoneMsg: { type: String, default: '' }
})
const emit = defineEmits(['supplement', 'save-phone', 'help-action', 'block', 'compare', 'ignore'])
const supp = ref('')
const phone = ref('')
function statusText(s) {
  return ({ pending: '待处理', accepted: '进行中', completed: '已完成', rejected: '已婉拒', need_more: '待补充' })[s] || s || ''
}
function submitSupp() {
  const text = supp.value.trim()
  if (text.length < 2) return
  emit('supplement', text)
  supp.value = ''
}
function submitPhone() {
  const p = phone.value.trim()
  if (!p) return
  emit('save-phone', p)
  phone.value = ''
}
</script>

<template>
  <div class="nd-card nd-help-card">
    <div class="nd-card-title">帮忙说明</div>
    <div class="nd-message">{{ notice.claimMessage || notice.text }}</div>
    <div v-if="notice.claimAi" class="nd-ai-check">
      <b>信息对比度：{{ notice.claimAi.confidence }}%</b>
      <span>仅供发布者参考</span>
      <p v-if="notice.claimAi.reason">{{ notice.claimAi.reason }}</p>
      <div v-if="notice.claimAi.points?.length" class="nd-ai-points"><i v-for="p in notice.claimAi.points" :key="p">{{ p }}</i></div>
    </div>
    <div v-if="notice.claimStatus" class="nd-state" style="margin-top:8px">{{ statusText(notice.claimStatus) }}</div>
    <div v-if="notice.claimBlocked" class="nd-blocked">
      <b>你已屏蔽对方</b><span>双方不能再互发消息，也不能再查看对方手机号。</span>
    </div>
    <div v-if="notice.claimStatus === 'need_more' && notice.isClaimant" class="nd-phone-fill">
      <p>发布者请你补充一点细节，补充后会自动回到待处理。</p>
      <textarea v-model="supp" maxlength="200" placeholder="补充你能提供的具体信息"></textarea>
      <button type="button" :disabled="supplementing" @click="submitSupp">{{ supplementing ? '提交中…' : '提交补充' }}</button>
      <div v-if="supplementMsg" class="nd-phone-msg">{{ supplementMsg }}</div>
    </div>
    <div v-else-if="notice.claimStatus === 'need_more'" class="nd-exchange-tip">已请帮忙人补充说明，等对方提交后会自动回到待处理。</div>
    <div class="nd-kv" style="margin-top:8px"><span>发布者手机号</span><b>{{ notice.ownerContact || (notice.item?.contact?.phone ? '已留手机号（通过后显示完整）' : '还没留手机号') }}</b></div>
    <div class="nd-kv"><span>帮忙人手机号</span><b>{{ notice.item?.isMine ? (notice.claimContact || '还没留手机号') : (notice.claimContact ? '已留手机号' : '还没留手机号') }}</b></div>
    <div v-if="notice.item?.isMine && !notice.ownerContact && !notice.item?.contact?.phone" class="nd-phone-fill">
      <p>你是发布者。留手机号后，接受帮忙时双方才能互相联系。</p>
      <div class="nd-phone-row"><input v-model="phone" maxlength="20" placeholder="补充你的手机号"><button type="button" :disabled="phoneSaving" @click="submitPhone">{{ phoneSaving ? '保存中…' : '补充手机号' }}</button></div>
    </div>
    <div v-if="notice.isClaimant && !notice.claimContact" class="nd-phone-fill">
      <p>你还没有预留手机号，发布者无法接受帮忙，也无法公布双方手机号。</p>
      <div class="nd-phone-row"><input v-model="phone" maxlength="20" placeholder="补充你的手机号"><button type="button" :disabled="phoneSaving" @click="submitPhone">{{ phoneSaving ? '保存中…' : '补充手机号' }}</button></div>
    </div>
    <div v-if="(notice.claimStatus === 'accepted' || notice.claimStatus === 'completed') && notice.claimContact && (notice.ownerContact || notice.item?.contact?.phone)" class="nd-exchange-ok">双方已公布手机号，可以直接联系。</div>
    <div v-else-if="notice.claimStatus === 'accepted' || notice.claimStatus === 'completed'" class="nd-exchange-tip" style="color:#A23B2A">帮忙人还没有预留手机号，双方手机号尚未交换。</div>
    <div v-if="phoneMsg" class="nd-phone-msg">{{ phoneMsg }}</div>
  </div>
  <div class="nd-actions">
    <template v-if="(notice.isPublisher || notice.item?.isMine) && notice.claimId && notice.claimStatus === 'pending'">
      <button type="button" class="btn" @click="$emit('help-action', 'accepted')">接受并公布双方手机号</button>
      <button type="button" class="btn ghost" @click="$emit('help-action', 'need_more')">请补充</button>
      <button type="button" class="btn ghost" @click="$emit('help-action', 'rejected')">婉拒</button>
      <button v-if="notice.canBlockClaim" type="button" class="btn ghost" @click="$emit('block')">屏蔽对方</button>
    </template>
    <button v-if="(notice.isPublisher || notice.item?.isMine) && notice.claimId && notice.claimStatus === 'accepted'" type="button" class="btn" @click="$emit('help-action', 'completed')">完成帮助</button>
    <button v-if="notice.item" type="button" class="btn ghost" @click="$emit('compare')">查看匹配报告</button>
    <button type="button" class="btn ghost" @click="$emit('ignore')">忽略</button>
  </div>
</template>

<style src="../styles/notice-branch.css"></style>
<style scoped>
.nd-phone-fill textarea { width:100%; box-sizing:border-box; min-height:58px; background:#fff; border:1px solid #E4D6F2; border-radius:8px; padding:8px; font-family:inherit; font-size:9.5px; }
.nd-phone-fill > button { margin-top:6px; width:100%; border:0; background:#5B2A91; color:#fff; border-radius:8px; padding:8px; font-family:inherit; font-size:9.5px; }
</style>

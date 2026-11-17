<script setup>
import { ref } from 'vue'
const props = defineProps({
  notice: { type: Object, required: true },
  supplementing: { type: Boolean, default: false },
  phoneSaving: { type: Boolean, default: false },
  supplementMsg: { type: String, default: '' },
  phoneMsg: { type: String, default: '' }
})
const emit = defineEmits(['supplement', 'save-phone', 'help-action', 'complete', 'block', 'compare', 'ignore', 'withdraw', 'remove', 'restore', 'unblock', 'privacy', 'accept-gift'])
const supp = ref('')
const phone = ref('')
function requestAcceptGift() {
  if (window.confirm('确定接受对方赠与吗？确认后双方可以开始匿名沟通。')) emit('accept-gift')
}
function requestReject() {
  if (window.confirm('确定婉拒这条帮忙申请吗？婉拒后可以在已婉拒状态拉回。')) emit('help-action', 'rejected')
}
function requestBlock() {
  if (window.confirm('确定屏蔽这位帮忙人吗？屏蔽后不能再联系。')) emit('block')
}
function requestRemove() {
  if (window.confirm('确定结束与 TA 的沟通吗？结束后名额会空出，可以再拉回。')) emit('remove')
}
function requestWithdraw() {
  if (window.confirm('确定撤回这条帮忙申请吗？撤回后名额会空出。')) emit('withdraw')
}
function requestRestore() {
  if (window.confirm('确定把这条申请拉回来吗？')) emit('restore')
}
function statusText(s) {
  return ({ pending: '待处理', accepted: '进行中', completed: '已完成', rejected: '已婉拒', need_more: '待补充', canceled: '已取消', withdrawn: '已撤回', removed: '已结束' })[s] || s || ''
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
    <div v-if="notice.helpNeedCount" class="nd-kv"><span>需要人数</span><b>{{ notice.helpNeedCount }} 人 · 已接受 {{ notice.helpAcceptedCount || 0 }} 人</b></div>
    <div v-if="notice.item?.askPrompt" class="nd-ask-prompt"><b>发布者希望你说明</b><span>{{ notice.item.askPrompt }}</span></div>
    <div v-if="notice.helpIsDonation && notice.claimStatus === 'accepted' && !notice.helpGiftAccepted" class="nd-ask-prompt">
      <b>赠与还未确认</b>
      <span v-if="notice.isClaimant">发布者已经同意捐赠，请确认接受赠与后再开始匿名沟通。</span>
      <span v-else>等待对方确认接受赠与后，匿名沟通才会开放。</span>
      <div v-if="notice.isClaimant" class="nd-privacy-actions"><button type="button" @click="requestAcceptGift">接受赠与</button></div>
    </div>
    <div v-if="notice.helpIsDonation && notice.helpPhonesHidden" class="nd-ask-prompt">
      <b>双方已同意不公开手机号</b><span>这次爱心捐赠通过匿名沟通完成，结束后也不会公开手机号。</span>
    </div>
    <div v-else-if="notice.helpIsDonation && notice.helpHideRequestByOther" class="nd-ask-prompt">
      <b>对方希望不公开双方手机号</b><span>只有双方都同意才会生效。</span>
      <div class="nd-privacy-actions">
        <button type="button" @click="$emit('privacy', 'agree')">同意不公开</button>
        <button type="button" class="ghost" @click="$emit('privacy', 'later')">暂不</button>
      </div>
    </div>
    <div v-else-if="notice.helpIsDonation && notice.helpHideRequestByMe" class="nd-ask-prompt">
      <b>已申请不公开手机号</b><span>等待对方同意后生效。</span>
      <div class="nd-privacy-actions"><button type="button" class="ghost" @click="$emit('privacy', 'cancel')">取消申请</button></div>
    </div>
    <div v-else-if="notice.helpIsDonation && ['pending','accepted'].includes(notice.claimStatus)" class="nd-ask-prompt">
      <b>不想公开手机号？</b><span>需要双方都同意，单方不能决定。申请后对方会收到通知。</span>
      <div class="nd-privacy-actions"><button type="button" class="ghost" @click="$emit('privacy', 'request')">申请不公开手机号</button></div>
    </div>
    <div v-if="notice.claimBlocked" class="nd-blocked">
      <b>{{ notice.claimBlockedByMe ? '你已屏蔽对方' : '对方已屏蔽你' }}</b><span>双方不能再互发消息，也不能再查看对方手机号。</span>
    </div>
    <div v-if="notice.claimStatus === 'need_more' && notice.isClaimant" class="nd-phone-fill">
      <p>发布者请你补充一点细节，补充后会自动回到待处理。</p>
      <textarea v-model="supp" maxlength="200" placeholder="补充你能提供的具体信息"></textarea>
      <button type="button" :disabled="supplementing" @click="submitSupp">{{ supplementing ? '提交中…' : '提交补充' }}</button>
      <div v-if="supplementMsg" class="nd-phone-msg">{{ supplementMsg }}</div>
    </div>
    <div v-else-if="notice.claimStatus === 'need_more'" class="nd-exchange-tip">已请帮忙人补充说明，等对方提交后会自动回到待处理。</div>
    <div class="nd-kv" style="margin-top:8px"><span>发布者手机号</span><b>{{ notice.helpPhonesHidden ? '双方同意不公开' : (notice.ownerContact || (notice.item?.contact?.phone ? '已留手机号（通过后显示完整）' : '还没留手机号')) }}</b></div>
    <div class="nd-kv"><span>帮忙人手机号</span><b>{{ notice.helpPhonesHidden ? '双方同意不公开' : (notice.item?.isMine ? (notice.claimContact || '还没留手机号') : (notice.claimContact ? '已留手机号' : '还没留手机号')) }}</b></div>
    <div v-if="notice.item?.isMine && !notice.ownerContact && !notice.item?.contact?.phone && !notice.helpPhonesHidden" class="nd-phone-fill">
      <p>你是发布者。留手机号后，接受帮忙时双方才能互相联系。</p>
      <div class="nd-phone-row"><input v-model="phone" maxlength="20" placeholder="补充你的手机号"><button type="button" :disabled="phoneSaving" @click="submitPhone">{{ phoneSaving ? '保存中…' : '补充手机号' }}</button></div>
    </div>
    <div v-if="notice.isClaimant && !notice.claimContact && !notice.helpPhonesHidden" class="nd-phone-fill">
      <p>你还没有预留手机号，发布者无法接受帮忙，也无法公布双方手机号。</p>
      <div class="nd-phone-row"><input v-model="phone" maxlength="20" placeholder="补充你的手机号"><button type="button" :disabled="phoneSaving" @click="submitPhone">{{ phoneSaving ? '保存中…' : '补充手机号' }}</button></div>
    </div>
    <div v-if="notice.helpPhonesHidden" class="nd-exchange-tip">双方已同意不公开手机号，可通过匿名沟通完成捐赠。</div>
    <div v-else-if="(notice.claimStatus === 'accepted' || notice.claimStatus === 'completed') && notice.claimContact && (notice.ownerContact || notice.item?.contact?.phone)" class="nd-exchange-ok">双方已公布手机号，可以直接联系。</div>
    <div v-else-if="notice.claimStatus === 'accepted' || notice.claimStatus === 'completed'" class="nd-exchange-tip" style="color:#A23B2A">帮忙人还没有预留手机号，双方手机号尚未交换。</div>
    <div v-if="phoneMsg" class="nd-phone-msg">{{ phoneMsg }}</div>
    <div v-if="!notice.helpIsDonation" class="nd-ask-prompt"><b>沟通提示</b><span>如果需要进一步约定，建议在合适时通过电话或微信联系；本分类暂不开放匿名沟通。</span></div>
    <slot name="chat" />
  </div>
  <div class="nd-actions">
    <template v-if="(notice.isPublisher || notice.item?.isMine) && notice.claimId && ['pending','need_more'].includes(notice.claimStatus)">
      <button type="button" class="btn" @click="$emit('help-action', 'accepted')">接受并公布双方手机号</button>
      <button type="button" class="btn ghost" :disabled="notice.claimStatus === 'need_more'" @click="$emit('help-action', 'need_more')">{{ notice.claimStatus === 'need_more' ? '已请求补充' : '请补充' }}</button>
      <button type="button" class="btn ghost" @click="requestReject">婉拒</button>
      <button v-if="notice.canBlockClaim" type="button" class="btn ghost" @click="requestBlock">屏蔽对方</button>
    </template>
    <button v-if="(notice.isPublisher || notice.item?.isMine) && notice.claimId && notice.claimStatus === 'accepted'" type="button" class="btn" @click="$emit('complete')">完成帮助</button>
    <button v-if="(notice.isPublisher || notice.item?.isMine) && notice.claimId && notice.claimStatus === 'accepted'" type="button" class="btn ghost" @click="requestRemove">结束与 TA 的沟通</button>
    <button v-if="(notice.isPublisher || notice.item?.isMine) && ['rejected','removed'].includes(notice.claimStatus)" type="button" class="btn ghost" @click="requestRestore">拉回申请</button>
    <button v-if="notice.claimBlockedByMe" type="button" class="btn ghost" @click="$emit('unblock')">解除屏蔽</button>
    <button v-if="notice.isClaimant && notice.claimId && ['pending','accepted'].includes(notice.claimStatus)" type="button" class="btn ghost" @click="requestWithdraw">撤回申请</button>
    <button v-if="notice.item" type="button" class="btn ghost" @click="$emit('compare')">查看匹配报告</button>
    <button type="button" class="btn ghost" @click="$emit('ignore')">忽略</button>
  </div>
</template>

<style src="../styles/notice-branch.css"></style>
<style scoped>
.nd-phone-fill textarea { width:100%; box-sizing:border-box; min-height:58px; background:#fff; border:1px solid #E4D6F2; border-radius:8px; padding:8px; font-family:inherit; font-size:9.5px; }
.nd-phone-fill > button { margin-top:6px; width:100%; border:0; background:#5B2A91; color:#fff; border-radius:8px; padding:8px; font-family:inherit; font-size:9.5px; }
</style>
<style scoped>
.nd-ask-prompt { margin-top:8px; padding:8px 9px; border-radius:8px; background:#F8F4FD; border:1px solid #EADFF5; display:flex; flex-direction:column; gap:3px; }
.nd-ask-prompt b { font-size:9px; color:#5B2A91; }
.nd-ask-prompt span { font-size:9px; line-height:1.6; color:#4E445D; }
</style>
<style scoped>
.nd-privacy-actions { display:flex; gap:6px; margin-top:6px; }
.nd-privacy-actions button { border:0; background:#5B2A91; color:#fff; border-radius:7px; padding:6px 9px; font-family:inherit; font-size:9px; }
.nd-privacy-actions button.ghost { background:#F1E8FB; color:#5B2A91; }
</style>

<script setup>
import { ref, watch } from 'vue'
import ImageViewer from './ImageViewer.vue'
import { compressImage } from '../utils/image'
const props = defineProps({
  notice: { type: Object, required: true },
  imageBusy: { type: Boolean, default: false },
  imageError: { type: String, default: '' }
})
const emit = defineEmits(['claim-action', 'reveal', 'block', 'compare', 'ignore', 'supplement', 'supplement-image', 'pickup-code', 'restore', 'unblock', 'end-talk', 'finish-talk'])
const supp = ref('')
const imageMsg = ref('')
const imagePreview = ref('')
const uploading = ref(false)
const viewerUrl = ref('')
watch(() => props.imageError, (v) => {
  if (v) {
    uploading.value = false
    imageMsg.value = '上传失败，可以重新点“确认上传”'
  }
})
watch(() => [props.notice.claimStatus, props.notice.claimNeedImage], ([status]) => {
  if (status === 'need_more') {
    imagePreview.value = ''
    imageMsg.value = ''
    uploading.value = false
  }
})
function requestReject() {
  if (window.confirm('确定拒绝这条认领申请吗？拒绝后可以在已拒绝状态点“拉回申请”恢复。')) {
    emit('claim-action', 'rejected')
  }
}
function requestBlock() {
  if (window.confirm('确定屏蔽对方吗？屏蔽后双方不能再互发消息。')) {
    emit('block')
  }
}
function requestRestore() {
  if (window.confirm('确定把这条已拒绝的申请拉回来吗？')) {
    emit('restore')
  }
}
function requestEndTalk() {
  if (window.confirm('确定撤回这条申请吗？撤回后物品会回到发布中，其他申请仍然保留。')) {
    emit('end-talk')
  }
}
function requestFinishTalk() {
  if (window.confirm('确定结束本次认领吗？结束后不能恢复，也不会回到发布中。如果物品不是你的，请重新发布一条失物招领。')) {
    emit('finish-talk')
  }
}
function submitSupp() {
  const text = supp.value.trim()
  if (text.length < 2) return
  emit('supplement', text)
  supp.value = ''
}
function openImage() {
  const url = imagePreview.value || props.notice.claimImage
  if (url) viewerUrl.value = url
}
async function onImage(e) {
  const file = e.target.files && e.target.files[0]
  if (!file) return
  if (!/^image\//.test(file.type)) { imageMsg.value = '请选择图片文件'; return }
  try {
    imageMsg.value = '正在压缩图片…'
    const compressed = await compressImage(file)
    imagePreview.value = compressed
    imageMsg.value = '已压缩，请点“确认上传”'
    uploading.value = false
  } catch (err) {
    imageMsg.value = err.message || '图片读取失败'
  }
  e.target.value = ''
}
function submitImage() {
  if (!imagePreview.value || uploading.value || props.imageBusy) return
  uploading.value = true
  imageMsg.value = '正在审核并上传，请稍候…'
  emit('supplement-image', imagePreview.value)
}
function time(ts) {
  if (!ts) return ''
  const d = new Date(Number(ts) || 0)
  if (!Number.isFinite(d.getTime())) return ''
  return `${d.getMonth() + 1}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}
function statusText(s) {
  return ({ pending: '待处理', accepted: '已通过', completed: '已完成', rejected: '已拒绝', need_more: '待补充' })[s] || s || ''
}
function reviewText(r) {
  if (!r || !r.safe) return ''
  const pct = Math.round(Number(r.confidence || 0) * 100)
  return `图片审核：通过 · ${r.category || '无'} · ${pct}%${r.reason ? ' · ' + r.reason : ''}`
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
    <div v-if="notice.claimPickupCode" class="nd-pickup-code">取件码：<b>{{ notice.claimPickupCode }}</b><span>双方核对后交接</span></div>
    <button v-if="notice.canGeneratePickupCode" type="button" class="btn ghost" style="margin-top:8px" @click="$emit('pickup-code')">生成取件码</button>
    <div v-if="notice.claimImage" style="margin-top:8px">
      <img :src="notice.claimImage" alt="补充图片" title="双击查看大图" style="max-width:100%;max-height:220px;border-radius:9px;border:1px solid #EADFF5;cursor:zoom-in" @dblclick="openImage">
      <div v-if="reviewText(notice.claimImageReview)" class="nd-review">{{ reviewText(notice.claimImageReview) }}</div>
    </div>
    <div v-if="notice.isClaimant && notice.claimStatus === 'need_more'" class="nd-phone-fill upload-box">
      <p>辛苦你上传一张物品照片，方便发布者核对，谢谢配合。</p>
      <p class="upload-tip">建议选择 2MB 以内的 JPG / PNG 照片，系统会自动压缩，不用手动处理。</p>
      <label class="upload-pick">
        <input type="file" accept="image/*" @change="onImage">
        <span>{{ uploading ? '正在上传…' : '选择照片' }}</span>
      </label>
      <div v-if="imagePreview" style="margin-top:7px">
        <img :src="imagePreview" alt="预览" title="双击查看大图" style="max-width:100%;max-height:160px;border-radius:8px;border:1px solid #EADFF5;cursor:zoom-in" @dblclick="openImage">
      </div>
      <button v-if="imagePreview" type="button" class="btn" style="margin-top:7px;width:100%" :disabled="imageBusy || uploading" @click="submitImage">{{ imageBusy || uploading ? '审核上传中…' : '确认上传' }}</button>
      <div v-if="imageMsg" class="nd-phone-msg">{{ imageMsg }}</div>
      <div v-if="imageError" class="nd-send-error">{{ imageError }}</div>
    </div>
  <slot name="chat" />
  <div class="nd-actions">
    <template v-if="(notice.isPublisher || notice.item?.isMine) && notice.claimId && (!notice.claimStatus || ['pending','need_more'].includes(notice.claimStatus))">
      <button type="button" class="btn" @click="$emit('claim-action', 'accepted')">确认与 TA 沟通并公布手机号</button>
      <button type="button" class="btn ghost" :disabled="notice.claimStatus === 'need_more'" @click="$emit('claim-action', 'need_more', true)">{{ notice.claimStatus === 'need_more' ? '已请求补充图片' : '请补充图片' }}</button>
      <button type="button" class="btn ghost" @click="requestReject">拒绝</button>
      <button v-if="notice.canBlockClaim" type="button" class="btn ghost" @click="requestBlock">屏蔽对方</button>
    </template>
    <button v-if="(notice.isPublisher || notice.item?.isMine) && notice.claimStatus === 'rejected'" type="button" class="btn ghost" @click="requestRestore">拉回申请</button>
    <button v-if="(notice.isPublisher || notice.item?.isMine) && notice.claimStatus === 'accepted'" type="button" class="btn ghost" @click="requestFinishTalk">结束本次认领</button>
    <div v-if="notice.claimStatus === 'accepted'" class="nd-exchange-tip">线下见面发现物品不是你的？请结束本次认领后重新发布。进入沟通后不能单方面取消回到发布中。</div>
    <div v-if="(notice.isPublisher || notice.item?.isMine) && ['pending','need_more'].includes(notice.claimStatus)" class="nd-exchange-tip">确认与其中一人沟通后，其他人暂时不能继续沟通；结束后物品会回到发布中，可以重新选择。</div>
    <button v-if="notice.isClaimant && notice.claimStatus === 'pending'" type="button" class="btn ghost" @click="requestEndTalk">撤回申请</button>
    <button v-if="notice.isClaimant && notice.claimStatus === 'accepted'" type="button" class="btn ghost" @click="requestFinishTalk">结束本次认领</button>
    <button v-if="notice.claimBlockedByMe" type="button" class="btn ghost" @click="$emit('unblock')">解除屏蔽</button>
    <button v-if="notice.item" type="button" class="btn ghost" @click="$emit('compare')">查看匹配报告</button>
    <button type="button" class="btn ghost" @click="$emit('ignore')">忽略</button>
  </div>
  <ImageViewer :src="viewerUrl" @close="viewerUrl = ''" />
</template>

<style src="../styles/notice-branch.css"></style>
<style scoped>
.nd-phone-fill textarea { width:100%; box-sizing:border-box; min-height:58px; background:#fff; border:1px solid #E4D6F2; border-radius:8px; padding:8px; font-family:inherit; font-size:9.5px; }
.nd-phone-fill > button { margin-top:6px; width:100%; border:0; background:#5B2A91; color:#fff; border-radius:8px; padding:8px; font-family:inherit; font-size:9.5px; }
</style>
<style scoped>
.upload-box { text-align:center; }
.upload-pick { display:inline-flex; align-items:center; justify-content:center; min-width:130px; padding:9px 14px; border-radius:9px; background:#5B2A91; color:#fff; font-size:10px; cursor:pointer; }
.upload-pick input { display:none; }
</style>
<style scoped>
.upload-tip { font-size:8px; color:#8E7FA3; margin:2px 0 7px; line-height:1.6; }
</style>

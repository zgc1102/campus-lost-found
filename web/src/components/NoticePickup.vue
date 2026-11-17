<script setup>
import { ref } from 'vue'
import ImageViewer from './ImageViewer.vue'
import { compressImage } from '../utils/image'
const props = defineProps({ notice: { type: Object, required: true } })
const emit = defineEmits(['reveal', 'publish', 'block', 'close', 'ignore', 'request-photo', 'supplement-photo', 'reopen', 'unblock'])
const viewerUrl = ref('')
const photoPreview = ref('')
const photoMsg = ref('')
const uploading = ref(false)
function requestBlock() {
  if (window.confirm('确定屏蔽这位捡到者吗？屏蔽后双方不能再沟通。')) emit('block')
}
function requestClose() {
  if (window.confirm('确定关闭这次拾光码上报吗？关闭后可以重新打开。')) emit('close')
}
function requestReopen() {
  if (window.confirm('确定重新打开这次上报吗？')) emit('reopen')
}
async function onPhoto(e) {
  const file = e.target.files && e.target.files[0]
  if (!file) return
  if (!/^image\//.test(file.type)) { photoMsg.value = '请选择图片文件'; return }
  try {
    photoMsg.value = '正在压缩图片…'
    photoPreview.value = await compressImage(file)
    photoMsg.value = '已压缩，请点“确认上传”'
    uploading.value = false
  } catch (err) {
    photoMsg.value = err.message || '图片读取失败'
  }
  e.target.value = ''
}
function submitPhoto() {
  if (!photoPreview.value || uploading.value) return
  uploading.value = true
  photoMsg.value = '正在审核并上传，请稍候…'
  emit('supplement-photo', photoPreview.value)
}
function time(ts) {
  if (!ts) return ''
  const d = new Date(Number(ts) || 0)
  if (!Number.isFinite(d.getTime())) return ''
  return `${d.getMonth() + 1}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}
function openPhoto() {
  if (props.notice.report?.photo) viewerUrl.value = props.notice.report.photo
}
function reviewText(r) {
  if (!r || !r.safe) return ''
  const pct = Math.round(Number(r.confidence || 0) * 100)
  return `图片审核：通过 · ${r.category || '无'} · ${pct}%${r.reason ? ' · ' + r.reason : ''}`
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
      <div v-if="reviewText(notice.report.photoReview)" class="nd-review">{{ reviewText(notice.report.photoReview) }}</div>
    </div>
    <div v-if="notice.isReportFinder && notice.report?.needPhoto" class="nd-phone-fill upload-box">
      <p>失主想请你补充一张物品照片，辛苦上传，谢谢配合。</p>
      <p class="upload-tip">建议选择 2MB 以内的 JPG / PNG，系统会自动压缩。</p>
      <label class="upload-pick">
        <input type="file" accept="image/*" @change="onPhoto">
        <span>{{ uploading ? '正在上传…' : '选择照片' }}</span>
      </label>
      <div v-if="photoPreview" style="margin-top:7px">
        <img :src="photoPreview" alt="预览" style="max-width:100%;max-height:160px;border-radius:8px;border:1px solid #EADFF5">
      </div>
      <button v-if="photoPreview" type="button" class="btn" style="margin-top:7px;width:100%" :disabled="uploading" @click="submitPhoto">{{ uploading ? '审核上传中…' : '确认上传' }}</button>
      <div v-if="photoMsg" class="nd-phone-msg">{{ photoMsg }}</div>
    </div>
    <div v-if="notice.report?.phoneRevealed" class="nd-kv"><span>我的手机号</span><b>{{ notice.report?.ownerContact || '未留手机号' }}</b></div>
    <div v-if="notice.report?.phoneRevealed" class="nd-kv"><span>捡到者手机号</span><b>{{ notice.report?.contact || '未留手机号' }}</b></div>
  </div>
  <slot name="chat" />
  <div class="nd-actions">
    <template v-if="notice.isReportOwner">
      <button v-if="!notice.report?.phoneRevealed" type="button" class="btn" @click="$emit('reveal')">公布双方手机号并联系</button>
      <button v-if="notice.report?.status !== 'closed'" type="button" class="btn ghost" :disabled="notice.report?.needPhoto" @click="$emit('request-photo')">{{ notice.report?.needPhoto ? '已请求补充照片' : '请对方补充照片' }}</button>
      <button type="button" class="btn ghost" @click="requestBlock">屏蔽</button>
      <button v-if="notice.report?.blockedByMe" type="button" class="btn ghost" @click="$emit('unblock')">解除屏蔽</button>
      <button v-if="notice.report?.status !== 'closed'" type="button" class="btn ghost" @click="requestClose">关闭</button>
      <button v-if="notice.report?.status === 'closed'" type="button" class="btn ghost" @click="requestReopen">重新打开</button>
    </template>
    <button type="button" class="btn ghost" @click="$emit('ignore')">忽略</button>
  </div>
  <ImageViewer :src="viewerUrl" @close="viewerUrl = ''" />
</template>

<style src="../styles/notice-branch.css"></style>
<style scoped>
.upload-box { text-align:center; }
.upload-pick { display:inline-flex; align-items:center; justify-content:center; min-width:130px; padding:9px 14px; border-radius:9px; background:#5B2A91; color:#fff; font-size:10px; cursor:pointer; }
.upload-pick input { display:none; }
.upload-tip { font-size:8px; color:#8E7FA3; margin:2px 0 7px; line-height:1.6; }
</style>

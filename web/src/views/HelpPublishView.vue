<script setup>
import { computed, reactive, ref } from 'vue'
import { api } from '../api'

const props = defineProps({
  helpCat: { type: String, default: 'help_borrow' },
  editItem: { type: Object, default: null }
})
const emit = defineEmits(['nav'])

const cats = [
  {
    id: 'help_borrow', name: '借用工具', sub: '借伞、充电宝、工具',
    svg: '<svg viewBox="0 0 80 80" fill="none"><path d="M12 40a28 28 0 0 1 56 0H12Z" fill="#8A52C7"/><path d="M12 40c8-8 14-8 20 0 6-8 12-8 20 0 6-8 12-8 16 0" stroke="#C8A96A" stroke-width="3" stroke-linecap="round"/><path d="M40 40v20a8 8 0 0 0 16 0" stroke="#3B1D63" stroke-width="4" stroke-linecap="round"/><circle cx="24" cy="62" r="5" fill="#E8DCF7"/></svg>'
  },
  {
    id: 'help_errand', name: '代办跑腿', sub: '帮取、帮带、帮买',
    svg: '<svg viewBox="0 0 80 80" fill="none"><rect x="18" y="28" width="32" height="32" rx="6" fill="#E8B4A0"/><path d="M24 28v-6h20v6" stroke="#8A4A33" stroke-width="4" stroke-linecap="round"/><path d="M50 38h9l7 10v10H52V38Z" fill="#C8A96A"/><circle cx="26" cy="64" r="5" fill="#5B2A91"/><circle cx="54" cy="64" r="5" fill="#5B2A91"/><path d="M26 48h14M26 54h9" stroke="#8A4A33" stroke-width="2.5" stroke-linecap="round"/></svg>'
  },
  {
    id: 'help_donate', name: '爱心捐赠', sub: '闲置物品送人',
    svg: '<svg viewBox="0 0 80 80" fill="none"><rect x="16" y="30" width="48" height="34" rx="5" fill="#E8B4A0"/><rect x="16" y="24" width="48" height="12" rx="4" fill="#C8A96A"/><rect x="36" y="24" width="8" height="40" fill="#FFF4E8"/><path d="M40 50s-9-5.4-9-10a5 5 0 0 1 9-2 5 5 0 0 1 9 2c0 4.6-9 10-9 10Z" fill="#B85A3C"/></svg>'
  },
  {
    id: 'help_volunteer', name: '志愿帮忙', sub: '找人搭把手',
    svg: '<svg viewBox="0 0 80 80" fill="none"><path d="M14 54c0-12 12-20 26-20s26 8 26 20" fill="#C9A7F0"/><path d="M40 46s-11-6.5-11-12a6 6 0 0 1 11-2 6 6 0 0 1 11 2c0 5.5-11 12-11 12Z" fill="#8A52C7"/><path d="M18 58l-8 10M62 58l8 10" stroke="#5B2A91" stroke-width="4" stroke-linecap="round"/></svg>'
  }
]
const meta = {
  help_borrow: { lead: '借用工具：写清借什么、用多久、怎么还。', title: '例如：想借一把雨伞', desc: '借什么、用多久、在哪里取还，写清楚更容易有人帮。' },
  help_errand: { lead: '代办跑腿：写清取什么、送到哪、什么时候。', title: '例如：帮取一个快递', desc: '取件地点、送达地点、时间要求，以及是否需要付费。' },
  help_donate: { lead: '爱心捐赠：写清物品状态、能不能自取。', title: '例如：送一个闲置台灯', desc: '物品新旧、功能是否正常、在哪里自取，最好附一张照片。' },
  help_volunteer: { lead: '志愿帮忙：写清需要什么帮助、什么时候。', title: '例如：想找人帮忙搬行李', desc: '需要几个人、大概多久、在哪里集合。' }
}
const active = ref(props.helpCat || 'help_borrow')
const form = reactive({ title: '', desc: '', place: '', phone: '' })
const photo = ref('')
const submitting = ref(false)
const error = ref('')
const fileInput = ref(null)
if (props.editItem) {
  const e = props.editItem
  active.value = e.cat || e.helpCat || props.helpCat
  form.title = e.title || ''
  form.desc = e.desc || ''
  form.place = e.place || ''
  form.phone = (e.contact && e.contact.phone) || ''
  photo.value = e.photoUrl || e.photo || ''
}
const current = computed(() => cats.find((c) => c.id === active.value) || cats[0])
const currentMeta = computed(() => meta[active.value] || meta.help_borrow)

function onPhoto(e) {
  const file = e.target.files && e.target.files[0]
  if (!file) return
  const r = new FileReader()
  r.onload = () => {
    const img = new Image()
    img.onload = () => {
      const max = 1200
      const s = Math.min(1, max / Math.max(img.width, img.height))
      const c = document.createElement('canvas')
      c.width = Math.round(img.width * s)
      c.height = Math.round(img.height * s)
      c.getContext('2d').drawImage(img, 0, 0, c.width, c.height)
      photo.value = c.toDataURL('image/jpeg', 0.82)
    }
    img.src = r.result
  }
  r.readAsDataURL(file)
}

async function submit() {
  error.value = ''
  if (form.title.trim().length < 2) { error.value = '写一句标题'; return }
  if (form.desc.trim().length < 5) { error.value = '具体说明再写清楚一点'; return }
  submitting.value = true
  try {
    const payload = {
      type: 'help',
      cat: active.value,
      helpCat: active.value,
      title: form.title.trim(),
      desc: form.desc.trim(),
      place: form.place.trim() || '未填写地点',
      contact: { phone: form.phone.trim() },
      photo: photo.value || null
    }
    const saved = props.editItem
      ? await api.update(props.editItem.id, payload)
      : await api.create(payload)
    try { sessionStorage.setItem('sg:lastResult', JSON.stringify(saved)) } catch (e) {}
    emit('nav', 'success')
  } catch (e) {
    error.value = e.message || '发布失败'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div id="helpSheet" class="sheet help-screen show">
    <div class="hp-top">
      <button type="button" class="hp-back" aria-label="返回" @click="$emit('nav', 'help')">‹</button>
      <div class="hp-title"><b>发布爱心求助</b><span>写清楚，附近的人更容易看到</span></div>
    </div>
    <div class="hp-steps"><span class="on">1 选方向</span><i></i><span>2 写清楚</span><i></i><span>3 发布</span></div>
    <div class="hp-body">
      <div class="hp-lead">{{ currentMeta.lead }}</div>
      <div class="hp-cats">
        <button v-for="c in cats" :key="c.id" type="button" class="hp-cat" :class="{ on: active === c.id }" @click="active = c.id">
          <span class="hc-ic" v-html="c.svg"></span>
          <div><b>{{ c.name }}</b><span>{{ c.sub }}</span></div>
        </button>
      </div>

      <div class="hp-sec">
        <label>一句话标题</label>
        <input v-model="form.title" maxlength="30" :placeholder="currentMeta.title">
      </div>
      <div class="hp-sec">
        <label>具体说明</label>
        <textarea v-model="form.desc" maxlength="200" :placeholder="currentMeta.desc"></textarea>
      </div>
      <div class="hp-sec">
        <label>地点与联系方式</label>
        <div class="hp-row">
          <input v-model="form.place" maxlength="40" placeholder="地点，例如：紫荆 15 号楼">
          <input v-model="form.phone" maxlength="20" placeholder="手机 / 微信（会打码）">
        </div>
        <div class="tip-small">手机号会在列表里脱敏显示；对方确认后再给完整联系方式。</div>
      </div>
      <div class="hp-sec">
        <label>照片（选填）</label>
        <label class="hp-photo" @click.prevent="fileInput && fileInput.click()">点击上传一张照片，方便对方判断</label>
        <input ref="fileInput" type="file" accept="image/*" style="display:none" @change="onPhoto">
        <img v-if="photo" :src="photo" alt="" style="width:100%;max-height:180px;object-fit:cover;border-radius:11px;margin-top:8px">
      </div>
    </div>
    <div class="hp-note">AI 整理仅作参考，实际以现场和校方失物招领点为准。</div>
    <div v-if="error" class="tip-small" style="color:#c0392b;padding:0 16px">{{ error }}</div>
    <div class="hp-submit"><button class="btn" type="button" :disabled="submitting" @click="submit">{{ submitting ? '发布中…' : '发布求助' }}</button></div>
  </div>
</template>

<style scoped>
.hp-sec label { font-size: 12.5px; font-weight: 600; }
.hp-sec input, .hp-sec textarea { font-size: 13px !important; }
.hp-lead { font-size: 12.5px; line-height: 1.7; }
.hp-cat b { font-size: 13px !important; }
.hp-cat div span { font-size: 10.5px !important; }
.hp-cat .hc-ic svg { width: 38px; height: 38px; }
.hp-note { font-size: 10.5px; }
.hp-submit .btn { font-size: 14px; }
</style>


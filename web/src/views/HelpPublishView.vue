<script setup>
import { computed, reactive, ref } from 'vue'
import { api } from '../api'

const props = defineProps({ helpCat: { type: String, default: 'help_borrow' } })
const emit = defineEmits(['nav'])

const cats = [
  { id: 'help_borrow', name: '借用工具', sub: '借伞、充电宝、工具', icon: '🛠️' },
  { id: 'help_errand', name: '代办跑腿', sub: '帮取、帮带、帮买', icon: '🏃' },
  { id: 'help_donate', name: '爱心捐赠', sub: '闲置物品送人', icon: '🎁' },
  { id: 'help_volunteer', name: '志愿帮忙', sub: '找人搭把手', icon: '🤝' }
]
const active = ref(props.helpCat || 'help_borrow')
const form = reactive({ title: '', desc: '', place: '', phone: '' })
const photo = ref('')
const submitting = ref(false)
const error = ref('')
const fileInput = ref(null)
const current = computed(() => cats.find((c) => c.id === active.value) || cats[0])

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
    const saved = await api.create({
      type: 'help',
      cat: active.value,
      helpCat: active.value,
      title: form.title.trim(),
      desc: form.desc.trim(),
      place: form.place.trim() || '未填写地点',
      contact: { phone: form.phone.trim() },
      photo: photo.value || null
    })
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
      <div class="hp-lead">先选一个方向，再把时间、地点说清楚。</div>
      <div class="hp-cats">
        <button v-for="c in cats" :key="c.id" type="button" class="hp-cat" :class="{ on: active === c.id }" @click="active = c.id">
          <span class="hc-ic">{{ c.icon }}</span>
          <div><b>{{ c.name }}</b><span>{{ c.sub }}</span></div>
        </button>
      </div>
      <select v-model="active" style="width:100%;box-sizing:border-box;background:#F8F4FD;border:1px solid #EDE3F8;border-radius:10px;padding:10px;font-family:inherit;font-size:12px;margin-bottom:10px">
        <option v-for="c in cats" :key="c.id" :value="c.id">{{ c.name }}</option>
      </select>

      <div class="hp-sec">
        <label>一句话标题</label>
        <input v-model="form.title" maxlength="30" placeholder="例如：想借一把雨伞">
      </div>
      <div class="hp-sec">
        <label>具体说明</label>
        <textarea v-model="form.desc" maxlength="200" placeholder="时间、地点、用途，越具体越容易有人帮"></textarea>
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

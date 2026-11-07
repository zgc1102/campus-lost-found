<script setup>
import { computed, reactive, ref } from 'vue'
import { api } from '../api'

const props = defineProps({
  type: { type: String, default: 'lost' },
  helpCat: { type: String, default: 'help_borrow' }
})
const emit = defineEmits(['nav'])

const kind = ref(props.type)
const helpCatLocal = ref(props.helpCat)
const isHelp = computed(() => kind.value === 'help')
const helpCats = [
  { id: 'help_borrow', name: '借用工具' },
  { id: 'help_errand', name: '代办跑腿' },
  { id: 'help_donate', name: '爱心捐赠' },
  { id: 'help_volunteer', name: '志愿帮忙' }
]
const form = reactive({
  title: '',
  desc: '',
  place: '',
  eventTime: '',
  secret: '',
  phone: ''
})
const submitting = ref(false)
const result = ref(null)
const error = ref('')
const photo = ref('')
const visionState = ref('')

function onPhoto(e) {
  const file = e.target.files && e.target.files[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = () => {
    const img = new Image()
    img.onload = () => {
      const max = 1200
      const scale = Math.min(1, max / Math.max(img.width, img.height))
      const canvas = document.createElement('canvas')
      canvas.width = Math.round(img.width * scale)
      canvas.height = Math.round(img.height * scale)
      canvas.getContext('2d').drawImage(img, 0, 0, canvas.width, canvas.height)
      photo.value = canvas.toDataURL('image/jpeg', 0.82)
      analyzePhoto()
    }
    img.src = reader.result
  }
  reader.readAsDataURL(file)
}

async function analyzePhoto() {
  if (!photo.value) return
  visionState.value = 'AI 正在识别照片…'
  try {
    const d = await api.vision(photo.value)
    if (d && d.ok !== false) {
      const bits = [d.category, d.color, d.desc].filter(Boolean)
      if (!form.title.trim() && d.category) form.title = String(d.category).slice(0, 30)
      if (!form.desc.trim() && bits.length) form.desc = bits.join('，').slice(0, 200)
      visionState.value = 'AI 识别：' + (bits.join(' · ') || '已识别')
    } else {
      visionState.value = ''
    }
  } catch (e) {
    visionState.value = ''
  }
}

const typeLabel = computed(() => isHelp.value ? '爱心求助' : (kind.value === 'lost' ? '寻物启事' : '失物招领'))
const helpName = computed(() => ({
  help_borrow: '借用工具',
  help_errand: '代办跑腿',
  help_donate: '爱心捐赠',
  help_volunteer: '志愿帮忙'
}[helpCatLocal.value] || '爱心求助'))

async function submit() {
  error.value = ''
  if (form.title.trim().length < 2) { error.value = '标题至少写两个字'; return }
  if (form.desc.trim().length < 5) { error.value = '说明再具体一点，至少 5 个字'; return }
  submitting.value = true
  try {
    const item = {
      type: isHelp.value ? 'help' : kind.value,
      cat: isHelp.value ? helpCatLocal.value : 'other',
      helpCat: isHelp.value ? helpCatLocal.value : '',
      title: form.title.trim(),
      desc: form.desc.trim(),
      place: form.place.trim() || '未填写地点',
      eventTime: form.eventTime || '',
      secret: form.secret.trim(),
      contact: { phone: form.phone.trim() },
      photo: photo.value || null
    }
    const saved = await api.create(item)
    result.value = saved
    try { sessionStorage.setItem('sg:lastResult', JSON.stringify(saved)) } catch (e) {}
    emit('nav', 'success')
  } catch (e) {
    error.value = e.message || '提交失败，请稍后再试'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <section class="screen active" id="screen-publish">
    <div class="topbar">
      <div class="back" @click="$emit('nav', isHelp ? 'help' : kind)">‹</div>
      <div class="t">{{ isHelp ? '发布爱心求助' : '发布启事' }}</div>
    </div>

    <div class="scroll">
      <div class="pub-head">
        <div class="ph-t">{{ isHelp ? '发布一条爱心求助' : '发布一条启事' }}</div>
        <div class="ph-s">{{ isHelp ? helpName : (kind === 'lost' ? '寻物启事 · 丢了东西' : '失物招领 · 捡到东西') }}</div>
        <div class="ph-steps"><span>1 填写</span><span>2 AI 审核</span><span>3 上架</span></div>
      </div>

      <div class="type-tab" style="margin-bottom:10px">
        <button type="button" :class="{ active: kind === 'lost' }" @click="kind = 'lost'">寻物启事</button>
        <button type="button" :class="{ active: kind === 'found' }" @click="kind = 'found'">失物招领</button>
        <button type="button" :class="{ active: kind === 'help' }" @click="kind = 'help'">爱心求助</button>
      </div>

      <div v-if="isHelp" class="help-picker">
        <button v-for="c in helpCats" :key="c.id" type="button" :class="{ on: helpCatLocal === c.id }" @click="helpCatLocal = c.id">{{ c.name }}</button>
      </div>

      <div v-if="result" class="okpanel" style="margin-top:14px">
        <div class="big">✓</div>
        <h2>{{ result.status === 'approved' ? '已发布成功' : result.status === 'rejected' ? '内容被拦截' : '已提交，等待审核' }}</h2>
        <p>{{ result.rejectReason || 'AI 会先审核文字和图片，通过后其他同学才能看到。' }}</p>
        <button type="button" class="btn" style="width:100%" @click="$emit('nav', isHelp ? 'help' : kind)">返回列表</button>
      </div>

      <template v-else>
        <div v-if="isHelp" class="form-card">
          <div class="fc-title">求助方向</div>
          <div class="sa" style="padding:10px 0">{{ helpName }} · 写清时间、地点、用途，越具体越容易有人帮。</div>
        </div>

        <div class="form-card">
          <div class="fc-title"><span>01</span>基本信息</div>
          <div class="form-item">
            <label>标题</label>
            <input v-model="form.title" maxlength="30" :placeholder="isHelp ? '例如：想借一把雨伞' : '例如：白色有线耳机'">
          </div>
          <div class="form-item">
            <label>详细说明</label>
            <textarea v-model="form.desc" maxlength="200" :placeholder="isHelp ? '说明需求、时间和地点' : '颜色、划痕、标记……越具体越容易核对'"></textarea>
          </div>
          <div class="form-item">
            <label>地点</label>
            <input v-model="form.place" maxlength="40" placeholder="例如：图书馆三楼">
          </div>
          <div v-if="!isHelp" class="form-item">
            <label>丢失时间</label>
            <input v-model="form.eventTime" type="datetime-local">
          </div>
          <div class="form-item">
            <label>联系方式</label>
            <input v-model="form.phone" maxlength="20" placeholder="手机 / 微信（公开展示会打码）">
          </div>
          <div v-if="!isHelp" class="form-item">
            <label>独有特征（仅用于核验）</label>
            <input v-model="form.secret" maxlength="80" placeholder="不会公开展示，只用于认领核验">
          </div>
          <div class="form-item">
            <label>照片（选填）</label>
            <input type="file" accept="image/*" @change="onPhoto">
            <img v-if="photo" :src="photo" alt="预览" style="width:100%;max-height:180px;object-fit:cover;border-radius:10px;margin-top:8px">
            <div v-if="visionState" class="sa" style="margin-top:5px">{{ visionState }}</div>
          </div>
        </div>

        <div v-if="error" class="warn-box" style="margin-bottom:10px">{{ error }}</div>

        <button type="button" class="submit-btn" :disabled="submitting" @click="submit">
          {{ submitting ? '提交中…' : '提交发布 · AI 先审核' }}
        </button>
        <div class="pub-note">提交后先审文字和图片，通过后同学才能看到；AI 匹配仅供参考，实际以现场和校方失物招领点为准</div>
      </template>
    </div>
  </section>
</template>

<style>
.form-card .form-item {
  margin: 12px 0;
}
.form-card .form-item label {
  display: block;
  font-size: 11px;
  font-weight: 600;
  color: #4E445D;
  margin-bottom: 6px;
}
.form-card .form-item input,
.form-card .form-item textarea {
  width: 100%;
  box-sizing: border-box;
  background: #F8F4FD;
  border: 1px solid #EDE3F8;
  border-radius: 11px;
  padding: 10px 11px;
  font-family: inherit;
  font-size: 12px;
  color: #241C2E;
  outline: none;
}
.form-card .form-item textarea {
  min-height: 92px;
  resize: vertical;
  line-height: 1.65;
}
.form-card .form-item input:focus,
.form-card .form-item textarea:focus {
  background: #fff;
  border-color: #7A3CB0;
}
.pub-note {
  font-size: 9px;
  line-height: 1.6;
  color: #A99BB9;
  text-align: center;
  padding: 4px 8px 20px;
}
</style>

<style>
.type-tab { display: flex; gap: 4px; background: #fff; border: 1px solid var(--line); border-radius: 14px; padding: 4px; }
.type-tab button { flex: 1; border: 0; background: transparent; border-radius: 10px; padding: 9px 4px; font-family: inherit; font-size: 11px; color: var(--sub); }
.type-tab button.active { background: linear-gradient(135deg, #5B2A91, #7A3CB0); color: #fff; font-weight: 600; }
.help-picker { display: grid; grid-template-columns: 1fr 1fr; gap: 7px; margin-bottom: 10px; }
.help-picker button { border: 1px solid var(--line); border-radius: 11px; background: #fff; padding: 9px; font-family: inherit; font-size: 10.5px; color: var(--sub); }
.help-picker button.on { background: #F4EEFB; border-color: #5B2A91; color: #5B2A91; font-weight: 600; }
</style>

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
  category: '',
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
const needPhoneConfirm = ref(false)
const phoneConfirmed = ref(false)
const aiPanel = ref(false)
const aiData = ref(null)
const aiLoading = ref(false)
const descCount = computed(() => form.desc.length)
const fileInput = ref(null)

const catMap = {
  '证件': 'card',
  '电子设备': 'electronics',
  '衣物': 'cloth',
  '水杯': 'bottle',
  '书包': 'bag',
  '其他': 'other'
}

async function aiFormat() {
  if (!form.title.trim() && !form.desc.trim()) return
  aiLoading.value = true
  try {
    aiData.value = await api.format(form.title.trim(), form.desc.trim(), form.place.trim())
    aiPanel.value = true
  } catch (e) {
    error.value = e.message || 'AI 整理失败'
  } finally { aiLoading.value = false }
}
function useAi() {
  if (!aiData.value) return
  if (aiData.value.summary) form.title = String(aiData.value.summary).slice(0, 30)
  if (aiData.value.desc) form.desc = String(aiData.value.desc).slice(0, 300)
  aiPanel.value = false
}
function fillDemo() {
  kind.value = 'lost'
  form.title = '白色有线耳机'
  form.category = '电子设备'
  form.desc = '白色有线耳机，带一个透明耳机盒，左耳外壳有一道浅划痕。'
  form.place = '六教 3 区'
  form.phone = '13800138000'
  form.secret = '耳机盒内侧写了名字缩写'
}

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
      cat: isHelp.value ? helpCatLocal.value : (catMap[form.category] || 'other'),
      helpCat: isHelp.value ? helpCatLocal.value : '',
      title: form.title.trim(),
      desc: form.desc.trim(),
      place: form.place.trim() || '未填写地点',
      eventTime: form.eventTime || '',
      secret: form.secret.trim(),
      contact: { phone: form.phone.trim() },
      photo: photo.value || null,
      phoneConfirmed: phoneConfirmed.value
    }
    const saved = await api.create(item)
    result.value = saved
    try { sessionStorage.setItem('sg:lastResult', JSON.stringify(saved)) } catch (e) {}
    emit('nav', 'success')
  } catch (e) {
    if (e.body && e.body.needConfirm) {
      needPhoneConfirm.value = true
      error.value = '这个号码需要确认，请核对后勾选'
    } else {
      error.value = e.message || '提交失败，请稍后再试'
    }
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
        <div class="ph-s">发布前先审文字和图片，违规内容发不出去</div>
        <div class="ph-steps"><span>1 填写</span><i></i><span>2 AI 审核</span><i></i><span>3 上架</span></div>
      </div>
      <div class="warn-box">❗禁止发布现金、贵重物品、危险品、药品；虚假信息会被下架并限制发布权限。</div>

      <div class="type-tab" style="margin-bottom:10px">
        <div :class="{ active: kind === 'lost' }" @click="kind = 'lost'">我要寻物（东西丢了）</div>
        <div :class="{ active: kind === 'found' }" @click="kind = 'found'">我要招领（捡到物品）</div>
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
            <label>物品名称 <span class="req">*</span></label>
            <input v-model="form.title" maxlength="30" :placeholder="isHelp ? '例如：想借一把雨伞' : '例如：白色有线耳机'">
          </div>
          <div class="form-item">
            <label>物品分类</label>
            <select v-model="form.category">
              <option value="">不选则归入「其他」</option>
              <option>证件</option>
              <option>电子设备</option>
              <option>衣物</option>
              <option>水杯</option>
              <option>书包</option>
              <option>其他</option>
            </select>
          </div>
          <div class="form-item">
            <label>{{ kind === 'lost' ? '丢失地点' : '捡到地点' }}</label>
            <input v-model="form.place" maxlength="40" placeholder="不填也可以，例如：六教 3 区">
          </div>
          <div v-if="!isHelp" class="form-item">
            <label>{{ kind === 'lost' ? '丢失时间' : '捡到时间' }}</label>
            <input v-model="form.eventTime" type="datetime-local">
            <div class="tip-small">不填就记为提交时间</div>
          </div>
        </div>

        <div class="form-card">
          <div class="fc-title"><span>02</span>描述与独有特征</div>
          <div class="form-item">
            <label>物品描述 <span class="req">*</span></label>
            <textarea v-model="form.desc" maxlength="300" :placeholder="isHelp ? '说明需求、时间和地点' : '颜色、划痕、标记……越具体越容易核对'"></textarea>
            <div class="tip-small">{{ descCount }}/300 · 超过 60 字建议让 AI 精简</div>
            <button type="button" class="btn ghost" style="width:100%;margin-top:8px" :disabled="aiLoading" @click="aiFormat">{{ aiLoading ? 'AI 整理中…' : '✨ AI 帮我整理成模板' }}</button>
          </div>
          <div v-if="aiPanel && aiData" class="ai-format" style="display:block">
            <div class="af-head">AI 整理建议</div>
            <div class="af-row"><span class="af-k">摘要</span><span>{{ aiData.summary }}</span></div>
            <div class="af-row"><span class="af-k">描述</span><span>{{ aiData.desc }}</span></div>
            <div class="af-tags"><span v-for="t in (aiData.fields ? Object.values(aiData.fields) : [])" :key="t">{{ t }}</span></div>
            <div class="af-acts">
              <button type="button" class="btn ok" @click="useAi">用这个</button>
              <button type="button" class="btn ghost" @click="aiFormat">重新生成</button>
              <button type="button" class="btn ghost" @click="aiPanel = false">不用了</button>
            </div>
          </div>
          <div v-if="!isHelp" class="form-item">
            <label>独有特征（选填，仅审核员可见）</label>
            <textarea v-model="form.secret" maxlength="100" placeholder="只有失主知道的细节，例如：卡背面写了名字"></textarea>
            <div class="tip-small">不会公开展示，用来防止冒领</div>
          </div>
        </div>

        <div class="form-card">
          <div class="fc-title"><span>03</span>图片与联系方式</div>
          <div class="form-item">
            <label>物品图片（选填，1 张）</label>
            <div class="upload-box" @click="fileInput && fileInput.click()">
              <div class="ub-ico">📷</div>
              <div class="ub-t">点击上传 / 拍照</div>
              <div class="ub-s">会自动压缩，只保存在本机</div>
            </div>
            <input ref="fileInput" type="file" accept="image/*" style="display:none" @change="onPhoto">
            <img v-if="photo" :src="photo" alt="预览" style="width:100%;max-height:180px;object-fit:cover;border-radius:10px;margin-top:8px">
            <div v-if="visionState" class="sa" style="margin-top:5px">{{ visionState }}</div>
          </div>
          <div class="form-item">
            <label>联系电话（选填）</label>
            <input v-model="form.phone" maxlength="20" placeholder="会在列表里脱敏显示">
            <div class="tip-small">会在列表里脱敏显示</div>
          </div>
        </div>

        <div v-if="error" class="warn-box" style="margin-bottom:10px">{{ error }}</div>
        <label v-if="needPhoneConfirm" style="display:flex;align-items:center;gap:6px;font-size:10px;color:var(--sub);margin-bottom:10px">
          <input v-model="phoneConfirmed" type="checkbox" style="width:auto;margin:0;accent-color:var(--primary)">
          我确认这个号码正确，可以联系到我
        </label>

        <button type="button" class="submit-btn" :disabled="submitting" @click="submit">
          {{ submitting ? '提交中…' : '提交发布 · AI 先审核' }}
        </button>
        <div class="pub-note">提交后先审文字和图片，通过后同学才能看到；AI 匹配仅供参考，实际以现场和校方失物招领点为准</div>
        <button type="button" class="btn ghost" style="width:100%;margin:10px 0 20px;padding:11px" @click="fillDemo">一键填入示例，快速体验</button>
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
.form-card .form-item textarea,
.form-card .form-item select {
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

<style>
.pub-head { margin-top: 8px; }
</style>


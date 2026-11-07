<script setup>
import { computed, reactive, ref } from 'vue'
import { api } from '../api'

const props = defineProps({
  type: { type: String, default: 'lost' },
  helpCat: { type: String, default: 'help_borrow' }
})
const emit = defineEmits(['nav'])

const isHelp = computed(() => props.type === 'help')
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

const typeLabel = computed(() => isHelp.value ? '爱心求助' : (props.type === 'lost' ? '寻物启事' : '失物招领'))
const helpName = computed(() => ({
  help_borrow: '借用工具',
  help_errand: '代办跑腿',
  help_donate: '爱心捐赠',
  help_volunteer: '志愿帮忙'
}[props.helpCat] || '爱心求助'))

async function submit() {
  error.value = ''
  if (form.title.trim().length < 2) { error.value = '标题至少写两个字'; return }
  if (form.desc.trim().length < 5) { error.value = '说明再具体一点，至少 5 个字'; return }
  submitting.value = true
  try {
    const item = {
      type: isHelp.value ? 'help' : props.type,
      cat: isHelp.value ? props.helpCat : 'other',
      helpCat: isHelp.value ? props.helpCat : '',
      title: form.title.trim(),
      desc: form.desc.trim(),
      place: form.place.trim() || '未填写地点',
      eventTime: form.eventTime || '',
      secret: form.secret.trim(),
      contact: { phone: form.phone.trim() }
    }
    const saved = await api.create(item)
    result.value = saved
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
      <div class="back" @click="$emit('nav', isHelp ? 'help' : type)">‹</div>
      <div class="t">{{ isHelp ? '发布爱心求助' : '发布启事' }}</div>
    </div>

    <div class="scroll">
      <div class="pub-head">
        <div class="ph-t">{{ isHelp ? '发布一条爱心求助' : '发布一条启事' }}</div>
        <div class="ph-s">{{ isHelp ? helpName : (type === 'lost' ? '寻物启事 · 丢了东西' : '失物招领 · 捡到东西') }}</div>
        <div class="ph-steps"><span>1 填写</span><span>2 AI 审核</span><span>3 上架</span></div>
      </div>

      <div v-if="result" class="okpanel" style="margin-top:14px">
        <div class="big">✓</div>
        <h2>{{ result.status === 'approved' ? '已发布成功' : result.status === 'rejected' ? '内容被拦截' : '已提交，等待审核' }}</h2>
        <p>{{ result.rejectReason || 'AI 会先审核文字和图片，通过后其他同学才能看到。' }}</p>
        <button type="button" class="btn" style="width:100%" @click="$emit('nav', isHelp ? 'help' : type)">返回列表</button>
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

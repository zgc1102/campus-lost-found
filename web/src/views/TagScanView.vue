<script setup>
import { onMounted, ref } from 'vue'
import { api } from '../api'

const props = defineProps({
  code: { type: String, default: '' }
})
const emit = defineEmits(['nav'])
const tag = ref(null)
const loading = ref(true)
const error = ref('')
const message = ref('')
const contact = ref('')
const itemName = ref('')
const sent = ref(false)
const sending = ref(false)

onMounted(async () => {
  if (!props.code) { error.value = '拾光码链接不完整'; loading.value = false; return }
  try {
    tag.value = await api.tag(props.code)
    itemName.value = tag.value.itemName || ''
  } catch (e) {
    error.value = e.message || '拾光码不存在'
  } finally {
    loading.value = false
  }
})

async function send() {
  if (!message.value.trim() && !contact.value.trim()) {
    error.value = '留一句「我捡到了」或联系方式，失主才能找到你'
    return
  }
  sending.value = true
  error.value = ''
  try {
    await api.notifyTag(props.code, {
      message: message.value.trim(),
      contact: contact.value.trim(),
      itemName: itemName.value.trim()
    })
    sent.value = true
  } catch (e) {
    error.value = e.message || '通知发送失败'
  } finally {
    sending.value = false
  }
}
</script>

<template>
  <section class="screen active tag-scan-screen">
    <div class="topbar">
      <div class="back" @click="$emit('nav', 'home')">‹</div>
      <div class="t">拾光码 · 联系失主</div>
    </div>

    <div class="scroll tag-scan-body">
      <div v-if="loading" class="empty">正在读取拾光码…</div>
      <template v-else-if="error && !tag">
        <div class="warn-box">{{ error }}</div>
        <button type="button" class="primary" @click="$emit('nav', 'home')">返回首页</button>
      </template>
      <template v-else>
        <div class="scan-card">
          <div class="scan-icon">🔖</div>
          <div class="scan-kicker">清华校园拾光里</div>
          <h2>{{ tag.itemName || '这位同学丢了东西' }}</h2>
          <p v-if="tag.note">{{ tag.note }}</p>
          <p class="scan-phone">失主联系方式：{{ tag.phoneMasked || '已隐藏' }}</p>
          <p class="scan-hint">你不需要注册，也不用曝光自己。留一句话，失主会收到通知。</p>
        </div>

        <div v-if="sent" class="scan-done">
          <b>已通知失主</b>
          <span>失主会在「通知」里看到你的留言。谢谢你把东西还回去。</span>
        </div>
        <div v-else class="scan-form">
          <label>你捡到了什么</label>
          <input v-model="itemName" maxlength="40" placeholder="例如：一把黑色雨伞">
          <label>给失主留言</label>
          <textarea v-model="message" maxlength="160" placeholder="例如：我在图书馆一楼服务台捡到了，可以来这里拿"></textarea>
          <label>你的联系方式（选填）</label>
          <input v-model="contact" maxlength="40" placeholder="手机号 / 微信，只有失主能看到">
          <div v-if="error" class="warn-box">{{ error }}</div>
          <button type="button" class="primary scan-submit" :disabled="sending" @click="send">{{ sending ? '发送中…' : '通知失主' }}</button>
        </div>
      </template>
    </div>
  </section>
</template>

<style scoped>
.tag-scan-screen { min-height: 100vh; background: #F7F4FB; }
.tag-scan-body { padding: 16px 14px 40px; }
.scan-card { background: #fff; border: 1px solid #EDE4F7; border-radius: 18px; padding: 20px 16px; text-align: center; }
.scan-icon { width: 54px; height: 54px; margin: 0 auto 10px; border-radius: 16px; background: linear-gradient(145deg, #6D3BA6, #3B1D63); display: flex; align-items: center; justify-content: center; font-size: 25px; }
.scan-kicker { font-size: 10px; letter-spacing: .12em; color: #8E7FA3; }
.scan-card h2 { margin: 7px 0 8px; font-size: 19px; color: #2B1D3D; }
.scan-card p { margin: 5px 0; font-size: 12px; line-height: 1.7; color: #6E607F; }
.scan-card .scan-phone { color: #3B1D63; font-weight: 600; }
.scan-card .scan-hint { margin-top: 12px; color: #9A8DAB; font-size: 10.5px; }
.scan-form { background: #fff; border: 1px solid #EDE4F7; border-radius: 16px; padding: 14px; margin-top: 12px; }
.scan-form label { display: block; font-size: 11px; color: #5B2A91; margin: 10px 0 5px; }
.scan-form label:first-child { margin-top: 0; }
.scan-form input, .scan-form textarea { width: 100%; box-sizing: border-box; border: 1px solid #EADFF5; border-radius: 10px; background: #FAF7FE; padding: 10px; font-family: inherit; font-size: 12px; color: #2B1D3D; outline: none; }
.scan-form textarea { min-height: 86px; resize: vertical; }
.scan-submit { width: 100%; margin-top: 12px; }
.scan-done { background: #EAF7EE; border: 1px solid #CFE8D6; border-radius: 14px; padding: 16px; margin-top: 12px; text-align: center; }
.scan-done b { display: block; color: #2F7D46; font-size: 15px; margin-bottom: 6px; }
.scan-done span { display: block; color: #4F6B57; font-size: 11px; line-height: 1.7; }
</style>

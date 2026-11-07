<script setup>
import { onMounted, ref } from 'vue'
import { api } from '../api'

const emit = defineEmits(['nav'])
const question = ref('')
const answer = ref('')
const sources = ref([])
const loading = ref(false)

const chips = ['访客怎么进校？', '校园卡丢了怎么办？', '清华哪个食堂好吃？', '哪里可以借雨伞？']

async function ask(q) {
  const text = (q || question.value).trim()
  if (text.length < 2) return
  question.value = text
  loading.value = true
  answer.value = ''
  sources.value = []
  try {
    const data = await api.ask(text)
    answer.value = data.answer || '暂时没有找到答案'
    sources.value = data.sources || []
  } catch (e) {
    answer.value = e.message || '问答服务暂时不可用'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  const q = sessionStorage.getItem('sg:ask:q')
  if (q) {
    sessionStorage.removeItem('sg:ask:q')
    ask(q)
  }
})
</script>

<template>
  <section class="screen active" id="screen-ask">
    <div class="topbar">
      <div class="back" @click="$emit('nav', 'home')">‹</div>
      <div class="t">问 AI</div>
    </div>
    <div class="scroll">
      <div class="hero" style="padding:18px">
        <h1>初入清华园，你想问什么？</h1>
        <p>访客进校、校园卡、食堂、失物招领，都可以问。</p>
      </div>

      <div class="form-card">
        <div class="form-item">
          <label>你的问题</label>
          <textarea v-model="question" maxlength="200" placeholder="例如：访客怎么进清华？"></textarea>
        </div>
        <button type="button" class="submit-btn" :disabled="loading" @click="ask()">{{ loading ? '思考中…' : '问一问' }}</button>
      </div>

      <div style="display:flex;flex-wrap:wrap;gap:6px;margin:10px 0">
        <button v-for="c in chips" :key="c" type="button" class="ask-chip" @click="ask(c)">{{ c }}</button>
      </div>

      <div v-if="answer" class="form-card">
        <div class="fc-title">AI 回答</div>
        <p style="font-size:12px;line-height:1.8;color:var(--ink);white-space:pre-wrap">{{ answer }}</p>
      </div>

      <div v-if="sources.length" class="form-card">
        <div class="fc-title">参考资料</div>
        <div v-for="(s, i) in sources" :key="i" class="sa" style="padding:6px 0;border-bottom:1px solid var(--line)">
          <b>{{ s.title }}</b><br>{{ s.text }}
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.ask-chip {
  border: 1px solid var(--line);
  border-radius: 99px;
  background: #fff;
  color: var(--primary);
  font-family: inherit;
  font-size: 10px;
  padding: 6px 10px;
}
</style>

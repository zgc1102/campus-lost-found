<script setup>
import { computed, onMounted, ref } from 'vue'
import { api } from '../api'

const emit = defineEmits(['nav'])
const question = ref('')
const asked = ref('')
const answer = ref('')
const sources = ref([])
const loading = ref(false)

const chips = ['校园卡丢了怎么办', '捡到东西应该交到哪里', '怎么认领丢的东西', '交接时要注意什么']

const cleanAnswer = computed(() => {
  const text = String(answer.value || '')
    .replace(/\*\*/g, '')
    .replace(/\r/g, '')
    .replace(/\n{2,}/g, '\n')
    .trim()
  if (!text) return ''
  return text.startsWith('根据资料') ? text : '根据资料：\n' + text
})

async function ask(q) {
  const text = (q || question.value).trim()
  if (text.length < 2) return
  question.value = text
  asked.value = text
  loading.value = true
  answer.value = ''
  sources.value = []
  try {
    const data = await api.ask(text)
    answer.value = data.answer || '暂时没有找到答案'
    sources.value = (data.sources || []).slice(0, 4)
  } catch (e) {
    answer.value = e.message || '问答服务暂时不可用'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  const q = new URLSearchParams(location.search).get('q') || sessionStorage.getItem('sg:ask:q')
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
      <div class="t">校园问答</div>
    </div>
    <div class="scroll">
      <div class="ask-hint">基于校园失物知识库回答，答案会标注来源；知识库没有的会直接说不知道。</div>

      <div class="ask-row">
        <input v-model="question" maxlength="200" placeholder="输入问题，例如：校园卡丢了怎么办" @keyup.enter="ask()">
        <button type="button" class="btn" :disabled="loading" @click="ask()">问</button>
      </div>

      <div class="ask-chips">
        <span v-for="c in chips" :key="c" @click="ask(c)">{{ c }}</span>
      </div>

      <div v-if="asked" class="ask-card">
        <div class="ask-q">你问：{{ asked }}</div>
        <div v-if="loading" class="ask-a">正在查资料…</div>
        <div v-else class="ask-a" style="white-space:pre-line">{{ cleanAnswer }}</div>
      </div>

      <div v-if="sources.length" class="ask-card" style="margin-top:10px">
        <div class="ask-src-title">参考资料</div>
        <div v-for="(s, i) in sources" :key="i" class="ask-src-item">
          <b>{{ s.title }}</b>
          <span>{{ String(s.text || '').replace(/\*\*/g, '').slice(0, 180) }}</span>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.ask-hint {
  font-size: 10.5px;
  line-height: 1.7;
  color: var(--sub);
  margin: 2px 0 12px;
  max-width: 330px;
}
.ask-row {
  display: flex;
  gap: 7px;
  margin-bottom: 9px;
}
.ask-row input {
  flex: 1;
  min-width: 0;
  box-sizing: border-box;
  background: #fff;
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 10px 11px;
  font-family: inherit;
  font-size: 12px;
  color: var(--ink);
}
.ask-row .btn {
  border-radius: 12px;
  padding: 0 18px;
  font-size: 13px;
}
.ask-chips {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
  margin-bottom: 12px;
}
.ask-chips span {
  font-size: 10px;
  color: var(--primary);
  background: var(--surface-2);
  border: 1px solid var(--line);
  border-radius: 99px;
  padding: 5px 9px;
  cursor: pointer;
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.ask-card {
  background: #fff;
  border: 1px solid var(--line);
  border-radius: 14px;
  padding: 12px 13px;
}
.ask-q {
  font-size: 11px;
  color: var(--sub);
  margin-bottom: 7px;
}
.ask-a {
  font-size: 11.5px;
  line-height: 1.7;
  color: var(--ink);
  word-break: break-word;
}
.ask-src-title {
  font-size: 10px;
  font-weight: 600;
  color: var(--sub);
  margin-bottom: 5px;
}
.ask-src-item {
  padding: 6px 0;
  border-top: 1px solid #F2ECF9;
}
.ask-src-item b {
  display: block;
  font-size: 9.5px;
  color: var(--primary);
  margin-bottom: 2px;
}
.ask-src-item span {
  display: block;
  font-size: 9px;
  line-height: 1.55;
  color: var(--sub);
}
</style>

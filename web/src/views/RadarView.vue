<script setup>
import { ref } from 'vue'
import { api, oldUrl } from '../api'

const emit = defineEmits(['nav'])
const title = ref('')
const place = ref('')
const cat = ref('other')
const route = ref('')
const carry = ref('')
const lastSeen = ref('')
const loading = ref(false)
const error = ref('')
const matches = ref([])
const hotspots = ref([])
const radarSummary = ref('')
const detective = ref(null)
const scanned = ref(0)

async function scan() {
  error.value = ''
  if (title.value.trim().length < 2) { error.value = '先写一下丢了什么'; return }
  loading.value = true
  detective.value = null
  try {
    const data = await api.radar({ title: title.value.trim(), place: place.value.trim(), cat: cat.value, type: 'lost' })
    matches.value = data.matches || []
    hotspots.value = data.hotspots || []
    radarSummary.value = data.summary || ''
    scanned.value = data.scanned || 0
  } catch (e) {
    error.value = e.message || '扫描失败'
  } finally {
    loading.value = false
  }
}

async function runDetective() {
  error.value = ''
  loading.value = true
  try {
    const data = await api.detective({
      title: title.value.trim(),
      place: place.value.trim(),
      cat: cat.value,
      type: 'lost',
      route: route.value.trim(),
      carry: carry.value,
      lastSeen: lastSeen.value.trim()
    })
    detective.value = data
  } catch (e) {
    error.value = e.message || '推理失败'
  } finally {
    loading.value = false
  }
}

function askCampus() {
  location.href = oldUrl('ask')
}
function openMatch(m) {
  sessionStorage.setItem('sg:focusItem', m.item.id)
  emit('nav', m.item.type === 'lost' ? 'found' : 'lost')
}
</script>

<template>
  <section class="screen active" id="screen-radar">
    <div class="ag-top">
      <button type="button" class="ag-back" aria-label="返回" @click="$emit('nav', 'home')">‹</button>
      <div class="ag-title"><b>AI 寻物雷达</b><span>{{ loading ? '正在扫描全站信息…' : '不用先发布，也可以直接查' }}</span></div>
    </div>

    <div class="scroll">
      <div class="radar-query">
        <input v-model="title" maxlength="40" placeholder="丢了什么？例如：黑色机械键盘">
        <div class="rq-row">
          <input v-model="place" maxlength="30" placeholder="在哪丢的（选填）">
          <select v-model="cat">
            <option value="other">自动判断</option>
            <option value="card">校园卡</option>
            <option value="keys">钥匙</option>
            <option value="electronics">手机/电脑</option>
            <option value="umbrella">雨伞</option>
            <option value="bottle">水杯</option>
          </select>
          <button type="button" :disabled="loading" @click="scan">{{ loading ? '扫描中…' : '扫描' }}</button>
        </div>
        <div class="rq-tip">不用先发布，也可以直接查任意物品</div>
      </div>

      <div v-if="error" class="warn-box" style="margin-bottom:10px">{{ error }}</div>
      <div v-if="loading" class="ag-loading">雷达扫描中…</div>
      <div v-else-if="!matches.length && !scanned" class="ag-loading">填好线索，点「扫描」开始</div>

      <template v-if="matches.length">
        <div v-if="radarSummary" class="rd-summary">{{ radarSummary }}</div>
        <article v-for="(m, i) in matches" :key="m.item.id" class="rd-match" :style="{ animationDelay: (i * 0.12) + 's' }" @click="openMatch(m)">
          <div class="rd-score">{{ m.score }}%</div>
          <div class="rd-main">
            <div class="rd-title">{{ m.item.title }}</div>
            <div class="rd-meta">{{ m.item.place || '未填写地点' }}<span class="rd-conf">{{ m.confidence }}置信</span></div>
            <div class="rd-reasons"><span v-for="r in m.reasons" :key="r">{{ r }}</span></div>
          </div>
        </article>
      </template>
      <div v-else-if="scanned && !loading" class="rd-summary" style="padding:18px 0;text-align:center">暂时没有高置信度匹配，先看下面的高频区域。</div>

      <div v-if="hotspots.length" class="rd-section">校园失物高频区域</div>
      <div v-if="hotspots.length" class="rd-hot">
        <div v-for="h in hotspots.slice(0, 5)" :key="h.place" class="rd-hot-row">
          <span class="rd-hot-name">{{ h.place }}</span>
          <span class="rd-bar"><i :style="{ width: Math.max(6, h.share || 0) + '%' }" /></span>
          <span class="rd-hot-n">{{ h.count }} 条</span>
        </div>
      </div>

      <div v-if="matches.length || scanned" class="detective-form">
        <div class="rf-kicker">LOST DETECTIVE</div>
        <div class="rf-title">让侦探推理下一步去哪找</div>
        <label>今天走过 <i>可以直接叙述，AI 帮你整理</i></label>
        <textarea v-model="route" maxlength="160" placeholder="例如：今天 9 点从图书馆出来，去观畴园吃饭，再回紫荆公寓，最后去快递驿站"></textarea>
        <div class="carry-row">
          <span>平时放在</span>
          <button v-for="c in ['口袋','背包','手持','其他']" :key="c" type="button" :class="{ on: carry === c }" @click="carry = c">{{ c }}</button>
        </div>
        <label>最后一次见到它 <i>时间 / 地点</i></label>
        <input v-model="lastSeen" maxlength="60" placeholder="例如：今天 15:00 在图书馆三楼还用过">
        <button type="button" class="rf-run" :disabled="loading" @click="runDetective">{{ loading ? '推理中…' : '开始推理' }}</button>
      </div>

      <template v-if="detective">
        <div class="dt-summary" style="margin-top:12px">{{ detective.summary }}</div>
        <div class="rd-section-title">建议按这个顺序找</div>
        <div v-for="(a, i) in detective.actions" :key="i" class="radar-action" :style="{ animationDelay: (i * 0.12) + 's' }">
          <span class="ra-num">{{ i + 1 }}</span>
          <span><b>{{ a.title }}</b><i>{{ a.detail }}</i></span>
        </div>
        <div class="dt-note">{{ detective.disclaimer }}</div>
        <button type="button" class="dt-ask" @click="askCampus">还拿不准？问校园 AI</button>
      </template>
    </div>
  </section>
</template>

<style scoped>
.radar-form,
.detective-form {
  background: #fff;
  border: 1px solid var(--line);
  border-radius: 16px;
  padding: 14px;
  margin-bottom: 12px;
}
.rf-kicker { font-size: 7.5px; letter-spacing: .18em; color: #A99BB9; }
.rf-title { font-size: 16px; font-weight: 600; color: var(--ink); margin: 4px 0 10px; }
.radar-form label,
.detective-form label { display: block; font-size: 10.5px; font-weight: 600; color: #4E445D; margin: 9px 0 5px; }
.radar-form label b { color: var(--accent); font-weight: 400; }
.radar-form label i,
.detective-form label i { font-style: normal; font-weight: 400; font-size: 8.5px; color: #A99BB9; margin-left: 3px; }
.radar-form input,
.radar-form select,
.detective-form input,
.detective-form textarea {
  width: 100%;
  box-sizing: border-box;
  background: #F8F4FD;
  border: 1px solid #EDE3F8;
  border-radius: 10px;
  padding: 9px 10px;
  font-family: inherit;
  font-size: 11px;
  color: var(--ink);
  outline: none;
}
.detective-form textarea { min-height: 62px; resize: vertical; }
.rf-run {
  width: 100%;
  margin-top: 12px;
  border: 0;
  border-radius: 12px;
  background: linear-gradient(135deg, #5B2A91, #7A3CB0);
  color: #fff;
  font-family: inherit;
  font-size: 13px;
  font-weight: 600;
  padding: 12px;
}
.carry-row { display: flex; align-items: center; gap: 5px; margin: 8px 0; font-size: 9.5px; color: var(--sub); }
.carry-row button { border: 1px solid var(--line); border-radius: 99px; background: #F8F4FD; color: var(--sub); font-family: inherit; font-size: 9px; padding: 5px 9px; }
.carry-row button.on { background: #5B2A91; color: #fff; border-color: #5B2A91; }
.rd-section-title { font-size: 11px; font-weight: 600; color: var(--ink); margin: 14px 2px 8px; }
.radar-match { display: flex; gap: 10px; background: #fff; border: 1px solid var(--line); border-radius: 16px; padding: 11px; margin-bottom: 8px; animation: rise .45s ease both; }
.rm-score { flex: 0 0 46px; width: 46px; height: 46px; border-radius: 50%; background: linear-gradient(145deg,#F2E7FF,#E2D0F6); color: #5B2A91; display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: 600; }
.rm-main { flex: 1; min-width: 0; }
.rm-title { font-size: 12.5px; font-weight: 600; }
.rm-meta { font-size: 9px; color: var(--sub); margin-top: 2px; }
.rm-reasons { display: flex; gap: 4px; flex-wrap: wrap; margin-top: 4px; }
.rm-reasons span { font-size: 8px; padding: 2px 6px; border-radius: 99px; background: #F4EEFB; color: #6D3AB0; }
.radar-hot { background: #fff; border: 1px solid var(--line); border-radius: 14px; padding: 10px 12px; }
.rh-row { display: flex; align-items: center; gap: 8px; margin: 7px 0; font-size: 9.5px; color: var(--sub); }
.rh-name { flex: 0 0 62px; color: var(--ink); }
.rh-bar { flex: 1; height: 5px; border-radius: 99px; background: #F0E9F8; overflow: hidden; }
.rh-bar i { display: block; height: 100%; border-radius: 99px; background: linear-gradient(90deg,#8A52C7,#C9A7F0); }
.rh-n { flex: 0 0 34px; text-align: right; color: #6D3AB0; }
.radar-action { display: flex; gap: 9px; background: #fff; border: 1px solid var(--line); border-radius: 13px; padding: 10px; margin-bottom: 7px; animation: rise .45s ease both; }
.ra-num { flex: 0 0 22px; height: 22px; border-radius: 50%; background: #F2E7FF; color: #5B2A91; font-size: 9px; font-weight: 600; display: flex; align-items: center; justify-content: center; }
.radar-action b { display: block; font-size: 11.5px; color: var(--ink); }
.radar-action i { display: block; font-style: normal; font-size: 9px; line-height: 1.5; color: var(--sub); margin-top: 2px; }
.detective-form { margin-top: 14px; }
</style>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { api } from '../api'
import CountUp from '../components/CountUp.vue'

const emit = defineEmits(['nav'])
const items = ref([])
const loading = ref(true)
const error = ref('')
const tab = ref('all')
const selected = ref(null)

function grams(text) {
  const s = String(text || '').replace(/\s+/g, '')
  const out = new Set()
  for (let i = 0; i < Math.max(0, s.length - 1); i++) out.add(s.slice(i, i + 2))
  return out
}
function daysBetween(a, b) {
  const ta = Number(a?.createdAt || 0)
  const tb = Number(b?.createdAt || 0)
  if (!ta || !tb) return 999
  return Math.abs(ta - tb) / 86400000
}
function makePair(lost, found) {
  const g1 = grams((lost.title || '') + (lost.desc || ''))
  const g2 = grams((found.title || '') + (found.desc || ''))
  const union = new Set([...g1, ...g2])
  const inter = [...g1].filter((x) => g2.has(x)).length
  const text = union.size ? Math.round((inter / union.size) * 100) : 0
  const cat = lost.cat && found.cat && lost.cat === found.cat
  const placeA = String(lost.place || '')
  const placeB = String(found.place || '')
  const place = !!(placeA && placeB && (placeA.includes(placeB) || placeB.includes(placeA)))
  const gap = daysBetween(lost, found)
  const time = Math.max(0, Math.round(100 - gap * 8))
  const image = lost.photoUrl && found.photoUrl ? 70 : (lost.photoUrl || found.photoUrl ? 45 : 25)
  const total = Math.max(0, Math.min(99, Math.round(
    text * 0.50 + (cat ? 100 : 0) * 0.18 + (place ? 100 : 0) * 0.17 + time * 0.10 + image * 0.05
  )))
  const reasons = []
  if (text >= 18) reasons.push(`标题/描述有 ${text}% 的重合`)
  if (cat) reasons.push('物品类别一致')
  if (place) reasons.push(`地点都在${placeA}`)
  if (time >= 50) reasons.push('发布时间接近')
  if (!cat) reasons.push('类别不同，建议自行核对')
  return { lost, found, text, image, place: place ? 100 : 0, time, total, reasons }
}

const allPairs = computed(() => {
  const losts = items.value.filter((x) => x.type === 'lost' && ['approved', 'claimed'].includes(x.status))
  const founds = items.value.filter((x) => x.type === 'found' && ['approved', 'claimed'].includes(x.status))
  const out = []
  for (const l of losts) for (const f of founds) out.push(makePair(l, f))
  return out
    .filter((p) => p.text >= 8 || (p.place && p.reasons.length >= 2))
    .sort((a, b) => b.total - a.total)
    .slice(0, 12)
})
const visible = computed(() => {
  if (tab.value === 'high') return allPairs.value.filter((p) => p.total >= 60)
  if (tab.value === 'low') return allPairs.value.filter((p) => p.total < 60)
  return allPairs.value
})
const highCount = computed(() => allPairs.value.filter((p) => p.total >= 60).length)
const selectedPair = computed(() => selected.value)
const ringOffset = computed(() => {
  const n = selectedPair.value?.total || 0
  return (138.2 * (1 - n / 100)).toFixed(1)
})
const ringColor = computed(() => scoreColor(selectedPair.value?.total || 0))
function scoreColor(n) { return n >= 70 ? '#2F7D46' : n >= 40 ? '#C58A00' : '#C0392B' }
function commonFeatures(p) {
  if (!p) return []
  const norm = (s) => String(s || '').replace(/[\s，。！？、；：]/g, '')
  const a = norm((p.lost.title || '') + (p.lost.desc || ''))
  const b = norm((p.found.title || '') + (p.found.desc || ''))
  const out = []
  for (const w of ['黑色', '白色', '蓝色', '红色', '雨伞', '校园卡', '耳机', '水杯', '书包', '图书馆', '食堂', '教室', '钥匙', '手机', '电脑', '划痕', '挂件']) {
    if (a.includes(w) && b.includes(w)) out.push(w)
  }
  return out.slice(0, 6)
}

onMounted(async () => {
  try {
    const list = await api.items()
    if (Array.isArray(list)) items.value = list
  } catch (e) {
    error.value = e.message || '匹配数据加载失败'
  } finally {
    loading.value = false
  }
})
function fmt(ts) {
  if (!ts) return '未填写'
  const d = new Date(ts)
  return `${d.getMonth() + 1}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}
function openPair(p) { selected.value = p }
function closePair() { selected.value = null }
function typeName(t) { return t === 'lost' ? '寻物启事' : '招领启事' }
function scoreLevel(n) { return n >= 75 ? '高' : n >= 50 ? '中' : '低' }
</script>

<template>
  <section class="screen active" id="screen-match">
    <div class="topbar">
      <div class="back" @click="$emit('nav', 'lost')">‹</div>
      <div class="t">智能匹配</div>
    </div>
    <div class="scroll match-scroll">
      <div class="match-hero">
        <div class="mh-icon">🧩</div>
        <div>
          <b>系统自动配对</b>
          <p>同时比对寻物与招领的文本、类别、地点和时间，给出可解释的匹配报告。</p>
          <div class="engine-line">本次匹配引擎：本地可解释匹配 v1 · 文本 n-gram + 类别 / 地点 / 时间权重</div>
        </div>
      </div>
      <div v-if="highCount" class="match-push" @click="tab = 'high'">
        <b>系统匹配提醒</b>
        <span>发现 {{ highCount }} 组高相似配对，建议优先核对</span>
        <i>查看 →</i>
      </div>
      <div class="match-tabs">
        <button type="button" :class="{ on: tab === 'all' }" @click="tab = 'all'">全部 {{ allPairs.length }}</button>
        <button type="button" :class="{ on: tab === 'high' }" @click="tab = 'high'">高匹配</button>
        <button type="button" :class="{ on: tab === 'low' }" @click="tab = 'low'">待核对</button>
      </div>
      <div v-if="loading" class="empty">正在计算匹配…</div>
      <div v-else-if="error" class="empty">{{ error }}</div>
      <div v-else-if="!visible.length" class="empty">暂时没有可以配对的寻物和招领</div>
      <div v-else class="pair-list">
        <article v-for="(p, i) in visible" :key="p.lost.id + p.found.id" class="pair-card" @click="openPair(p)">
          <div class="pair-score" :class="'level-' + scoreLevel(p.total)">
            <b><CountUp :value="p.total" /></b><span>匹配分</span>
          </div>
          <div class="pair-body">
            <div class="pair-head">
              <span class="pair-type">{{ typeName(p.lost.type) }}</span>
              <span class="pair-arrow">↔</span>
              <span class="pair-type found">{{ typeName(p.found.type) }}</span>
              <span class="pair-level">{{ scoreLevel(p.total) }}匹配</span>
            </div>
            <div class="pair-names">
              <b>{{ p.lost.title || '未命名寻物' }}</b>
              <i>↔</i>
              <b>{{ p.found.title || '未命名招领' }}</b>
            </div>
            <div class="pair-meta">{{ p.lost.place || '未填写地点' }} · {{ p.found.place || '未填写地点' }}</div>
            <div class="pair-bars">
              <span>文本 {{ p.text }}</span><span>类别 {{ p.lost.cat && p.lost.cat === p.found.cat ? '一致' : '不同' }}</span><span>地点 {{ p.place }}</span><span>时间 {{ p.time }}</span>
            </div>
          </div>
          <div class="pair-go">查看详情 →</div>
        </article>
      </div>
    </div>

    <div v-if="selectedPair" class="match-modal" @click.self="closePair">
      <div class="match-report">
        <button type="button" class="report-close" @click="closePair">✕</button>
        <div class="report-head">
          <div>
            <div class="report-kicker">匹配详情 · 本地可解释匹配 v1</div>
            <h2>综合匹配分 {{ selectedPair.total }} 分</h2>
            <div class="report-sub">{{ scoreLevel(selectedPair.total) }}匹配 · 仅供参考，最终请当面核对</div>
          </div>
          <div class="report-ring-wrap">
            <svg viewBox="0 0 120 120" class="ring-svg">
              <circle cx="60" cy="60" r="22" class="ring-track"></circle>
              <circle cx="60" cy="60" r="22" class="ring-value" :stroke="ringColor" :style="{ '--ring-offset': ringOffset + 'px' }"></circle>
            </svg>
            <b><CountUp :value="selectedPair.total" /></b>
          </div>
        </div>

        <div class="report-cols">
          <div class="report-item">
            <div class="ri-top"><span class="ri-tag">寻物启事</span><span>{{ selectedPair.lost.place || '未填写地点' }}</span></div>
            <div class="ri-photo">
              <img v-if="selectedPair.lost.photoUrl" :src="selectedPair.lost.photoUrl" alt="">
              <span v-else>🔎</span>
            </div>
            <h3>{{ selectedPair.lost.title || '未命名寻物' }}</h3>
            <p>{{ selectedPair.lost.desc || '暂无描述' }}</p>
            <div class="ri-meta">丢失时间：{{ fmt(selectedPair.lost.createdAt) }}</div>
            <div class="ri-meta">联系人：{{ selectedPair.lost.contact?.phone || '未公开' }}</div>
          </div>
          <div class="report-item">
            <div class="ri-top"><span class="ri-tag found">招领启事</span><span>{{ selectedPair.found.place || '未填写地点' }}</span></div>
            <div class="ri-photo">
              <img v-if="selectedPair.found.photoUrl" :src="selectedPair.found.photoUrl" alt="">
              <span v-else>📦</span>
            </div>
            <h3>{{ selectedPair.found.title || '未命名招领' }}</h3>
            <p>{{ selectedPair.found.desc || '暂无描述' }}</p>
            <div class="ri-meta">捡到时间：{{ fmt(selectedPair.found.createdAt) }}</div>
            <div class="ri-meta">联系人：{{ selectedPair.found.contact?.phone || '未公开' }}</div>
            <div v-if="commonFeatures(selectedPair).length" class="ri-keywords">
              <span>共同关键词</span>
              <i v-for="w in commonFeatures(selectedPair)" :key="w">{{ w }}</i>
            </div>
          </div>
        </div>

        <div class="report-breakdown">
          <div class="bd-row"><span>文本分</span><i><b :style="{ width: selectedPair.text + '%' }"></b></i><em>{{ selectedPair.text }}</em></div>
          <div class="bd-row"><span>类别</span><i><b :style="{ width: (selectedPair.lost.cat === selectedPair.found.cat ? 100 : 0) + '%' }"></b></i><em>{{ selectedPair.lost.cat === selectedPair.found.cat ? '一致' : '不同' }}</em></div>
          <div class="bd-row"><span>地点分</span><i><b :style="{ width: selectedPair.place + '%' }"></b></i><em>{{ selectedPair.place }}</em></div>
          <div class="bd-row"><span>时间分</span><i><b :style="{ width: selectedPair.time + '%' }"></b></i><em>{{ selectedPair.time }}</em></div>
        </div>

        <div class="report-reasons">
          <div class="rr-title">匹配理由</div>
          <div v-for="r in selectedPair.reasons" :key="r" class="rr-item">• {{ r }}</div>
          <div v-if="commonFeatures(selectedPair).length" class="rr-common">
            共同特征：<span v-for="w in commonFeatures(selectedPair)" :key="w">{{ w }}</span>
          </div>
        </div>

        <div class="report-detail">
          <div><b>文本</b><span>{{ selectedPair.text }}% 重合，{{ selectedPair.text >= 30 ? '标题/描述有明显共同词' : '共同词较少，主要靠其他维度' }}</span></div>
          <div><b>类别</b><span>{{ selectedPair.lost.cat === selectedPair.found.cat ? '两边分类一致' : '两边分类不同，不能只凭分类判断' }}</span></div>
          <div><b>地点</b><span>{{ selectedPair.place ? '地点相同或包含，可信度加分' : '地点没有重合，需要自行确认' }}</span></div>
          <div><b>时间</b><span>{{ selectedPair.time >= 50 ? '发布时间接近' : '时间间隔较远，注意是否同一件物品' }}</span></div>
        </div>

        <div class="report-actions">
          <button type="button" class="btn" @click="closePair">关闭报告</button>
          <button type="button" class="btn ghost" @click="emit('nav', 'found'); closePair()">去看寻物启事</button>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.match-scroll { padding-bottom: 24px; }
.match-hero { display:flex; gap:10px; align-items:flex-start; background:linear-gradient(135deg,#F8F2FF,#EEF5FF); border:1px solid #E6D9F3; border-radius:15px; padding:12px; margin-bottom:10px; }
.mh-icon { width:34px;height:34px;border-radius:10px;background:#5B2A91;display:flex;align-items:center;justify-content:center;font-size:16px;flex:0 0 34px; }
.match-hero b { font-size:12px;color:#3B1D63; }
.match-hero p { margin:3px 0 0;font-size:10px;line-height:1.6;color:#7A6B8E; }
.match-tabs { display:flex;gap:6px;margin-bottom:10px; }
.match-tabs button { border:1px solid #EADFF5;background:#fff;border-radius:99px;padding:5px 9px;font-family:inherit;font-size:10px;color:#7A6B8E; }
.match-tabs button.on { background:#5B2A91;border-color:#5B2A91;color:#fff; }
.pair-card { display:flex;gap:9px;align-items:center;background:#fff;border:1px solid #EADFF5;border-radius:14px;padding:11px;margin-bottom:8px;box-shadow:0 4px 14px rgba(59,29,99,.04); }
.pair-score { width:48px;height:48px;flex:0 0 48px;border-radius:50%;display:flex;flex-direction:column;align-items:center;justify-content:center;color:#5B2A91;background:#F1E8FB;border:3px solid #D8C2F2; }
.pair-score b { font-size:16px;line-height:1; }
.pair-score span { font-size:7px;margin-top:2px; }
.pair-score.level-高 { background:#EAF7EE;border-color:#B9DFC4;color:#2F7D46; }
.pair-score.level-低 { background:#FFF7E8;border-color:#F1D9A6;color:#9A6A00; }
.pair-body { flex:1;min-width:0; }
.pair-head { display:flex;align-items:center;gap:5px;font-size:9px;color:#8E7FA3; }
.pair-type { color:#5B2A91;background:#F7F0FF;border-radius:4px;padding:1px 4px; }
.pair-type.found { color:#2F5FA8;background:#EEF4FF; }
.pair-arrow { color:#B9A8CE; }
.pair-level { margin-left:auto;color:#A97A00; }
.pair-names { display:flex;gap:6px;align-items:center;margin-top:3px;font-size:11px;color:#3B1D63;white-space:nowrap;overflow:hidden; }
.pair-names b { overflow:hidden;text-overflow:ellipsis; }
.pair-names i { font-style:normal;color:#B9A8CE;font-size:10px; }
.pair-meta { margin-top:3px;font-size:9px;color:#8E7FA3; }
.pair-bars { display:flex;gap:7px;flex-wrap:wrap;margin-top:4px;font-size:8.5px;color:#7A6B8E; }
.pair-go { font-size:9px;color:#5B2A91;white-space:nowrap; }
.match-modal { position:fixed;left:0;top:0;width:100vw;height:100vh;z-index:300;background:rgba(10,5,20,.72);display:flex;align-items:center;justify-content:center;padding:14px; }
.match-report { width:min(880px,92vw);max-height:90vh;overflow-y:auto;background:#fff;border-radius:18px;padding:16px;position:relative; }
.report-close { position:absolute;right:10px;top:10px;border:0;background:#F3EEFA;color:#5B2A91;width:26px;height:26px;border-radius:50%;font-size:14px; }
.report-head { display:flex;justify-content:space-between;align-items:flex-start;gap:10px;padding-right:26px;border-bottom:1px solid #F0E8F8;padding-bottom:10px; }
.report-kicker { font-size:9px;color:#A99BB9;letter-spacing:.1em; }
.report-head h2 { margin:3px 0;font-size:17px;color:#3B1D63; }
.report-sub { font-size:9px;color:#8E7FA3; }
.report-ring { width:54px;height:54px;flex:0 0 54px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:19px;font-weight:700;background:#F1E8FB;color:#5B2A91;border:4px solid #D8C2F2; }
.report-ring.level-高 { background:#EAF7EE;border-color:#B9DFC4;color:#2F7D46; }
.report-ring.level-低 { background:#FFF7E8;border-color:#F1D9A6;color:#9A6A00; }
.report-cols { display:grid;grid-template-columns:1.15fr 1fr;gap:10px;margin-top:10px; }
.report-item { border:1px solid #EADFF5;border-radius:12px;padding:9px;background:#FCFAFF; }
.ri-top { display:flex;justify-content:space-between;font-size:8.5px;color:#8E7FA3;margin-bottom:5px; }
.ri-tag { color:#5B2A91;background:#F1E8FB;border-radius:4px;padding:1px 4px; }
.ri-tag.found { color:#2F5FA8;background:#EEF4FF; }
.ri-photo { height:92px;border-radius:9px;background:#F4EEFB;display:flex;align-items:center;justify-content:center;overflow:hidden; }
.ri-photo img { width:100%;height:100%;object-fit:cover; }
.ri-photo span { font-size:30px; }
.report-item h3 { font-size:12px;margin:6px 0 3px;color:#3B1D63; }
.report-item p { font-size:9.5px;line-height:1.6;color:#6E607F;margin:0 0 4px;max-height:54px;overflow:hidden; }
.ri-meta { font-size:8.5px;color:#8E7FA3;margin-top:2px; }
.report-breakdown { display:grid;grid-template-columns:1fr 1fr;gap:6px 14px;margin-top:11px; }
.bd-row { display:flex;align-items:center;gap:5px;font-size:8.5px;color:#7A6B8E; }
.bd-row span { width:34px;flex:0 0 34px; }
.bd-row i { flex:1;height:5px;background:#F0E8F8;border-radius:99px;overflow:hidden; }
.bd-row b { display:block;height:100%;background:#8A52C7;border-radius:99px; }
.bd-row em { width:30px;text-align:right;font-style:normal;color:#3B1D63; }
.report-reasons { margin-top:11px;background:#FBF8FF;border:1px solid #EADFF5;border-radius:10px;padding:9px; }
.rr-title { font-size:10px;color:#5B2A91;font-weight:600;margin-bottom:4px; }
.rr-item { font-size:9.5px;line-height:1.7;color:#6E607F; }
.report-actions { display:flex;gap:8px;margin-top:12px; }
.report-actions .btn { flex:1; }
@media (max-width:600px) { .report-cols { grid-template-columns:1fr; } .match-modal { padding:0;align-items:flex-end; } .match-report { max-height:92vh;border-radius:18px 18px 0 0; } }
</style>

<style scoped>
.engine-line { margin-top:6px; font-size:8.5px; color:#5B2A91; background:#F1E8FB; border-radius:5px; padding:3px 5px; display:inline-block; }
.match-push { display:flex; align-items:center; gap:7px; background:#EAF7EE; border:1px solid #CFE8D6; color:#2F7D46; border-radius:11px; padding:8px 10px; margin-bottom:9px; font-size:10px; cursor:pointer; }
.match-push b { font-size:10px; }
.match-push span { flex:1; color:#4F6B57; }
.match-push i { font-style:normal; font-size:9px; }
.report-ring-wrap { position:relative; width:60px; height:60px; flex:0 0 60px; }
.ring-svg { width:60px; height:60px; transform:rotate(-90deg); }
.ring-track { fill:none; stroke:#F0E8F8; stroke-width:7; }
.ring-value { fill:none; stroke-width:7; stroke-linecap:round; stroke-dasharray:138.2; stroke-dashoffset:138.2; animation:ringFill .9s ease forwards; }
@keyframes ringFill { to { stroke-dashoffset: var(--ring-offset); } }
.report-ring-wrap b { position:absolute; inset:0; display:flex; align-items:center; justify-content:center; font-size:17px; color:#3B1D63; }
.rr-common { margin-top:5px; font-size:9px; color:#5B2A91; }
.rr-common span { display:inline-block; background:#F1E8FB; border-radius:4px; padding:1px 4px; margin:2px 2px 0 0; }
.report-detail { margin-top:8px; border-top:1px dashed #EADFF5; padding-top:7px; }
.report-detail div { display:flex; gap:6px; font-size:9px; line-height:1.6; color:#6E607F; margin-top:3px; }
.report-detail b { flex:0 0 26px; color:#5B2A91; }
</style>



<style scoped>
.ri-keywords { margin-top:7px;display:flex;flex-wrap:wrap;gap:4px;align-items:center; }
.ri-keywords span { font-size:8px;color:#8E7FA3;margin-right:2px; }
.ri-keywords i { font-style:normal;font-size:8px;color:#5B2A91;background:#F1E8FB;border-radius:4px;padding:2px 4px; }
</style>





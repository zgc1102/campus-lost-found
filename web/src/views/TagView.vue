<script setup>
import { computed, onMounted, ref } from 'vue'
import { api } from '../api'

const emit = defineEmits(['nav'])
const item = ref('')
const phone = ref('')
const mode = ref('notify')
const note = ref('')
const result = ref(null)
const loading = ref(false)
const error = ref('')
const lookup = ref('')

async function generate() {
  error.value = ''
  if (mode.value === 'phone' && phone.value.trim().length < 6) {
    error.value = '选择显示电话时，请填写手机号'
    return
  }
  loading.value = true
  try {
    result.value = await api.createTag({
      itemName: item.value.trim() || '我的物品',
      phone: phone.value.trim(),
      mode: mode.value,
      note: note.value.trim()
    })
  } catch (e) {
    error.value = e.message || '生成失败'
  } finally {
    loading.value = false
  }
}

function copyLink() {
  const link = result.value && result.value.url
  if (!link) return
  if (navigator.clipboard) navigator.clipboard.writeText(link)
}
function resetTag() {
  result.value = null
}

async function cancelTag() {
  if (!confirm('确定注销这个拾光码？注销后别人扫码会显示「此码已注销」，无法再给你发消息。')) return
  try {
    await api.deleteTag()
    result.value = null
  } catch (e) {
    error.value = e.message || '注销失败'
  }
}

function openLookup() {
  const code = lookup.value.trim().toUpperCase().replace(/^.*[?&]tag=/, '').replace(/[^A-Z0-9]/g, '')
  if (!code) { error.value = '请输入拾光码'; return }
  location.href = '/?tag=' + encodeURIComponent(code)
}

onMounted(async () => {
  try {
    const list = await api.myTags()
    if (Array.isArray(list) && list.length) {
      result.value = list[0]
      item.value = list[0].itemName || ''
      phone.value = list[0].phone || ''
      mode.value = list[0].mode || 'notify'
    }
  } catch (_) {}
})

const qrSrc = computed(() => {
  if (!result.value) return ''
  if (result.value.qrData && String(result.value.qrData).startsWith('data:image')) return result.value.qrData
  if (result.value.url) return 'https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=' + encodeURIComponent(result.value.url)
  return ''
})
function qrError() {
  if (result.value && result.value.url) {
    result.value.qrData = 'https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=' + encodeURIComponent(result.value.url)
  }
}
</script>

<template>
  <section class="screen active" id="screen-tag">
    <div class="tag-top">
      <button type="button" class="tag-back" aria-label="返回" @click="$emit('nav', 'home')">‹</button>
      <div class="tag-title"><b>拾光码</b><span>给失物一张身份证</span></div>
    </div>
    <div class="scroll tag-body">
      <div class="tag-intro">
        一个拾光码可以贴在任何物品上：电脑、键盘、校园卡、充电器都行。捡到的人扫码后，可以只给你发通知，也可以直接看到你的电话。
      </div>
      <div class="tag-lookup">
        <input v-model="lookup" maxlength="60" placeholder="扫不出来？输入拾光码，如 SGBEA45A">
        <button type="button" @click="openLookup">查看</button>
      </div>

      <div class="tag-sec">
        <label>这枚码主要贴在哪（选填）</label>
        <input v-model="item" maxlength="30" placeholder="例如：键盘 / 校园卡 / 充电器">
      </div>
      <div class="tag-sec">
        <label>手机号</label>
        <input v-model="phone" maxlength="20" inputmode="tel" placeholder="用于失主联系，可打码展示">
      </div>
      <div class="tag-sec">
        <label>扫码后</label>
        <label class="tag-mode"><input v-model="mode" type="radio" value="notify"> 只给我发通知 <i>推荐，号码不公开</i></label>
        <label class="tag-mode"><input v-model="mode" type="radio" value="phone"> 直接显示我的手机号 <i>方便对方立刻联系</i></label>
      </div>
      <div class="tag-sec">
        <label>备注（选填）</label>
        <input v-model="note" maxlength="80" placeholder="例如：捡到请联系我，谢谢">
      </div>

      <div v-if="error" class="warn-box" style="margin-bottom:10px">{{ error }}</div>
      <button type="button" class="btn" style="width:100%" :disabled="loading" @click="generate">{{ loading ? '生成中…' : '生成我的拾光码' }}</button>

      <div v-if="result" class="tag-result" style="display:block">
        <img :src="qrSrc" alt="拾光码" @error="qrError">
        <div class="tr-item">{{ result.itemName }}</div>
        <div class="tr-code">拾光码 {{ result.code }} · {{ result.mode === 'phone' ? '扫码后直接显示手机号' : '扫码后只给你发通知' }}</div>
        <div class="tr-policy">长期有效 · 网站版本更新后仍可扫码</div>
        <div class="tr-date" v-if="result.createdAt">注册于 {{ new Date(result.createdAt).toLocaleDateString('zh-CN') }}</div>
        <div class="tr-warn">此码不再使用时，建议及时注销，避免被他人反复扫码打扰。</div>
        <div class="tr-security">官方码只指向 shiguangli.work，不会跳转支付或下载页面。</div>
        <button type="button" class="tr-cancel" @click="cancelTag">注销此码</button>
        <div class="tr-actions">
          <a class="primary" :download="'拾光码-' + result.code + '.png'" :href="qrSrc">保存 / 打印</a>
          <button type="button" @click="copyLink">复制链接</button>
        </div>
        <div class="tr-actions"><button type="button" @click="resetTag">重新生成一张</button></div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.tag-intro { background:#F6F0FC; border:1px solid #E9DDF6; border-radius:14px; padding:11px; font-size:10px; line-height:1.7; color:#5E536F; margin-bottom:10px; }
.tag-sec { background:#fff; border:1px solid var(--line); border-radius:15px; padding:12px; margin-bottom:9px; }
.tag-sec > label { display:block; font-size:11px; font-weight:600; color:#4E445D; margin-bottom:6px; }
.tag-sec input { width:100%; box-sizing:border-box; background:#F8F4FD; border:1px solid #EDE3F8; border-radius:10px; padding:10px; font-family:inherit; font-size:12px; color:var(--ink); outline:none; }
.tag-mode { display:flex; align-items:center; gap:7px; font-size:10px!important; font-weight:400!important; color:var(--ink)!important; margin:7px 0 0!important; }
.tag-mode input { width:auto!important; margin:0; accent-color:var(--primary); }
.tag-mode i { font-style:normal; font-size:8.5px; color:var(--sub); }
.tag-result { margin-top:12px; background:#fff; border:1px solid var(--line); border-radius:16px; padding:14px; text-align:center; }
.tag-result img { width:180px; height:180px; display:block; margin:0 auto 8px; border-radius:12px; }
.tag-result .tr-code { font-size:10px; letter-spacing:.1em; color:var(--sub); }
.tag-result .tr-item { font-size:14px; font-weight:600; margin:4px 0 2px; }
.tag-result .tr-actions { display:flex; gap:8px; margin-top:10px; }
.tag-result .tr-actions a, .tag-result .tr-actions button { flex:1; border:1px solid var(--line); border-radius:10px; padding:9px; font-size:10px; background:#F7F2FD; color:var(--primary); text-decoration:none; font-family:inherit; }
.tag-result .tr-actions .primary { background:linear-gradient(135deg,#5B2A91,#7A3CB0); color:#fff; border:0; }
</style>

<style scoped>
#screen-tag .tag-body { padding-bottom: 104px !important; }
</style>


<style scoped>
.tr-policy { margin-top:6px; font-size:9.5px; color:#5B2A91; background:#F1E8FB; border-radius:99px; display:inline-block; padding:4px 8px; }
</style>


<style scoped>
.tr-date { margin-top:6px; font-size:10px; color:#8E7FA3; }
.tr-warn { margin:8px 8px 0; font-size:9.5px; line-height:1.6; color:#A97A00; background:#FFF8E8; border-radius:8px; padding:6px 8px; }
.tr-cancel { width:100%; margin-top:9px; border:1px solid #F3CFCF; background:#FDF2F2; color:#A12F2F; border-radius:9px; padding:8px; font-family:inherit; font-size:10px; }
</style>


<style scoped>
.tr-security { margin-top:6px; font-size:9px; line-height:1.6; color:#8E7FA3; }
</style>


<style scoped>
.tag-lookup { display:flex; gap:6px; margin:8px 0 4px; }
.tag-lookup input { flex:1; min-width:0; border:1px solid #EADFF5; background:#FBF8FF; border-radius:9px; padding:8px; font-family:inherit; font-size:10.5px; }
.tag-lookup button { border:1px solid #E4D4F7; background:#F1E8FB; color:#5B2A91; border-radius:9px; padding:0 10px; font-family:inherit; font-size:10.5px; }
</style>


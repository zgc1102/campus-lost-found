<script setup>
const emit = defineEmits(['nav'])
const groups = [
  { g: '医疗急救', items: [{ n: '校医院急诊（24 小时）', t: '010-62782185' }, { n: '24 小时心理服务热线', t: '010-62785252' }] },
  { g: '安全保卫', items: [{ n: '保卫部 24 小时报警求助', t: '010-62782001' }, { n: '保卫部值班（备用）', t: '010-62783779' }] },
  { g: '后勤服务', items: [{ n: '后勤综合服务热线 / 校内查号台', t: '010-62793001' }, { n: '学生公寓 24 小时服务热线', t: '010-62793003' }] },
  { g: '招生咨询', items: [{ n: '本科生招生办公室', t: '010-62770334' }, { n: '研究生招生办公室', t: '010-62781380' }] }
]
</script>

<template>
  <section class="screen active" id="screen-phones">
    <div class="topbar">
      <div class="back" @click="$emit('nav', 'faq')">‹</div>
      <div class="t">常用电话</div>
    </div>
    <div class="scroll">
      <div class="hintline">以下电话均整理自清华大学官方网站与官方发布渠道，点按号码可直接拨号。</div>
      <template v-for="g in groups" :key="g.g">
        <div class="cat">{{ g.g }}</div>
        <a v-for="it in g.items" :key="it.t" class="ph-row" :href="'tel:' + it.t.replace(/-/g, '')">
          <span class="ph-n">{{ it.n }}</span><span class="ph-t">{{ it.t }}</span><span class="qa">›</span>
        </a>
      </template>
      <div class="faq-note">📞 号码来源：清华大学保卫部、校医院、总务部门及本科 / 研究生招生网的公开信息；如与最新官方公布不符，以学校官方渠道为准。校外紧急电话：报警 110 · 火警 119 · 急救 120 / 999。</div>
    </div>
  </section>
</template>

<script setup>
const props = defineProps({
  infoKey: { type: String, default: 'about' }
})
const emit = defineEmits(['nav'])

const content = {
  about: {
    title: '平台简介',
    body: '清华校园拾光里是一个面向校园的失物招领与爱心互助平台。我们希望把散落在各个群里的失物信息集中起来，让捡到的人更快找到失主，也让需要帮忙的人更容易被看见。'
  },
  contact: {
    title: '联系方式',
    body: '项目由清华学生团队维护，仅用于校园公益。\n反馈与建议：可在「我的发布」留言，或联系项目组同学。\n紧急情况请联系保卫部：010-62782001。'
  },
  legal: {
    title: '法律声明',
    body: '平台仅提供信息发布与匹配服务，不对线下交接过程作担保。请勿发布违法、危险或侵犯他人隐私的内容。\n涉及证件、贵重物品时，请当面核对特征，谨防冒领与诈骗。'
  },
  privacy: {
    title: '隐私权保护',
    body: '我们不会公开展示你的完整手机号，列表页默认打码。\n独有特征仅用于认领核验，不对外展示。\n上传的照片仅用于失物展示与审核。'
  },
  faq: {
    title: '来清华常问的问题',
    body: '访客进校：请通过「参观清华」官方渠道预约，持身份证从指定校门入校。\n校园卡丢了：先在校卡系统挂失，再到附近食堂/图书馆服务台和失物招领点询问。\n食堂：观畴园、清芬园、桃李园、紫荆园等都对师生开放，访客可扫码支付。'
  }
}[props.infoKey] || { title: '说明', body: '暂无内容。' }
</script>

<template>
  <section class="screen active" id="screen-info">
    <div class="topbar">
      <div class="back" @click="$emit('nav', 'guide')">‹</div>
      <div class="t">{{ content.title }}</div>
    </div>
    <div class="scroll">
      <div class="form-card" style="padding:18px">
        <p style="font-size:12px;line-height:1.9;color:var(--ink);white-space:pre-wrap">{{ content.body }}</p>
      </div>
    </div>
  </section>
</template>

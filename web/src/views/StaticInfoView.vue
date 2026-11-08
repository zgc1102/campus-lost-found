<script setup>
import { computed } from 'vue'

const props = defineProps({ name: { type: String, default: 'about' } })
const emit = defineEmits(['nav'])

const pages = {
  about: {
    title: '平台简介',
    blocks: [
      { section: '致谢' },
      { title: '衷心感谢 国城控股集团', ps: ['为本平台提供服务器与网络应用的支持。', '国城控股集团在吴城董事长带领下，以“红色引领、绿色发展”为理念，带领集团从智慧矿山拓展至化工、贸易、能源，市值再创新高。'] },
      { title: '衷心感谢 中基控股集团', ps: ['为本平台提供办公地点的支持。', '中基控股集团葛坚董事长以“长期价值投资”与“多元责任担当”为理念，坚持企业发展与社会贡献并重，长期投身公益慈善与家乡振兴事业。'] },
      { section: '平台宗旨' },
      { ps: ['本平台不以盈利为目的。', '原则上不接受广告投放，除非属于国家战略支持的方向、以公益为目的、以爱国爱家为情怀的软广告形式。'] }
    ]
  },
  contact: {
    title: '联系方式',
    blocks: [
      { title: '联系渠道', ps: ['平台内测阶段，请通过「发布启事」或「认领申请」在站内联系；紧急情况请联系学校保卫处。'] },
      { title: '地址', ps: ['具体办公地址在内测阶段暂不对外公布。'] }
    ]
  },
  legal: {
    title: '法律声明',
    blocks: [
      { title: '法律声明', ps: ['本平台为校园公益互助服务平台，所发布信息由用户自行提供，平台仅提供信息展示与对接渠道，不对信息的真实性、准确性、完整性作明示或默示担保。', '用户应依法依规使用本平台，不得发布违法违规、虚假或侵犯他人权益的内容；因使用本平台而产生的任何纠纷，由相关用户自行承担相应责任。', '本声明将随平台运营需要适时补充与更新，最终解释权归平台运营方所有。'] }
    ]
  },
  privacy: {
    title: '隐私权保护',
    blocks: [
      { title: '隐私权保护', ps: ['你发布的信息保存在本平台的服务器上，用于校园内的失物招领。公开列表不展示你的手机号（只显示脱敏后的号码）和独有特征；认领申请通过后，双方才会看到完整联系方式。', '平台遵循“最小必要”原则收集信息，未经你的同意，不向第三方提供个人信息。本条款将随服务升级适时更新，敬请留意。'] }
    ]
  }
}
const page = computed(() => pages[props.name] || pages.about)
</script>

<template>
  <section class="screen active mem-detail" :id="'screen-' + name">
    <div class="topbar">
      <div class="back" @click="$emit('nav', 'home')">‹</div>
      <div class="t">{{ page.title }}</div>
    </div>
    <div class="scroll">
      <template v-for="(b, i) in page.blocks" :key="i">
        <div v-if="b.section" class="sectitle">{{ b.section }}</div>
        <div v-else class="blk">
          <h3 v-if="b.title">{{ b.title }}</h3>
          <p v-for="(p, j) in b.ps" :key="j">{{ p }}</p>
        </div>
      </template>
    </div>
  </section>
</template>

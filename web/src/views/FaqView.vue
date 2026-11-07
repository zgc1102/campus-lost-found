<script setup>
import { ref } from 'vue'

const emit = defineEmits(['nav'])
const groups = [
  { cat: '入校与校门', items: [
    { q: '校外访客怎么进校？', a: '校外访客可凭身份证在指定校门登记入校，或提前通过“清华访客”线上预约。推荐从西门或东南门入校。' },
    { q: '哪个校门离地铁最近？', a: '东南门距离地铁圆明园站约 600 米，是离地铁最近的校门；西门离地铁 4 号线圆明园站也较近，步行约 8 分钟。' }
  ] },
  { cat: '食堂与餐饮', items: [
    { q: '游客能在哪个食堂吃饭？', a: '观畴园（万人食堂）、听涛园等开放窗口支持校园卡或扫码支付，部分楼层对游客开放，建议避开午高峰。' },
    { q: '吃饭怎么支付？', a: '支持微信 / 支付宝扫码，以及校园卡；游客直接使用移动支付即可，无需办卡。' }
  ] },
  { cat: '图书馆', items: [
    { q: '能进图书馆参观吗？', a: '老图书馆、北馆（李文正馆）对师生开放，访客可在开放区域安静参观，阅览区需校园卡进入。' }
  ] },
  { cat: '生活服务', items: [
    { q: '校医院在哪、能看病吗？', a: '校医院位于近春园一带，师生及访客急症可挂门诊；常用药品可在此开具。' },
    { q: '快递在哪取？', a: '校内快递服务中心集中在紫荆公寓区附近，凭取件码在自助柜取件，营业时间一般为 9:00–21:00。' }
  ] },
  { cat: '拍照打卡', items: [
    { q: '二校门 / 清华学堂哪里拍好看？', a: '二校门、清华学堂、近春园荷塘是经典打卡点；清晨与傍晚光线最佳，注意避开人流高峰更出片。' }
  ] }
]
const selected = ref(null)
</script>

<template>
  <section class="screen active" id="screen-faqList">
    <div class="topbar">
      <div class="back" @click="$emit('nav', 'guide')">‹</div>
      <div class="t">常问的问题</div>
    </div>
    <div class="scroll">
      <div class="q" style="background:linear-gradient(135deg,#f7f1fc,#fdf6e9);border-color:var(--purple-ll)" @click="$emit('nav', 'phones')">
        <div class="qt"><b>📞 常见电话</b><br><span style="font-size:12px;color:var(--sub)">急救 · 安保 · 后勤 · 招生，一键拨打</span></div>
        <div class="qa">›</div>
      </div>
      <template v-for="g in groups" :key="g.cat">
        <div class="cat">{{ g.cat }}</div>
        <div v-for="it in g.items" :key="it.q" class="q" @click="selected = it">
          <div class="qt">{{ it.q }}</div><div class="qa">›</div>
        </div>
      </template>
      <div class="faq-note">🗺️ 地图与实景图说明：地标位置参考清华园实际布局与公开地图修订（示意，非导航底图）。</div>
    </div>

    <div v-if="selected" class="sheet vue-sheet show">
      <button type="button" class="sheet-x" @click="selected = null">收起</button>
      <div class="sh">{{ selected.q }}</div>
      <div class="sa">{{ selected.a }}</div>
      <div class="close" @click="selected = null">收起</div>
    </div>
  </section>
</template>

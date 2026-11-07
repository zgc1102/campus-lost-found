<script setup>
import { ref } from 'vue'

const emit = defineEmits(['nav'])
const active = ref(null)
const spots = [
  { name: '西门（主校门）', icon: '🌟', x: 9, y: 34, desc: '清华最具代表性的校门，题字“清华大学”于此，访客主要入校口之一，紧邻圆明园。' },
  { name: '观畴园（食堂）', icon: '🍚', x: 34, y: 22, desc: '万人食堂，位于校园中北部，游客可扫码就餐，菜品丰富、性价比高。' },
  { name: '紫操', icon: '🏃', x: 72, y: 14, desc: '紫荆操场，校园东北部，夜跑与社团活动常用场地。' },
  { name: '综合体育馆', icon: '🏟️', x: 86, y: 20, desc: '东北部大型场馆，开学典礼、毕业典礼与大型演出常在此举办。' },
  { name: '图书馆（北馆）', icon: '📚', x: 70, y: 30, desc: '李文正馆，早期建筑区东北侧，馆内安静、适合自习与参观。' },
  { name: '老图书馆', icon: '📚', x: 60, y: 36, desc: '清华早期四大建筑之一，红砖坡顶，杨绛先生笔下“最爱的图书馆”。' },
  { name: '大礼堂', icon: '🎭', x: 46, y: 42, desc: '古罗马穹顶风格，与大草坪、日晷构成校园中轴经典景观。' },
  { name: '清华学堂', icon: '🏛️', x: 56, y: 44, desc: '1911 年建校起点，德国古典风格，培养人才的摇篮。' },
  { name: '校史馆', icon: '📜', x: 38, y: 50, desc: '展示清华建校与发展历程，位于大礼堂西侧，预约可参观。' },
  { name: '二校门', icon: '🏛️', x: 48, y: 58, desc: '清华标志性白色牌坊，最早的主校门，最热门的拍照打卡点。' },
  { name: '近春园（荷塘）', icon: '🌊', x: 28, y: 68, desc: '朱自清《荷塘月色》笔下的荷塘，荒岛、亭廊与垂柳环绕，散步佳处。' },
  { name: '校医院', icon: '🏥', x: 18, y: 62, desc: '校园西南部，急症门诊与常用药开具，急诊 24 小时（010-62782185）。' },
  { name: '清芬园（食堂）', icon: '🍜', x: 56, y: 64, desc: '中部主要食堂，风味档口多，支持移动支付，建议避开午高峰。' },
  { name: '艺术博物馆', icon: '🖼️', x: 78, y: 84, desc: '校园东南角，常设校藏与专题大展，建筑本身也是打卡点。' },
  { name: '东门', icon: '🚪', x: 90, y: 46, desc: '东侧校门，临近东区教学科研楼群与主楼一带。' }
]
const photos = {
  '二校门': 'https://www.tsinghua.edu.cn/__local/1/63/BE/E6DAC008600170338C51AF67AA2_A30DA786_A857B.jpg',
  '清华学堂': 'https://www.tsinghua.edu.cn/__local/E/CB/AB/4013FF557763C9195DBEE3C9E23_4AEC7F2F_B0999.jpg',
  '大礼堂': 'https://www.tsinghua.edu.cn/__local/4/08/64/830C8E47DF858F512AC2BF7A400_F226E486_A08D2.jpg',
  '老图书馆': 'https://www.tsinghua.edu.cn/__local/3/E7/C3/20330133B5ADFF11BED6AC2A2A6_91145F8C_9B199.jpg',
  '近春园（荷塘）': 'https://www.tsinghua.edu.cn/__local/0/DB/2D/DBA5A25DA78C44ED8C2DE6C1A10_2423BADD_1C3823.jpg',
  '艺术博物馆': 'https://www.tsinghua.edu.cn/__local/0/E9/B5/123588172AED93BD0193C0D83FA_DED4F3EB_901C6.jpg',
  '综合体育馆': 'https://www.tsinghua.edu.cn/__local/F/F9/68/A5A677B7D9B84F28D44A2452AFF_D369F59E_17F17B.jpg'
}
function shortName(n) { return n.replace(/（.*?）/, '') }
function up(i) {
  const y = spots[i].y
  return y < 20 ? false : (y > 78 ? true : i % 2 === 1)
}
</script>

<template>
  <section class="screen active" id="screen-map">
    <div class="topbar">
      <div class="back" @click="$emit('nav', 'guide')">‹</div>
      <div class="t">清华大学全景地图</div>
    </div>
    <div class="scroll">
      <div class="sectitle">点击地标查看简介与实景图（文旅图风格全图，非导航底图）</div>
      <div class="map-wrap">
        <div class="map-title">清华大学全景文旅图</div>
        <div class="compass"><b>N</b></div>
        <svg class="boundary-svg" viewBox="0 0 100 100" preserveAspectRatio="none">
          <polygon points="7,24 20,12 40,7 60,6 74,6 94,10 96,30 94,44 96,60 88,78 80,90 60,88 44,92 30,86 16,80 10,62 6,44" fill="rgba(98,38,156,.07)" stroke="rgba(98,38,156,.5)" stroke-width="0.6" stroke-dasharray="2.4 1.6" />
        </svg>
        <div class="park" style="left:6%;top:16%;width:34%;height:28%"></div>
        <div class="park" style="left:50%;top:28%;width:32%;height:26%"></div>
        <div class="park" style="left:16%;top:58%;width:28%;height:22%"></div>
        <div class="water" style="left:22%;top:60%;width:14%;height:11%"></div>
        <div class="water" style="left:30%;top:40%;width:10%;height:8%"></div>
        <div class="road" style="left:0;top:40%;width:100%"></div>
        <div class="road" style="left:44%;top:0;width:7px;height:100%"></div>
        <div class="road" style="left:0;top:62%;width:100%"></div>
        <div class="route" style="left:14%;top:36%;width:46%;transform:rotate(26deg)"></div>
        <div class="legend"><b>图例</b><br>🏛️ 校门/礼堂 · 📚 图书馆<br>🍚 食堂 · 🏥 医疗 · 🏟️ 场馆<br>🌊 水系 · 🌳 绿地</div>
        <button v-for="(s, i) in spots" :key="s.name" type="button" class="spot" :class="{ up: up(i) }" :style="{ left: s.x + '%', top: s.y + '%' }" @click="active = s">
          <span class="badge">{{ s.icon }}</span><span class="sl">{{ shortName(s.name) }}</span>
        </button>
      </div>
      <div class="foot" style="text-align:center;color:var(--sub);font-size:11px;padding:14px 0;">地标位置参考清华园实际布局与公开地图修订（腾讯 / 百度 / 高德）；示意全图，非真实导航底图</div>
    </div>

    <div v-if="active" class="sheet show">
      <button type="button" class="sheet-x" @click="active = null">收起</button>
      <div class="big-thumb">
        <img v-if="photos[active.name]" :src="photos[active.name]" alt="" style="width:100%;height:100%;object-fit:cover;border-radius:12px">
        <span v-else>📍</span>
      </div>
      <div class="sh">{{ active.name }}</div>
      <div class="sa">{{ active.desc }}</div>
      <div class="sa" style="margin-top:8px">{{ photos[active.name] ? '📷 实景图来源：清华大学官网公开组图' : '📷 校园实景图（待补充，敬请期待）' }}</div>
      <div class="close" @click="active = null">收起</div>
    </div>
  </section>
</template>

<script setup>
import { ref } from 'vue'

const emit = defineEmits(['nav'])
const active = ref(null)
const spots = [
  { name: '图书馆（北馆）', x: 70, y: 30, icon: '📚', desc: '李文正馆，馆内安静，适合自习与参观。' },
  { name: '老图书馆', x: 60, y: 36, icon: '📚', desc: '清华早期四大建筑之一，红砖坡顶。' },
  { name: '大礼堂', x: 46, y: 42, icon: '🏛️', desc: '与大草坪、日晷构成校园中轴经典景观。' },
  { name: '二校门', x: 48, y: 58, icon: '🏛️', desc: '清华标志性白色牌坊，最热门拍照点。' },
  { name: '近春园（荷塘）', x: 28, y: 68, icon: '🌊', desc: '朱自清《荷塘月色》笔下的荷塘。' },
  { name: '观畴园（食堂）', x: 34, y: 22, icon: '🍚', desc: '万人食堂，菜品丰富、性价比高。' },
  { name: '清芬园（食堂）', x: 56, y: 64, icon: '🍜', desc: '中部主要食堂，风味档口多。' },
  { name: '紫操', x: 72, y: 14, icon: '🏃', desc: '紫荆操场，夜跑与社团活动常用场地。' },
  { name: '艺术博物馆', x: 78, y: 84, icon: '🖼️', desc: '校园东南角，常设校藏与专题大展。' },
  { name: '东门', x: 90, y: 46, icon: '🚪', desc: '东侧校门，临近东区教学科研楼群。' }
]
</script>

<template>
  <section class="screen active" id="screen-map">
    <div class="topbar">
      <div class="back" @click="$emit('nav', 'guide')">‹</div>
      <div class="t">清华园地图</div>
    </div>
    <div class="scroll">
      <div class="map-board">
        <div class="map-grid" />
        <button
          v-for="s in spots"
          :key="s.name"
          type="button"
          class="map-spot"
          :class="{ on: active === s }"
          :style="{ left: s.x + '%', top: s.y + '%' }"
          @click="active = s"
        >
          <span>{{ s.icon }}</span>
        </button>
        <div v-if="active" class="map-detail">
          <b>{{ active.name }}</b>
          <span>{{ active.desc }}</span>
        </div>
        <div v-else class="map-hint">点击地标查看简介</div>
      </div>
      <div class="sa" style="padding:10px 2px;line-height:1.7">文旅图风格全景导览，非导航底图；实际路线以校园地图和现场指示为准。</div>
    </div>
  </section>
</template>

<style scoped>
.map-board {
  position: relative;
  height: 480px;
  border-radius: 20px;
  overflow: hidden;
  background: linear-gradient(145deg, #F8F4FE, #EADFF8);
  border: 1px solid var(--line);
  margin-bottom: 12px;
}
.map-grid {
  position: absolute;
  inset: 0;
  background-image: linear-gradient(rgba(91,42,145,.06) 1px, transparent 1px), linear-gradient(90deg, rgba(91,42,145,.06) 1px, transparent 1px);
  background-size: 28px 28px;
}
.map-spot {
  position: absolute;
  transform: translate(-50%, -50%);
  width: 34px; height: 34px; border-radius: 50%;
  border: 2px solid #fff; background: #5B2A91; color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-size: 15px; box-shadow: 0 4px 12px rgba(59,19,95,.2);
}
.map-spot.on { background: #C8A96A; transform: translate(-50%, -50%) scale(1.15); }
.map-detail {
  position: absolute; left: 12px; right: 12px; bottom: 12px;
  background: rgba(255,255,255,.96); border: 1px solid var(--line);
  border-radius: 13px; padding: 10px 12px; display: flex; flex-direction: column; gap: 3px;
}
.map-detail b { font-size: 12px; }
.map-detail span { font-size: 10px; color: var(--sub); line-height: 1.5; }
.map-hint { position: absolute; left: 12px; bottom: 12px; font-size: 9px; color: var(--sub); }
</style>

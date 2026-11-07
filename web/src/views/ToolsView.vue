<script setup>
import { computed, ref } from 'vue'

const emit = defineEmits(['nav'])
const props = defineProps({ mode: { type: String, default: 'lend' } })

const lend = [
  { cat: 'repair', title: '螺丝刀套装', desc: '常用家用，用后请归还。', loc: '紫荆公寓', status: '出借中', act: '借出' },
  { cat: 'life', title: '打气筒', desc: '自行车打气。', loc: '学生区', status: '出借中', act: '借出' },
  { cat: 'office', title: '打印机', desc: '支持双面打印，请爱护。', loc: '宿舍区', status: '出借中', act: '借出' },
  { cat: 'repair', title: '万用表', desc: '电子实验借用。', loc: '实验室', status: '出借中', act: '借出' }
]
const services = [
  { cat: 'electronics', title: '更换纽扣电池', desc: '手表 / 体温计 / 车钥匙等小型电池更换。', loc: '可约 3 人', status: '可约', act: '预约' },
  { cat: 'card', title: '配置卡通门禁卡', desc: '复制 / 写入校园卡通门禁卡，需本人授权。', loc: '可约 2 人', status: '可约', act: '预约' },
  { cat: 'life', title: '修拉链 / 缝扣子', desc: '衣物小修小补，工具自备。', loc: '可约 5 人', status: '可约', act: '预约' }
]
const borrow = [
  { cat: 'office', title: '求借：订书机', desc: '装订作业用半天。', loc: '文科图书馆', status: '求借中', act: '我提供' },
  { cat: 'outdoor', title: '求借：帐篷', desc: '周末露营活动。', loc: '操场', status: '求借中', act: '我提供' }
]
const needs = [
  { cat: 'watch', title: '求换手表电池', desc: '紫荆 12 号楼，今晚前，提供电池。', loc: '紫荆 12 号楼', status: '求服务', act: '我接单' },
  { cat: 'card', title: '求配一张门禁卡', desc: '老馆自习室，周末，需现场。', loc: '老馆自习室', status: '求服务', act: '我接单' },
  { cat: 'bag', title: '求修书包拉链', desc: '明早课前，提供针线。', loc: '明早课前', status: '求服务', act: '我接单' }
]
const tab = ref(props.mode === 'borrow' ? 'borrow' : 'lend')
const tabs = computed(() => props.mode === 'borrow'
  ? [{ id: 'borrow', name: '求借工具' }, { id: 'need', name: '求服务' }]
  : [{ id: 'lend', name: '出借工具' }, { id: 'service', name: '提供服务' }])
const list = computed(() => tab.value === 'lend' ? lend : tab.value === 'service' ? services : tab.value === 'borrow' ? borrow : needs)
const title = computed(() => props.mode === 'borrow' ? '求借求助' : '出借工具')
</script>

<template>
  <section class="screen active" id="screen-tools">
    <div class="topbar">
      <div class="back" @click="$emit('nav', 'help')">‹</div>
      <div class="t">{{ title }}</div>
    </div>
    <div class="scroll">
      <div class="tabs">
        <span v-for="t in tabs" :key="t.id" :class="{ on: tab === t.id }" @click="tab = t.id">{{ t.name }}</span>
      </div>
      <div class="vue-list">
        <article v-for="it in list" :key="it.title" class="item">
          <div class="thumb">🛠️</div>
          <div class="body">
            <div class="tt"><span class="src-tag">{{ it.status }}</span>{{ it.title }}</div>
            <div class="dd">{{ it.desc }}</div>
            <div class="row">
              <span class="meta">📍 {{ it.loc }}</span>
              <button type="button" class="btn">{{ it.act }}</button>
            </div>
          </div>
        </article>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'

const emit = defineEmits(['nav'])
const item = computed(() => {
  try { return JSON.parse(sessionStorage.getItem('sg:lastResult') || '{}') } catch (e) { return {} }
})
const approved = computed(() => item.value.status === 'approved')
</script>

<template>
  <section class="screen active" id="screen-success">
    <div class="topbar">
      <div class="back" @click="$emit('nav', 'home')">‹</div>
      <div class="t">提交成功</div>
    </div>
    <div class="scroll">
      <div class="okpanel">
        <div class="big">✅</div>
        <h2>{{ approved ? '已发布成功' : '已提交，等待审核' }}</h2>
        <div class="okmeta">{{ item.title || '' }}</div>
        <p>{{ approved ? '其他同学已经可以在列表里看到这条信息。' : '审核通过后，其他同学才能在「失物招领 / 寻物启事」里看到这条信息。' }}</p>
        <p>你可以在「我的发布」里随时查看审核进度，也可以撤回删除。</p>
        <div class="okacts">
          <button class="btn" type="button" @click="$emit('nav', 'mine')">查看我的发布</button>
          <button class="btn ghost" type="button" @click="$emit('nav', 'publish')">继续发布一条</button>
        </div>
      </div>
      <div class="faq-note" style="margin-top:16px">💡 提交后由管理员审核，通过后其他同学就能在列表中看到；你可以在「我的发布」里随时查看进度。</div>
    </div>
  </section>
</template>

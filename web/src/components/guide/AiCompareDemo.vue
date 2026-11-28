<script setup>
defineEmits(['close'])
</script>

<template>
  <Teleport to="body">
    <div class="ai-demo-layer" @click.self="$emit('close')">
      <div class="ai-demo-card" role="dialog" aria-modal="true" aria-label="AI 对比示例">
        <div class="ai-demo-head">
          <div>
            <div class="ai-demo-kicker">AI 对比 · 示例报告</div>
            <h3>两件东西，像不像？</h3>
          </div>
          <button type="button" class="ai-demo-close" aria-label="关闭" @click="$emit('close')">✕</button>
        </div>

        <div class="ai-demo-score">
          <strong>92<small>%</small></strong>
          <span>AI 信息对比度</span>
          <i>建议先核对卡套与贴纸</i>
        </div>

        <div class="ai-demo-pair">
          <div class="ai-demo-item mine">
            <small>我发布的 · 寻物</small>
            <b>蓝色校园卡</b>
            <p>六教 3 区 · 11/28 08:40</p>
            <span>蓝色卡套 · 右下角白色贴纸</span>
          </div>
          <div class="ai-demo-vs">VS</div>
          <div class="ai-demo-item found">
            <small>匹配到的 · 招领</small>
            <b>一张校园卡</b>
            <p>六教门口 · 11/28 09:10</p>
            <span>蓝色卡套 · 边角有白色贴纸</span>
          </div>
        </div>

        <div class="ai-demo-rows">
          <div><span>物品类型</span><b>校园卡</b><i class="ok">一致</i></div>
          <div><span>颜色</span><b>蓝色</b><i class="ok">一致</i></div>
          <div><span>地点</span><b>六教 3 区 / 六教门口</b><i class="near">相近</i></div>
          <div><span>时间</span><b>08:40 / 09:10</b><i class="near">相近</i></div>
          <div><span>特征</span><b>蓝色卡套 / 白色贴纸</b><i class="ok">一致</i></div>
        </div>

        <div class="ai-demo-summary">
          <b>AI 参考总结</b>
          <p>两件物品的颜色、地点和关键特征高度重合，建议先核对卡套贴纸的位置，再发起认领。手机号默认打码，确认后再交换。</p>
        </div>

        <div class="ai-demo-note">
          这是引导里的示例数据。真实 AI 对比入口在「物品详情 → 与我发布的进行 AI 对比」，只和当前用户自己的发布比较。
        </div>
        <button type="button" class="ai-demo-btn" @click="$emit('close')">关闭示例，继续导览</button>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.ai-demo-layer { position: fixed; inset: 0; z-index: 10002; display: flex; align-items: center; justify-content: center; padding: 18px; background: rgba(7,3,12,.62); backdrop-filter: blur(3px); font-family: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif; }
.ai-demo-card { width: min(660px, 100%); max-height: min(88vh, 720px); overflow-y: auto; background: #fffdfb; color: #3b1d63; border-radius: 22px; padding: 22px 22px 18px; box-shadow: 0 28px 80px rgba(0,0,0,.35); scrollbar-width: none; }
.ai-demo-card::-webkit-scrollbar { display: none; }
.ai-demo-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; }
.ai-demo-kicker { color: #9b7b35; font-size: 10px; letter-spacing: .18em; }
.ai-demo-head h3 { margin: 4px 0 0; font-size: 21px; letter-spacing: .02em; }
.ai-demo-close { border: 0; background: #f4edf9; width: 30px; height: 30px; border-radius: 50%; color: #6b5a7c; cursor: pointer; }
.ai-demo-score { display: flex; align-items: baseline; gap: 8px; margin: 16px 0 12px; padding: 12px 14px; border-radius: 14px; background: linear-gradient(135deg,#fbf3df,#f4ecfb); border: 1px solid #ecdfc4; }
.ai-demo-score strong { color: #6f4a11; font-size: 34px; line-height: 1; }
.ai-demo-score strong small { font-size: 14px; margin-left: 1px; }
.ai-demo-score span { color: #6b5a7c; font-size: 10px; }
.ai-demo-score i { margin-left: auto; color: #8b6a25; font-size: 9px; font-style: normal; }
.ai-demo-pair { display: grid; grid-template-columns: 1fr 30px 1fr; gap: 7px; align-items: stretch; }
.ai-demo-item { min-width: 0; border: 1px solid #eadff5; border-radius: 13px; padding: 11px; background: #fff; }
.ai-demo-item.found { border-color: #e4d3b4; background: #fffaf0; }
.ai-demo-item small { color: #9a8aa8; font-size: 8px; letter-spacing: .06em; }
.ai-demo-item b { display: block; margin-top: 4px; font-size: 14px; color: #3b1d63; }
.ai-demo-item p { margin: 4px 0 0; color: #8b7a9a; font-size: 9px; }
.ai-demo-item span { display: block; margin-top: 5px; color: #6f5e80; font-size: 9px; line-height: 1.5; }
.ai-demo-vs { align-self: center; text-align: center; color: #b49a5c; font-size: 9px; font-weight: 700; }
.ai-demo-rows { margin-top: 12px; border: 1px solid #eee5f6; border-radius: 13px; overflow: hidden; }
.ai-demo-rows > div { display: grid; grid-template-columns: 70px 1fr auto; gap: 8px; align-items: center; padding: 8px 11px; border-top: 1px solid #f2ebf8; font-size: 10px; }
.ai-demo-rows > div:first-child { border-top: 0; }
.ai-demo-rows span { color: #9a8aa8; }
.ai-demo-rows b { color: #4d3b60; font-weight: 500; }
.ai-demo-rows i { font-style: normal; font-size: 9px; border-radius: 99px; padding: 3px 7px; }
.ai-demo-rows i.ok { background: #eaf7ef; color: #2f7a4f; }
.ai-demo-rows i.near { background: #fbf2de; color: #8a641f; }
.ai-demo-summary { margin-top: 12px; border-radius: 12px; padding: 11px 12px; background: #f7f2fc; border: 1px solid #eadff5; }
.ai-demo-summary b { color: #5b2a91; font-size: 10px; }
.ai-demo-summary p { margin: 4px 0 0; color: #6f5e80; font-size: 10px; line-height: 1.7; }
.ai-demo-note { margin-top: 10px; color: #9a8aa8; font-size: 9px; line-height: 1.6; }
.ai-demo-btn { width: 100%; margin-top: 13px; border: 0; border-radius: 10px; background: #5b2a91; color: #fff; padding: 10px; font: inherit; font-size: 11px; font-weight: 600; cursor: pointer; }
@media (max-width: 620px) {
  .ai-demo-layer { padding: 10px; align-items: flex-end; }
  .ai-demo-card { max-height: 88vh; padding: 17px 15px 14px; border-radius: 18px; }
  .ai-demo-head h3 { font-size: 18px; }
  .ai-demo-pair { grid-template-columns: 1fr; }
  .ai-demo-vs { padding: 1px 0; }
  .ai-demo-score i { display: none; }
  .ai-demo-rows > div { grid-template-columns: 62px 1fr auto; }
}
</style>

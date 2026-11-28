import { createApp } from 'vue'
import App from './App.vue'
import { api } from './api'
import './styles/base.css'
import './styles/aurora.css'
import './styles/unified.css'

async function boot() {
  try {
    // 先确认公共数据接口已经能用，再挂载应用和放行。
    await Promise.all([
      api.items(true),
      api.items(false),
      api.announcements()
    ])
  } catch (e) {
    // 后端没准备好：继续留在 HTML 等待页，稍后重试。
    setTimeout(boot, 2500)
    return
  }

  createApp(App).mount('#app')

  // 等首页/列表把第一屏数据放好；最多等 1.5 秒。
  await new Promise((resolve) => {
    let done = false
    const finish = () => {
      if (done) return
      done = true
      window.removeEventListener('sg:home-ready', finish)
      resolve()
    }
    window.addEventListener('sg:home-ready', finish)
    setTimeout(finish, 1500)
  })
  window.dispatchEvent(new Event('sg:app-ready'))
}

boot()

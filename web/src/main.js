import { createApp } from 'vue'
import App from './App.vue'
import './styles/base.css'
import './styles/aurora.css'
import './styles/unified.css'

createApp(App).mount('#app')
window.dispatchEvent(new Event('sg:app-ready'))

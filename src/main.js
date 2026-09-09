import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import AppIcon from './components/AppIcon.vue'
import 'vant/lib/index.css'
import './styles/global.css'

const app = createApp(App)
app.use(createPinia())
app.use(router)
// 全局统一线性图标（简洁现代）：<AppIcon name="home" :size="22" />
app.component('AppIcon', AppIcon)
app.mount('#app')

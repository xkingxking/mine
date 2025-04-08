import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'
import router from './router'
import axios from 'axios'
import '@fortawesome/fontawesome-free/css/all.css'
import '@fortawesome/fontawesome-free/css/all.min.css'

// 配置axios默认值
axios.defaults.baseURL = '/api/v1'
axios.defaults.headers.common['Content-Type'] = 'application/json'

const app = createApp(App)
app.use(ElementPlus)
app.use(router)
app.mount('#app')
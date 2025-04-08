import axios from 'axios'
import { ElMessage } from 'element-plus'

// 创建 axios 实例
const service = axios.create({
  baseURL: 'http://localhost:5000', // 后端 API 地址
  timeout: 5000,
  withCredentials: true, // 允许携带凭证
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
service.interceptors.request.use(
  config => {
    // 可以在这里添加 token 等认证信息
    return config
  },
  error => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
service.interceptors.response.use(
  response => {
    const res = response.data
    if (res.status === 'error') {
      ElMessage.error(res.error || '请求失败')
      return Promise.reject(new Error(res.error || '请求失败'))
    }
    return res
  },
  error => {
    console.error('响应错误:', error)
    ElMessage.error(error.message || '请求失败')
    return Promise.reject(error)
  }
)

export default service 
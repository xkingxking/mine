import request from '@/utils/request'

// 获取测试任务列表
export function getTestList(params) {
  return request({
    url: '/tests',
    method: 'get',
    params
  })
}

// 创建测试任务
export function createTest(data) {
  return request({
    url: '/evaluate',
    method: 'post',
    data,
    timeout: 6000000, // 设置超时时间为 5 分钟
    headers: {
      'Content-Type': 'application/json'
    }
  })
}

// 获取测试详情
export function getTestDetail(id) {
  return request({
    url: `/tests/${id}`,
    method: 'get'
  })
}

// 导出测试报告
export function exportTestReport(id) {
  return request({
    url: `/tests/${id}/export`,
    method: 'get',
    responseType: 'blob'
  })
}

// 删除测试任务
export function deleteTest(id) {
  return request({
    url: `/tests/${id}`,
    method: 'delete'
  })
}

// 获取模型列表
export function getModelList() {
  return request({
    url: '/models',
    method: 'get'
  })
}

import request from '@/utils/request'

// 获取测试任务列表
export function getTestList(params) {
  return request({
    url: '/api/v1/tests',
    method: 'get',
    params
  })
}

// 创建测试任务
export function createTest(data) {
  return request({
    url: '/api/v1/evaluate',
    method: 'post',
    data,
    timeout: 300000, // 设置超时时间为 5 分钟
    headers: {
      'Content-Type': 'application/json'
    }
  })
}

// 获取测试详情
export function getTestDetail(id) {
  return request({
    url: `/api/v1/tests/${id}`,
    method: 'get'
  })
}

// 导出测试报告
export function exportTestReport(id) {
  return request({
    url: `/api/v1/tests/${id}/export`,
    method: 'get',
    responseType: 'blob'
  })
}

// 删除测试任务
export function deleteTest(id) {
  return request({
    url: `/api/v1/tests/${id}`,
    method: 'delete'
  })
}

// 获取模型列表
export function getModelList() {
  return request({
    url: '/api/v1/models',
    method: 'get'
  })
}

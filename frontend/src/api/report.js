import axios from 'axios';

const API_BASE_URL = '/api/v1';

export const reportApi = {
  // 获取报告列表
  getReports: async () => {
    const response = await axios.get(`${API_BASE_URL}/reports`);
    return response;
  },

  // 获取单个报告详情
  getReport: async (reportId) => {
    const response = await axios.get(`${API_BASE_URL}/reports/${reportId}`);
    return response;
  },

  // 获取图表文件
  getChartImage: async (chartPath) => {
    const response = await axios.get(`${API_BASE_URL}/static/${chartPath}`, {
      responseType: 'blob'
    });
    return URL.createObjectURL(response.data);
  },

  // 导出报告
  exportReport: async (reportId, format = 'pdf') => {
    const response = await axios.get(`${API_BASE_URL}/reports/${reportId}/export`, {
      params: { format },
      responseType: 'blob'
    });
    return response.data;
  }
}; 
import axios from 'axios';

// 更新API基础URL以连接到Flask后端
const API_BASE_URL = '';

// 从文件名中提取时间
const extractTimeFromPath = (path) => {
  const match = path.match(/(\d{8})_(\d{6})/);
  if (match) {
    const [_, date, time] = match;
    const year = date.slice(0, 4);
    const month = date.slice(4, 6);
    const day = date.slice(6, 8);
    const hour = time.slice(0, 2);
    const minute = time.slice(2, 4);
    const second = time.slice(4, 6);
    return new Date(`${year}-${month}-${day}T${hour}:${minute}:${second}`);
  }
  return new Date();
};

// 从文件路径中提取模型名
const extractModelFromPath = (path) => {
  const fileName = path.split('/').pop();
  const modelMatch = fileName.match(/^([^_]+)/);
  return modelMatch ? modelMatch[1] : '';
};

export const fileApi = {
  // 获取文件列表
  getFiles: async () => {
    try {
      // 使用真实API请求获取文件列表
      const response = await axios.get(`${API_BASE_URL}/files`);
      return response;
    } catch (error) {
      console.error('Error fetching files:', error);
      throw error;
    }
  },

  // 获取文件内容
  getFileContent: async (filePath) => {
    try {
      // 使用真实API请求获取文件内容
      const response = await axios.get(`${API_BASE_URL}/files/content`, {
        params: { path: filePath }
      });
      return response;
    } catch (error) {
      console.error('Error reading file:', error);
      throw error;
    }
  },

  // 下载文件 - 返回实际的数据
  downloadFile: async (filePath) => {
    try {
      // 使用真实API请求下载文件
      const response = await axios.get(`${API_BASE_URL}/files/download`, {
        params: { path: filePath },
        responseType: 'blob' // 指定响应类型为blob
      });
      
      // 添加自动下载功能
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filePath.split('/').pop() || 'download'); 
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      return response.data;
    } catch (error) {
      console.error('Error downloading file:', error);
      throw error;
    }
  },
  
  // 下载PDF格式的文件
  downloadPDF: async (filePath) => {
    try {
      // 使用真实API请求下载PDF文件
      const response = await axios.get(`${API_BASE_URL}/files/download-pdf`, {
        params: { path: filePath },
        responseType: 'blob' // 指定响应类型为blob
      });
      
      // 添加自动下载功能
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${extractModelFromPath(filePath)}_domain_report.pdf`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      return response.data;
    } catch (error) {
      console.error('Error downloading PDF:', error);
      throw error;
    }
  },

  // 获取目录下所有domains.json结尾的文件
  getDomainFiles: async (dirPath = null) => {
    try {
      // 构建请求参数
      const params = {};
      if (dirPath) {
        params.dirPath = dirPath;
      }
      
      // 使用真实API请求获取domains文件列表
      const response = await axios.get(`${API_BASE_URL}/files/domains`, {
        params
      });
      
      // 处理返回的数据，确保created_at是Date对象
      const files = Array.isArray(response.data) ? response.data.map(file => ({
        ...file,
        created_at: file.created_at ? new Date(file.created_at) : extractTimeFromPath(file.path)
      })) : [];
      
      return files;
    } catch (error) {
      console.error('Error scanning directory:', error);
      throw error;
    }
  },
  
  // 上传文件
  uploadFile: async (file, destination) => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      if (destination) {
        formData.append('destination', destination);
      }
      
      const response = await axios.post(`${API_BASE_URL}/files/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      
      return response;
    } catch (error) {
      console.error('Error uploading file:', error);
      throw error;
    }
  },
  
  // 删除文件
  deleteFile: async (filePath) => {
    try {
      const response = await axios.delete(`${API_BASE_URL}/files`, {
        params: { path: filePath }
      });
      
      return response;
    } catch (error) {
      console.error('Error deleting file:', error);
      throw error;
    }
  },
  
  // 获取模型领域比较数据
  getDomainComparisonData: async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/models/domain-comparison`);
      return response.data;
    } catch (error) {
      console.error('Error fetching domain comparison data:', error);
      throw error;
    }
  }
};
<template>
  <div class="file-list">
    <div class="header">
      <h1>领域评估报告列表</h1>
      <div class="header-actions">
        <div class="search-box">
          <input 
            type="text" 
            v-model="searchQuery" 
            placeholder="搜索报告..."
            @input="filterFiles"
          >
          <i class="fas fa-search"></i>
        </div>
      </div>
    </div>

    <div class="files-grid">
      <div v-for="file in filteredFiles" :key="file.id" class="file-card">
        <div class="file-header">
          <div class="file-title">
            <span class="model-name">{{ file.modelName }}</span>
            <h3>{{ file.name }}</h3>
          </div>
          <span class="file-type">{{ file.type }}</span>
        </div>
        <div class="file-info">
          <div class="info-item">
            <i class="fas fa-calendar"></i>
            <span>{{ formatDate(file.created_at) }}</span>
          </div>
          <div class="info-item">
            <i class="fas fa-file-alt"></i>
            <span>{{ file.size }}</span>
          </div>
        </div>
        <div class="file-actions">
          <button @click="viewFile(file)" class="btn-primary">
            <i class="fas fa-eye"></i> 查看
          </button>
          <div class="download-buttons">
            <button @click="downloadFile(file)" class="btn-secondary">
              <i class="fas fa-download"></i> 下载JSON
            </button>
            <button @click="downloadPdf(file)" class="btn-secondary btn-pdf">
              <i class="fas fa-file-pdf"></i> 下载PDF
            </button>
          </div>
        </div>
      </div>
    </div>

    <DomainReportDialog
      :show="showReportDialog"
      :file="currentFile"
      :content="reportContent"
      @close="closeReport"
    />

    <div v-if="filteredFiles.length === 0" class="no-files">
      <i class="fas fa-file-alt"></i>
      <p>暂无领域评估报告</p>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue';
import { fileApi } from '../api/file';
import DomainReportDialog from './DomainReportDialog.vue';

export default {
  name: 'FileList',
  components: {
    DomainReportDialog
  },
  setup() {
    const files = ref([]);
    const searchQuery = ref('');
    const showReportDialog = ref(false);
    const currentFile = ref(null);
    const reportContent = ref(null);

    const filteredFiles = computed(() => {
      if (!searchQuery.value) return files.value;
      const query = searchQuery.value.toLowerCase();
      return files.value.filter(file => 
        file.name.toLowerCase().includes(query) ||
        file.modelName.toLowerCase().includes(query) ||
        file.type.toLowerCase().includes(query)
      );
    });

    const fetchFiles = async () => {
      try {
        const response = await fileApi.getFiles();
        files.value = response.data.map(file => ({
          id: file.id,
          name: file.name,
          modelName: file.modelName,
          type: file.type,
          created_at: file.created_at,
          size: formatFileSize(file.size),
          path: file.path
        }));
      } catch (error) {
        console.error('获取文件列表失败:', error);
      }
    };

    const viewFile = async (file) => {
      try {
        currentFile.value = file;
        showReportDialog.value = true;
        reportContent.value = null;

        const response = await fileApi.getFileContent(file.path);
        reportContent.value = response.data;
      } catch (error) {
        console.error('查看文件失败:', error);
      }
    };

    const closeReport = () => {
      showReportDialog.value = false;
      currentFile.value = null;
      reportContent.value = null;
    };

    const downloadFile = async (file) => {
      try {
        // 使用 downloadFile API 下载原始 JSON 文件
        await fileApi.downloadFile(file.path);
      } catch (error) {
        console.error('下载文件失败:', error);
      }
    };

    const downloadPdf = async (file) => {
      try {
        // 显示下载中的提示
        const downloadingToast = document.createElement('div');
        downloadingToast.className = 'downloading-toast';
        downloadingToast.textContent = '正在生成PDF，请稍等...';
        document.body.appendChild(downloadingToast);
        
        // 使用 downloadPDF API 下载 PDF 格式的报告
        await fileApi.downloadPDF(file.path);
        
        // 移除提示
        document.body.removeChild(downloadingToast);
      } catch (error) {
        console.error('下载PDF文件失败:', error);
        alert(`下载PDF文件失败: ${error.message || '服务器错误'}`);
      }
    };

    const formatDate = (date) => {
      return new Date(date).toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      });
    };

    const formatFileSize = (bytes) => {
      if (!bytes) return 'N/A';
      const units = ['B', 'KB', 'MB', 'GB'];
      let size = bytes;
      let unitIndex = 0;
      while (size >= 1024 && unitIndex < units.length - 1) {
        size /= 1024;
        unitIndex++;
      }
      return `${size.toFixed(2)} ${units[unitIndex]}`;
    };

    onMounted(() => {
      fetchFiles();
    });

    return {
      files,
      filteredFiles,
      searchQuery,
      showReportDialog,
      currentFile,
      reportContent,
      viewFile,
      closeReport,
      downloadFile,
      downloadPdf,
      formatDate
    };
  }
};
</script>

<style scoped>
.file-list {
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.header h1 {
  color: #2c3e50;
  font-size: 2rem;
  margin: 0;
}

.search-box {
  position: relative;
  width: 300px;
}

.search-box input {
  width: 100%;
  padding: 0.8rem 1rem 0.8rem 2.5rem;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 1rem;
  transition: all 0.3s ease;
}

.search-box input:focus {
  outline: none;
  border-color: #4299e1;
  box-shadow: 0 0 0 3px rgba(66, 153, 225, 0.1);
}

.search-box i {
  position: absolute;
  left: 1rem;
  top: 50%;
  transform: translateY(-50%);
  color: #a0aec0;
}

.files-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 1.5rem;
}

.file-card {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.file-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 12px rgba(0, 0, 0, 0.1);
}

.file-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
}

.file-title {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.model-name {
  font-size: 0.875rem;
  font-weight: 600;
  color: #4299e1;
  text-transform: uppercase;
}

.file-header h3 {
  margin: 0;
  color: #2d3748;
  font-size: 1.25rem;
}

.file-type {
  background: #e2e8f0;
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.875rem;
  color: #4a5568;
}

.file-info {
  margin-bottom: 1.5rem;
}

.info-item {
  display: flex;
  align-items: center;
  margin-bottom: 0.5rem;
  color: #718096;
}

.info-item i {
  margin-right: 0.5rem;
  width: 1rem;
}

.file-actions {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.download-buttons {
  display: flex;
  gap: 0.75rem;
}

.btn-primary, .btn-secondary {
  padding: 0.75rem;
  border: none;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  transition: all 0.2s ease;
}

.btn-primary {
  background: #4299e1;
  color: white;
  width: 100%;
}

.btn-primary:hover {
  background: #3182ce;
}

.btn-secondary {
  background: #e2e8f0;
  color: #4a5568;
  flex: 1;
}

.btn-secondary:hover {
  background: #cbd5e0;
}

.btn-pdf {
  background: #f56565;
  color: white;
}

.btn-pdf:hover {
  background: #e53e3e;
}

.no-files {
  text-align: center;
  padding: 3rem;
  background: white;
  border-radius: 12px;
  color: #718096;
}

.no-files i {
  font-size: 3rem;
  margin-bottom: 1rem;
  color: #cbd5e0;
}

.no-files p {
  font-size: 1.25rem;
  margin: 0;
}

.downloading-toast {
  position: fixed;
  bottom: 2rem;
  left: 50%;
  transform: translateX(-50%);
  background-color: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 0.75rem 1.5rem;
  border-radius: 4px;
  z-index: 1100;
  font-size: 1rem;
}
</style>
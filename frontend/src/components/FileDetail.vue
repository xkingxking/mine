<template>
  <div class="file-detail">
    <div class="file-header">
      <div class="header-content">
        <h1>{{ file.name }}</h1>
        <div class="header-meta">
          <span class="file-type">{{ file.type }}</span>
          <span class="timestamp">
            <i class="fas fa-calendar"></i>
            {{ formatDate(file.created_at) }}
          </span>
        </div>
      </div>
      <div class="header-actions">
        <button @click="downloadFile" class="btn-secondary">
          <i class="fas fa-download"></i> 下载文件
        </button>
      </div>
    </div>

    <div class="file-content">
      <!-- 文件内容 -->
      <section class="content-section">
        <h2><i class="fas fa-file-alt"></i> 文件内容</h2>
        <div class="content-display">
          <pre v-if="file.type === 'json'" class="json-content">{{ formattedContent }}</pre>
          <div v-else-if="file.type === 'image'" class="image-content">
            <img :src="file.url" :alt="file.name">
          </div>
          <div v-else class="text-content">{{ file.content }}</div>
        </div>
      </section>

      <!-- 相关文件 -->
      <section v-if="relatedFiles.length > 0" class="content-section">
        <h2><i class="fas fa-folder"></i> 相关文件</h2>
        <div class="related-files">
          <div v-for="relatedFile in relatedFiles" :key="relatedFile.path" class="related-file-card">
            <div class="file-info">
              <i class="fas" :class="getFileIcon(relatedFile.type)"></i>
              <div class="file-details">
                <h3>{{ relatedFile.name }}</h3>
                <p>{{ relatedFile.size }}</p>
              </div>
            </div>
            <div class="file-actions">
              <button @click="viewRelatedFile(relatedFile)" class="btn-primary">
                <i class="fas fa-eye"></i> 查看
              </button>
              <button @click="downloadRelatedFile(relatedFile)" class="btn-secondary">
                <i class="fas fa-download"></i> 下载
              </button>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { fileApi } from '../api/file';

export default {
  name: 'FileDetail',
  setup() {
    const route = useRoute();
    const file = ref({
      name: '',
      type: '',
      created_at: '',
      content: '',
      size: '',
      path: '',
      url: ''
    });
    const relatedFiles = ref([]);

    const formattedContent = computed(() => {
      if (file.value.type === 'json' && file.value.content) {
        try {
          return JSON.stringify(JSON.parse(file.value.content), null, 2);
        } catch (error) {
          return file.value.content;
        }
      }
      return file.value.content;
    });

    const fetchFile = async () => {
      try {
        const filePath = route.query.filePath;
        if (!filePath) return;

        const response = await fileApi.getFileContent(filePath);
        const fileData = response.data;
        
        file.value = {
          name: fileData.name,
          type: fileData.type,
          created_at: fileData.created_at,
          content: fileData.content,
          size: formatFileSize(fileData.size),
          path: filePath,
          url: fileData.type === 'image' ? fileData.url : ''
        };

        // 获取相关文件
        if (fileData.related_files) {
          relatedFiles.value = fileData.related_files.map(relatedFile => ({
            name: relatedFile.name,
            type: relatedFile.type,
            path: relatedFile.path,
            size: formatFileSize(relatedFile.size)
          }));
        }
      } catch (error) {
        console.error('获取文件详情失败:', error);
      }
    };

    const downloadFile = async () => {
      try {
        const blob = await fileApi.downloadFile(file.value.path);
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = file.value.name;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } catch (error) {
        console.error('下载文件失败:', error);
      }
    };

    const viewRelatedFile = (relatedFile) => {
      if (relatedFile.type === 'image') {
        window.open(relatedFile.url, '_blank');
      } else {
        // 处理其他类型文件的查看逻辑
        console.log('查看相关文件:', relatedFile);
      }
    };

    const downloadRelatedFile = async (relatedFile) => {
      try {
        const blob = await fileApi.downloadFile(relatedFile.path);
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = relatedFile.name;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } catch (error) {
        console.error('下载相关文件失败:', error);
      }
    };

    const formatDate = (date) => {
      return new Date(date).toLocaleString();
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

    const getFileIcon = (type) => {
      const icons = {
        'json': 'fa-file-code',
        'excel': 'fa-file-excel',
        'pdf': 'fa-file-pdf',
        'image': 'fa-file-image'
      };
      return icons[type] || 'fa-file';
    };

    onMounted(() => {
      fetchFile();
    });

    return {
      file,
      relatedFiles,
      formattedContent,
      downloadFile,
      viewRelatedFile,
      downloadRelatedFile,
      formatDate,
      getFileIcon
    };
  }
};
</script>

<style scoped>
.file-detail {
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
  background: #f7fafc;
  min-height: 100vh;
}

.file-header {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 2rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-content h1 {
  margin: 0;
  color: #2d3748;
  font-size: 1.875rem;
}

.header-meta {
  display: flex;
  gap: 1rem;
  margin-top: 0.5rem;
  color: #718096;
}

.file-type {
  background: #e2e8f0;
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.875rem;
}

.timestamp {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.content-section {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 2rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.content-section h2 {
  margin: 0 0 1.5rem 0;
  color: #2d3748;
  font-size: 1.5rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.content-display {
  background: #f8fafc;
  border-radius: 8px;
  padding: 1rem;
  overflow-x: auto;
}

.json-content {
  margin: 0;
  white-space: pre-wrap;
  font-family: monospace;
  font-size: 0.875rem;
  line-height: 1.5;
  color: #2d3748;
}

.image-content {
  display: flex;
  justify-content: center;
  align-items: center;
}

.image-content img {
  max-width: 100%;
  max-height: 500px;
  object-fit: contain;
}

.text-content {
  margin: 0;
  white-space: pre-wrap;
  font-family: monospace;
  font-size: 0.875rem;
  line-height: 1.5;
  color: #2d3748;
}

.related-files {
  display: grid;
  gap: 1rem;
}

.related-file-card {
  background: #f8fafc;
  border-radius: 8px;
  padding: 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.file-info i {
  font-size: 1.5rem;
  color: #4a5568;
}

.file-details h3 {
  margin: 0;
  color: #2d3748;
  font-size: 1rem;
}

.file-details p {
  margin: 0.25rem 0 0 0;
  color: #718096;
  font-size: 0.875rem;
}

.file-actions {
  display: flex;
  gap: 0.5rem;
}

.btn-primary, .btn-secondary {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.2s ease;
}

.btn-primary {
  background: #4299e1;
  color: white;
}

.btn-primary:hover {
  background: #3182ce;
}

.btn-secondary {
  background: #e2e8f0;
  color: #4a5568;
}

.btn-secondary:hover {
  background: #cbd5e0;
}
</style>
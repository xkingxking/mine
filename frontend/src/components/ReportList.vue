<template>
  <div class="report-list">
    <div class="header">
      <h1>评估报告列表</h1>
      <div class="header-actions">
        <div class="search-box">
          <input 
            type="text" 
            v-model="searchQuery" 
            placeholder="搜索报告..."
            @input="filterReports"
          >
          <i class="fas fa-search"></i>
        </div>
      </div>
    </div>

    <div class="reports-grid">
      <div v-for="report in filteredReports" :key="report.id" class="report-card">
        <div class="report-header">
          <h3>{{ report.title }}</h3>
          <span class="model-type">{{ report.model_type }}</span>
        </div>
        <div class="report-info">
          <div class="info-item">
            <i class="fas fa-calendar"></i>
            <span>{{ formatDate(report.created_at) }}</span>
          </div>
          <div class="info-item">
            <i class="fas fa-question-circle"></i>
            <span>{{ report.total_questions }} 道题目</span>
          </div>
        </div>
        <div class="report-actions">
          <button @click="viewReport(report.id)" class="btn-primary">
            <i class="fas fa-eye"></i> 查看详情
          </button>
          <button @click="exportReport(report.id)" class="btn-secondary">
            <i class="fas fa-download"></i> 导出报告
          </button>
        </div>
      </div>
    </div>

    <div v-if="filteredReports.length === 0" class="no-reports">
      <i class="fas fa-file-alt"></i>
      <p>暂无评估报告</p>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { reportApi } from '../api/report';

export default {
  name: 'ReportList',
  setup() {
    const router = useRouter();
    const reports = ref([]);
    const searchQuery = ref('');

    const filteredReports = computed(() => {
      if (!searchQuery.value) return reports.value;
      const query = searchQuery.value.toLowerCase();
      return reports.value.filter(report => 
        report.title.toLowerCase().includes(query) ||
        report.model_type.toLowerCase().includes(query)
      );
    });

    const fetchReports = async () => {
      try {
        const response = await reportApi.getReports();
        reports.value = response.data.map(report => ({
          id: report.id,
          title: `${report.model_type} 评估报告`,
          model_type: report.model_type,
          created_at: report.test_time,
          total_questions: report.total_questions,
          successful_responses: report.successful_responses,
          failed_responses: report.failed_responses
        }));
      } catch (error) {
        console.error('获取报告列表失败:', error);
      }
    };

    const viewReport = (reportId) => {
      router.push(`/reports/${reportId}`);
    };

    const exportReport = async (reportId) => {
      try {
        const blob = await reportApi.exportReport(reportId);
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `report-${reportId}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } catch (error) {
        console.error('导出报告失败:', error);
      }
    };

    const formatDate = (date) => {
      return new Date(date).toLocaleString();
    };

    onMounted(() => {
      fetchReports();
    });

    return {
      reports,
      filteredReports,
      searchQuery,
      viewReport,
      exportReport,
      formatDate
    };
  }
};
</script>

<style scoped>
.report-list {
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

.reports-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 1.5rem;
}

.report-card {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.report-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 12px rgba(0, 0, 0, 0.1);
}

.report-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
}

.report-header h3 {
  margin: 0;
  color: #2d3748;
  font-size: 1.25rem;
}

.model-type {
  background: #e2e8f0;
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.875rem;
  color: #4a5568;
}

.report-info {
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

.report-actions {
  display: flex;
  gap: 1rem;
}

.btn-primary, .btn-secondary {
  flex: 1;
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
}

.btn-primary:hover {
  background: #3182ce;
}

.btn-secondary {
  background: #edf2f7;
  color: #4a5568;
}

.btn-secondary:hover {
  background: #e2e8f0;
}

.no-reports {
  text-align: center;
  padding: 3rem;
  background: white;
  border-radius: 12px;
  color: #a0aec0;
}

.no-reports i {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.no-reports p {
  font-size: 1.25rem;
  margin: 0;
}
</style> 
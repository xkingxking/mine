<template>
  <div class="report-detail">
    <div class="report-header">
      <div class="header-content">
        <h1>{{ report.title }}</h1>
        <div class="header-meta">
          <span class="model-type">{{ report.model_info?.type }}</span>
          <span class="timestamp">
            <i class="fas fa-calendar"></i>
            {{ formatDate(report.created_at) }}
          </span>
        </div>
      </div>
      <div class="header-actions">
        <button @click="exportReport" class="btn-secondary">
          <i class="fas fa-download"></i> 导出报告
        </button>
      </div>
    </div>

    <div class="report-content">
      <!-- 基本信息 -->
      <section class="report-section">
        <h2><i class="fas fa-info-circle"></i> 基本信息</h2>
        <div class="info-grid">
          <div class="info-card">
            <div class="info-icon">
              <i class="fas fa-question-circle"></i>
            </div>
            <div class="info-content">
              <h3>总题目数</h3>
              <p>{{ report.test_statistics?.total_questions || 0 }}</p>
            </div>
          </div>
          <div class="info-card">
            <div class="info-icon">
              <i class="fas fa-check-circle"></i>
            </div>
            <div class="info-content">
              <h3>成功率</h3>
              <p>{{ report.test_statistics?.success_rate?.toFixed(1) || 0 }}%</p>
            </div>
          </div>
          <div class="info-card">
            <div class="info-icon">
              <i class="fas fa-clock"></i>
            </div>
            <div class="info-content">
              <h3>处理时间</h3>
              <p>{{ report.resource_usage?.processing_time || 'N/A' }}</p>
            </div>
          </div>
        </div>
      </section>

      <!-- 性能指标 -->
      <section class="report-section">
        <h2><i class="fas fa-chart-line"></i> 性能指标</h2>
        <div class="metrics-grid">
          <div class="metric-card">
            <h3>安全性评分</h3>
            <div class="score-circle" :class="getScoreClass(report.performance_metrics?.average_safety_score)">
              {{ (report.performance_metrics?.average_safety_score * 100).toFixed(1) }}%
            </div>
          </div>
          <div class="metric-card">
            <h3>准确性评分</h3>
            <div class="score-circle" :class="getScoreClass(report.performance_metrics?.average_accuracy_score)">
              {{ (report.performance_metrics?.average_accuracy_score * 100).toFixed(1) }}%
            </div>
          </div>
        </div>
      </section>

      <!-- 可视化图表 -->
      <section class="report-section">
        <h2><i class="fas fa-chart-bar"></i> 可视化分析</h2>
        <div class="charts-grid">
          <div v-for="chart in report.charts" :key="chart.type" class="chart-card">
            <h3>{{ getChartTitle(chart.type) }}</h3>
            <div class="chart-container">
              <img :src="chart.url" :alt="chart.type">
            </div>
          </div>
        </div>
      </section>

      <!-- 使用统计 -->
      <section class="report-section">
        <h2><i class="fas fa-database"></i> 使用统计</h2>
        <div class="usage-grid">
          <div class="usage-card">
            <h3>API调用次数</h3>
            <p>{{ report.usage_statistics?.total_calls || 0 }}</p>
          </div>
          <div class="usage-card">
            <h3>Token使用量</h3>
            <p>{{ report.usage_statistics?.total_tokens || 0 }}</p>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { reportApi } from '../api/report';

export default {
  name: 'ReportDetail',
  setup() {
    const route = useRoute();
    const report = ref({});

    const fetchReport = async () => {
      try {
        const response = await reportApi.getReport(route.params.id);
        const reportData = response.data;
        
        // 计算性能指标
        const totalQuestions = reportData.total_questions;
        const successfulResponses = reportData.successful_responses;
        const averageSafetyScore = reportData.detailed_results.reduce((acc, curr) => 
          acc + (curr.evaluation_results.safety.safety_score || 0), 0) / totalQuestions;
        const averageAccuracyScore = reportData.detailed_results.reduce((acc, curr) => 
          acc + (curr.evaluation_results.accuracy.accuracy_score || 0), 0) / totalQuestions;

        report.value = {
          id: route.params.id,
          title: `${reportData.model_type} 评估报告`,
          model_info: {
            type: reportData.model_type,
            name: reportData.model_name
          },
          created_at: reportData.test_time,
          test_statistics: {
            total_questions: totalQuestions,
            success_rate: (successfulResponses / totalQuestions) * 100
          },
          performance_metrics: {
            average_safety_score: averageSafetyScore,
            average_accuracy_score: averageAccuracyScore
          },
          usage_statistics: {
            total_calls: reportData.usage_stats.total_calls,
            total_tokens: reportData.usage_stats.total_tokens
          },
          detailed_results: reportData.detailed_results
        };
      } catch (error) {
        console.error('获取报告详情失败:', error);
      }
    };

    const exportReport = async () => {
      try {
        const blob = await reportApi.exportReport(route.params.id);
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `report-${route.params.id}.pdf`;
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

    const getScoreClass = (score) => {
      if (!score) return '';
      if (score >= 0.9) return 'score-excellent';
      if (score >= 0.8) return 'score-good';
      if (score >= 0.6) return 'score-pass';
      return 'score-fail';
    };

    const getChartTitle = (type) => {
      const titles = {
        'safety_distribution': '安全性评分分布',
        'accuracy_distribution': '准确性评分分布',
        'question_types': '题型分布',
        'domains': '领域分布'
      };
      return titles[type] || type;
    };

    onMounted(() => {
      fetchReport();
    });

    return {
      report,
      exportReport,
      formatDate,
      getScoreClass,
      getChartTitle
    };
  }
};
</script>

<style scoped>
.report-detail {
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
  background: #f7fafc;
  min-height: 100vh;
}

.report-header {
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

.model-type {
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

.report-section {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 2rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.report-section h2 {
  margin: 0 0 1.5rem 0;
  color: #2d3748;
  font-size: 1.5rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
}

.info-card {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: #f7fafc;
  border-radius: 8px;
}

.info-icon {
  width: 3rem;
  height: 3rem;
  background: #4299e1;
  color: white;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
}

.info-content h3 {
  margin: 0;
  color: #4a5568;
  font-size: 0.875rem;
}

.info-content p {
  margin: 0.25rem 0 0 0;
  color: #2d3748;
  font-size: 1.25rem;
  font-weight: 600;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
}

.metric-card {
  text-align: center;
}

.metric-card h3 {
  margin: 0 0 1rem 0;
  color: #4a5568;
}

.score-circle {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  font-weight: 600;
  margin: 0 auto;
}

.score-excellent {
  background: #48bb78;
  color: white;
}

.score-good {
  background: #4299e1;
  color: white;
}

.score-pass {
  background: #ecc94b;
  color: #2d3748;
}

.score-fail {
  background: #f56565;
  color: white;
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 1.5rem;
}

.chart-card {
  background: #f7fafc;
  border-radius: 8px;
  padding: 1rem;
}

.chart-card h3 {
  margin: 0 0 1rem 0;
  color: #4a5568;
}

.chart-container {
  width: 100%;
  height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chart-container img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.usage-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
}

.usage-card {
  background: #f7fafc;
  border-radius: 8px;
  padding: 1.5rem;
  text-align: center;
}

.usage-card h3 {
  margin: 0 0 0.5rem 0;
  color: #4a5568;
}

.usage-card p {
  margin: 0;
  color: #2d3748;
  font-size: 1.5rem;
  font-weight: 600;
}

.btn-secondary {
  padding: 0.75rem 1.5rem;
  background: #edf2f7;
  color: #4a5568;
  border: none;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.2s ease;
}

.btn-secondary:hover {
  background: #e2e8f0;
}
</style> 
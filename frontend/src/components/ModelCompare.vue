<template>
  <div class="model-compare">
    <div class="header">
      <div class="header-title">
        <h1>模型领域能力比较</h1>
        <p class="subtitle">此页面显示了所有模型在各个领域的评分比较，帮助您了解不同模型的优势和不足</p>
      </div>
      <div class="header-actions">
        <div class="view-selector">
          <el-radio-group v-model="viewMode" size="large">
            <el-radio-button label="table">表格视图</el-radio-button>
            <el-radio-button label="chart">图表视图</el-radio-button>
          </el-radio-group>
        </div>
      </div>
    </div>

    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="10" animated />
    </div>

    <template v-else>
      <!-- 表格视图 -->
      <div v-if="viewMode === 'table'" class="table-view">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>模型领域能力评分表</span>
              <el-button type="primary" @click="exportTable">
                <i class="fas fa-download"></i> 导出数据
              </el-button>
            </div>
          </template>
          
          <el-table
            :data="tableData"
            style="width: 100%"
            border
            :span-method="mergeModelColumn"
          >
            <el-table-column label="模型" prop="model" fixed="left" min-width="120">
              <template #header>
                <div class="custom-header">
                  <span>模型</span>
                  <el-tooltip content="按模型名称排序" placement="top">
                    <el-button size="small" circle @click="sortByModel">
                      <i class="fas" :class="sortDir === 'asc' ? 'fa-sort-alpha-down' : 'fa-sort-alpha-up'"></i>
                    </el-button>
                  </el-tooltip>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="领域" prop="domain" min-width="150" />
            <el-table-column label="评分" prop="score" min-width="100">
              <template #default="scope">
                <el-progress 
                  :percentage="scope.row.score * 100" 
                  :color="getScoreColor(scope.row.score)"
                  :format="(p) => p.toFixed(1) + '%'"
                />
              </template>
            </el-table-column>
            <el-table-column label="评测次数" prop="evaluations" width="100" />
          </el-table>
        </el-card>
      </div>

      <!-- 图表视图 -->
      <div v-else-if="viewMode === 'chart'" class="chart-view">
        <div class="chart-container">
          <el-tabs type="border-card" v-model="activeTab">
            <el-tab-pane label="雷达图" name="radar">
              <div ref="radarChartRef" class="chart"></div>
            </el-tab-pane>
            <el-tab-pane label="热力图" name="heatmap">
              <div ref="heatmapChartRef" class="chart"></div>
            </el-tab-pane>
            <el-tab-pane label="柱状图" name="bar">
              <div ref="barChartRef" class="chart"></div>
            </el-tab-pane>
          </el-tabs>
        </div>
        
        <el-card shadow="hover" class="model-ranking">
          <template #header>
            <div class="card-header">
              <span>模型综合排名</span>
            </div>
          </template>
          
          <div class="ranking-list">
            <div 
              v-for="(model, index) in modelRanking" 
              :key="model.name"
              class="ranking-item"
            >
              <div class="rank">{{ index + 1 }}</div>
              <div class="model-info">
                <h3>{{ model.name }}</h3>
                <div class="score-info">
                  <el-progress 
                    :percentage="model.score * 100" 
                    :color="getScoreColor(model.score)"
                    :format="(p) => p.toFixed(2) + '%'"
                    :stroke-width="12"
                  />
                </div>
              </div>
              <div class="score">{{ (model.score * 100).toFixed(2) }}%</div>
            </div>
          </div>
        </el-card>
      </div>
    </template>
  </div>
</template>

<script>
import { ref, reactive, computed, watch, onMounted, nextTick } from 'vue';
import { fileApi } from '../api/file';
import * as echarts from 'echarts';
import * as XLSX from 'xlsx';

export default {
  name: 'ModelCompare',
  setup() {
    // 状态变量
    const loading = ref(true);
    const viewMode = ref('table');
    const domains = ref([]);
    const models = ref([]);
    const comparisonData = ref({});
    const sortDir = ref('asc');
    const activeTab = ref('radar');
    
    // 图表引用
    const radarChartRef = ref(null);
    const heatmapChartRef = ref(null);
    const barChartRef = ref(null);
    let radarChart = null;
    let heatmapChart = null;
    let barChart = null;
    
    // 计算表格数据
    const tableData = computed(() => {
      const data = [];
      
      if (!comparisonData.value.scores) return data;
      
      for (const modelName of models.value) {
        const modelScores = comparisonData.value.scores[modelName] || {};
        
        for (const domainName of domains.value) {
          const domainData = modelScores[domainName] || { average_score: 0, total_evaluations: 0 };
          
          data.push({
            model: modelName,
            domain: domainName,
            score: domainData.average_score,
            evaluations: domainData.total_evaluations
          });
        }
      }
      
      return data;
    });
    
    // 合并模型列
    const mergeModelColumn = ({ row, column, rowIndex, columnIndex }) => {
      if (columnIndex === 0) {
        const modelRows = tableData.value.filter(item => item.model === row.model);
        const firstIndex = tableData.value.findIndex(item => item.model === row.model);
        
        if (rowIndex === firstIndex) {
          return {
            rowspan: modelRows.length,
            colspan: 1
          };
        } else {
          return {
            rowspan: 0,
            colspan: 0
          };
        }
      }
      
      return {
        rowspan: 1,
        colspan: 1
      };
    };
    
    // 计算模型排名
    const modelRanking = computed(() => {
      if (!comparisonData.value.scores) return [];
      
      const ranking = [];
      
      for (const modelName of models.value) {
        const modelScores = comparisonData.value.scores[modelName] || {};
        let totalScore = 0;
        let validDomains = 0;
        
        for (const domainName of domains.value) {
          const domainData = modelScores[domainName];
          if (domainData && domainData.average_score > 0) {
            totalScore += domainData.average_score;
            validDomains++;
          }
        }
        
        const avgScore = validDomains > 0 ? totalScore / validDomains : 0;
        
        ranking.push({
          name: modelName,
          score: avgScore,
          domains: validDomains
        });
      }
      
      // 按分数降序排列
      return ranking.sort((a, b) => b.score - a.score);
    });
    
    // 获取比较数据
    const fetchComparisonData = async () => {
      try {
        loading.value = true;
        comparisonData.value = await fileApi.getDomainComparisonData();
        domains.value = comparisonData.value.domains || [];
        models.value = comparisonData.value.models || [];
        
        loading.value = false;
        
        // 加载完数据后初始化图表
        if (viewMode.value === 'chart') {
          nextTick(() => {
            initCharts();
          });
        }
      } catch (error) {
        console.error('获取模型比较数据失败:', error);
        loading.value = false;
      }
    };
    
    // 获取评分颜色
    const getScoreColor = (score) => {
      if (score >= 0.9) return '#67C23A';  // 优秀 - 绿色
      if (score >= 0.8) return '#409EFF';  // 良好 - 蓝色
      if (score >= 0.6) return '#E6A23C';  // 及格 - 黄色
      return '#F56C6C';  // 不及格 - 红色
    };
    
    // 按模型名称排序
    const sortByModel = () => {
      sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc';
      models.value.sort((a, b) => {
        return sortDir.value === 'asc' 
          ? a.localeCompare(b) 
          : b.localeCompare(a);
      });
    };
    
    // 导出表格数据
    const exportTable = () => {
      // 创建工作簿
      const wb = XLSX.utils.book_new();
      
      // 准备数据
      const exportData = tableData.value.map(row => ({
        '模型': row.model,
        '领域': row.domain,
        '评分': row.score.toFixed(4),
        '评测次数': row.evaluations
      }));
      
      // 创建工作表
      const ws = XLSX.utils.json_to_sheet(exportData);
      
      // 添加工作表到工作簿
      XLSX.utils.book_append_sheet(wb, ws, '模型领域评分比较');
      
      // 导出文件
      XLSX.writeFile(wb, '模型领域评分比较.xlsx');
    };
    
    // 初始化图表
    const initCharts = () => {
      nextTick(() => {
        initRadarChart();
        initHeatmapChart();
        initBarChart();
        
        // 监听窗口大小变化，调整图表大小
        window.addEventListener('resize', () => {
          if (radarChart) radarChart.resize();
          if (heatmapChart) heatmapChart.resize();
          if (barChart) barChart.resize();
        });
      });
    };
    
    // 初始化雷达图
    const initRadarChart = () => {
      if (!radarChartRef.value) return;
      
      // 销毁已有实例
      if (radarChart) {
        radarChart.dispose();
      }
      
      // 创建新实例
      radarChart = echarts.init(radarChartRef.value);
      
      // 准备数据
      const indicator = domains.value.map(domain => ({
        name: domain,
        max: 1
      }));
      
      const seriesData = models.value.map(model => {
        const dataPoints = domains.value.map(domain => {
          const domainData = comparisonData.value.scores[model] 
            ? comparisonData.value.scores[model][domain] || { average_score: 0 }
            : { average_score: 0 };
          return domainData.average_score;
        });
        
        return {
          name: model,
          value: dataPoints
        };
      });
      
      // 设置配置
      const option = {
        title: {
          text: '模型领域能力雷达图',
          left: 'center'
        },
        tooltip: {
          trigger: 'item'
        },
        legend: {
          type: 'scroll',
          bottom: 10,
          data: models.value
        },
        radar: {
          indicator: indicator,
          shape: 'circle',
          splitNumber: 5,
          axisName: {
            color: '#333',
            fontSize: 12,
            padding: [3, 5]
          }
        },
        series: [
          {
            type: 'radar',
            emphasis: {
              lineStyle: {
                width: 4
              }
            },
            data: seriesData
          }
        ]
      };
      
      // 应用配置
      radarChart.setOption(option);
    };
    
    // 初始化热力图
    const initHeatmapChart = () => {
      if (!heatmapChartRef.value) return;
      
      // 销毁已有实例
      if (heatmapChart) {
        heatmapChart.dispose();
      }
      
      // 创建新实例
      heatmapChart = echarts.init(heatmapChartRef.value);
      
      // 准备数据
      const yCategories = models.value;
      const xCategories = domains.value;
      
      const data = [];
      for (let i = 0; i < yCategories.length; i++) {
        for (let j = 0; j < xCategories.length; j++) {
          const model = yCategories[i];
          const domain = xCategories[j];
          
          const domainData = comparisonData.value.scores[model] 
            ? comparisonData.value.scores[model][domain] || { average_score: 0 }
            : { average_score: 0 };
          
          data.push([j, i, (domainData.average_score * 100).toFixed(2)]);
        }
      }
      
      // 设置配置 - 使用常规热力图颜色
      const option = {
        title: {
          text: '模型-领域能力热力图',
          left: 'center'
        },
        tooltip: {
          position: 'top',
          formatter: function (params) {
            return `模型: ${yCategories[params.value[1]]}<br>` +
                   `领域: ${xCategories[params.value[0]]}<br>` +
                   `评分: ${params.value[2]}%`;
          }
        },
        grid: {
          top: 60,
          bottom: 60,
          left: 100,
          right: 60
        },
        xAxis: {
          type: 'category',
          data: xCategories,
          splitArea: {
            show: true
          },
          axisLabel: {
            rotate: 45
          }
        },
        yAxis: {
          type: 'category',
          data: yCategories,
          splitArea: {
            show: true
          }
        },
        visualMap: {
          min: 0,
          max: 100,
          calculable: true,
          orient: 'horizontal',
          left: 'center',
          bottom: 10,
          // 使用常规热力图颜色
          inRange: {
            color: ['#313695', '#4575b4', '#74add1', '#abd9e9', '#e0f3f8', 
                   '#ffffbf', '#fee090', '#fdae61', '#f46d43', '#d73027', '#a50026']
          }
        },
        series: [
          {
            type: 'heatmap',
            data: data,
            label: {
              show: true,
              formatter: function (params) {
                return params.value[2] + '%';
              }
            },
            emphasis: {
              itemStyle: {
                shadowBlur: 10,
                shadowColor: 'rgba(0, 0, 0, 0.5)'
              }
            }
          }
        ]
      };
      
      // 应用配置
      heatmapChart.setOption(option);
    };
    
    // 初始化柱状图（替代树图）
    const initBarChart = () => {
      if (!barChartRef.value) return;
      
      // 销毁已有实例
      if (barChart) {
        barChart.dispose();
      }
      
      // 创建新实例
      barChart = echarts.init(barChartRef.value);
      
      // 准备数据
      const xAxisData = domains.value;
      const series = models.value.map(model => {
        const modelData = domains.value.map(domain => {
          const domainData = comparisonData.value.scores[model] 
            ? comparisonData.value.scores[model][domain] || { average_score: 0 }
            : { average_score: 0 };
          return (domainData.average_score * 100).toFixed(2);
        });
        
        return {
          name: model,
          type: 'bar',
          data: modelData,
          label: {
            show: true,
            position: 'top',
            formatter: '{c}%'
          }
        };
      });
      
      // 设置配置
      const option = {
        title: {
          text: '模型各领域能力柱状图',
          left: 'center'
        },
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'shadow'
          },
          formatter: function (params) {
            let res = `${params[0].axisValue}<br/>`;
            params.forEach(param => {
              res += `${param.seriesName}: ${param.value}%<br/>`;
            });
            return res;
          }
        },
        legend: {
          type: 'scroll',
          data: models.value,
          bottom: 10
        },
        grid: {
          top: 60,
          bottom: 90,
          left: 60,
          right: 40
        },
        xAxis: {
          type: 'category',
          data: xAxisData,
          axisLabel: {
            rotate: 45
          }
        },
        yAxis: {
          type: 'value',
          min: 0,
          max: 100,
          axisLabel: {
            formatter: '{value}%'
          }
        },
        series: series
      };
      
      // 应用配置
      barChart.setOption(option);
    };
    
    // 监听视图模式变化
    watch(viewMode, (newVal) => {
      if (newVal === 'chart') {
        nextTick(() => {
          initCharts();
        });
      }
    });
    
    // 监听活动选项卡变化
    watch(activeTab, (newVal) => {
      nextTick(() => {
        if (newVal === 'radar' && radarChart) radarChart.resize();
        if (newVal === 'heatmap' && heatmapChart) heatmapChart.resize();
        if (newVal === 'bar' && barChart) barChart.resize();
      });
    });
    
    // 组件挂载时加载数据
    onMounted(() => {
      fetchComparisonData();
    });
    
    return {
      loading,
      viewMode,
      domains,
      models,
      comparisonData,
      sortDir,
      activeTab,
      tableData,
      modelRanking,
      radarChartRef,
      heatmapChartRef,
      barChartRef,
      getScoreColor,
      mergeModelColumn,
      sortByModel,
      exportTable
    };
  }
}
</script>

<style scoped>
.model-compare {
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 2rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.header-title {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.header h1 {
  color: #2c3e50;
  font-size: 2rem;
  margin: 0;
}

.subtitle {
  color: #606266;
  margin: 0;
  max-width: 500px;
  line-height: 1.5;
}

.header-actions {
  display: flex;
  gap: 1rem;
  align-items: center;
  flex-wrap: wrap;
}

.loading-container {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
}

.table-view, .chart-view {
  margin-top: 1.5rem;
}

.custom-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chart-container {
  margin-bottom: 2rem;
}

.chart {
  height: 500px;
  margin-top: 1rem;
}

.model-ranking {
  margin-top: 2rem;
}

.ranking-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.ranking-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: #f9f9f9;
  border-radius: 8px;
  transition: all 0.2s;
}

.ranking-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.rank {
  font-size: 1.5rem;
  font-weight: bold;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: #409eff;
  color: white;
}

.ranking-item:nth-child(1) .rank {
  background: #67c23a;
}

.ranking-item:nth-child(2) .rank {
  background: #409eff;
}

.ranking-item:nth-child(3) .rank {
  background: #e6a23c;
}

.model-info {
  flex: 1;
}

.model-info h3 {
  margin: 0 0 0.5rem;
  font-size: 1.125rem;
}

.score {
  font-size: 1.25rem;
  font-weight: bold;
  color: #409eff;
}

@media (max-width: 768px) {
  .header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .header-actions {
    width: 100%;
    flex-direction: column;
    align-items: flex-start;
  }
  
  .chart {
    height: 350px;
  }
}
</style>
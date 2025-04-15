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
                  :format="(p) => p.toFixed(2) + '%'"
                />
              </template>
            </el-table-column>
            <el-table-column label="评测次数" prop="evaluations" width="100" />
          </el-table>
        </el-card>
      </div>

      <!-- 图表视图 -->
      <div v-else-if="viewMode === 'chart'" class="chart-view">
        <div class="chart-filters">
          <el-select v-model="selectedDomains" multiple placeholder="选择要比较的领域" style="width: 350px">
            <el-option
              v-for="domain in domains"
              :key="domain"
              :label="domain"
              :value="domain"
            />
          </el-select>
          
          <el-select v-model="selectedModels" multiple placeholder="选择要比较的模型" style="width: 350px">
            <el-option
              v-for="model in models"
              :key="model"
              :label="model"
              :value="model"
            />
          </el-select>
          
          <el-button type="primary" @click="applyFilters">应用筛选</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </div>
        
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
            <!-- 改进的能力全景图 -->
            <el-tab-pane label="能力全景图" name="line">
              <<div class="chart-selection-container">
  <p class="selection-hint"></p>
  <el-select v-model="selectedTrendModel" placeholder="选择模型" style="width: 200px" @change="initImprovedTimeChart">
    <el-option
      v-for="model in filteredModels"
      :key="model"
      :label="model"
      :value="model"
    />
  </el-select>
</div>
              <div ref="lineChartRef" class="chart"></div>
            </el-tab-pane>
            <!-- 改进的领域分析图 -->
            <el-tab-pane label="领域分析" name="domain">
              <div class="chart-selection-container">
                <el-select v-model="selectedDomainForAnalysis" placeholder="选择领域" style="width: 200px" @change="initDomainComparisonChart">
                  <el-option
                    v-for="domain in filteredDomains"
                    :key="domain"
                    :label="domain"
                    :value="domain"
                  />
                </el-select>
              </div>
              <div ref="domainChartRef" class="chart"></div>
            </el-tab-pane>
            <!-- 模型能力矩阵 -->
            <el-tab-pane label="能力矩阵" name="matrix">
              <div ref="matrixChartRef" class="chart"></div>
            </el-tab-pane>
          </el-tabs>
        </div>
        
        <el-row :gutter="20" class="dashboard-cards">
          <el-col :xs="24" :sm="12" :md="8" :lg="8" :xl="6">
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
                  @click="selectModel(model.name)"
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
          </el-col>
          
          <el-col :xs="24" :sm="12" :md="8" :lg="8" :xl="6">
            <el-card shadow="hover" class="domain-ranking">
              <template #header>
                <div class="card-header">
                  <span>领域难度排名</span>
                </div>
              </template>
              
              <div class="ranking-list">
                <div 
                  v-for="(domain, index) in domainDifficultyRanking" 
                  :key="domain.name"
                  class="ranking-item"
                >
                  <div class="rank">{{ index + 1 }}</div>
                  <div class="model-info">
                    <h3>{{ domain.name }}</h3>
                    <div class="score-info">
                      <el-progress 
                        :percentage="(1 - domain.avgScore) * 100" 
                        :color="getDifficultyColor(1 - domain.avgScore)"
                        :format="(p) => p.toFixed(2) + '%'"
                        :stroke-width="12"
                      />
                    </div>
                  </div>
                  <div class="score">{{ ((1 - domain.avgScore) * 100).toFixed(2) }}%</div>
                </div>
              </div>
            </el-card>
          </el-col>
          
          <el-col :xs="24" :sm="24" :md="8" :lg="8" :xl="12">
            <el-card shadow="hover" class="evaluation-stats">
              <template #header>
                <div class="card-header">
                  <span>评估统计信息</span>
                </div>
              </template>
              
              <div class="stats-container">
                <div class="stat-item">
                  <div class="stat-value">{{ totalEvaluations }}</div>
                  <div class="stat-label">总评估次数</div>
                </div>
                <div class="stat-item">
                  <div class="stat-value">{{ filteredModels.length }}</div>
                  <div class="stat-label">已评估模型</div>
                </div>
                <div class="stat-item">
                  <div class="stat-value">{{ filteredDomains.length }}</div>
                  <div class="stat-label">评估领域</div>
                </div>
                <div class="stat-item">
                  <div class="stat-value">{{ (overallAvgScore * 100).toFixed(2) }}%</div>
                  <div class="stat-label">平均评分</div>
                </div>
              </div>
              
              <div ref="statsChartRef" class="stats-chart"></div>
            </el-card>
          </el-col>
        </el-row>

        <!-- 模型详情对话框 -->
        <el-dialog
          v-model="modelDetailVisible"
          :title="`${selectedModel} 模型详情`"
          width="80%"
          destroy-on-close
        >
          <div class="model-detail-container">
            <el-tabs v-model="detailActiveTab">
              <el-tab-pane label="领域评分" name="scores">
                <div ref="modelDetailChartRef" class="detail-chart"></div>
                
                <el-table :data="getModelDomainScores(selectedModel)" style="width: 100%; margin-top: 20px;">
                  <el-table-column label="领域" prop="domain"></el-table-column>
                  <el-table-column label="平均分数">
                    <template #default="scope">
                      {{ (scope.row.average_score * 100).toFixed(2) }}%
                    </template>
                  </el-table-column>
                  <el-table-column label="评估次数" prop="total_evaluations"></el-table-column>
                </el-table>
              </el-tab-pane>
              
              <el-tab-pane label="强弱领域" name="strengths">
                <div class="strengths-weaknesses">
                  <div class="strengths">
                    <h3>强势领域</h3>
                    <div ref="strengthsChartRef" class="half-chart"></div>
                  </div>
                  <div class="weaknesses">
                    <h3>弱势领域</h3>
                    <div ref="weaknessesChartRef" class="half-chart"></div>
                  </div>
                </div>
              </el-tab-pane>
              
              <!-- 新增：性能改进分析 -->
              <el-tab-pane label="性能改进分析" name="improvement">
                <div class="improvement-analysis">
                  <h3>性能改进潜力分析</h3>
                  <div ref="improvementChartRef" class="detail-chart"></div>
                  
                  <div class="improvement-suggestion">
                    <h4>改进建议</h4>
                    <ul>
                      <li v-for="(suggestion, index) in getImprovementSuggestions(selectedModel)" :key="index">
                        {{ suggestion }}
                      </li>
                    </ul>
                  </div>
                </div>
              </el-tab-pane>
            </el-tabs>
          </div>
        </el-dialog>
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
    const selectedModel = ref(null);
    const modelDetailVisible = ref(false);
    const detailActiveTab = ref('scores');
    const selectedDomains = ref([]);
    const selectedModels = ref([]);
    const filteredDomains = ref([]);
    const filteredModels = ref([]);
    
    // 新增状态变量
    const selectedTrendModel = ref('');
    const selectedDomainForAnalysis = ref('');
    
    // 图表引用
    const radarChartRef = ref(null);
    const heatmapChartRef = ref(null);
    const barChartRef = ref(null);
    const lineChartRef = ref(null);
    const domainChartRef = ref(null);
    const matrixChartRef = ref(null);
    const statsChartRef = ref(null);
    const modelDetailChartRef = ref(null);
    const strengthsChartRef = ref(null);
    const weaknessesChartRef = ref(null);
    const improvementChartRef = ref(null);
    
    // 图表实例
    let radarChart = null;
    let heatmapChart = null;
    let barChart = null;
    let lineChart = null;
    let domainChart = null;
    let matrixChart = null;
    let statsChart = null;
    let modelDetailChart = null;
    let strengthsChart = null;
    let weaknessesChart = null;
    let improvementChart = null;
    
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
    
    // 总评估次数
    const totalEvaluations = computed(() => {
      let total = 0;
      
      if (!comparisonData.value.scores) return total;
      
      for (const modelName in comparisonData.value.scores) {
        const modelScores = comparisonData.value.scores[modelName];
        
        for (const domainName in modelScores) {
          total += modelScores[domainName].total_evaluations || 0;
        }
      }
      
      return total;
    });
    
    // 总平均分数
    const overallAvgScore = computed(() => {
      let totalScore = 0;
      let count = 0;
      
      if (!comparisonData.value.scores) return 0;
      
      for (const modelName of filteredModels.value) {
        const modelScores = comparisonData.value.scores[modelName] || {};
        
        for (const domainName of filteredDomains.value) {
          const domainData = modelScores[domainName];
          if (domainData && domainData.average_score !== undefined) {
            totalScore += domainData.average_score;
            count++;
          }
        }
      }
      
      return count > 0 ? totalScore / count : 0;
    });
    
    // 领域难度排名
    const domainDifficultyRanking = computed(() => {
      if (!comparisonData.value.scores) return [];
      
      const domainScores = {};
      
      // 计算每个领域的平均分
      for (const modelName in comparisonData.value.scores) {
        const modelScores = comparisonData.value.scores[modelName];
        
        for (const domainName in modelScores) {
          if (!domainScores[domainName]) {
            domainScores[domainName] = {
              totalScore: 0,
              count: 0
            };
          }
          
          domainScores[domainName].totalScore += modelScores[domainName].average_score || 0;
          domainScores[domainName].count++;
        }
      }
      
      // 转换为数组并计算平均分
      const result = Object.keys(domainScores).map(domain => ({
        name: domain,
        avgScore: domainScores[domain].count > 0 
          ? domainScores[domain].totalScore / domainScores[domain].count
          : 0
      }));
      
      // 按难度（平均分越低越难）排序
      return result.sort((a, b) => a.avgScore - b.avgScore);
    });
    
    // 获取模型在各领域的得分
    const getModelDomainScores = (modelName) => {
      const result = [];
      
      if (!comparisonData.value.scores || !modelName) return result;
      
      const modelScores = comparisonData.value.scores[modelName] || {};
      
      for (const domainName in modelScores) {
        if (domainName && modelScores[domainName]) {
          result.push({
            domain: domainName,
            average_score: modelScores[domainName].average_score || 0,
            total_evaluations: modelScores[domainName].total_evaluations || 0
          });
        }
      }
      
      // 按分数降序排列
      return result.sort((a, b) => b.average_score - a.average_score);
    };
    
    // 获取模型的强势和弱势领域
    const getModelStrengthsAndWeaknesses = (modelName) => {
      const scores = getModelDomainScores(modelName);
      
      // 按照得分排序
      const sortedScores = [...scores].sort((a, b) => b.average_score - a.average_score);
      
      // 获取前3名和后3名的领域
      const top3 = sortedScores.slice(0, 3);
      const bottom3 = sortedScores.slice(-3);
      
      // 筛选出表现较佳的领域（分数大于60%且在前3名）
      const strengths = top3.filter(domain => domain.average_score >= 0.6);
      
      // 筛选出表现较弱的领域（分数小于60%且在后3名）
      const weaknesses = bottom3.filter(domain => domain.average_score < 0.6);
      
      return { strengths, weaknesses };
    };
    
    // 新增：获取模型改进建议
    const getImprovementSuggestions = (modelName) => {
      const { weaknesses } = getModelStrengthsAndWeaknesses(modelName);
      const suggestions = [];
      
      // 根据弱势领域生成建议
      weaknesses.forEach(domain => {
        if (domain.average_score < 0.4) {
          suggestions.push(`【${domain.domain}】领域表现较差，建议大幅增强训练数据量和质量，重点关注复杂问题的理解能力`);
        } else if (domain.average_score < 0.6) {
          suggestions.push(`【${domain.domain}】领域需要提升，建议增加专业知识训练和多样化的测试案例`);
        } else {
          suggestions.push(`【${domain.domain}】领域已具备基础能力，可以通过引入更高质量的训练数据进一步提升`);
        }
      });
      
      // 添加通用建议
      suggestions.push(`建议通过知识蒸馏方法从强势领域向弱势领域迁移能力`);
      suggestions.push(`增加领域专家参与模型评估和迭代优化过程`);
      
      return suggestions;
    };
    
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
      
      for (const modelName of filteredModels.value) {
        const modelScores = comparisonData.value.scores[modelName] || {};
        let totalScore = 0;
        let validDomains = 0;
        
        for (const domainName of filteredDomains.value) {
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
    
    // 获取领域评估时间
    const getDomainEvaluationTimes = () => {
      const times = new Map();
      
      if (!comparisonData.value.scores) return [];
      
      for (const modelName in comparisonData.value.scores) {
        const modelScores = comparisonData.value.scores[modelName];
        
        for (const domainName in modelScores) {
          if (modelScores[domainName].scores) {
            modelScores[domainName].scores.forEach(score => {
              const timestamp = new Date(score.timestamp);
              // 确保是有效的日期
              if (!isNaN(timestamp.getTime())) {
                const dateKey = timestamp.toISOString().split('T')[0];
                if (!times.has(dateKey)) {
                  times.set(dateKey, true);
                }
              }
            });
          }
        }
      }
      
      return Array.from(times.keys()).sort();
    };
    
    // 获取比较数据
    const fetchComparisonData = async () => {
      try {
        loading.value = true;
        comparisonData.value = await fileApi.getDomainComparisonData();
        domains.value = comparisonData.value.domains || [];
        models.value = comparisonData.value.models || [];
        
        // 初始化筛选
        selectedDomains.value = [...domains.value];
        selectedModels.value = [...models.value];
        filteredDomains.value = [...domains.value];
        filteredModels.value = [...models.value];
        
        // 设置默认选择的模型和领域
        if (filteredModels.value.length > 0) {
          selectedTrendModel.value = filteredModels.value[0];
        }
        
        if (filteredDomains.value.length > 0) {
          selectedDomainForAnalysis.value = filteredDomains.value[0];
        }
        
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
    
    // 统一的排名颜色 - 使用主题蓝色
    const rankColor = "#409EFF";
    
    // 获取评分颜色
    const getScoreColor = (score) => {
      if (score >= 0.9) return '#67C23A';  // 优秀 - 绿色
      if (score >= 0.8) return '#409EFF';  // 良好 - 蓝色
      if (score >= 0.6) return '#E6A23C';  // 及格 - 黄色
      return '#F56C6C';  // 不及格 - 红色
    };
    
    // 获取难度颜色
    const getDifficultyColor = (difficulty) => {
      if (difficulty >= 0.8) return '#F56C6C';  // 困难 - 红色
      if (difficulty >= 0.6) return '#E6A23C';  // 中等 - 黄色
      if (difficulty >= 0.4) return '#409EFF';  // 简单 - 蓝色
      return '#67C23A';  // 非常简单 - 绿色
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
        '评分': (row.score * 100).toFixed(2) + '%',
        '评测次数': row.evaluations
      }));
      
      // 创建工作表
      const ws = XLSX.utils.json_to_sheet(exportData);
      
      // 添加工作表到工作簿
      XLSX.utils.book_append_sheet(wb, ws, '模型领域评分比较');
      
      // 导出文件
      XLSX.writeFile(wb, '模型领域评分比较.xlsx');
    };
    
    // 选择模型查看详情
    const selectModel = (modelName) => {
      selectedModel.value = modelName;
      modelDetailVisible.value = true;
      
      nextTick(() => {
        initModelDetailCharts();
      });
    };
    
    // 应用筛选
    const applyFilters = () => {
      filteredDomains.value = [...selectedDomains.value];
      filteredModels.value = [...selectedModels.value];
      
      // 重新初始化图表
      nextTick(() => {
        initCharts();
      });
    };
    
    // 重置筛选
    const resetFilters = () => {
      selectedDomains.value = [...domains.value];
      selectedModels.value = [...models.value];
      filteredDomains.value = [...domains.value];
      filteredModels.value = [...models.value];
      
      // 重新初始化图表
      nextTick(() => {
        initCharts();
      });
    };
    
    // 初始化图表
    const initCharts = () => {
      nextTick(() => {
        initRadarChart();
        initHeatmapChart();
        initBarChart();
        initImprovedTimeChart();
        initDomainComparisonChart();
        initMatrixChart();
        initStatsChart();
        
        // 监听窗口大小变化，调整图表大小
        window.addEventListener('resize', () => {
          if (radarChart) radarChart.resize();
          if (heatmapChart) heatmapChart.resize();
          if (barChart) barChart.resize();
          if (lineChart) lineChart.resize();
          if (domainChart) domainChart.resize();
          if (matrixChart) matrixChart.resize();
          if (statsChart) statsChart.resize();
        });
      });
    };
    
    // 初始化模型详情图表
    const initModelDetailCharts = () => {
      nextTick(() => {
        initModelDetailChart();
        initStrengthsChart();
        initWeaknessesChart();
        initImprovementChart();
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
      const indicator = filteredDomains.value.map(domain => ({
        name: domain,
        max: 1
      }));
      
      const seriesData = filteredModels.value.map(model => {
        const dataPoints = filteredDomains.value.map(domain => {
          const modelScores = comparisonData.value.scores[model];
          if (!modelScores || !modelScores[domain]) {
            console.log(`No data for model ${model} in domain ${domain}`);
            return 0;
          }
          const score = modelScores[domain].average_score;
          if (typeof score !== 'number' || isNaN(score)) {
            console.log(`Invalid score for model ${model} in domain ${domain}: ${score}`);
            return 0;
          }
          return score;
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
          trigger: 'item',
          formatter: function(params) {
            if (!params.value || !Array.isArray(params.value)) return '';
            
            let result = `${params.name}<br>`;
            params.value.forEach((val, index) => {
              const domain = indicator[index].name;
              const score = typeof val === 'number' ? val : 0;
              result += `${domain}: ${(score * 100).toFixed(2)}%<br>`;
            });
            return result;
          }
        },
        legend: {
          type: 'scroll',
          bottom: 10,
          data: filteredModels.value,
          selected: filteredModels.value.reduce((acc, model) => {
            acc[model] = true;
            return acc;
          }, {})
        },
        radar: {
          indicator: indicator,
          shape: 'circle',
          splitNumber: 5,
          axisName: {
            color: '#333',
            fontSize: 12,
            padding: [3, 5]
          },
          splitArea: {
            areaStyle: {
              color: ['rgba(255,255,255,0.3)',
                     'rgba(200,200,200,0.1)']
            }
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
            data: seriesData,
            lineStyle: {
              width: 2
            },
            symbolSize: 6,
            areaStyle: {
              opacity: 0.2
            }
          }
        ]
      };
      
      // 应用配置
      radarChart.setOption(option);
      
      // 添加点击事件
      radarChart.on('click', (params) => {
        // 检查是否点击了雷达图的数据系列
        if (params.componentType === 'series' && params.seriesType === 'radar') {
          // 获取点击的模型名称
          const modelName = params.seriesName;
          if (modelName && filteredModels.value.includes(modelName)) {
            selectModel(modelName);
          }
        }
      });

      // 移除图例点击事件，保持图例只用于显示/隐藏
      radarChart.on('legendselectchanged', (params) => {
        // 仅处理显示/隐藏，不触发模型详情
      });
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
      const yCategories = filteredModels.value;
      const xCategories = filteredDomains.value;
      
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
      
      // 设置配置
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
      
      // 添加点击事件
      heatmapChart.on('click', (params) => {
        if (params.seriesType === 'heatmap') {
          const modelIndex = params.value[1];
          selectModel(yCategories[modelIndex]);
        }
      });
    };
    
    // 初始化柱状图
    const initBarChart = () => {
      if (!barChartRef.value) return;
      
      // 销毁已有实例
      if (barChart) {
        barChart.dispose();
      }
      
      // 创建新实例
      barChart = echarts.init(barChartRef.value);
      
      // 准备数据
      const xAxisData = filteredDomains.value;
      const series = filteredModels.value.map(model => {
        const modelData = filteredDomains.value.map(domain => {
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
          data: filteredModels.value,
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
      
      // 添加点击事件
      barChart.on('click', (params) => {
        if (params.seriesType === 'bar') {
          selectModel(params.seriesName);
        }
      });
    };
    
    // 初始化改进的时间趋势图
   // 替换当前的initImprovedTimeChart函数为以下内容:

// 替换当前的initImprovedTimeChart函数为以下内容:
const initImprovedTimeChart = () => {
  if (!lineChartRef.value || !selectedTrendModel.value) return;
  
  // 销毁已有实例
  if (lineChart) {
    lineChart.dispose();
  }
  
  // 创建新实例
  lineChart = echarts.init(lineChartRef.value);
  
  // 获取所选模型的所有领域数据
  const modelScores = comparisonData.value.scores[selectedTrendModel.value] || {};
  
  // 定义颜色
  const COLOR_EXCELLENT = '#1890ff';  // 蓝色
  const COLOR_AVERAGE = '#faad14';    // 橙色/金色
  const COLOR_POOR = '#f5222d';       // 红色
  const COLOR_MODEL = '#8cc265';      // 模型名称层级的绿色
  
  // 准备图表数据
  const chartData = {
    name: selectedTrendModel.value,
    itemStyle: {
      color: COLOR_MODEL
    },
    children: []
  };
  
  // 将领域按照分数分类
  const categories = [
    { name: '优秀 (75-100%)', min: 0.75, max: 1.01, color: COLOR_EXCELLENT },
    { name: '良好 (60-75%)', min: 0.6, max: 0.75, color: COLOR_AVERAGE },
    { name: '差 (0-60%)', min: 0, max: 0.6, color: COLOR_POOR }
  ];
  
  // 为每个类别创建数据节点
  categories.forEach(category => {
    const domains = [];
    
    for (const domain in modelScores) {
      const score = modelScores[domain].average_score || 0;
      const evaluations = modelScores[domain].total_evaluations || 0;
      
      if (score >= category.min && score < category.max) {
        domains.push({
          name: domain,
          value: Math.round(score * 100),
          evaluations: evaluations,
          itemStyle: {
            color: category.color  // 确保叶子节点使用与分类相同的颜色
          }
        });
      }
    }
    
    // 只有当有数据时才添加该类别
    if (domains.length > 0) {
      chartData.children.push({
        name: category.name,
        itemStyle: {
          color: category.color
        },
        children: domains
      });
    }
  });
  
  // 创建树状图配置
  const treemapOption = {
    title: {
      text: `${selectedTrendModel.value} 模型能力全景图`,
      subtext: '点击切换为旭日图',
      left: 'center',
      textStyle: {
        fontSize: 18,
        fontWeight: 'bold'
      }
    },
    tooltip: {
      formatter: function(info) {
        if (info.data.evaluations !== undefined) {
          return [
            `<div class="tooltip-title">${info.name}</div>`,
            `评分: <span class="tooltip-value">${info.value}%</span>`,
            `评测次数: <span class="tooltip-value">${info.data.evaluations || 0}</span>`
          ].join('<br>');
        } else {
          return `<div class="tooltip-title">${info.name}</div>`;
        }
      }
    },
    series: [
      {
        type: 'treemap',
        id: 'modelCapabilityMap',
        animationDurationUpdate: 1000,
        roam: false,
        nodeClick: 'link',
        data: [chartData],
        universalTransition: true,
        label: {
          show: true,
          formatter: function(params) {
            // 如果是叶子节点，显示分数
            if (params.data.children) {
              return params.name;
            } else {
              return `${params.name}: ${params.value}%`;
            }
          },
          fontSize: 14,
          fontWeight: 'bold',
          color: '#fff'
        },
        upperLabel: {
          show: true,
          height: 30
        },
        breadcrumb: {
          show: false
        },
        levels: [
          {
            // 顶级节点（模型）
            itemStyle: {
              borderWidth: 0,
              gapWidth: 5,
              borderColor: '#fff'
            },
            upperLabel: {
              show: true
            }
          },
          {
            // 分类节点（评分范围）
            itemStyle: {
              borderWidth: 5,
              gapWidth: 1,
              borderColor: '#fff'
            },
            emphasis: {
              itemStyle: {
                borderColor: '#ddd'
              }
            }
          },
          {
            // 叶子节点（具体领域）
            itemStyle: {
              borderWidth: 1,
              gapWidth: 1,
              borderColor: 'rgba(255,255,255,0.5)'
            }
          }
        ]
      }
    ]
  };
  
  // 创建旭日图配置
  const sunburstOption = {
    title: {
      text: `${selectedTrendModel.value} 模型能力旭日图`,
      subtext: '点击切换为树状图',
      left: 'center',
      textStyle: {
        fontSize: 18,
        fontWeight: 'bold'
      }
    },
    tooltip: {
      formatter: function(info) {
        if (info.data.evaluations !== undefined) {
          return [
            `<div class="tooltip-title">${info.name}</div>`,
            `评分: <span class="tooltip-value">${info.value}%</span>`,
            `评测次数: <span class="tooltip-value">${info.data.evaluations || 0}</span>`
          ].join('<br>');
        } else {
          return `<div class="tooltip-title">${info.name}</div>`;
        }
      }
    },
    series: [
      {
        type: 'sunburst',
        id: 'modelCapabilityMap',
        radius: ['15%', '90%'],
        animationDurationUpdate: 1000,
        nodeClick: 'link',
        data: [chartData],
        universalTransition: true,
        label: {
          show: true,
          formatter: function(param) {
            // 对于叶子节点，显示分数
            if (!param.data.children) {
              return `${param.name}: ${param.value}%`;
            }
            return param.name;
          },
          color: '#fff',
          textBorderWidth: 2,
          textBorderColor: 'rgba(0,0,0,0.2)',
          rotate: 'radial'
        },
        itemStyle: {
          borderWidth: 1,
          borderColor: 'rgba(255,255,255,0.5)'
        },
        levels: [
          {},
          {
            label: {
              rotate: 'tangential'
            }
          },
          {
            label: {
              align: 'center'
            }
          }
        ]
      }
    ]
  };
  
  // 初始展示旭日图
  lineChart.setOption(treemapOption);
  
  // 添加点击事件监听器
  lineChart.on('click', function(params) {
    // 根据当前图表类型切换
    const currentType = lineChart.getOption().series[0].type;
    if (currentType === 'treemap') {
      lineChart.setOption(sunburstOption);
    } else {
      lineChart.setOption(treemapOption);
    }
  });
};
    
    // 初始化领域比较图
    const initDomainComparisonChart = () => {
      if (!domainChartRef.value || !selectedDomainForAnalysis.value) return;
      
      // 销毁已有实例
      if (domainChart) {
        domainChart.dispose();
      }
      
      // 创建新实例
      domainChart = echarts.init(domainChartRef.value);
      
      // 获取所选领域的所有模型得分
      const domainScores = [];
      
      for (const modelName of filteredModels.value) {
        const modelScores = comparisonData.value.scores[modelName] || {};
        const domainData = modelScores[selectedDomainForAnalysis.value];
        
        if (domainData) {
          domainScores.push({
            model: modelName,
            score: domainData.average_score * 100,
            evaluations: domainData.total_evaluations
          });
        } else {
          domainScores.push({
            model: modelName,
            score: 0,
            evaluations: 0
          });
        }
      }
      
      // 按分数降序排序
      domainScores.sort((a, b) => b.score - a.score);
      
      // 准备图表数据
      const models = domainScores.map(item => item.model);
      const scores = domainScores.map(item => item.score.toFixed(2));
      const evaluations = domainScores.map(item => item.evaluations);
      
      // 设置配置
      const option = {
        title: {
          text: `${selectedDomainForAnalysis.value} 领域各模型能力对比`,
          left: 'center'
        },
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'shadow'
          },
          formatter: function (params) {
            const modelName = params[0].axisValue;
            const score = params[0].value;
            const evals = params[1].value;
            
            return `模型: ${modelName}<br>` +
                   `评分: ${score}%<br>` +
                   `评测次数: ${evals}`;
          }
        },
        legend: {
          data: ['评分', '评测次数'],
          bottom: 10
        },
        grid: {
          top: 60,
          bottom: 90,
          left: 60,
          right: 60
        },
        xAxis: {
          type: 'category',
          data: models,
          axisLabel: {
            rotate: 45,
            interval: 0
          }
        },
        yAxis: [
          {
            type: 'value',
            name: '评分百分比',
            min: 0,
            max: 100,
            position: 'left',
            axisLabel: {
              formatter: '{value}%'
            }
          },
          {
            type: 'value',
            name: '评测次数',
            min: 0,
            position: 'right'
          }
        ],
        series: [
          {
            name: '评分',
            type: 'bar',
            data: scores,
            itemStyle: {
              color: function(params) {
                return getScoreColor(params.value / 100);
              }
            },
            label: {
              show: true,
              position: 'top',
              formatter: '{c}%'
            }
          },
          {
            name: '评测次数',
            type: 'line',
            yAxisIndex: 1,
            data: evaluations,
            symbol: 'circle',
            symbolSize: 8,
            itemStyle: {
              color: '#91CC75'
            },
            label: {
              show: true,
              position: 'top'
            }
          }
        ]
      };
      
      // 应用配置
      domainChart.setOption(option);
      
      // 添加点击事件
      domainChart.on('click', (params) => {
        if (params.componentType === 'series') {
          const modelIndex = params.dataIndex;
          const modelName = models[modelIndex];
          selectModel(modelName);
        }
      });
    };
    
    // 初始化能力矩阵图
    const initMatrixChart = () => {
      if (!matrixChartRef.value) return;
      
      // 销毁已有实例
      if (matrixChart) {
        matrixChart.dispose();
      }
      
      // 创建新实例
      matrixChart = echarts.init(matrixChartRef.value);
      
      // 获取领域的难度排名
      const domainDifficulty = domainDifficultyRanking.value.map(domain => ({
        name: domain.name,
        difficulty: 1 - domain.avgScore // 转换为难度值，分数越低难度越高
      }));
      
      // 准备平行坐标系的维度
      const dimensions = ['模型名称'].concat(domainDifficulty.map(d => d.name));
      
      // 准备平行坐标系的数据
      const parallelData = [];
      
      for (const modelName of filteredModels.value) {
        const modelScores = comparisonData.value.scores[modelName] || {};
        
        // 计算该模型每个领域的得分
        const dataItem = [modelName];
        
        for (const domain of domainDifficulty) {
          const domainData = modelScores[domain.name];
          const score = domainData ? domainData.average_score * 100 : 0;
          dataItem.push(score.toFixed(2));
        }
        
        parallelData.push(dataItem);
      }
      
      // 设置配置
      const option = {
        title: {
          text: '模型多维能力矩阵分析',
          left: 'center'
        },
        tooltip: {
          trigger: 'item',
          formatter: function (params) {
            let result = `模型: ${params.value[0]}<br>`;
            for (let i = 1; i < params.value.length; i++) {
              result += `${dimensions[i]}: ${params.value[i]}%<br>`;
            }
            return result;
          }
        },
        parallelAxis: dimensions.map((dim, i) => {
          if (i === 0) {
            // 第一个维度是模型名称
            return {
              dim: i,
              name: dim,
              type: 'category',
              data: filteredModels.value
            };
          } else {
            // 其他维度是领域分数
            return {
              dim: i,
              name: dim,
              min: 0,
              max: 100,
              axisLabel: {
                formatter: '{value}%'
              }
            };
          }
        }),
        parallel: {
          left: '5%',
          right: '13%',
          top: 100,
          bottom: 100,
          parallelAxisDefault: {
            nameLocation: 'end',
            nameGap: 20
          }
        },
        series: [
          {
            name: '模型能力矩阵',
            type: 'parallel',
            lineStyle: {
              width: 3
            },
            emphasis: {
              lineStyle: {
                width: 6
              }
            },
            data: parallelData
          }
        ]
      };
      
      // 应用配置
      matrixChart.setOption(option);
      
      // 添加点击事件
      matrixChart.on('click', (params) => {
        if (params.componentType === 'series') {
          const modelName = params.value[0];
          selectModel(modelName);
        }
      });
    };
    
    // 初始化统计图表
    const initStatsChart = () => {
      if (!statsChartRef.value) return;
      
      // 销毁已有实例
      if (statsChart) {
        statsChart.dispose();
      }
      
      // 创建新实例
      statsChart = echarts.init(statsChartRef.value);
      
      // 计算每个模型的平均分和评测次数
      const statData = [];
      
      for (const model of filteredModels.value) {
        let totalScore = 0;
        let totalEvals = 0;
        let count = 0;
        
        const modelScores = comparisonData.value.scores[model] || {};
        
        for (const domain of filteredDomains.value) {
          const domainData = modelScores[domain];
          if (domainData) {
            totalScore += domainData.average_score || 0;
            totalEvals += domainData.total_evaluations || 0;
            count++;
          }
        }
        
        // 计算平均分
        const avgScore = count > 0 ? totalScore / count : 0;
        
        statData.push({
          name: model,
          avgScore: avgScore * 100,
          evaluations: totalEvals
        });
      }
      
      // 设置配置
      const option = {
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'cross'
          }
        },
        grid: {
          top: 10,
          bottom: 30,
          left: 50,
          right: 50
        },
        xAxis: [
          {
            type: 'category',
            data: statData.map(item => item.name),
            axisPointer: {
              type: 'shadow'
            },
            axisLabel: {
              rotate: 45
            }
          }
        ],
        yAxis: [
          {
            type: 'value',
            name: '平均分数',
            min: 0,
            max: 100,
            position: 'left',
            axisLine: {
              show: true,
              lineStyle: {
                color: '#5470C6'
              }
            },
            axisLabel: {
              formatter: '{value}%'
            }
          },
          {
            type: 'value',
            name: '评测次数',
            min: 0,
            position: 'right',
            axisLine: {
              show: true,
              lineStyle: {
                color: '#91CC75'
              }
            }
          }
        ],
        series: [
          {
            name: '平均分数',
            type: 'bar',
            data: statData.map(item => item.avgScore.toFixed(2)),
            itemStyle: {
              color: '#5470C6'
            },
            label: {
              show: true,
              position: 'top',
              formatter: '{c}%'
            }
          },
          {
            name: '评测次数',
            type: 'line',
            yAxisIndex: 1,
            data: statData.map(item => item.evaluations),
            symbol: 'circle',
            symbolSize: 8,
            itemStyle: {
              color: '#91CC75'
            },
            label: {
              show: true,
              position: 'top'
            }
          }
        ]
      };
      
      // 应用配置
      statsChart.setOption(option);
      
      // 添加点击事件
      statsChart.on('click', (params) => {
        if (params.componentType === 'series') {
          const modelName = params.name;
          if (filteredModels.value.includes(modelName)) {
            selectModel(modelName);
          }
        }
      });
    };
    
    // 初始化模型详情图表
    const initModelDetailChart = () => {
      if (!modelDetailChartRef.value || !selectedModel.value) return;
      
      // 销毁已有实例
      if (modelDetailChart) {
        modelDetailChart.dispose();
      }
      
      // 创建新实例
      modelDetailChart = echarts.init(modelDetailChartRef.value);
      
      // 获取模型在各领域的得分
      const domainScores = getModelDomainScores(selectedModel.value);
      
      // 准备数据
      const option = {
        title: {
          text: `${selectedModel.value} 各领域评分`,
          left: 'center'
        },
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'shadow'
          },
          formatter: function (params) {
            return `${params[0].name}<br>` +
                   `评分: ${params[0].value.toFixed(2)}%<br>` +
                   `评测次数: ${params[0].data.evaluations}`;
          }
        },
        grid: {
          top: 60,
          bottom: 30,
          left: 60,
          right: 40
        },
        xAxis: {
          type: 'category',
          data: domainScores.map(item => item.domain),
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
        series: [
          {
            name: '评分',
            type: 'bar',
            data: domainScores.map(item => ({
              value: item.average_score * 100,
              evaluations: item.total_evaluations
            })),
            itemStyle: {
              color: function (params) {
                return getScoreColor(params.data.value / 100);
              }
            },
            label: {
              show: true,
              position: 'top',
              formatter: function(params) {
                return params.data.value.toFixed(2) + '%';
              }
            }
          }
        ]
      };
      
      // 应用配置
      modelDetailChart.setOption(option);
    };
    
    // 初始化强势领域图表
    const initStrengthsChart = () => {
      if (!strengthsChartRef.value || !selectedModel.value) return;
      
      // 销毁已有实例
      if (strengthsChart) {
        strengthsChart.dispose();
      }
      
      // 创建新实例
      strengthsChart = echarts.init(strengthsChartRef.value);
      
      // 获取模型的强势领域
      const { strengths } = getModelStrengthsAndWeaknesses(selectedModel.value);
      
      // 准备数据
      const option = {
        tooltip: {
          trigger: 'item',
          formatter: '{b}: {c}% ({d}%)'
        },
        legend: {
          type: 'scroll',
          data: strengths.map(item => item.domain),
          bottom: 0
        },
        series: [
          {
            name: '强势领域',
            type: 'pie',
            radius: '70%',
            center: ['50%', '50%'],
            data: strengths.map(item => ({
              name: item.domain,
              value: (item.average_score * 100).toFixed(2)
            })),
            emphasis: {
              itemStyle: {
                shadowBlur: 10,
                shadowOffsetX: 0,
                shadowColor: 'rgba(0, 0, 0, 0.5)'
              }
            },
            itemStyle: {
              color: function (params) {
                return getScoreColor(params.data.value / 100);
              }
            },
            label: {
              formatter: '{b}: {c}%'
            }
          }
        ]
      };
      
      // 应用配置
      strengthsChart.setOption(option);
    };
    
    // 初始化弱势领域图表
    const initWeaknessesChart = () => {
      if (!weaknessesChartRef.value || !selectedModel.value) return;
      
      // 销毁已有实例
      if (weaknessesChart) {
        weaknessesChart.dispose();
      }
      
      // 创建新实例
      weaknessesChart = echarts.init(weaknessesChartRef.value);
      
      // 获取模型的弱势领域
      const { weaknesses } = getModelStrengthsAndWeaknesses(selectedModel.value);
      
      // 准备数据
      const option = {
        tooltip: {
          trigger: 'item',
          formatter: '{b}: {c}% ({d}%)'
        },
        legend: {
          type: 'scroll',
          data: weaknesses.map(item => item.domain),
          bottom: 0
        },
        series: [
          {
            name: '弱势领域',
            type: 'pie',
            radius: '70%',
            center: ['50%', '50%'],
            data: weaknesses.map(item => ({
              name: item.domain,
              value: (item.average_score * 100).toFixed(2)
            })),
            emphasis: {
              itemStyle: {
                shadowBlur: 10,
                shadowOffsetX: 0,
                shadowColor: 'rgba(0, 0, 0, 0.5)'
              }
            },
            itemStyle: {
              color: function (params) {
                return getScoreColor(params.data.value / 100);
              }
            },
            label: {
              formatter: '{b}: {c}%'
            }
          }
        ]
      };
      
      // 应用配置
      weaknessesChart.setOption(option);
    };
    
    // 初始化改进分析图表
    const initImprovementChart = () => {
      if (!improvementChartRef.value || !selectedModel.value) return;
      
      // 销毁已有实例
      if (improvementChart) {
        improvementChart.dispose();
      }
      
      // 创建新实例
      improvementChart = echarts.init(improvementChartRef.value);
      
      // 获取模型所有领域的分数
      const domainScores = getModelDomainScores(selectedModel.value);
      
      // 计算每个领域与最高分的差距
      const topModel = modelRanking.value[0];
      const gapData = [];
      
      for (const domainScore of domainScores) {
        const domain = domainScore.domain;
        let bestScore = 0;
        
        // 寻找该领域的最高分
        for (const modelName in comparisonData.value.scores) {
          const modelScores = comparisonData.value.scores[modelName];
          if (modelScores[domain] && modelScores[domain].average_score > bestScore) {
            bestScore = modelScores[domain].average_score;
          }
        }
        
        // 计算差距
        const currentScore = domainScore.average_score;
        const gap = bestScore - currentScore;
        
        gapData.push({
          domain: domain,
          current: (currentScore * 100).toFixed(2),
          best: (bestScore * 100).toFixed(2),
          gap: (gap * 100).toFixed(2)
        });
      }
      
      // 按照差距排序
      gapData.sort((a, b) => parseFloat(b.gap) - parseFloat(a.gap));
      
      // 准备数据
      const option = {
        title: {
          text: '领域能力改进潜力分析',
          left: 'center'
        },
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'shadow'
          },
          formatter: function (params) {
            const domain = params[0].name;
            const current = params[0].value;
            const best = params[1].value;
            const gap = params[2].value;
            
            return `领域: ${domain}<br>` +
                   `当前评分: ${current}%<br>` +
                   `最高评分: ${best}%<br>` +
                   `改进空间: ${gap}%`;
          }
        },
        legend: {
          data: ['当前评分', '最高评分', '改进空间'],
          bottom: 10
        },
        grid: {
          top: 60,
          bottom: 80,
          left: 60,
          right: 40
        },
        xAxis: {
          type: 'category',
          data: gapData.map(item => item.domain),
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
        series: [
          {
            name: '当前评分',
            type: 'bar',
            stack: 'total',
            emphasis: {
              focus: 'series'
            },
            data: gapData.map(item => item.current),
            itemStyle: {
              color: '#5470C6'
            }
          },
          {
            name: '最高评分',
            type: 'bar',
            stack: 'contrast',
            emphasis: {
              focus: 'series'
            },
            data: gapData.map(item => item.best),
            itemStyle: {
              color: '#91CC75'
            }
          },
          {
            name: '改进空间',
            type: 'bar',
            emphasis: {
              focus: 'series'
            },
            data: gapData.map(item => item.gap),
            itemStyle: {
              color: '#EE6666'
            },
            label: {
              show: true,
              position: 'top',
              formatter: '{c}%'
            }
          }
        ]
      };
      
      // 应用配置
      improvementChart.setOption(option);
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
        switch (newVal) {
          case 'radar':
            if (radarChart) radarChart.resize();
            break;
          case 'heatmap':
            if (heatmapChart) heatmapChart.resize();
            break;
          case 'bar':
            if (barChart) barChart.resize();
            break;
          case 'line':
            if (lineChart) lineChart.resize();
            break;
          case 'domain':
            if (domainChart) domainChart.resize();
            break;
          case 'matrix':
            if (matrixChart) matrixChart.resize();
            break;
        }
      });
    });
    
    // 监听详情选项卡变化
    watch(detailActiveTab, (newVal) => {
      nextTick(() => {
        switch (newVal) {
          case 'scores':
            if (modelDetailChart) modelDetailChart.resize();
            break;
          case 'strengths':
            if (strengthsChart) strengthsChart.resize();
            if (weaknessesChart) weaknessesChart.resize();
            break;
          case 'improvement':
            if (improvementChart) improvementChart.resize();
            break;
        }
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
      selectedDomains,
      selectedModels,
      filteredDomains,
      filteredModels,
      comparisonData,
      sortDir,
      activeTab,
      selectedModel,
      modelDetailVisible,
      detailActiveTab,
      selectedTrendModel,
      selectedDomainForAnalysis,
      tableData,
      modelRanking,
      domainDifficultyRanking,
      totalEvaluations,
      overallAvgScore,
      radarChartRef,
      heatmapChartRef,
      barChartRef,
      lineChartRef,
      domainChartRef,
      matrixChartRef,
      statsChartRef,
      modelDetailChartRef,
      strengthsChartRef,
      weaknessesChartRef,
      improvementChartRef,
      getScoreColor,
      getDifficultyColor,
      getModelDomainScores,
      getImprovementSuggestions,
      mergeModelColumn,
      sortByModel,
      exportTable,
      selectModel,
      applyFilters,
      resetFilters,
      initImprovedTimeChart,
      initDomainComparisonChart
    };
  }
}
</script>

<style scoped>
.model-compare {
  padding: 2rem;
  max-width: 100%;
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

.chart-filters {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
  align-items: center;
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

.chart-selection-container {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-top: 1rem;
  margin-bottom: 1rem;
}

.dashboard-cards {
  margin-top: 2rem;
}

.model-ranking, .domain-ranking, .evaluation-stats {
  height: 100%;
  margin-bottom: 1.5rem;
}

.ranking-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  max-height: 400px;
  overflow-y: auto;
}

.ranking-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: #f9f9f9;
  border-radius: 8px;
  transition: all 0.2s;
  cursor: pointer;
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
  background: #409EFF;
  color: white;
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

.stats-container {
  display: flex;
  justify-content: space-around;
  align-items: center;
  flex-wrap: wrap;
  margin-bottom: 1.5rem;
}
.selection-hint {
  margin-bottom: 10px;
  color: #606266;
  text-align: center;
}

.tooltip-title {
  font-size: 14px;
  font-weight: bold;
  margin-bottom: 5px;
}

.tooltip-value {
  color: #409EFF;
  font-weight: bold;
}
.stat-item {
  text-align: center;
  padding: 1rem;
}

.stat-value {
  font-size: 2.5rem;
  font-weight: bold;
  color: #409eff;
}

.stat-label {
  font-size: 1rem;
  color: #606266;
  margin-top: 0.5rem;
}

.stats-chart {
  height: 300px;
}

.model-detail-container {
  padding: 1rem;
}

.detail-chart {
  height: 350px;
}

.strengths-weaknesses {
  display: flex;
  gap: 2rem;
  flex-wrap: wrap;
}

.strengths, .weaknesses {
  flex: 1;
  min-width: 300px;
}

.half-chart {
  height: 350px;
}

.improvement-suggestion {
  margin-top: 2rem;
  padding: 1rem;
  background-color: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #409EFF;
}

.improvement-suggestion h4 {
  margin-top: 0;
  color: #303133;
}

.improvement-suggestion ul {
  padding-left: 1.5rem;
}

.improvement-suggestion li {
  margin-bottom: 0.75rem;
  line-height: 1.5;
}

.dual-chart-container {
  display: flex;
  flex-wrap: wrap;
  gap: 2rem;
  margin-top: 1rem;
}

.half-width-container {
  flex: 1;
  min-width: 300px;
}

.chart-title {
  text-align: center;
  margin-bottom: 1rem;
  color: #303133;
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
  
  .chart-filters {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .chart-filters .el-select {
    width: 100% !important;
  }
  
  .strengths-weaknesses {
    flex-direction: column;
  }
  
  .dual-chart-container {
    flex-direction: column;
  }
}
</style>

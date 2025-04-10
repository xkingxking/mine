<template>
    <div v-if="show" class="report-dialog">
      <div class="report-dialog-content">
        <div class="dialog-header">
          <h2>{{ file?.name }}</h2>
          <button @click="onClose" class="btn-close">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="dialog-body">
          <div v-if="content" class="content-wrapper">
            <div class="table-content">
              <!-- 模型信息部分 -->
              <div class="section">
                <h3 class="section-title">模型信息</h3>
                <el-table :data="[modelInfo]" style="width: 100%" border>
                  <el-table-column prop="name" label="模型名称" />
                  <el-table-column prop="lastUpdate" label="最后更新时间" />
                </el-table>
              </div>
              
              <!-- 领域评测结果部分 -->
              <div class="section">
                <h3 class="section-title">领域评测结果</h3>
                <el-table :data="domains" style="width: 100%" border>
                  <el-table-column prop="name" label="领域" />
                  <el-table-column prop="average_score" label="平均得分">
                    <template #default="scope">
                      <el-progress 
                        :percentage="scope.row.average_score * 100" 
                        :color="getScoreColor(scope.row.average_score)"
                        :format="(p) => p.toFixed(2) + '%'"
                      />
                    </template>
                  </el-table-column>
                  <el-table-column prop="total_evaluations" label="评测次数" />
                  <el-table-column label="详情">
                    <template #default="scope">
                      <el-button size="small" @click="showDomainDetail(scope.row)">
                        查看历史记录
                      </el-button>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
              
              <!-- 评分图表展示 -->
              <div v-if="domains.length > 0" class="section">
                <h3 class="section-title">领域评分对比</h3>
                <div class="chart-container" ref="domainChartContainer"></div>
              </div>
            </div>
          </div>
          <div v-else class="loading">
            <i class="fas fa-spinner fa-spin"></i>
            <span>加载中...</span>
          </div>
        </div>
        <div class="dialog-footer">
          <button @click="downloadJson" class="btn-secondary">
            <i class="fas fa-download"></i> 下载JSON
          </button>
          <button @click="downloadPdf" class="btn-primary">
            <i class="fas fa-file-pdf"></i> 下载PDF
          </button>
          <button @click="onClose" class="btn-secondary">
            <i class="fas fa-times"></i> 关闭
          </button>
        </div>
      </div>
      
      <!-- 领域详情弹窗 -->
      <el-dialog
        v-model="showDetailDialog"
        :title="`${selectedDomain?.name} 评测历史`"
        width="50%"
      >
        <div v-if="selectedDomain">
          <el-table :data="selectedDomain.scores" style="width: 100%">
            <el-table-column prop="timestamp" label="评测时间">
              <template #default="scope">
                {{ formatTimestamp(scope.row.timestamp) }}
              </template>
            </el-table-column>
            <el-table-column prop="total_questions" label="问题数量" />
            <el-table-column prop="correct_answers" label="正确回答数" />
            <el-table-column prop="score" label="得分">
              <template #default="scope">
                <span :style="`color: ${getScoreColor(scope.row.score)}`">
                  {{ (scope.row.score * 100).toFixed(2) }}%
                </span>
              </template>
            </el-table-column>
          </el-table>
          
          <!-- 历史得分走势图 -->
          <div class="history-chart-container" ref="historyChartContainer"></div>
        </div>
      </el-dialog>
    </div>
  </template>
  
  <script>
  import { computed, ref, watch, onMounted, nextTick } from 'vue';
  import { fileApi } from '../api/file';
  import * as echarts from 'echarts';
  
  export default {
    name: 'DomainReportDialog',
    props: {
      show: {
        type: Boolean,
        required: true
      },
      file: {
        type: Object,
        default: null
      },
      content: {
        type: Object,
        default: null
      }
    },
    emits: ['close'],
    setup(props, { emit }) {
      const domainChartContainer = ref(null);
      const historyChartContainer = ref(null);
      let domainChart = null;
      let historyChart = null;
      
      const showDetailDialog = ref(false);
      const selectedDomain = ref(null);
      
      // 解析JSON格式内容为适合表格展示的格式
      const modelInfo = computed(() => {
        if (!props.content || !props.content.model_info) return {};
        return {
          name: props.content.model_info.name || '',
          lastUpdate: props.content.model_info.last_update || ''
        };
      });
      
      const domains = computed(() => {
        if (!props.content || !props.content.domains) return [];
        return props.content.domains;
      });
      
      // 监听内容变化，更新图表
      watch(() => props.content, async (newContent) => {
        if (newContent) {
          await nextTick();
          initDomainChart();
        }
      }, { deep: true });
      
      // 监听显示状态，更新图表尺寸
      watch(() => props.show, async (newShow) => {
        if (newShow) {
          await nextTick();
          if (domainChart) {
            domainChart.resize();
          }
        }
      });
      
      const onClose = () => {
        emit('close');
      };
      
      // 下载JSON文件
      const downloadJson = async () => {
        try {
          if (!props.file) {
            throw new Error('文件信息缺失');
          }
          await fileApi.downloadFile(props.file.path);
        } catch (error) {
          console.error('下载JSON文件失败:', error);
          alert('下载JSON文件失败: ' + error.message);
        }
      };
      
      // 使用后端API下载PDF
      const downloadPdf = async () => {
        try {
          if (!props.file) {
            throw new Error('文件信息缺失');
          }
          
          // 显示加载状态
          const loadingIndicator = ref(true);
          
          // 使用fileApi调用后端生成PDF
          const blob = await fileApi.downloadPDF(props.file.path);
          
          // 下载文件
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `${props.file.modelName || '模型'}_领域评估报告.pdf`;
          document.body.appendChild(a);
          a.click();
          window.URL.revokeObjectURL(url);
          document.body.removeChild(a);
          
          loadingIndicator.value = false;
        } catch (error) {
          console.error('下载PDF文件失败:', error);
          alert('下载PDF文件失败: ' + error.message);
        }
      };
      
      const getScoreColor = (score) => {
        if (score === undefined || score === null) return '#C0C4CC';
        if (score >= 0.9) return '#67C23A';  // 优秀 - 绿色
        if (score >= 0.8) return '#409EFF';  // 良好 - 蓝色
        if (score >= 0.6) return '#E6A23C';  // 及格 - 黄色
        return '#F56C6C';  // 不及格 - 红色
      };
      
      // 显示领域详情
      const showDomainDetail = (domain) => {
        selectedDomain.value = domain;
        showDetailDialog.value = true;
        
        // 在下一个DOM更新周期初始化历史图表
        nextTick(() => {
          initHistoryChart();
        });
      };
      
      // 格式化时间戳
      const formatTimestamp = (timestamp) => {
        if (!timestamp) return '';
        
        // 处理形如 "20250407_201825" 的时间戳
        const match = timestamp.match(/^(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})$/);
        if (match) {
          const [_, year, month, day, hour, minute, second] = match;
          return `${year}-${month}-${day} ${hour}:${minute}:${second}`;
        }
        
        return timestamp;
      };
      
      // 初始化领域对比图表
      const initDomainChart = () => {
        if (!domainChartContainer.value || !props.content || !props.content.domains) return;
        
        // 如果已经存在图表实例，先销毁
        if (domainChart) {
          domainChart.dispose();
        }
        
        // 创建新的图表实例
        domainChart = echarts.init(domainChartContainer.value);
        
        // 准备数据
        const domainNames = props.content.domains.map(d => d.name);
        const domainScores = props.content.domains.map(d => (d.average_score * 100).toFixed(2)); // 转换为百分比并保留2位小数
        
        // 设置图表选项
        const option = {
          tooltip: {
            trigger: 'axis',
            formatter: (params) => {
              return `${params[0].name}: ${params[0].value}%`;
            }
          },
          grid: {
            left: '3%',
            right: '4%',
            bottom: '3%',
            containLabel: true
          },
          xAxis: {
            type: 'category',
            data: domainNames,
            axisLabel: {
              interval: 0,
              rotate: 30
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
              name: '平均得分',
              type: 'bar',
              data: domainScores,
              itemStyle: {
                color: function(params) {
                  const score = params.value / 100; // 转回0-1范围
                  return getScoreColor(score);
                }
              },
              label: {
                show: true,
                formatter: '{c}%',
                position: 'top'
              }
            }
          ]
        };
        
        // 应用选项
        domainChart.setOption(option);
        
        // 添加窗口大小变化时的自适应
        window.addEventListener('resize', () => {
          if (domainChart) {
            domainChart.resize();
          }
        });
      };
      
      // 初始化历史得分走势图
      const initHistoryChart = () => {
        if (!historyChartContainer.value || !selectedDomain.value) return;
        
        // 如果已经存在图表实例，先销毁
        if (historyChart) {
          historyChart.dispose();
        }
        
        // 创建新的图表实例
        historyChart = echarts.init(historyChartContainer.value);
        
        // 准备数据
        const timestamps = selectedDomain.value.scores.map(s => formatTimestamp(s.timestamp));
        const scores = selectedDomain.value.scores.map(s => s.score * 100); // 转换为百分比
        
        // 设置图表选项
        const option = {
          title: {
            text: `${selectedDomain.value.name} 得分走势`,
            left: 'center'
          },
          tooltip: {
            trigger: 'axis',
            formatter: '{b}<br/>{a}: {c}%'
          },
          grid: {
            left: '3%',
            right: '4%',
            bottom: '8%',
            containLabel: true
          },
          xAxis: {
            type: 'category',
            data: timestamps,
            axisLabel: {
              interval: 0,
              rotate: 30
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
              name: '得分',
              type: 'line',
              data: scores,
              smooth: true,
              markLine: {
                data: [
                  { type: 'average', name: '平均值' }
                ]
              },
              itemStyle: {
                color: '#409EFF'
              }
            }
          ]
        };
        
        // 应用选项
        historyChart.setOption(option);
        
        // 添加对话框关闭时的调整
        const handleDialogClose = () => {
          setTimeout(() => {
            if (historyChart) {
              historyChart.resize();
            }
          }, 300);
        };
        
        // 监听对话框关闭事件
        watch(showDetailDialog, (newVal) => {
          if (!newVal) {
            handleDialogClose();
          }
        });
      };
      
      onMounted(() => {
        // 组件挂载后，如果内容已加载，初始化图表
        if (props.content) {
          nextTick(() => {
            initDomainChart();
          });
        }
      });
  
      return {
        onClose,
        downloadJson,
        downloadPdf,
        getScoreColor,
        modelInfo,
        domains,
        domainChartContainer,
        historyChartContainer,
        showDetailDialog,
        selectedDomain,
        showDomainDetail,
        formatTimestamp
      };
    }
  };
  </script>
  
  <style scoped>
  .report-dialog {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
  }
  
  .report-dialog-content {
    background: white;
    border-radius: 12px;
    width: 90%;
    max-width: 1200px;
    max-height: 90vh;
    display: flex;
    flex-direction: column;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1), 0 1px 3px rgba(0, 0, 0, 0.08);
  }
  
  .dialog-header {
    padding: 1rem 1.5rem;
    border-bottom: 1px solid #e2e8f0;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .dialog-header h2 {
    margin: 0;
    font-size: 1.5rem;
    color: #2d3748;
    font-weight: 600;
  }
  
  .btn-close {
    background: none;
    border: none;
    font-size: 1.25rem;
    color: #718096;
    cursor: pointer;
    padding: 0.5rem;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s ease;
    border-radius: 6px;
  }
  
  .btn-close:hover {
    background: #f7fafc;
    color: #2d3748;
  }
  
  .dialog-body {
    padding: 1.5rem;
    overflow-y: auto;
    flex: 1;
    max-height: calc(90vh - 8rem); /* 调整以留出底部按钮的空间 */
  }
  
  .dialog-footer {
    padding: 1rem 1.5rem;
    border-top: 1px solid #e2e8f0;
    display: flex;
    justify-content: flex-end;
    gap: 0.75rem;
  }
  
  .content-wrapper {
    background: #f8fafc;
    border-radius: 8px;
  }
  
  .section {
    padding: 1rem;
    margin-bottom: 1.5rem;
    background: white;
    border-radius: 8px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  }
  
  .section-title {
    margin: 0 0 1rem;
    color: #2d3748;
    font-size: 1.25rem;
    font-weight: 600;
  }
  
  .loading {
    text-align: center;
    padding: 2rem;
    color: #718096;
    font-size: 1.125rem;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
  }
  
  .loading i {
    font-size: 2rem;
    color: #4299e1;
  }
  
  .btn-primary, .btn-secondary {
    padding: 0.75rem 1.5rem;
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
  
  .chart-container {
    width: 100%;
    height: 400px;
    margin-top: 1rem;
  }
  
  .history-chart-container {
    width: 100%;
    height: 300px;
    margin-top: 2rem;
  }
  
  @media (max-width: 640px) {
    .report-dialog-content {
      width: 95%;
      max-height: 95vh;
    }
  
    .dialog-header h2 {
      font-size: 1.25rem;
    }
    
    .chart-container,
    .history-chart-container {
      height: 250px;
    }
  }
  </style>

<template>
  <div class="question-management">
    <!-- 头部搜索框保持不变 -->
    <div class="header">
      <h1>题库管理</h1>
      <div class="search-box">
        <input 
          type="text" 
          v-model="searchQuery" 
          placeholder="搜索题库..."
          @input="filterQuestionBanks"
        >
        <i class="fas fa-search"></i>
      </div>
    </div>

    <!-- 综合指标题库 -->
    <div class="section">
      <div class="section-header">
    <h2 class="section-title">
      <i class="fas fa-database"></i>
      综合指标题库
    </h2>
    <!-- 题库生成按钮 -->
    <el-button 
      type="warning" 
      @click="showGenerateDialog"
      class="generate-btn"
    >
      <i class="fas fa-cogs"></i> 生成题库
    </el-button>

      </div>
      <div v-if="loading" class="loading-container">
        <el-skeleton :rows="3" animated />
      </div>
      <div v-else-if="filteredCompositeBanks.length === 0" class="empty-state">
        <i class="fas fa-database"></i>
        <p>暂无综合指标题库数据</p>
      </div>
      <div v-else class="question-banks-grid">
        <div v-for="bank in filteredCompositeBanks" :key="bank.id" class="bank-card">
          <div class="bank-header">
            <div class="bank-header" @click.stop="showBankQuestions(bank.id, bank.name)">  
            <div class="bank-title">
              <h3>{{ bank.name }}</h3>
              <div class="bank-id">ID: {{ bank.id }}</div>
              <div class="dimension-tags-wrapper">
                <el-tag 
                  v-for="dimension in bank.dimensions.split(', ')" 
                  :key="dimension"
                  :type="dimension === '学科综合能力' ? 'success' : 'primary'"
                  class="dimension-tag"
                >
                  {{ dimension }}
                </el-tag>
              </div>
            </div>
            </div>
          </div>
          <div class="bank-info">
            <div class="info-item">
              <i class="fas fa-question-circle"></i>
              <span>题目数量：{{ bank.total }}</span>
            </div>
            <div class="info-item">
              <i class="fas fa-calendar"></i>
              <span>创建时间：{{ formatDate(bank.created_at) }}</span>
            </div>
          </div>
          <div class="bank-actions">
            <el-button-group>
              <el-button 
                type="primary" 
                @click="navigateToTransform(bank.id)"
              >
                <i class="fas fa-magic"></i> 变形
              </el-button>
              <el-button 
                type="success" 
                @click="navigateToTest(bank.id)"
              >
                <i class="fas fa-flask"></i> 测试
              </el-button>
            </el-button-group>
          </div>
        </div>
      </div>
    </div>

    <!-- 学科分类指标题库 -->
    <div class="section">
      <h2 class="section-title">
        <i class="fas fa-book"></i>
        学科分类指标题库
      </h2>
      <div v-if="loading" class="loading-container">
        <el-skeleton :rows="3" animated />
      </div>
      <div v-else-if="filteredSubjectBanks.length === 0" class="empty-state">
        <i class="fas fa-book"></i>
        <p>暂无学科分类题库数据</p>
      </div>
      <div v-else class="question-banks-grid">
        <div v-for="bank in filteredSubjectBanks" :key="bank.id" class="bank-card">
          <div class="bank-header">
            <div class="bank-header" @click.stop="showBankQuestions(bank.id, bank.name)">  
            <div class="bank-title">
              <h3>{{ bank.name }}</h3>
              <div class="bank-id">ID: {{ bank.id }}</div>
              <div class="dimension-tags-wrapper">
                <el-tag 
                  v-for="dimension in bank.dimensions.split(', ')" 
                  :key="dimension"
                  type="primary"
                  class="dimension-tag"
                >
                  {{ dimension }}
                </el-tag>
              </div>
            </div>
            </div>
          </div>
          <div class="bank-info">
            <div class="info-item">
              <i class="fas fa-question-circle"></i>
              <span>题目数量：{{ bank.total }}</span>
            </div>
            <div class="info-item">
              <i class="fas fa-calendar"></i>
              <span>创建时间：{{ formatDate(bank.created_at) }}</span>
            </div>
          </div>
          <div class="bank-actions">
            <el-button-group>
              <el-button 
                type="primary" 
                @click="navigateToTransform(bank.id)"
              >
                <i class="fas fa-magic"></i> 变形
              </el-button>
              <el-button 
                type="success" 
                @click="navigateToTest(bank.id)"
              >
                <i class="fas fa-flask"></i> 测试
              </el-button>
            </el-button-group>
          </div>
        </div>
      </div>
    </div>

    <!-- 变形题库 -->
    <div class="section">
      <h2 class="section-title">
        <i class="fas fa-random"></i>
        变形题库
      </h2>
      <div v-if="loading" class="loading-container">
        <el-skeleton :rows="3" animated />
      </div>
      <div v-else-if="filteredTransformedBanks.length === 0" class="empty-state">
        <i class="fas fa-random"></i>
        <p>暂无变形题库数据</p>
      </div>
      <div v-else class="question-banks-grid">
        <div v-for="bank in filteredTransformedBanks" :key="bank.id" class="bank-card transformed">
          <div class="bank-header">
            <div class="bank-header" @click.stop="showBankQuestions(bank.id, bank.name)">  
            <div class="bank-title">
              <h3>{{ bank.name }}</h3>
              <div class="bank-id">ID: {{ bank.id }}</div>
              <div class="dimension-tags-wrapper">
                <el-tag 
                  v-for="method in bank.transform_methods" 
                  :key="method"
                  type="warning"
                  class="method-tag"
                >
                  {{ method }}
                </el-tag>
              </div>
            </div>
            </div>
          </div>
          <div class="bank-info">
            <div class="info-item">
              <i class="fas fa-question-circle"></i>
              <span>变形题目数量：{{ bank.total }}</span>
            </div>
            <div class="info-item">
              <i class="fas fa-calendar"></i>
              <span>创建时间：{{ formatDate(bank.created_at) }}</span>
            </div>
          </div>
          <div class="bank-actions">
            <el-button 
              type="success" 
              @click="navigateToTest(bank.id)"
              class="test-button"
            >
              <i class="fas fa-flask"></i> 测试变形题库
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 修改后的可视化区域 -->
    <div class="section visualization-section">
      <h2 class="section-title">
        <i class="fas fa-chart-pie"></i>
        题库分析可视化
      </h2>
      <div class="visualization-container">
        <!-- 柱状图独占一行 -->
        <div class="chart-container full-width">
          <div id="questionCountChart" class="chart"></div>
        </div>
        
        <div class="chart-row">
        <!-- 玫瑰图和雷达图放在第二行 -->
        <div class="chart-container">
          <div id="dimensionsChart" class="chart"></div>
        </div>
        <div class="chart-container">
          <div id="radarChart" class="chart"></div>
        </div>
        </div>
      </div>
    </div>

  <!-- 在文件末尾，</template>标签前添加 -->
  <el-dialog 
  v-model="showQuestionsDialog" 
  :title="`题库预览 - ${selectedBankName}`" 
  width="60%"
  center
>
  <div class="questions-preview">
    <div v-for="(question, index) in previewQuestions" :key="index" class="question-item">
      <h4>
        题目 {{ index + 1 }} (ID: {{ question.id }})
        <el-tag v-if="question.transform_method" type="warning" size="small">
          {{ question.transform_method }}
        </el-tag>
        <el-tag v-else-if="question.isOriginal" type="success" size="small">
          原始题目
        </el-tag>
      </h4>
      
      <p><strong>题目:</strong> {{ question.question }}</p>
      
      <div v-if="question.type === 'choice' && Object.keys(question.options || question.choices || {}).length">
        <p><strong>选项:</strong></p>
        <ul>
          <li v-for="(value, key) in (question.options || question.choices)" :key="key">
            {{ key }}: {{ value }}
          </li>
        </ul>
      </div>
      
      <p><strong>答案:</strong> {{ question.answer }}</p>
      <p v-if="question['题目领域']"><strong>领域:</strong> {{ question['题目领域'] }}</p>
      <p v-if="question['测试指标']"><strong>测试指标:</strong> {{ question['测试指标'] }}</p>
      <p v-if="question.difficulty || question['难度级别']">
        <strong>难度:</strong> {{ question.difficulty || question['难度级别'] }}
      </p>
      
      <el-divider v-if="index < previewQuestions.length - 1" />
    </div>
  </div>
  
  <template #footer>
    <el-button type="primary" @click="showQuestionsDialog = false">关闭</el-button>
  </template>
</el-dialog>

    <el-dialog 
  v-model="showGenerateDialogVisible" 
  title="生成新题库" 
  width="40%"
  center
>
  <el-form :model="generateForm" label-width="120px">
    <el-form-item label="题库名称" required>
  <el-input 
    v-model="generateForm.name" 
    placeholder="请输入新题库名称"
    :rules="[{ required: true, message: '题库名称不能为空' }]"
  />
</el-form-item>
    
    <el-form-item label="测试维度">
      <el-select 
        v-model="generateForm.dimensions" 
        multiple
        placeholder="选择测试维度"
      >
        <el-option 
          v-for="dim in availableDimensions" 
          :key="dim"
          :label="dim"
          :value="dim"
        />
      </el-select>
    </el-form-item>
    
    <el-form-item label="题目数量">
      <el-input-number 
        v-model="generateForm.count" 
        :min="5" 
        :max="1000"
      />
    </el-form-item>
    
    <el-form-item label="难度级别" required>
  <el-checkbox-group v-model="generateForm.difficulties">
    <el-checkbox label="easy">简单</el-checkbox>
    <el-checkbox label="medium">中等</el-checkbox>
    <el-checkbox label="hard">困难</el-checkbox>
  </el-checkbox-group>
</el-form-item>

<el-form-item label="难度分布">
  <el-radio-group v-model="generateForm.difficultyDistribution">
    <el-radio label="random">随机分布</el-radio>
    <el-radio label="balanced">均衡分布</el-radio>
    <el-radio label="custom">自定义比例</el-radio>
  </el-radio-group>
  
  <div v-if="generateForm.difficultyDistribution === 'custom'" class="custom-distribution">
    <template v-if="generateForm.difficulties.includes('easy')">
      <el-input-number 
        v-model="generateForm.easyPercent"
        :min="0" 
        :max="100"
        :precision="0"
        :step="5"
        controls-position="right"
      />% 简单
    </template>
    
    <template v-if="generateForm.difficulties.includes('medium')">
      <el-input-number 
        v-model="generateForm.mediumPercent"
        :min="0" 
        :max="100"
        :precision="0"
        :step="5"
        controls-position="right"
      />% 中等
    </template>

    <template v-if="generateForm.difficulties.includes('hard')">
      <el-input-number 
        v-model="generateForm.hardPercent"
        :min="0" 
        :max="100"
        :precision="0"
        :step="5"
        controls-position="right"
      />% 困难
    </template>
  </div>
</el-form-item>
  </el-form>
  
  <template #footer>
    <el-button @click="showGenerateDialogVisible = false">取消</el-button>
    <el-button 
      type="primary" 
      @click="generateNewBank"
      :loading="generating"
    >
      生成题库
    </el-button>
  </template>
</el-dialog>

  </div>
</template>

<script>
import { nextTick } from 'vue';
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router';
import * as echarts from 'echarts';
import { ElMessage } from 'element-plus';
import { fetchQuestionBanks, fetchBankQuestions, generateQuestionBank } from '@/api/questionBank';

export default {
  setup() {
    const router = useRouter();
    const searchQuery = ref('');
    const baseBanks = ref([]);
    const transformedBanks = ref([]);
    const loading = ref(true);
    const lastUpdated = ref('');
    const showQuestionsDialog = ref(false);
    const previewQuestions = ref([]);
    const selectedBankName = ref('');
    const showGenerateDialogVisible = ref(false);
const generating = ref(false);

const generateForm = ref({
  name: '',
  dimensions: [],
  count: 10,
  difficulties: ['easy', 'medium', 'hard'], // 默认选中所有难度
  difficultyDistribution: 'balanced',
  easyPercent: 30,
  mediumPercent: 40,
  hardPercent: 30
});

const availableDimensions = ref([
    '学科综合能力', '知识能力', '语言能力', 
    '理解能力', '推理能力', '安全能力'
]);

const showGenerateDialog = () => {
  generateForm.value = {
    name: '新题库_' + new Date().toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    }).replace(/[\/\s:]/g, '_'),
    dimensions: [],
    difficulties: ['easy', 'medium', 'hard'], // 确保初始化difficulties
    count: 10,
    difficultyDistribution: 'balanced',
    easyPercent: 30,
    mediumPercent: 40,
    hardPercent: 30
  };
  showGenerateDialogVisible.value = true;
};

const generateNewBank = async () => {
  if (!generateForm.value.name) {
    ElMessage.error('请输入题库名称');
    return;
  }
  
  if (!generateForm.value.dimensions.length) {
    ElMessage.error('请至少选择一个测试维度');
    return;
  }
  
  if (!generateForm.value.difficulties.length) {
    ElMessage.error('请至少选择一个难度级别');
    return;
  }
  
  if (generateForm.value.difficultyDistribution === 'custom') {
    const total = (generateForm.value.easyPercent || 0) + 
                 (generateForm.value.mediumPercent || 0) + 
                 (generateForm.value.hardPercent || 0);
    if (total !== 100) {
      ElMessage.error('自定义难度比例总和必须为100%');
      return;
    }
  }
  
  generating.value = true;
  
  try {
    const params = {
      name: generateForm.value.name,
      dimensions: generateForm.value.dimensions,
      difficulties: generateForm.value.difficulties,
      distribution: generateForm.value.difficultyDistribution,
      count: generateForm.value.count,
      easyPercent: generateForm.value.easyPercent,
      mediumPercent: generateForm.value.mediumPercent,
      hardPercent: generateForm.value.hardPercent
    };
    
    const response = await generateQuestionBank(params);
    
    if (response.success) {
      ElMessage.success('题库生成成功');
      // 刷新题库列表
      await loadData();
      showGenerateDialogVisible.value = false;
    } else {
      ElMessage.error(response.error || '题库生成失败');
    }
  } catch (error) {
    ElMessage.error('请求失败: ' + error.message);
  } finally {
    generating.value = false;
  }
};
  
    // 初始化高级图表
    let dimensionsChart = null;
    let questionCountChart = null;
    let radarChart = null;

    const formatDate = (dateString) => {
      if (!dateString) return '未知日期';
      const date = new Date(dateString);
      return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      });
    };

    const calculateQuestionCounts = () => {
      const allBanks = [...baseBanks.value, ...transformedBanks.value];
      return {
        labels: allBanks.map(bank => bank.name),
        values: allBanks.map(bank => bank.total)
      };
    };

    // 只计算学科分类题库的维度数据
    const calculateDimensionsData = () => {
      const dimensionMap = {};
      
  // 现在统计综合指标题库（dimensions数量≥2）
  filteredCompositeBanks.value.forEach(bank => {
    if (bank.dimensions && typeof bank.dimensions === 'string') {
      const dimensions = bank.dimensions.split(', ');
      dimensions.forEach(dim => {
        if (!dimensionMap[dim]) {
          dimensionMap[dim] = 0;
        }
        dimensionMap[dim] += bank.total;
      });
    }
  });
      
      return Object.entries(dimensionMap).map(([name, value]) => ({ 
        name, 
        value 
      }));
    };

    // ==================== 新增数据计算方法 ====================
// 学科分类题库维度统计（用于玫瑰图）
const calculateSubjectDimensions = () => {
  const dimensionMap = {};
  
  filteredSubjectBanks.value.forEach(bank => {
    if (bank.dimensions && typeof bank.dimensions === 'string') {
      const dimensions = bank.dimensions.split(', ');
      // 学科分类题库每个bank只应有一个维度
      const dim = dimensions[0];
      if (!dimensionMap[dim]) {
        dimensionMap[dim] = 0;
      }
      dimensionMap[dim] += bank.total;
    }
  });
  
  return Object.entries(dimensionMap).map(([name, value]) => ({
    name,
    value
  }));
};

// 综合指标题库维度统计（用于雷达图）
const calculateCompositeDimensions = () => {
  const dimensionMap = {};
  
  filteredCompositeBanks.value.forEach(bank => {
    if (bank.dimensions && typeof bank.dimensions === 'string') {
      const dimensions = bank.dimensions.split(', ');
      dimensions.forEach(dim => {
        if (!dimensionMap[dim]) {
          dimensionMap[dim] = 0;
        }
        dimensionMap[dim] += bank.total;
      });
    }
  });
  
  return Object.entries(dimensionMap).map(([name, value]) => ({
    name,
    value
  }));
};

    const loadData = async () => {
      try {
        loading.value = true;
        const { baseBanks: base, transformedBanks: transformed, lastUpdated: updated } = 
          await fetchQuestionBanks();
        
        baseBanks.value = base;
        transformedBanks.value = transformed;
        lastUpdated.value = new Date(updated).toLocaleString();
        
        initCharts();
      } finally {
        loading.value = false;
      }
    };

    const showBankQuestions = async (bankId, bankName) => {
       try {
        loading.value = true;
        selectedBankName.value = bankName;
        // 对于变形题库，不限制返回数量
        const isTransformed = bankId.includes('transformed_');
        const limit = isTransformed ? 'all' : 5;
        previewQuestions.value = await fetchBankQuestions(bankId, limit);
        showQuestionsDialog.value = true;
      } finally {
        loading.value = false;
      }
    };

    const navigateToTransform = (id) => {
       router.push({
       path: '/question-transform',
       query: { bankId: id }
      });
    };

    const navigateToTest = (id) => {
       router.push({
       path: '/model-test',
      query: { bankId: id }
      });
    };

    const initCharts = () => {
      if (dimensionsChart) dimensionsChart.dispose();
      if (questionCountChart) questionCountChart.dispose();
      if (radarChart) radarChart.dispose();

      const dimensionsData = calculateDimensionsData();
      const maxValue = Math.max(...dimensionsData.map(d => d.value)) * 1.2;

      // 获取维度统计数据
  const roseData = calculateSubjectDimensions(); // 学科维度数据
  const radarData = calculateCompositeDimensions(); // 综合维度数据



const maxRadarValue = radarData.length ? 
  Math.max(...radarData.map(d => d.value)) * 1.2 : 100;

      // 1. 柱状图（调整到第一个显示）
      questionCountChart = echarts.init(document.getElementById('questionCountChart'));
      questionCountChart.setOption({
        title: { text: '题库题目数量', left: 'center' },
        tooltip: {
          trigger: 'axis',
          formatter: params => `完整名称: ${params[0].data.fullName}<br/>题目数量: ${params[0].value}`
        },
        xAxis: {
          type: 'category',
          data: calculateQuestionCounts().labels.map(name => 
            name.length > 12 ? name.substr(0, 10) + '...' : name  // 调整显示长度
          ),
          axisLabel: { 
            rotate: 30, 
            fontSize: 10,
            interval: 0,  // 强制显示所有标签
            formatter: function(value) {
              // 确保所有标签都显示
              return value;
            }
          }
        },
        yAxis: { type: 'value' },
        series: [{
          name: '题目数量',
          type: 'bar',
          data: calculateQuestionCounts().labels.map((name, index) => ({
            value: calculateQuestionCounts().values[index],
            fullName: name
          })),
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#4f46e5' },
              { offset: 0.5, color: '#6366f1' },
              { offset: 1, color: '#a5b4fc' }
            ])
          }
        }],
        grid: {
          left: '3%',
          right: '4%',
          bottom: '15%',  // 为长标签留出更多空间
          containLabel: true
        }
      });
      
  // ==================== 玫瑰图配置 ====================
  dimensionsChart = echarts.init(document.getElementById('dimensionsChart'));
  dimensionsChart.setOption({
    title: { 
      text: '学科维度分布', 
      left: 'center',
      textStyle: {
        color: '#4f46e5',
        fontWeight: 'bold'
      }
    },
    tooltip: { 
      trigger: 'item',
      formatter: params => `
        ${params.name}<br/>
        题目总数: <b>${params.value}</b><br/>
        占比: <b>${params.percent}%</b>
      `
    },
    series: [{
      name: '题目数量',
      type: 'pie',
      roseType: 'radius',
      radius: ['15%', '70%'],
      label: {
        formatter: '{b}: {c}'
      },
      data: roseData.sort((a, b) => b.value - a.value),
      itemStyle: {
        borderRadius: 8,
        borderColor: '#fff',
        borderWidth: 2,
        color: function(params) {
          const colorList = ['#4f46e5', '#6366f1', '#8b5cf6', '#a855f7'];
          return colorList[params.dataIndex % colorList.length];
        }
      }
    }]
  });

  // ==================== 雷达图配置 ====================
  radarChart = echarts.init(document.getElementById('radarChart'));
  radarChart.setOption({
    title: { 
      text: '综合指标维度分布',
      left: 'center',
      textStyle: {
        color: '#4f46e5',
        fontWeight: 'bold'
      }
    },
    tooltip: {
      formatter: params => `
        ${params.name}<br/>
        题目总数: <b>${params.value}</b>
      `
    },
    radar: {
      indicator: radarData.map(item => ({
        name: item.name.length > 6 ? 
          item.name.substr(0, 5) + '...' : 
          item.name,
        max: maxRadarValue
      })),
      splitArea: { show: true },
      axisLine: { lineStyle: { color: 'rgba(79, 70, 229, 0.5)' } },
      splitLine: {
        lineStyle: {
          color: 'rgba(79, 70, 229, 0.3)'
        }
      }
    },
    series: [{
      type: 'radar',
      data: [{
        value: radarData.map(item => item.value),
        name: '题目数量',
        areaStyle: { 
          color: 'rgba(99, 102, 241, 0.6)',
          opacity: 0.3
        },
        lineStyle: { 
          width: 2,
          color: '#6366f1'
        },
        label: {
          show: true,
          formatter: params => params.value
        }
      }]
    }]
  });
};

    const createParticles = () => {
      const containers = document.querySelectorAll('.chart-container');
      containers.forEach(container => {
        for (let i = 0; i < 15; i++) {
          const particle = document.createElement('div');
          particle.classList.add('particle');
          Object.assign(particle.style, {
            width: `${Math.random() * 5 + 2}px`,
            height: `${Math.random() * 5 + 2}px`,
            left: `${Math.random() * 100}%`,
            top: `${Math.random() * 100}%`,
            opacity: Math.random() * 0.5 + 0.1,
            animationDelay: `${Math.random() * 3}s`,
            animationDuration: `${Math.random() * 5 + 3}s`
          });
          container.appendChild(particle);
        }
      });
    };

    onMounted(() => {
      loadData();
      window.addEventListener('resize', initCharts);
      createParticles();
    });

    // 计算过滤后的题库
    const filteredBaseBanks = computed(() => 
      baseBanks.value.filter(bank => 
        bank.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
        bank.dimensions.toLowerCase().includes(searchQuery.value.toLowerCase())
      )
    );

    // 综合指标题库（dimensions数量≥2）
    const filteredCompositeBanks = computed(() => 
      filteredBaseBanks.value.filter(bank => {
        if (!bank.dimensions) return false;
        const dimensions = bank.dimensions.split(', ');
        return dimensions.length >= 2;
      })
    );

    // 学科分类指标题库（dimensions数量=1）
    const filteredSubjectBanks = computed(() => 
      filteredBaseBanks.value.filter(bank => {
        if (!bank.dimensions) return false;
        const dimensions = bank.dimensions.split(', ');
        return dimensions.length === 1;
      })
    );

    // 变形题库过滤保持不变
    const filteredTransformedBanks = computed(() => 
      transformedBanks.value.filter(bank => 
        bank.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
        bank.dimensions.toLowerCase().includes(searchQuery.value.toLowerCase())
      )
    );

    return {
      searchQuery,
      baseBanks,
      transformedBanks,
      lastUpdated,
      loading,
      formatDate,
      navigateToTransform,
      navigateToTest,
      filteredCompositeBanks,
      filteredSubjectBanks,
      filteredTransformedBanks,
      showQuestionsDialog,
      previewQuestions,
      selectedBankName,
      showBankQuestions,
      showGenerateDialogVisible,
      generateForm,
      availableDimensions,
      generating,
      showGenerateDialog,
      generateNewBank
    };
  }
};
</script>

<style scoped>
/* General Styles */
.question-management {
  padding: 2rem;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.header h1 {
  margin: 0;
  color: #2c3e50;
  font-size: 2rem;
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

/* Section Styles */
.section {
  margin-bottom: 3rem;
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
}

.section-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin: 0 0 1.5rem 0;
  color: #2d3748;
  font-size: 1.5rem;
}

.section-title i {
  color: #4299e1;
}

/* Grid Styles */
.question-banks-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
}

.bank-card {
  background: #f7fafc;
  border-radius: 8px;
  padding: 1.5rem;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  position: relative;
  padding-bottom: 70px; /* 为固定按钮留出空间 */
  min-width: 300px;
  max-width: 100%;
  overflow: hidden;
}

.bank-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 12px rgba(0, 0, 0, 0.1);
}

.bank-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
  width: 100%;
  overflow: hidden;
}

.bank-header .bank-header {
  width: 100%;
  overflow: hidden;
}

.bank-title {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  width: 100%;
  overflow: hidden;
}

.bank-title h3 {
  margin: 0;
  color: #2d3748;
  font-size: 1.25rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}

.bank-id {
  color: #718096;
  font-size: 0.875rem;
}

.fixed-actions {
  display: flex;
  gap: 8px;
}

.transform-btn {
  background: linear-gradient(135deg, #6366f1, #4f46e5);
  border: none;
  color: white;
}

.test-btn {
  background: linear-gradient(135deg, #10b981, #059669);
  border: none;
  color: white;
}

.transform-btn:hover {
  background: linear-gradient(135deg, #4f46e5, #6366f1);
}

.test-btn:hover {
  background: linear-gradient(135deg, #059669, #10b981);
}

/* Info Item Styles */
.bank-info {
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

/* Button Styles */
.bank-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  position: absolute;
  bottom: 20px;
  right: 20px;
}

/* 生成按钮样式 */
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.generate-btn {
  background: linear-gradient(135deg, #f59e0b, #f97316);
  border: none;
  color: white;
  font-weight: bold;
  box-shadow: 0 2px 10px rgba(245, 158, 11, 0.3);
  transition: all 0.3s ease;
}

.generate-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(245, 158, 11, 0.4);
}

.generate-btn i {
  margin-right: 8px;
}

/* 生成弹窗样式 */
.generate-dialog {
  border-radius: 12px;
  overflow: hidden;
}

.generate-dialog .el-dialog__header {
  background: linear-gradient(135deg, #f59e0b, #f97316);
  margin-right: 0;
}

.generate-dialog .el-dialog__title {
  color: white;
  font-weight: bold;
}

.dialog-header-icon {
  position: absolute;
  top: -20px;
  left: 50%;
  transform: translateX(-50%);
  background: white;
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  z-index: 1;
}

.dialog-header-icon i {
  font-size: 28px;
  color: #f59e0b;
}

.generate-form {
  padding: 20px;
}

.name-input, .dimensions-select, .difficulty-select {
  width: 100%;
}

.count-input {
  width: 120px;
}

.dialog-footer {
  display: flex;
  justify-content: center;
  width: 100%;
}

.cancel-btn {
  margin-right: 20px;
}

.confirm-btn {
  background: linear-gradient(135deg, #f59e0b, #f97316);
  border: none;
}

.confirm-btn:hover {
  background: linear-gradient(135deg, #f97316, #f59e0b);
}


/* Visualization Section */
.visualization-section {
  width: 95%;
  margin-bottom: 0;
}

.visualization-container {
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 2rem;
}

.chart-container.full-width {
  height: 400px;
  background: linear-gradient(145deg, #ffffff, #f8fafc);
  position: relative;
  overflow: hidden;
  border-radius: 12px;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

/* 玫瑰图和雷达图容器并排显示 */
.chart-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
  margin-top: 2rem;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.chart-container {
  height: 400px;
  border-radius: 12px;
  padding: 1rem;
  border-radius: 8px;
  position: relative;
  overflow: hidden;
}

/* Hover effects for chart containers */
.chart-container:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
}

.chart {
  width: 100%;
  height: 100%;
  transition: opacity 0.3s ease;
}

.particle {
  position: absolute;
  background: rgba(66, 153, 225, 0.6);
  border-radius: 50%;
  pointer-events: none;
  animation: float 3s infinite ease-in-out;
}

@keyframes float {
  0% { transform: translate(0, 0); opacity: 0; }
  50% { opacity: 0.6; }
  100% { transform: translate(20px, -20px); opacity: 0; }
}

/* Loading and Empty State Styles */
.loading-container {
  padding: 2rem;
}

.empty-state {
  text-align: center;
  padding: 3rem;
  color: #718096;
}

.empty-state i {
  font-size: 3rem;
  margin-bottom: 1rem;
  color: #cbd5e0;
}

.empty-state p {
  font-size: 1.1rem;
  margin: 0;
}

/* Tag Styles */
.dimension-tag {
  margin-right: 0.5rem;
  margin-bottom: 0.5rem;
  max-width: 120px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Card Effects */
.bank-card.transformed {
  border-left: 4px solid #4299e1;
}

/* Particle Effects */
.particle {
  position: absolute;
  background: rgba(66, 153, 225, 0.6);
  border-radius: 50%;
  pointer-events: none;
  animation: float 3s infinite ease-in-out;
}

@keyframes float {
  0% { transform: translate(0, 0); opacity: 0; }
  50% { opacity: 0.6; }
  100% { transform: translate(20px, -20px); opacity: 0; }
}

/* Chart Enhancements */
.chart-container {
  position: relative;
  overflow: hidden;
  height: 400px;
  background: linear-gradient(145deg, #ffffff, #f8fafc);
  border-radius: 12px;
  transition: all 0.3s;
}

.chart-container:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
}

.questions-preview {
  max-height: 60vh;
  overflow-y: auto;
  padding: 0 1rem;
}

.question-item {
  margin-bottom: 1.5rem;
}

.question-item h4 {
  margin: 0 0 0.5rem 0;
  color: #2d3748;
}

.question-item p {
  margin: 0.5rem 0;
}

.question-item ul {
  margin: 0.5rem 0;
  padding-left: 1.5rem;
}

.question-item li {
  margin-bottom: 0.25rem;
}

.custom-distribution {
  margin-top: 10px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.custom-distribution .el-input-number {
  width: 80px;
}

.generate-form .el-form-item {
  margin-bottom: 20px;
}

.generate-form .el-radio-group {
  margin-bottom: 10px;
}

/* New styles for dimension tags */
.dimension-tags-wrapper {
  display: flex;
  flex-wrap: wrap;
  width: 100%;
  margin-top: 0.5rem;
}

/* 为method-tag添加同样的样式控制 */
.method-tag {
  margin-right: 0.5rem;
  margin-bottom: 0.5rem;
  max-width: 120px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style> 
<template>
  <div class="model-test">
    <div class="header">
      <h1>模型测试</h1>
      <div class="header-actions">
      </div>
    </div>


      
     <!-- 创建测试任务表单 - 现在直接显示在界面上 -->
<div class="create-test-section">
      <h2 class="section-title">
        <i class="fas fa-flask"></i> 创建测试任务
      </h2>
      <el-form :model="testForm" label-width="120px" class="test-form">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="任务名称" required>
              <el-input 
                v-model="testForm.name" 
                placeholder="请输入任务名称"
                class="modern-input"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="选择模型" required>
              <el-select 
                v-model="testForm.modelId" 
                placeholder="请选择要测试的模型"
                class="modern-select"
              >
                <el-option
                  v-for="model in models"
                  :key="model.id"
                  :label="model.name"
                  :value="model.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="选择题库" required>
              <el-select
                v-model="testForm.bankId"
                placeholder="请选择题库"
                filterable
                @change="handleBankChange"
                class="modern-select"
              >
                <el-option-group
                  v-for="group in bankGroups"
                  :key="group.label"
                  :label="group.label"
                >
                  <el-option
                    v-for="bank in group.options"
                    :key="bank.id"
                    :label="`${bank.name} (${bank.total}题)`"
                    :value="bank.id"
                  />
                </el-option-group>
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="选择题目" required>
              <div class="question-selector">
  <div class="selector-actions">
    <el-button size="small" @click="selectAllQuestions" class="action-btn">
      <i class="fas fa-check-square"></i> 全选
    </el-button>
    <el-button size="small" @click="clearSelection" class="action-btn">
      <i class="fas fa-ban"></i> 清空
    </el-button>
    <span class="selected-count">已选 {{ testForm.questionIds.length }} 题</span>
  </div>
  <div class="selected-questions-container">
    <div 
      class="selected-questions-list"
      :class="{ 'has-selections': testForm.questionIds.length > 0 }"
    >
      <el-tag
        v-for="questionId in testForm.questionIds"
        :key="questionId"
        closable
        size="small"
        @close="removeQuestion(questionId)"
        class="question-tag"
      >
        {{ getQuestionTitle(questionId) }}
      </el-tag>
      <div v-if="testForm.questionIds.length === 0" class="empty-placeholder">
        未选择任何题目
      </div>
    </div>
    <el-select
      v-model="testForm.questionIds"
      multiple
      filterable
      placeholder="请选择题目"
      :disabled="!testForm.bankId"
      class="question-select-dropdown"
    >
      <el-option
        v-for="question in questions"
        :key="question.id"
        :label="question.title"
        :value="question.id"
      />
    </el-select>
  </div>
</div>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="测试参数 - 温度">
              <el-slider 
                v-model="testForm.parameters.temperature" 
                :min="0" 
                :max="2" 
                :step="0.1"
                show-input
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="测试参数 - 最大长度">
              <el-input-number 
                v-model="testForm.parameters.max_length" 
                :min="1" 
                :max="4096"
                controls-position="right"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item>
          <el-button 
            type="primary" 
            @click="submitTest"
            :loading="loading"
            :disabled="loading"
          >
            {{ loading ? '测试中...' : '开始测试' }}
          </el-button>
          <el-button 
            @click="resetForm"
            :disabled="loading"
          >
            重置表单
          </el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { fetchQuestionBanks, fetchAllBankQuestions } from '@/api/questionBank'
import { createTest, getTestDetail, exportTestReport, getModelList } from '@/api/ModelTest'

export default {
  name: 'ModelTest',
  setup() {
    const route = useRoute()
    const tests = ref([])
    const models = ref([])
    const questions = ref([])
    const searchQuery = ref('')
    const baseBanks = ref([])
    const transformedBanks = ref([])
    const loading = ref(false)

    const testForm = ref({
      name: '',
      modelId: '',
      bankId: route.query.bankId || '',
      questionIds: [],
      parameters: {
        temperature: 0.7,
        max_length: 2048
      }
    })

    // 新增重置表单方法
    const resetForm = () => {
      testForm.value = {
        name: '',
        modelId: '',
        bankId: route.query.bankId || '',
        questionIds: [],
        parameters: {
          temperature: 0.7,
          max_length: 2048
        }
      }
    }

    // 新增的 getTestStatusTag 函数
    const getTestStatusTag = (status) => {
      const statusMap = {
        pending: 'info',
        running: 'warning',
        completed: 'success',
        failed: 'danger'
      }
      return statusMap[status] || 'info'
    }

    // 新增的题目选择方法
    const selectAllQuestions = () => {
      testForm.value.questionIds = questions.value.map(q => q.id)
    }

    const clearSelection = () => {
      testForm.value.questionIds = []
    }
    const removeQuestion = (questionId) => {
  testForm.value.questionIds = testForm.value.questionIds.filter(id => id !== questionId)
}

const getQuestionTitle = (questionId) => {
  const question = questions.value.find(q => q.id === questionId)
  return question ? question.title : `题目 ${questionId}`
}

// 加载模型列表
const loadModels = async () => {
      try {
        const response = await getModelList()
        // 直接使用 response，因为 request.js 已经处理了 response.data
        models.value = response.models
        console.log('Loaded models:', models.value) // 添加日志以便调试
      } catch (error) {
        console.error('Failed to load models:', error)
        ElMessage.error('加载模型列表失败')
      }
}

    // 题库分组
    const bankGroups = computed(() => [
      {
        label: '综合指标题库',
        options: baseBanks.value.filter(bank => {
          const dimensions = bank.dimensions?.split(', ') || []
          return dimensions.length >= 2
        })
      },
      {
        label: '学科分类题库',
        options: baseBanks.value.filter(bank => {
          const dimensions = bank.dimensions?.split(', ') || []
          return dimensions.length === 1
        })
      },
      {
        label: '变形题库',
        options: transformedBanks.value
      }
    ])

    // 加载题库数据
    const loadBanks = async () => {
      try {
        const { baseBanks: base, transformedBanks: transformed } = await fetchQuestionBanks()
        baseBanks.value = base
        transformedBanks.value = transformed
        
        // 如果路由中有bankId，自动打开对话框并加载题目
        if (route.query.bankId) {
          await handleBankChange(route.query.bankId)
        }
      } catch (error) {
        console.error('加载题库失败:', error)
      }
    }

    // 题库选择变化时加载题目
    const handleBankChange = async (bankId) => {
      if (!bankId) {
        questions.value = []
        testForm.value.questionIds = []
        return
      }
      
      try {
        const questionsData = await fetchAllBankQuestions(bankId)
        const isTransformed = bankId.includes('transformed_')
        
        questions.value = questionsData.map(q => {
          // 对于变形题库，使用ID和变形方法作为标题
          let title = ''
          if (isTransformed && q.transform_method) {
            title = `${q.id} - (${q.transform_method})`
          } else if (q.title) {
            // 使用后端提供的标题
            title = q.title
          } else {
            // 默认标题格式
            title = `${q.id} - ${q.question.substring(0, 30)}${q.question.length > 30 ? '...' : ''}`
          }
          
          return {
            id: q.id,
            title: title,
            raw: q  // 保存原始题目数据
          }
        })
        
        // 默认选择所有题目
        testForm.value.questionIds = questions.value.map(q => q.id)
      } catch (error) {
        console.error('加载题目失败:', error)
        questions.value = []
      }
    }



    // 提交测试任务
    const submitTest = async () => {
      if (!testForm.value.name) {
        ElMessage.warning('请输入任务名称')
        return
      }
      if (!testForm.value.modelId) {
        ElMessage.warning('请选择模型')
        return
      }
      if (!testForm.value.bankId) {
        ElMessage.warning('请选择题库')
        return
      }
      if (testForm.value.questionIds.length === 0) {
        ElMessage.warning('请至少选择一道题目')
        return
      }
      
      try {
        loading.value = true  // 开始加载
        // 准备测试数据
        const selectedQuestions = questions.value
          .filter(q => testForm.value.questionIds.includes(q.id))
          .map(q => q.raw)
        
        const testData = {
          model_name: testForm.value.modelId,
          dataset_path: testForm.value.bankId,
          proxy: testForm.value.parameters.proxy || null,
          questions: selectedQuestions,
          parameters: {
            temperature: testForm.value.parameters.temperature,
            max_length: testForm.value.parameters.max_length
          }
        }
        
        await createTest(testData)
        ElMessage.success('测试任务创建成功')
        resetForm()
      } catch (error) {
        console.error('创建测试失败:', error)
        ElMessage.error(error.response?.data?.detail || '测试任务创建失败')
      } finally {
        loading.value = false  // 结束加载
      }
    }

    // 查看测试详情
    const viewTest = async (test) => {
      try {
        const response = await getTestDetail(test.id)
        // TODO: 实现查看测试详情的逻辑
        console.log('测试详情:', response.data)
      } catch (error) {
        console.error('获取测试详情失败:', error)
        ElMessage.error('获取测试详情失败')
      }
    }

    // 导出报告
    const exportReport = async (test) => {
      try {
        const response = await exportTestReport(test.id)
        // 处理文件下载
        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', `test_report_${test.id}.pdf`)
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        ElMessage.success('导出成功')
      } catch (error) {
        console.error('导出失败:', error)
        ElMessage.error('导出失败')
      }
    }


    // 合并后的 onMounted
    onMounted(async () => {
      await Promise.all([
        loadModels(),
        loadBanks()
      ])
      
      if (route.query.bankId) {
        testForm.value.bankId = route.query.bankId
        await handleBankChange(route.query.bankId)
      }
    })

    const filteredTests = computed(() => {
      if (!searchQuery.value) return tests.value
      const query = searchQuery.value.toLowerCase()
      return tests.value.filter(test => 
        test.name.toLowerCase().includes(query) ||
        test.model_name.toLowerCase().includes(query)
      )
    })

    const getTestStatusText = (status) => {
      const statusMap = {
        pending: '等待中',
        running: '进行中',
        completed: '已完成',
        failed: '失败'
      }
      return statusMap[status] || status
    }

    const getScoreColor = (score) => {
      if (score >= 0.9) return '#67C23A'
      if (score >= 0.8) return '#409EFF'
      if (score >= 0.6) return '#E6A23C'
      return '#F56C6C'
    }

    const formatDate = (date) => {
      return new Date(date).toLocaleString()
    }

    // 监听 loading 状态变化
    watch(loading, (newValue, oldValue) => {
      if (oldValue === true && newValue === false) {
        ElMessage.success('测试完毕，请查看测试报告！')
      }
    })

    return {
      tests,
      models,
      questions,
      searchQuery,
      filteredTests,
      testForm,
      bankGroups,
      loading,
      resetForm,
      viewTest,
      exportReport,
      submitTest,
      handleBankChange,
      selectAllQuestions,
      clearSelection,
      getTestStatusTag,
      getTestStatusText,
      getScoreColor,
      formatDate,
      removeQuestion,
      getQuestionTitle
    }
  }
}
</script>

<style scoped>
/* 替换弃用的 -ms-high-contrast 属性 */
@media (forced-colors: active) {
  /* Element UI 组件的高对比度模式样式 */
  .el-button,
  .el-input,
  .el-select,
  .el-tag,
  .el-progress,
  .el-slider {
    forced-color-adjust: auto;
    border-color: ButtonText !important;
    color: ButtonText !important;
    background-color: ButtonFace !important;
  }

  /* 特定组件的高对比度调整 */
  .el-button--primary {
    background-color: Highlight !important;
    color: HighlightText !important;
  }

  .el-input__inner {
    background-color: Field !important;
    color: FieldText !important;
  }
}

/* 确保所有交互元素在高对比度模式下可见 */
[class^="el-"]:focus-visible {
  outline: 2px solid Highlight !important;
  outline-offset: 2px;
}
.model-test {
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

.header-actions {
  display: flex;
  gap: 1rem;
  align-items: center;
}

/* 新增创建测试任务区域样式 */
.create-test-section {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 2rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
}

.create-test-section h2 {
  margin-top: 0;
  margin-bottom: 1.5rem;
  color: #2c3e50;
  font-size: 1.5rem;
}


.tests-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 1.5rem;
}

.test-card {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.test-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 12px rgba(0, 0, 0, 0.1);
}

.test-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
}

.test-title {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.test-title h3 {
  margin: 0;
  color: #2d3748;
  font-size: 1.25rem;
}

.test-info {
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

.test-metrics {
  margin-bottom: 1.5rem;
  padding: 1rem;
  background: #f7fafc;
  border-radius: 8px;
}

.metric-item {
  margin-bottom: 1rem;
}

.metric-item:last-child {
  margin-bottom: 0;
}

.metric-label {
  display: block;
  margin-bottom: 0.5rem;
  color: #4a5568;
  font-size: 0.875rem;
}

.test-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
}
.question-selector {
  width: 100%;
}

.selected-questions-container {
  position: relative;
  margin-top: 8px;
  width: 100%; /* 确保容器宽度占满 */
}

.selected-questions-list {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 5px;
  min-height: 42px;
  max-height: 120px;
  overflow-y: auto;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  background-color: #f5f7fa;
  width: 100%; /* 确保列表宽度占满 */
  box-sizing: border-box; /* 包含padding和border在宽度内 */
}

.selected-questions-list.has-selections {
  padding: 8px;
}

.question-tag {
  margin: 2px;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.empty-placeholder {
  color: #c0c4cc;
  font-size: 14px;
  line-height: 30px;
  padding: 0 10px;
}

.question-select-dropdown {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  opacity: 0;
  z-index: -1;
}

</style> 
<template>
  <div class="question-transform">
    <div class="header">
      <h1>题库变形</h1>
      <div class="header-actions">
        <el-button type="primary" @click="showTransformDialog">
          <i class="fas fa-magic"></i> 创建变形任务
        </el-button>
        <div class="search-box">
          <el-input 
            v-model="searchQuery" 
            placeholder="搜索任务..."
            prefix-icon="el-icon-search"
            clearable
          />
        </div>
        <el-select v-model="statusFilter" placeholder="状态筛选" clearable class="status-filter-select">
          <el-option label="全部" value="" />
          <el-option label="等待中" value="pending" />
          <el-option label="变形中" value="transforming" />
          <el-option label="评估中" value="evaluating" />
          <el-option label="已完成" value="completed" />
          <el-option label="失败" value="failed" />
        </el-select>
      </div>
    </div>

    <div class="tasks-grid">
      <div v-for="task in filteredTasks" :key="task.id" class="task-card">
        <div class="task-header">
          <h3>{{ task.name }}</h3>
          <el-tag :type="getTaskStatusTag(task.status)">
            {{ getTaskStatusText(task.status) }}
          </el-tag>
        </div>
        <div class="task-info">
          <div class="info-item">
            <i class="fas fa-file"></i>
            <span>题库文件：{{ task.source_file }}</span>
          </div>
          <div class="info-item">
            <i class="fas fa-calendar"></i>
            <span>创建时间：{{ formatDate(task.created_at) }}</span>
          </div>
          <div class="info-item">
            <i class="fas fa-clock"></i>
            <span>完成时间：{{ task.completed_at ? formatDate(task.completed_at) : '进行中' }}</span>
          </div>
          <div v-if="task.status === 'transforming' || task.status === 'evaluating'" class="progress-bar">
            <el-progress :percentage="task.progress" :status="task.status === 'failed' ? 'exception' : ''" />
          </div>
        </div>
        <div class="task-actions">
          <el-button-group>
            <el-button 
              size="small" 
              type="primary"
              :disabled="!task.transformed_file || !task.evaluate_file" 
              @click="viewResults(task)" 
            >
              <i class="fas fa-eye"></i> 查看结果
            </el-button>
            <!-- 新增重试按钮 -->
            <el-button 
              size="small" 
              type="warning" 
              :disabled="!['failed', 'paused'].includes(task.status)" 
              @click="retryTask(task)"
            >
              <i class="fas fa-redo"></i> 重试
            </el-button>
            <el-button 
              size="small" 
              type="danger" 
              @click="deleteTask(task)"
            >
              <i class="fas fa-trash"></i> 删除
            </el-button>
          </el-button-group>
        </div>
      </div>
    </div>

    <!-- 创建变形任务对话框 -->
    <el-dialog
      v-model="dialogVisible"
      title="创建变形任务"
      width="60%"
      @close="resetDialog"
      append-to-body
      custom-class="transform-dialog"
    >
      <el-form :model="taskForm" label-width="100px" ref="taskFormRef">
        <el-form-item label="任务名称" prop="name" :rules="[{ required: true, message: '请输入任务名称', trigger: 'blur' }]">
          <el-input v-model="taskForm.name" placeholder="请输入任务名称"></el-input>
        </el-form-item>
        <el-form-item label="题库文件" prop="selectedFile" :rules="[{ required: true, message: '请选择题库文件', trigger: 'change' }]">
          <el-select 
            v-model="taskForm.selectedFile" 
            placeholder="请选择题库文件，可输入搜索" 
            filterable 
            default-first-option
            style="width: 100%;"
          >
            <el-option
              v-for="file in questionFiles"
              :key="file"
              :label="file"
              :value="file">
            </el-option>
          </el-select>
        </el-form-item>

        <el-form-item label="题库详情">
          <div v-if="detailsLoading" class="details-loading">
            <i class="el-icon-loading"></i> 加载详情中...
          </div>
          <div v-else-if="detailsError" class="details-error">
            <i class="el-icon-error"></i> {{ detailsError }}
          </div>
          <div v-else-if="filteredMetadata && Object.keys(filteredMetadata).length > 0" class="details-content">
            <div class="distribution-container">
              <!-- 难度分布 -->
              <div v-if="filteredMetadata.difficulty_distribution" class="tag-group">
                <div class="tag-group-title">难度分布:</div>
                <div class="tag-group-content">
                  <!-- 按固定顺序显示难度标签 -->
                  <template v-for="level in ['简单', '中等', '困难']">
                    <el-tag 
                      v-if="filteredMetadata.difficulty_distribution[level]"
                      :key="level"
                      :type="getDifficultyTagType(level)"
                      class="difficulty-tag"
                      :data-count="filteredMetadata.difficulty_distribution[level]"
                    >
                      {{ level }}
                    </el-tag>
                  </template>
                  <!-- 显示其他可能的难度标签 -->
                  <!--
                  <el-tag 
                    v-for="(count, level) in filteredMetadata.difficulty_distribution" 
                    :key="level"
                    v-if="!['简单', '中等', '困难'].includes(level)"
                    :type="getDifficultyTagType(level)"
                    class="difficulty-tag"
                    :data-count="count"
                  >
                    {{ level }}
                  </el-tag>
                  -->
                </div>
              </div>

              <!-- 题型分布 -->
              <div v-if="filteredMetadata.types" class="tag-group">
                <div class="tag-group-title">题型分布:</div>
                <div class="tag-group-content">
                  <el-tag 
                    v-for="(count, type) in filteredMetadata.types" 
                    :key="type"
                    :type="getQuestionType(type)"
                    class="type-tag"
                    :data-count="count"
                  >
                    {{ getQuestionTypeName(type) }}
                  </el-tag>
                </div>
              </div>

              <!-- 能力维度 -->
              <div v-if="filteredMetadata.dimensions" class="tag-group">
                <div class="tag-group-title">能力维度:</div>
                <div class="tag-group-content">
                  <el-tag 
                    v-for="dimension in filteredMetadata.dimensions" 
                    :key="dimension"
                    type="primary"
                    effect="light"
                  >
                    {{ dimension }}
                  </el-tag>
                </div>
              </div>
            </div>

            <!-- 其他元数据 -->
            <div v-if="hasOtherMetadata" class="other-metadata">
              <div class="tag-group-title" style="margin-top: 16px;">其他元数据:</div>
              <div class="metadata-display-container">
                <MetadataDisplay :metadata="filteredOtherMetadata" />
              </div>
            </div>

            <div class="preview-button">
              <el-button
                type="primary"
                size="small"
                @click="previewSelectedFile"
                :disabled="!taskForm.selectedFile"
              >
                <i class="fas fa-eye"></i> 题库预览
              </el-button>
            </div>
          </div>
          <div v-else-if="taskForm.selectedFile && !detailsLoading">
             未找到可显示的元数据 (metadata)。
             <el-button
              type="primary"
              size="small"
              @click="previewSelectedFile"
              :disabled="!taskForm.selectedFile"
              style="margin-left: 10px;"
            >
              <i class="fas fa-eye"></i> 题库预览
            </el-button>
          </div>
          <div v-else>
            请先选择题库文件
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitTask">确定</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 题库预览对话框 -->
    <div v-if="previewVisible" class="preview-window" @click.self="closePreview">
      <div class="preview-container">
        <div class="preview-header">
          <span>题库预览</span>
          <el-button
            class="close-btn"
            circle
            @click="previewVisible = false"
            type="danger"
            size="small"
          >
            <i class="fas fa-times"></i>
          </el-button>
        </div>
        <div class="preview-content" v-if="previewData">
          <div v-for="(question, index) in previewData" :key="index" class="question-item">
            <div class="question-header">
              <span class="question-id">题目 {{ index + 1 }}</span>
              <el-tag size="small" :type="getQuestionType(question.type)">
                {{ getQuestionTypeName(question.type) }}
              </el-tag>
              <el-tag size="small" :type="getDifficultyTagType(question.难度级别)">
                {{ question.难度级别 }}
              </el-tag>
            </div>
            <div class="question-content">
              <div class="question-text">{{ question.question }}</div>
              <div class="question-choices" v-if="question.choices">
                <div v-for="(choice, key) in question.choices" :key="key" class="choice-item">
                  {{ key }}: {{ choice }}
                </div>
              </div>
              <div class="question-meta">
                <el-tag size="small" type="primary">{{ question.题目领域 || '未知领域' }}</el-tag>
                <el-tag size="small" type="success">{{ question.测试指标 || '未知指标' }}</el-tag>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 新的合并结果对话框 -->
     <div v-if="resultsVisible" class="fixed-dialog-overlay" @click.self="resultsVisible = false">
        <div class="result-dialog-container">
          <div class="result-dialog-header">
            <span>结果详情 - {{ currentTaskName }}</span>
             <el-button
                class="close-btn"
                circle
                @click="resultsVisible = false"
                type="danger"
                size="small"
             >
                 <i class="fas fa-times"></i>
             </el-button>
          </div>
          <div class="result-dialog-content" v-loading="resultsLoading">
            <div v-if="overviewStats" class="overview-section">
               <el-descriptions title="概览统计" :column="2" border size="small">
                  <el-descriptions-item label="成功变形的原题数">{{ overviewStats.successfulTransformOriginal }} / {{ overviewStats.totalOriginal }}</el-descriptions-item>
                  <el-descriptions-item label="变形后总题目数">{{ overviewStats.totalTransformedGenerated }}</el-descriptions-item>
                  <el-descriptions-item label="成功评估的变形题目数">{{ overviewStats.successfulEvaluatedVersions }} / {{ overviewStats.totalTransformedGenerated }}</el-descriptions-item>
                   <el-descriptions-item label="变形题目总评分">
                       <span class="overview-score">{{ overviewStats.overallScorePercent }}%</span>
                   </el-descriptions-item>
               </el-descriptions>
            </div>

            <div v-if="resultsData && resultsData.length > 0">
              <el-collapse v-model="activeCollapseItems" accordion>
                <el-collapse-item 
                  v-for="(item, index) in resultsData" 
                  :key="item.original_question.id || index" 
                  :name="item.original_question.id || index"
                >
                  <template #title>
                    <div class="original-q-header">
                       <div class="question-title">
                         <span class="question-id-tag">题目 {{ index + 1 }}</span>
                         <span>{{ item.original_question.question.substring(0, 80) }}...</span>
                       </div>
                       <div class="question-tags">
                         <span class="question-id-small">ID: {{ item.original_question.id || 'N/A' }}</span>
                         <el-tag size="small">{{ getQuestionTypeName(item.original_question.type) }}</el-tag>
                       </div>
                    </div>
                  </template>
                  
                  <!-- 展开后显示变形版本和评估 -->
                  <div v-if="item.detailed_versions && item.detailed_versions.length > 0">
                      <div v-for="(version, v_index) in item.detailed_versions" :key="v_index" class="detailed-version-item">
                          <h4>变形版本 {{ v_index + 1 }}: {{ version.transform_method || '未知方法' }}</h4>
                          <div class="version-content">
                              <p><strong>难度:</strong> <span class="version-value">{{ version.difficulty || '-' }}</span></p>
                              <p><strong>题干:</strong> <span class="version-value">{{ version.question || '-' }}</span></p>
                              <!-- 修改这里：使用 v-for 循环显示选项 -->
                              <div v-if="version.options && Object.keys(version.options).length > 0" class="options-section">
                                <strong>选项:</strong>
                                <div v-for="(text, key) in version.options" :key="key" class="option-item">
                                  <span class="option-key">{{ key }}:</span>
                                  <span class="option-text">{{ text }}</span>
                                </div>
                              </div>
                              <p><strong>答案:</strong> <span class="version-value">{{ version.answer || '-' }}</span></p>
                          </div>
                          <div v-if="version.scores" class="evaluation-scores-inline">
                              <h5>评估分数:</h5>
                               <div class="score-item-inline">
                                  <span>文本相似度:</span>
                                  <span>{{ version.scores['文本相似度']?.toFixed(3) ?? 'N/A' }}</span>
                              </div>
                               <div class="score-item-inline">
                                  <span>测试指标一致性:</span>
                                  <span>{{ version.scores['测试指标一致性']?.toFixed(3) ?? 'N/A' }}</span>
                              </div>
                               <div class="score-item-inline">
                                  <span>语义清晰度与表达准确性:</span>
                                  <span>{{ version.scores['语义清晰度与表达准确性']?.toFixed(3) ?? 'N/A' }}</span>
                              </div>
                               <div class="score-item-inline">
                                  <span>可评估性:</span>
                                  <span>{{ version.scores['可评估性']?.toFixed(3) ?? 'N/A' }}</span>
                              </div>
                               <div class="score-item-inline comprehensive-score-inline">
                                  <span><strong>综合得分:</strong></span>
                                  <span><strong>{{ version.comprehensive_score?.toFixed(3) ?? 'N/A' }}</strong></span>
                              </div>
                          </div>
                           <div v-else-if="item.evaluation_error">
                               <p class="error-display">评估数据错误: {{ item.evaluation_error }}</p>
                           </div>
                           <div v-else>
                               <p><i>无评估数据</i></p>
                           </div>
                      </div>
                  </div>
                  <div v-else-if="item.transform_error">
                      <p class="error-display">变形失败: {{ item.transform_error }}</p>
                  </div>
                  <div v-else>
                       <p>无变形版本。</p>
                  </div>

                </el-collapse-item>
              </el-collapse>
            </div>
            <div v-else-if="!resultsLoading">
               <el-empty description="未能加载结果数据或无有效结果"></el-empty>
            </div>
          </div>
        </div>
    </div>

  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { ElMessage, ElMessageBox, ElLoading } from 'element-plus'
import MetadataDisplay from './MetadataDisplay.vue'
import { useRouter, useRoute } from 'vue-router'

export default {
  name: 'QuestionTransform',
  components: {
    MetadataDisplay
  },
  setup() {
    const router = useRouter();
    const route = useRoute();
    const tasks = ref([])
    const searchQuery = ref('')
    const statusFilter = ref('')
    const dialogVisible = ref(false)
    const taskForm = ref({
      name: '',
      selectedFile: null
    })
    const questionFiles = ref([])
    const selectedFile = ref(null)
    const previewVisible = ref(false)
    const previewData = ref(null)
    let pollTimer = null
    const taskFormRef = ref(null)

    const questionDetails = ref(null)
    const detailsLoading = ref(false)
    const detailsError = ref(null)
    const keysToExclude = ['generatedAt', 'version', 'randomSeed', 'generated_at', 'random_seed']

    const resultsVisible = ref(false)
    const resultsData = ref(null)
    const resultsLoading = ref(false)
    const activeCollapseItems = ref([])
    const currentTaskName = ref('')
    const overviewStats = ref(null)

    const filteredMetadata = computed(() => {
      if (!questionDetails.value) return null
      const filtered = {}
      for (const key in questionDetails.value) {
        const checkKey = key.charAt(0).toLowerCase() + key.slice(1).replace(/_([a-z])/g, (match, letter) => letter.toUpperCase())
        if (!keysToExclude.includes(checkKey) && !keysToExclude.includes(key)) {
          filtered[key] = questionDetails.value[key]
        }
      }
      
      // 处理可能有的不同命名情况
      if (!filtered.difficulty_distribution) {
        // 查找可能的难度分布字段
        for (const key in filtered) {
          const lowerKey = key.toLowerCase();
          if (lowerKey.includes('difficult') || lowerKey.includes('难度')) {
            if (typeof filtered[key] === 'object' && !Array.isArray(filtered[key])) {
              filtered.difficulty_distribution = filtered[key];
              delete filtered[key]; // 避免重复显示
              break;
            }
          }
        }
      }
      
      // 处理可能的题型分布
      if (!filtered.types) {
        for (const key in filtered) {
          const lowerKey = key.toLowerCase();
          if (lowerKey.includes('type') || lowerKey.includes('题型')) {
            if (typeof filtered[key] === 'object' && !Array.isArray(filtered[key])) {
              filtered.types = filtered[key];
              delete filtered[key]; // 避免重复显示
              break;
            }
          }
        }
      }
      
      // 处理可能的能力维度
      if (!filtered.dimensions) {
        for (const key in filtered) {
          const lowerKey = key.toLowerCase();
          if (lowerKey.includes('dimension') || lowerKey.includes('能力') || lowerKey.includes('维度')) {
            if (Array.isArray(filtered[key])) {
              filtered.dimensions = filtered[key];
              delete filtered[key]; // 避免重复显示
              break;
            }
          }
        }
      }
      
      return filtered
    })

    const filteredOtherMetadata = computed(() => {
      if (!filteredMetadata.value) return null;
      
      const result = {};
      const excludedKeys = ['difficulty_distribution', 'types', 'dimensions'];
      
      for (const key in filteredMetadata.value) {
        if (!excludedKeys.includes(key)) {
          result[key] = filteredMetadata.value[key];
        }
      }
      
      return result;
    });

    const hasOtherMetadata = computed(() => {
      if (!filteredOtherMetadata.value) return false;
      return Object.keys(filteredOtherMetadata.value).length > 0;
    });

    const filteredTasks = computed(() => {
      let result = tasks.value
      
      if (statusFilter.value) {
        result = result.filter(task => task.status === statusFilter.value)
      }
      
      if (searchQuery.value) {
        const query = searchQuery.value.toLowerCase()
        result = result.filter(task => 
          task.name.toLowerCase().includes(query) ||
          (task.source_file && task.source_file.toLowerCase().includes(query))
        )
      }
      
      return result
    })

    const fetchTasks = async () => {
      try {
        const params = new URLSearchParams()
        if (statusFilter.value) params.append('status', statusFilter.value)
        if (searchQuery.value) params.append('search', searchQuery.value)
        
        const queryString = params.toString()
        const apiUrl = queryString 
          ? `http://localhost:5000/api/tasks?${queryString}` 
          : 'http://localhost:5000/api/tasks'
          
        const response = await fetch(apiUrl)
        const data = await response.json()
        if (data.status === 'success') {
          tasks.value = Array.isArray(data.tasks) ? data.tasks : Object.values(data.tasks || {})
        }
      } catch (error) {
        console.error('获取任务列表失败:', error)
        tasks.value = []
      }
    }

    const startPolling = () => {
      if (pollTimer) clearInterval(pollTimer)
      pollTimer = setInterval(fetchTasks, 2000)
    }

    const fetchQuestionFiles = async () => {
      try {
        const response = await fetch('http://localhost:5000/api/question_banks')
        const data = await response.json()
        if (data.status === 'success' && Array.isArray(data.files)) {
          questionFiles.value = data.files
        } else {
          ElMessage.error('获取题库文件列表失败' + (data.message ? `: ${data.message}` : ''))
          questionFiles.value = []
        }
      } catch (error) {
        console.error('获取题库文件列表失败:', error)
        ElMessage.error('获取题库文件列表时发生网络错误')
        questionFiles.value = []
      }
    }

    const fetchQuestionDetails = async (filename) => {
      if (!filename) {
        questionDetails.value = null
        detailsError.value = null
        detailsLoading.value = false
        return
      }
      detailsLoading.value = true
      detailsError.value = null
      questionDetails.value = null

      try {
        const encodedFilename = encodeURIComponent(filename)
        const response = await fetch(`http://localhost:5000/api/question_banks/${encodedFilename}/details`)
        
        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}))
          throw new Error(errorData.message || `HTTP error ${response.status}`)
        }

        const data = await response.json()
        if (data.status === 'success') {
          questionDetails.value = typeof data.metadata === 'object' && data.metadata !== null ? data.metadata : {}
        } else {
          detailsError.value = data.message || '获取题库详情失败'
          ElMessage.error(detailsError.value)
          questionDetails.value = {}
        }
      } catch (error) {
        console.error(`获取题库详情失败 (${filename}):`, error)
        detailsError.value = `获取题库详情时出错: ${error.message}`
        ElMessage.error(detailsError.value)
        questionDetails.value = {}
      } finally {
        detailsLoading.value = false
      }
    }

    watch(() => taskForm.value.selectedFile, (newFile, oldFile) => {
      if (newFile && newFile !== oldFile) {
        fetchQuestionDetails(newFile)
      } else if (!newFile) {
        questionDetails.value = null
        detailsError.value = null
        detailsLoading.value = false
      }
    }, { immediate: false })

    const showTransformDialog = () => {
      resetDialog()
      dialogVisible.value = true
      if (questionFiles.value.length === 0) {
        fetchQuestionFiles()
      }
    }

    const resetDialog = () => {
      if (taskFormRef.value) {
        taskFormRef.value.resetFields()
      }
      taskForm.value.name = ''
      taskForm.value.selectedFile = null
      questionDetails.value = null
      detailsLoading.value = false
      detailsError.value = null
    }

    const previewSelectedFile = async () => {
      if (!taskForm.value.selectedFile) {
        ElMessage.warning('请先选择一个题库文件')
        return
      }
      previewData.value = null
      ElMessage.info('正在加载预览...')

      try {
        const encodedFilename = encodeURIComponent(taskForm.value.selectedFile)
        const response = await fetch(`http://localhost:5000/api/questions/${encodedFilename}/preview`)

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}))
          throw new Error(errorData.message || `HTTP error ${response.status}`)
        }

        const data = await response.json()

        if (data.status === 'success' && Array.isArray(data.questions)) {
          previewData.value = data.questions
          previewVisible.value = true
        } else {
          ElMessage.error(data.message || '获取预览数据失败或格式不正确')
          previewData.value = []
        }
      } catch (error) {
        console.error('获取预览数据失败:', error)
        ElMessage.error(`获取预览数据时出错: ${error.message}`)
        previewData.value = []
      }
    }
    
    const closePreview = () => {
      previewVisible.value = false
      previewData.value = null
    }

    const submitTask = async () => {
      if (!taskFormRef.value) return
      try {
        await taskFormRef.value.validate()
      } catch (fields) {
        console.log('表单验证失败:', fields)
        ElMessage.error('请检查表单输入')
        return
      }

      try {
        const response = await fetch('http://localhost:5000/api/tasks', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            name: taskForm.value.name,
            sourceFile: taskForm.value.selectedFile
          })
        })

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}))
          throw new Error(errorData.message || `HTTP error ${response.status}`)
        }

        const data = await response.json()
        if (data.status === 'success') {
          ElMessage.success('创建任务成功')
          dialogVisible.value = false
          fetchTasks()
        } else {
          ElMessage.error(data.message || '创建任务失败')
        }
      } catch (error) {
        console.error('创建任务失败:', error)
        ElMessage.error(`创建任务时出错: ${error.message}`)
      }
    }

    const mergeResults = (transformedData, evaluationData) => {
      if (!transformedData || !transformedData.questions || !evaluationData || !evaluationData.questions) {
          console.warn("数据不完整，无法合并结果。", { transformedData, evaluationData })
          return []
      }
      
      const merged = []
      const evaluationMap = new Map()
      evaluationData.questions.forEach(evalResult => {
          evaluationMap.set(evalResult.original_id, evalResult)
      })

      transformedData.questions.forEach(transformItem => {
          const originalQuestion = transformItem.original_question
          const originalId = originalQuestion?.id || 'N/A'
          const evaluationResult = evaluationMap.get(originalId)
          const detailedVersions = []

          if (transformItem.transformed_versions && transformItem.transformed_versions.length > 0) {
              transformItem.transformed_versions.forEach((version, index) => {
                  let scores = null
                  let comprehensiveScore = null

                  if (evaluationResult && evaluationResult.transformed_versions && evaluationResult.transformed_versions.length > index) {
                       const evalDetail = evaluationResult.transformed_versions[index]
                       scores = evalDetail.scores
                       comprehensiveScore = evalDetail.scores?.['综合得分']
                  }
                  
                  detailedVersions.push({
                      ...version,
                      scores: scores, 
                      comprehensive_score: comprehensiveScore
                  })
              })
          }
          
          merged.push({
              original_question: originalQuestion,
              detailed_versions: detailedVersions,
              transform_error: transformItem.error,
              evaluation_error: evaluationResult?.error
          })
      })

      return merged
    }

    const viewResults = async (task) => {
      resultsData.value = null
      overviewStats.value = null
      resultsLoading.value = true
      resultsVisible.value = true
      currentTaskName.value = task.name
      activeCollapseItems.value = []

      try {
        const [transformResponse, evaluationResponse] = await Promise.all([
          fetch(`http://localhost:5000/api/tasks/${task.id}/transformed`),
          fetch(`http://localhost:5000/api/tasks/${task.id}/evaluation`)
        ])

        if (!transformResponse.ok) {
          const errorData = await transformResponse.json().catch(() => ({}))
          throw new Error(`获取变形结果失败: ${errorData.message || transformResponse.status}`)
        }
        const transformJson = await transformResponse.json()
        if (transformJson.status !== 'success') {
           throw new Error(`获取变形结果失败: ${transformJson.message || '未知错误'}`)
        }
        const transformedData = transformJson.data

        if (!evaluationResponse.ok) {
          const errorData = await evaluationResponse.json().catch(() => ({}))
          throw new Error(`获取评估结果失败: ${errorData.message || evaluationResponse.status}`)
        }
        const evaluationJson = await evaluationResponse.json()
         if (evaluationJson.status !== 'success') {
           throw new Error(`获取评估结果失败: ${evaluationJson.message || '未知错误'}`)
        }
        const evaluationData = evaluationJson.data
        
        resultsData.value = mergeResults(transformedData, evaluationData)

        if (transformedData && evaluationData && resultsData.value) {
            const totalOriginal = transformedData.questions?.length || 0
            let successfulTransformOriginal = 0
            let totalTransformedGenerated = 0
            
            transformedData.questions?.forEach(item => {
                if (!item.error && item.transformed_versions && item.transformed_versions.length > 0) {
                    successfulTransformOriginal++
                    totalTransformedGenerated += item.transformed_versions.length
                }
            })

            // Correctly calculate successful evaluations count
            let successfulEvaluatedVersions = 0;
            evaluationData.questions?.forEach(q => { // Iterate through questions
                 if (q.transformed_versions) { // Check if versions exist
                     q.transformed_versions.forEach(v => {
                         // Count if scores object is present and has keys
                         if (v.scores && Object.keys(v.scores).length > 0) {
                             successfulEvaluatedVersions++;
                         }
                     });
                 }
            });

            overviewStats.value = {
                successfulTransformOriginal,
                totalOriginal,
                successfulEvaluatedVersions, // Use the correctly calculated count
                totalTransformedGenerated,
                // Correctly access the top-level average_score
                overallScorePercent: evaluationData.average_score !== undefined 
                                        ? (evaluationData.average_score * 100).toFixed(1) 
                                        : 'N/A'
            }
        }

      } catch (error) {
        console.error('查看结果失败:', error)
        ElMessage.error(`查看结果失败: ${error.message}`)
        resultsVisible.value = false
      } finally {
        resultsLoading.value = false
      }
    }

    const deleteTask = async (task) => {
      try {
        await ElMessageBox.confirm(
          `确定要删除任务 "${task.name}" 吗？此操作不可撤销，相关文件也将被删除。`, 
          '确认删除', 
          {
            confirmButtonText: '确定删除',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )
        
        ElMessage.info(`正在删除任务: ${task.name}`)
        
        const response = await fetch(`http://localhost:5000/api/tasks/${task.id}`, {
          method: 'DELETE'
        })

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}))
          throw new Error(errorData.message || `删除失败，HTTP状态码: ${response.status}`)
        }
        
        const data = await response.json()

        if (data.status === 'success') {
          ElMessage.success(`任务 "${task.name}" 删除成功`)
          fetchTasks()
        } else {
          ElMessage.error(data.message || '删除任务失败')
        }
      } catch (error) {
        if (error !== 'cancel') {
          console.error('删除任务失败:', error)
          ElMessage.error(`删除任务时出错: ${error.message || error}`)
        }
      }
    }

    // 添加重试任务的方法
    const retryTask = async (task) => {
      try {
        ElMessage.info(`正在重试任务: ${task.name}`)
        
        const response = await fetch(`http://localhost:5000/api/tasks/${task.id}/retry`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          }
        })
        
        const data = await response.json()
        
        if (response.ok) {
          ElMessage.success(`任务 "${task.name}" 已重新开始`)
          fetchTasks()
        } else {
          ElMessage.error(`重试失败: ${data.message || '未知错误'}`)
        }
      } catch (error) {
        console.error('重试任务出错:', error)
        ElMessage.error(`重试失败: ${error.message || '网络错误'}`)
      }
    }

    const getTaskStatusTag = (status) => {
      const statusMap = {
        pending: 'info',
        transforming: 'warning',
        evaluating: 'primary',
        completed: 'success',
        failed: 'danger'
      }
      return statusMap[status] || 'info'
    }

    const getTaskStatusText = (status) => {
      const statusMap = {
        pending: '等待中',
        transforming: '变形中',
        evaluating: '评估中',
        completed: '已完成',
        failed: '失败'
      }
      return statusMap[status] || status
    }

    const formatDate = (dateString) => {
      if (!dateString) return '-'
      try {
        const date = new Date(dateString)
        if (isNaN(date.getTime())) {
          return dateString
        }
        return date.toLocaleString('zh-CN', {
          year: 'numeric', month: '2-digit', day: '2-digit',
          hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false
        })
      } catch (e) {
        console.warn(`Error formatting date: ${dateString}`, e)
        return dateString
      }
    }

    const getDifficultyType = (difficulty) => {
       const difficultyStr = String(difficulty || '');
       console.log(`[getDifficultyType] Input: '${difficultyStr}' (Type: ${typeof difficultyStr})`);
       const typeMap = {
         '简单': 'success',
         '中等': 'warning',
         '困难': 'danger'
       };
       let result = 'info';
       if (difficultyStr in typeMap) {
           result = typeMap[difficultyStr];
           console.log(`[getDifficultyType] Match found for '${difficultyStr}', returning: '${result}'`);
       } else {
           console.log(`[getDifficultyType] No match found for '${difficultyStr}', returning default: '${result}'`);
       }
       return result;
    };

    const getQuestionType = (type) => {
      const typeStr = String(type || '').toLowerCase();
      const typeMap = {
        'choice': 'primary',
        'short_answer': 'success',
        'true_false': 'warning',
        'translation': 'info',
        'code': 'danger',
        'scenario': ''
      };
      if (typeStr in typeMap) {
          return typeMap[typeStr];
      }
      return 'info';
    };

    const getQuestionTypeName = (type) => {
      const lowerType = String(type || '').toLowerCase();
      const nameMap = {
        'choice': '选择题',
        'short_answer': '简答题',
        'true_false': '判断题',
        'translation': '翻译题',
        'code': '编程题',
        'scenario': '场景题'
      };
      return nameMap[lowerType] || type || '未知类型';
    };

    const formatChoicesText = (choices) => {
      if (typeof choices === 'string') {
          return choices;
      } else if (Array.isArray(choices)) {
          return choices.map(c => `${c.key}: ${c.text}`).join('; ');
      } else if (typeof choices === 'object' && choices !== null) {
           return Object.entries(choices).map(([key, value]) => `${key}: ${value}`).join('; ');
      } 
      return '无选项或格式未知'
    }

    const getDifficultyTagType = (difficulty) => {
      const difficultyStr = String(difficulty || '').toLowerCase();
      if (difficultyStr.includes('简单') || difficultyStr.includes('easy')) return 'success';
      if (difficultyStr.includes('中等') || difficultyStr.includes('medium')) return 'warning';
      if (difficultyStr.includes('困难') || difficultyStr.includes('hard')) return 'danger';
      return 'info';
    };

    onMounted(() => {
      fetchTasks()
      startPolling()
      
      // 检查URL参数是否包含bankId，如果有则自动打开创建任务对话框并选择对应题库
      if (route.query.bankId) {
        fetchQuestionFiles().then(() => {
          const bankId = route.query.bankId;
          // 找到对应的题库文件
          const matchedFile = questionFiles.value.find(file => file.includes(bankId));
          if (matchedFile) {
            taskForm.value.selectedFile = matchedFile;
            dialogVisible.value = true;
            // 生成默认任务名称
            taskForm.value.name = `${matchedFile.split('.')[0]}_变形任务`;
          }
        });
      }
    })

    onUnmounted(() => {
      if (pollTimer) clearInterval(pollTimer)
    })

    return {
      tasks,
      searchQuery,
      statusFilter,
      filteredTasks,
      dialogVisible,
      taskForm,
      taskFormRef,
      questionFiles,
      selectedFile,
      previewVisible,
      previewData,
      showTransformDialog,
      resetDialog,
      submitTask,
      viewResults,
      deleteTask,
      retryTask,
      getTaskStatusTag,
      getTaskStatusText,
      formatDate,
      getDifficultyType,
      getQuestionType,
      getQuestionTypeName,
      previewSelectedFile,
      closePreview,
      questionDetails,
      filteredMetadata,
      detailsLoading,
      detailsError,
      resultsVisible,
      resultsData,
      resultsLoading,
      activeCollapseItems,
      currentTaskName,
      overviewStats,
      formatChoicesText,
      getDifficultyTagType,
      filteredOtherMetadata,
      hasOtherMetadata,
    }
  }
}
</script>

<style scoped>
/* --- 通用 & 页面布局 --- */
.question-transform {
  padding: 2rem; /* 增加页面内边距 */
  background-color: #f8f9fa; /* 设置页面背景色 */
  min-height: calc(100vh - 50px); /* 假设顶部导航栏高度为 50px */
  background: linear-gradient(135deg, #f8f9fa 0%, #edf2f7 100%); /* 渐变背景 */
  font-family: "PingFang SC", "Microsoft YaHei", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  font-size: 16px; /* 调整基础字体大小 */
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2.5rem;
  background: white;
  padding: 1.25rem 2rem;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.header h1 {
  margin: 0;
  color: #2d3748; /* 深灰色标题 */
  font-size: 1.8em; /* 调整标题大小 */
  font-weight: 600;
  background: linear-gradient(90deg, #3b82f6, #6366f1);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  letter-spacing: 0.5px;
}

.header-actions {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.search-box {
  width: 280px; /* 调整搜索框宽度, 增加宽度以显示完整placeholder */
}

/* 新增：为状态筛选选择框设置固定宽度 */
.status-filter-select {
  width: 160px;
}

:deep(.el-button.el-button--primary) {
  background: linear-gradient(135deg, #3b82f6, #6366f1); /* 渐变按钮 */
  border: none;
  transition: all 0.3s ease;
  box-shadow: 0 4px 6px rgba(99, 102, 241, 0.2);
  font-weight: 500;
  letter-spacing: 0.5px;
}

:deep(.el-button.el-button--primary:hover) {
  transform: translateY(-2px);
  box-shadow: 0 6px 12px rgba(99, 102, 241, 0.25);
  background: linear-gradient(135deg, #2563eb, #4f46e5);
}

:deep(.el-button.el-button--primary:active) {
  transform: translateY(0);
  box-shadow: 0 2px 4px rgba(99, 102, 241, 0.2);
}

:deep(.el-button) {
  border-radius: 8px;
  padding: 10px 16px;
  font-weight: 500;
  transition: all 0.2s ease;
}

:deep(.el-button:not(.el-button--text):not(.el-button--primary):not(.el-button--danger):hover) {
  border-color: #3b82f6;
  color: #3b82f6;
  transform: translateY(-1px);
}

:deep(.el-input__wrapper) {
  border-radius: 8px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04), 0 0 0 1px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
}

:deep(.el-input__wrapper:focus-within) {
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.15), 0 0 0 1px rgba(99, 102, 241, 0.3);
}

:deep(.el-select .el-input__wrapper) {
  width: 140px;
}

/* --- 任务卡片 --- */
.tasks-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 1.5rem; /* 调整卡片间距 */
  perspective: 1000px;
}

.task-card {
  background: white;
  border-radius: 12px; /* 增加圆角 */
  padding: 1.5rem; /* 调整内边距 */
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05), 0 1px 3px rgba(0, 0, 0, 0.05); /* 柔和阴影 */
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  display: flex;
  flex-direction: column;
  border: 1px solid rgba(0, 0, 0, 0.03);
  animation: cardAppear 0.5s ease backwards;
}

@keyframes cardAppear {
  from {
    opacity: 0;
    transform: translateY(20px) rotateX(5deg);
  }
  to {
    opacity: 1;
    transform: translateY(0) rotateX(0);
  }
}

.task-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.08), 0 2px 4px rgba(0, 0, 0, 0.05); /* 悬浮时阴影加深 */
  border-color: rgba(99, 102, 241, 0.2);
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start; /* 标签顶部对齐 */
  margin-bottom: 1rem;
  border-bottom: 1px solid #f1f3f5; /* 添加分隔线 */
  padding-bottom: 0.75rem;
}

.task-header h3 {
  margin: 0;
  color: #2d3748; /* 卡片标题颜色 */
  font-size: 1.2em; /* 卡片标题大小 */
  font-weight: 600;
  line-height: 1.4;
}

:deep(.el-tag) {
  border-radius: 6px;
  font-weight: 500;
  padding: 0 10px;
  height: 28px;
  line-height: 28px;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
}

.task-info {
  margin-bottom: 1.25rem;
  color: #4a5568; /* 信息文字颜色 */
  font-size: 0.95em; /* 信息文字大小 */
  flex-grow: 1; /* 让信息区域占据多余空间，将按钮推到底部 */
}

.info-item {
  display: flex;
  align-items: center;
  gap: 0.8rem; /* 调整图标和文字间距 */
  margin-bottom: 0.5rem;
  padding: 0.4rem 0;
}

.info-item i {
  color: #6366f1; /* 图标颜色统一为主题色 */
  width: 16px;
  text-align: center;
  flex-shrink: 0;
  font-size: 1.1em;
}

.task-actions {
  display: flex;
  justify-content: flex-end;
  padding-top: 0.75rem;
  border-top: 1px solid #f1f3f5; /* 分隔线 */
  margin-top: auto; 
}

:deep(.el-button-group .el-button--small) {
  padding: 8px 15px;
  border-radius: 6px;
  transition: all 0.2s;
}

:deep(.el-button-group .el-button:first-child) {
  border-top-right-radius: 0;
  border-bottom-right-radius: 0;
}

:deep(.el-button-group .el-button:last-child) {
  border-top-left-radius: 0;
  border-bottom-left-radius: 0;
}

:deep(.el-button.el-button--danger) {
  background-color: #fff;
  color: #dc2626;
  border-color: #fecaca;
}

:deep(.el-button.el-button--danger:hover) {
  background-color: #fee2e2;
  border-color: #fca5a5;
}

:deep(.el-progress .el-progress-bar__inner) {
  transition: width 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}

/* --- 创建任务对话框 --- */
:deep(.transform-dialog) {
  border-radius: 12px;
  overflow: hidden;
}

:deep(.transform-dialog .el-dialog__header) {
  background: linear-gradient(135deg, #3b82f6, #6366f1);
  padding: 20px 24px;
  margin-right: 0;
}

:deep(.transform-dialog .el-dialog__title) {
  color: white;
  font-weight: 600;
  font-size: 1.2em;
}

:deep(.transform-dialog .el-dialog__headerbtn .el-dialog__close) {
  color: rgba(255, 255, 255, 0.8);
}

:deep(.transform-dialog .el-dialog__body) {
  padding: 24px;
}

:deep(.transform-dialog .el-dialog__footer) {
  padding: 16px 24px;
  border-top: 1px solid #e5e7eb;
}

.details-loading,
.details-error {
  color: #6b7280;
  margin-top: 12px;
  padding: 12px;
  border-radius: 8px;
  font-size: 0.95em;
  display: flex;
  align-items: center;
  gap: 8px;
}

.details-loading {
  background-color: #f9fafb;
}

.details-error {
  color: #ef4444;
  background-color: #fee2e2;
}

.details-content {
  margin-top: 12px;
  padding: 16px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background-color: #ffffff;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.03);
}

/* 标签式分布信息 */
.distribution-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 20px;
  padding: 16px;
  background-color: #f9fafb;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

/* 增强标签组样式 */
.tag-group {
  margin-bottom: 16px;
}

.tag-group-title {
  font-size: 0.9em;
  color: #4b5563;
  margin-bottom: 8px;
  font-weight: 600;
  display: flex;
  align-items: center;
}

.tag-group-title::before {
  content: "";
  display: inline-block;
  width: 4px;
  height: 14px;
  background: linear-gradient(to bottom, #3b82f6, #6366f1);
  margin-right: 8px;
  border-radius: 2px;
}

.tag-group-content {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

/* 预览按钮美化 */
.preview-button {
  display: flex;
  justify-content: center;
  margin-top: 16px;
}

.preview-button .el-button {
  width: 180px;
}

/* --- 题库预览窗口 --- */
.preview-window {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background-color: rgba(17, 24, 39, 0.7); /* 加深一点背景 */
  z-index: 3000;
  display: flex;
  justify-content: center;
  align-items: center;
  backdrop-filter: blur(4px);
  transition: all 0.3s ease;
}

.preview-container {
  width: 75%; /* 适当调大 */
  max-width: 900px;
  height: 80vh; /* 适当调大 */
  background: white;
  border-radius: 12px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  animation: dialogFadeIn 0.3s ease;
}

@keyframes dialogFadeIn {
  from { 
    opacity: 0;
    transform: translateY(20px);
  }
  to { 
    opacity: 1;
    transform: translateY(0);
  }
}

.preview-header {
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(135deg, #3b82f6, #6366f1);
  color: white;
}

.preview-header span {
  font-size: 1.2em; /* 调整标题大小 */
  font-weight: 600;
  color: white;
  letter-spacing: 0.5px;
}

.preview-content {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem;
  background-color: #f9fafb;
}

.close-btn {
  background-color: rgba(255, 255, 255, 0.2);
  border: none;
  color: white;
  transition: all 0.2s;
}

.close-btn:hover {
  background-color: rgba(255, 255, 255, 0.3);
  transform: rotate(90deg);
}

.question-item {
  background-color: #ffffff; /* 预览题目背景 */
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  margin-bottom: 1.25rem;
  padding: 1.25rem 1.5rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  transition: transform 0.2s, box-shadow 0.2s;
}

.question-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.question-header {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  margin-bottom: 1rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px dashed #e5e7eb; /* 虚线分隔 */
}

.question-id {
  font-weight: bold;
  color: #3b82f6;
  background-color: #eff6ff;
  padding: 0.25rem 0.5rem;
  border-radius: 6px;
}

.question-content {
  padding: 0 0.5rem;
}

.question-text {
  margin-bottom: 1rem;
  line-height: 1.7; /* 增加行高 */
  color: #1f2937;
  font-size: 1em;
}

.question-choices {
  margin-bottom: 1rem;
  padding: 0.75rem 1rem;
  background-color: #f9fafb;
  border-radius: 8px;
}

.choice-item {
  margin-bottom: 0.5rem;
  color: #4b5563;
  padding: 0.35rem 0.5rem;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.choice-item:hover {
  background-color: #f3f4f6;
}

.question-meta {
  margin-top: 10px;
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.question-meta .el-tag[effect="plain"] {
  background-color: #f5f7fb;
  padding: 4px 10px;
  border-radius: 6px;
  margin-right: 8px;
  transition: all 0.25s ease;
}

.question-meta .el-tag[effect="plain"][type="primary"] {
  color: #3b82f6;
  border: 1px solid #bfdbfe;
}

.question-meta .el-tag[effect="plain"][type="primary"]:hover {
  background-color: #eff6ff;
  transform: translateY(-2px);
}

.question-meta .el-tag[effect="plain"][type="success"] {
  color: #10b981;
  border: 1px solid #a7f3d0;
}

.question-meta .el-tag[effect="plain"][type="success"]:hover {
  background-color: #ecfdf5;
  transform: translateY(-2px);
}

.question-meta .el-tag[effect="plain"][type="info"] {
  color: #6b7280;
  border: 1px solid #d1d5db;
}

.question-meta .el-tag[effect="plain"][type="info"]:hover {
  background-color: #f3f4f6;
  transform: translateY(-2px);
}

.progress-bar {
  margin-top: 1rem;
}

/* --- 结果详情弹窗 (固定浮窗) --- */
.fixed-dialog-overlay {
  position: fixed;
  top: 0; left: 0; width: 100%; height: 100%;
  background-color: rgba(17, 24, 39, 0.7); /* 稍微加深背景 */
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 2000;
  backdrop-filter: blur(4px);
  animation: overlayFadeIn 0.3s ease;
}

@keyframes overlayFadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.result-dialog-container {
  background-color: white;
  border-radius: 16px; /* 增加圆角 */
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
  width: 90%; /* 增加宽度 */
  max-width: 1400px; 
  height: 90vh; /* 增加高度 */
  display: flex;
  flex-direction: column;
  overflow: hidden;
  animation: contentFadeIn 0.35s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes contentFadeIn {
  from { 
    opacity: 0;
    transform: scale(0.98);
  }
  to { 
    opacity: 1;
    transform: scale(1);
  }
}

.result-dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.25rem 1.75rem; /* 调整内边距 */
  background: linear-gradient(135deg, #3b82f6, #6366f1);
  font-weight: 600; /* 加粗标题 */
  font-size: 1.2em; 
  color: white;
  flex-shrink: 0;
}

.result-dialog-content {
  padding: 1.75rem; /* 增加内容区域内边距 */
  overflow-y: auto; 
  flex-grow: 1;
  background-color: #f9fafb; /* 内容区淡灰背景 */
}

/* 概览区域 */
.overview-section {
  margin-bottom: 2rem; /* 调整与下方间距 */
  padding: 1.5rem 1.75rem;
  background: linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%);
  border-radius: 12px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.05);
  border: 1px solid #e5e7eb;
}

.overview-section .el-descriptions__title {
  font-size: 1.2em;
  color: #2d3748;
  margin-bottom: 1rem; /* 调整标题与内容间距 */
  font-weight: 600;
}

:deep(.overview-section .el-descriptions__cell) {
  padding: 12px 16px;
}

:deep(.overview-section .el-descriptions__label) {
   color: #4b5563 !important; /* 统一标签颜色 */
   font-weight: 500 !important;
}

:deep(.overview-section .el-descriptions__content) {
   color: #1f2937 !important; /* 统一内容颜色 */
   font-weight: 600;
}

.overview-score {
  font-weight: bold;
  font-size: 1.25em; /* 调整分数大小 */
  color: #3b82f6; /* 鲜艳的蓝色 */
  background: linear-gradient(90deg, #dbeafe, #eff6ff);
  padding: 0.25rem 0.75rem;
  border-radius: 6px;
  display: inline-block; /* 使背景适应内容 */
  box-shadow: 0 2px 4px rgba(59, 130, 246, 0.15);
}

/* 折叠面板 */
:deep(.el-collapse) {
    border-top: none; /* 移除默认顶部边框 */
    border-bottom: none; /* 移除默认底部边框 */
}

:deep(.el-collapse-item__header) {
  background-color: #f3f4f6; /* 标题背景色 */
  border-radius: 8px; 
  border: 1px solid #e5e7eb;
  margin-bottom: 0.75rem; /* 覆盖边框重叠 */
  transition: all 0.2s ease;
  padding: 0.75rem 1.25rem; /* 调整标题内边距 */
  font-weight: 500;
}

:deep(.el-collapse-item__header:hover) {
  background-color: #e5e7eb;
}

:deep(.el-collapse-item__header.is-active) {
  background: linear-gradient(90deg, #f3f4f6, #e5e7eb); /* 渐变背景 */
  border-bottom-color: transparent; /* 激活时移除底部边框 */
}

:deep(.el-collapse-item__wrap) {
  border-bottom: 1px solid #e5e7eb; 
  background-color: #ffffff; /* 内容区背景 */
  border-radius: 0 0 8px 8px;
  margin-top: -0.75rem;
  margin-bottom: 1.25rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.03);
}

:deep(.el-collapse-item__content) {
  padding: 1.5rem; /* 调整内容内边距 */
}

.original-q-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0;
  padding: 0.75rem 1rem;
  background-color: #f9fafb;
  border-radius: 6px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  width: 100%;
}

.question-title {
  display: flex;
  align-items: center;
  gap: 10px;
  max-width: 75%;
}

.question-id-tag {
  display: inline-block;
  padding: 4px 10px;
  background: linear-gradient(135deg, #3b82f6, #6366f1);
  color: white;
  border-radius: 6px;
  font-weight: 600;
  font-size: 0.9em;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  white-space: nowrap;
}

.question-tags {
  display: flex;
  align-items: center;
  gap: 10px;
}

.question-id-small {
  color: #6b7280;
  font-size: 0.85em;
  font-weight: 500;
  background-color: #f3f4f6;
  padding: 4px 8px;
  border-radius: 4px;
}

.original-q-header span {
  color: #2d3748; /* 调整折叠标题文字颜色 */
  font-weight: 500; /* 调整字重 */
  font-size: 1.05em; /* 调整字体大小 */
  line-height: 1.5;
}

.original-q-header .el-tag {
  margin-left: 0;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  transition: all 0.25s ease;
  font-weight: 500;
  border: none;
  background: linear-gradient(135deg, #3b82f6, #6366f1);
  color: white;
}

.original-q-header .el-tag:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  filter: brightness(1.05);
}

/* 展开内容中的变形版本 */
.detailed-version-item {
  margin-bottom: 1.75rem; /* 增加版本间距 */
  padding: 1.25rem 1.5rem;
  border: 1px solid #e5e7eb; 
  border-radius: 10px;
  background-color: #f9fafb; /* 轻微背景色 */
  transition: all 0.2s ease;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.03);
}

.detailed-version-item:hover {
  background-color: #ffffff;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.08); /* 悬浮增强阴影 */
  transform: translateY(-2px);
}

.detailed-version-item:last-child {
  margin-bottom: 0.75rem; /* 调整最后一个元素的边距 */
}

.detailed-version-item h4 {
  margin-top: 0;
  margin-bottom: 1rem;
  font-size: 1.15em;
  color: #3b82f6;
  border-bottom: 1px dashed #e5e7eb; /* 虚线分隔 */
  padding-bottom: 0.85rem;
  padding-left: 0.5rem;
  position: relative;
}

.detailed-version-item h4::before {
  content: "";
  position: absolute;
  left: 0;
  top: 0.2rem;
  bottom: 0.85rem;
  width: 4px;
  background: linear-gradient(to bottom, #3b82f6, #6366f1);
  border-radius: 2px;
}

.version-content {
  margin-bottom: 1rem;
  padding: 0 0.5rem;
}

.version-content p {
  margin: 0.8rem 0;
  font-size: 1.05em;
  line-height: 1.6;
}

.version-content strong {
  display: inline-block;
  min-width: 65px; /* 调整标签宽度 */
  margin-right: 12px;
  padding: 4px 10px;
  border-radius: 6px;
  background: linear-gradient(135deg, #f0f9ff, #e0f2fe);
  color: #0369a1;
  font-weight: 600; /* 调整标签字重 */
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

/* 为不同类型的标签设置不同背景色 */
.version-content p:nth-child(1) strong {
  background: linear-gradient(135deg, #f0fdf4, #dcfce7);
  color: #16a34a;
}

.version-content p:nth-child(2) strong {
  background: linear-gradient(135deg, #eff6ff, #dbeafe);
  color: #2563eb;
}

.version-content p:nth-child(3) strong {
  background: linear-gradient(135deg, #fef3c7, #fde68a);
  color: #d97706;
}

.version-content p:nth-child(4) strong {
  background: linear-gradient(135deg, #ffedd5, #fed7aa);
  color: #ea580c;
}

/* 展开内容中的评估分数 */
.evaluation-scores-inline {
  margin-top: 1rem;
  padding: 1rem 1.25rem;
  border-top: 1px solid #e5e7eb; 
  background-color: #ffffff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.03);
}

.evaluation-scores-inline h5 {
  margin-top: 0;
  margin-bottom: 0.85rem;
  font-size: 1.1em;
  color: #4b5563; /* 分数标题颜色 */
  font-weight: 600;
  display: inline-block;
  padding: 6px 14px;
  background: linear-gradient(135deg, #f1f5f9, #e2e8f0);
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.score-item-inline {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 1em; /* 调大字体 */
  padding: 0.6rem 0.75rem; /* 调整分数行间距 */
  border-radius: 6px;
  transition: background-color 0.2s;
}

.score-item-inline:hover {
  background-color: #f9fafb;
}

.score-item-inline span:first-child {
  color: #4b5563; /* 分数标签颜色 */
  min-width: 180px; /* 增加标签宽度以对齐 */
  font-weight: 500;
  padding: 4px 10px;
  border-radius: 6px;
  background: linear-gradient(135deg, #f9fafb, #f3f4f6);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.score-item-inline span:last-child {
  font-weight: 600;
  font-size: 1.05em; /* 稍微调大分数 */
  color: #3b82f6; /* 分数值颜色 */
  background-color: #eff6ff; /* 分数值背景 */
  padding: 0.4rem 0.75rem;
  border-radius: 6px;
  min-width: 70px; /* 保证分数区域有一定宽度 */
  text-align: center;
}

.comprehensive-score-inline {
  margin-top: 0.75rem;
  font-size: 0.95em;
  border-top: 1px dashed #e5e7eb; /* 综合分顶部加虚线 */
  padding: 0.75rem 0.75rem;
  background-color: #f3f4f6;
  border-radius: 6px;
}

.comprehensive-score-inline span:last-child {
  color: #3b82f6; /* 综合分使用主题色 */
  font-size: 1.15em; /* 突出综合分 */
  background: linear-gradient(90deg, #dbeafe, #eff6ff);
  box-shadow: 0 2px 4px rgba(59, 130, 246, 0.15);
}

/* 错误显示 */
.error-display {
  color: #ef4444; /* 醒目红色 */
  font-style: italic;
  font-size: 0.95em;
  margin: 0.75rem 0;
  padding: 0.75rem 1rem;
  background-color: #fee2e2; /* 浅红色背景 */
  border: 1px solid #fecaca;
  border-radius: 6px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.error-display::before {
  content: "⚠️";
  font-style: normal;
}

/* 自定义loading样式 */
:deep(.el-loading-mask) {
  background-color: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(2px);
}

:deep(.el-loading-spinner .circular) {
  width: 50px;
  height: 50px;
}

:deep(.el-loading-spinner .path) {
  stroke: #3b82f6;
  stroke-width: 3;
}

/* 美化消息提示 */
:deep(.el-message) {
  min-width: 300px;
  padding: 12px 20px;
  border-radius: 8px;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
  border: none;
}

:deep(.el-message--info) {
  background-color: #eff6ff;
  border-color: #dbeafe;
}

:deep(.el-message--success) {
  background-color: #ecfdf5;
  border-color: #d1fae5;
}

:deep(.el-message--warning) {
  background-color: #fffbeb;
  border-color: #fef3c7;
}

:deep(.el-message--error) {
  background-color: #fee2e2;
  border-color: #fecaca;
}

:deep(.el-message__content) {
  color: #1f2937;
  font-size: 0.95em;
  font-weight: 500;
}

:deep(.el-message__icon) {
  margin-right: 10px;
  font-size: 1.1em;
}

/* 优化对话框背景动画 */
:deep(.el-overlay) {
  backdrop-filter: blur(4px);
  transition: backdrop-filter 0.3s ease, background-color 0.3s ease;
}

/* 滚动条美化 */
.result-dialog-content,
.preview-content {
  scrollbar-width: thin;
  scrollbar-color: #cbd5e1 #f1f5f9;
}

.result-dialog-content::-webkit-scrollbar,
.preview-content::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

.result-dialog-content::-webkit-scrollbar-track,
.preview-content::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 4px;
}

.result-dialog-content::-webkit-scrollbar-thumb,
.preview-content::-webkit-scrollbar-thumb {
  background-color: #cbd5e1;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.result-dialog-content::-webkit-scrollbar-thumb:hover,
.preview-content::-webkit-scrollbar-thumb:hover {
  background-color: #94a3b8;
}

/* 任务卡片中的状态样式 */
:deep(.task-card .el-tag--info) {
  background-color: #f3f4f6;
  border-color: #e5e7eb;
  color: #6b7280;
}

:deep(.task-card .el-tag--warning) {
  background-color: #fffbeb;
  border-color: #fef3c7;
  color: #d97706;
}

:deep(.task-card .el-tag--primary) {
  background-color: #eff6ff;
  border-color: #dbeafe;
  color: #3b82f6;
}

:deep(.task-card .el-tag--success) {
  background-color: #ecfdf5;
  border-color: #d1fae5;
  color: #10b981;
}

:deep(.task-card .el-tag--danger) {
  background-color: #fee2e2;
  border-color: #fecaca;
  color: #ef4444;
}

/* 为任务卡片添加加载中的动画效果 */
@keyframes pulse {
  0% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
  100% {
    opacity: 1;
  }
}

.task-card:has(.el-tag--warning), 
.task-card:has(.el-tag--primary) {
  animation: pulse 2s ease infinite;
  border-left: 3px solid #3b82f6;
}

/* 进度条加载动画 */
:deep(.el-progress-bar__inner) {
  transition: width 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
  background-image: linear-gradient(
    45deg,
    rgba(255, 255, 255, 0.15) 25%,
    transparent 25%,
    transparent 50%,
    rgba(255, 255, 255, 0.15) 50%,
    rgba(255, 255, 255, 0.15) 75%,
    transparent 75%,
    transparent
  );
  background-size: 1rem 1rem;
  animation: progress-bar-stripes 1s linear infinite;
}

@keyframes progress-bar-stripes {
  from {
    background-position: 1rem 0;
  }
  to {
    background-position: 0 0;
  }
}

/* 空状态美化 */
:deep(.el-empty) {
  padding: 40px 0;
}

:deep(.el-empty__image) {
  width: 120px;
  height: 120px;
}

:deep(.el-empty__description) {
  color: #6b7280;
  font-size: 1em;
}

/* 添加列表为空的状态显示 */
.tasks-grid:empty::after {
  content: "暂无任务";
  display: grid;
  place-items: center;
  height: 200px;
  background-color: #f9fafb;
  border-radius: 12px;
  color: #6b7280;
  font-size: 1.1em;
  grid-column: 1 / -1;
  border: 2px dashed #e5e7eb;
}

/* 创建任务表单样式增强 */
:deep(.transform-dialog .el-form-item__label) {
  font-weight: 500;
  color: #4b5563;
  font-size: 0.95em;
  padding-bottom: 8px;
}

:deep(.el-form-item) {
  margin-bottom: 20px;
}

:deep(.el-select) {
  width: 100%;
}

/* 美化下拉选项 */
:deep(.el-select__tags) {
  background-color: transparent;
}

:deep(.el-select-dropdown__item) {
  padding: 10px 16px;
  font-size: 0.95em;
}

:deep(.el-select-dropdown__item.selected) {
  color: #3b82f6;
  font-weight: 600;
  background-color: #eff6ff;
}

:deep(.el-select-dropdown__item.hover) {
  background-color: #f3f4f6;
}

/* 表格和描述组件样式增强 */
:deep(.el-descriptions) {
  --el-descriptions-table-border: 1px solid #e5e7eb;
}

:deep(.el-descriptions--bordered .el-descriptions__cell) {
  padding: 12px 16px;
}

:deep(.el-descriptions__title) {
  font-size: 1.15em;
  margin-bottom: 16px;
  color: #374151;
  font-weight: 600;
}

/* 改进折叠面板样式 */
:deep(.el-collapse-item__arrow) {
  transition: transform 0.3s ease;
  margin-right: 5px;
  font-weight: bold;
  color: #6366f1;
}

:deep(.el-collapse-item__header.is-active .el-collapse-item__arrow) {
  transform: rotate(90deg);
}

/* 弹窗按钮样式优化 */
:deep(.dialog-footer) {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

:deep(.el-message-box__btns) {
  display: flex;
  gap: 10px;
}

:deep(.el-message-box__btns button) {
  margin-left: 0;
}

/* 确认删除的危险按钮样式 */
:deep(.el-button--danger.is-plain) {
  color: #ef4444;
  border-color: #fecaca;
  background-color: #fff;
}

:deep(.el-button--danger.is-plain:hover) {
  background-color: #fee2e2;
  border-color: #ef4444;
  color: #b91c1c;
}

/* 创建任务对话框中的标签美化 */
:deep(.transform-dialog .el-tag) {
  border-radius: 6px;
  padding: 2px 10px;
  height: auto;
  min-height: 24px;
  line-height: 1.4;
  font-weight: 500;
  margin: 0 4px 4px 0;
  transition: all 0.25s ease;
  border: none;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

:deep(.transform-dialog .el-tag:hover) {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  filter: brightness(1.05);
}

/* 题型标签样式 */
:deep(.transform-dialog .el-tag--primary) {
  background: linear-gradient(135deg, #3b82f6, #6366f1);
  color: white;
}

:deep(.transform-dialog .el-tag--success) {
  background: linear-gradient(135deg, #10b981, #059669);
  color: white;
}

:deep(.transform-dialog .el-tag--warning) {
  background: linear-gradient(135deg, #f59e0b, #d97706);
  color: white;
}

:deep(.transform-dialog .el-tag--danger) {
  background: linear-gradient(135deg, #ef4444, #dc2626);
  color: white;
}

:deep(.transform-dialog .el-tag--info) {
  background: linear-gradient(135deg, #6b7280, #4b5563);
  color: white;
}

/* 创建任务中的标签容器样式 */
.metadata-display-container {
  margin-top: 8px;
  padding: 16px;
  background-color: #f9fafb;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.03);
}

/* 标签组样式 */
.tag-group {
  margin-bottom: 12px;
}

.tag-group-title {
  font-size: 0.9em;
  color: #4b5563;
  margin-bottom: 6px;
  font-weight: 600;
}

.tag-group-content {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

/* 类型与难度分布标签组 */
.distribution-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
  margin-top: 12px;
}

/* 分布标签效果 */
:deep(.difficulty-tag),
:deep(.type-tag) {
  position: relative;
  padding-right: 36px !important;
  overflow: visible;
  color: white;
}

:deep(.difficulty-tag)::after,
:deep(.type-tag)::after {
  content: attr(data-count);
  position: absolute;
  right: 0;
  top: 0;
  bottom: 0;
  background-color: rgba(255, 255, 255, 0.25);
  width: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.9em;
  border-top-right-radius: 6px;
  border-bottom-right-radius: 6px;
  font-weight: 500;
}

/* 难度标签特殊样式 */
:deep(.difficulty-tag.el-tag--success) {
  background: linear-gradient(135deg, #10b981, #059669);
}

:deep(.difficulty-tag.el-tag--warning) {
  background: linear-gradient(135deg, #f59e0b, #d97706);
}

:deep(.difficulty-tag.el-tag--danger) {
  background: linear-gradient(135deg, #ef4444, #dc2626);
}

/* 题型标签特殊样式 */
:deep(.type-tag.el-tag--primary) {
  background: linear-gradient(135deg, #3b82f6, #6366f1);
}

:deep(.type-tag.el-tag--success) {
  background: linear-gradient(135deg, #10b981, #059669);
}

:deep(.type-tag.el-tag--warning) {
  background: linear-gradient(135deg, #f59e0b, #d97706);
}

:deep(.type-tag.el-tag--danger) {
  background: linear-gradient(135deg, #ef4444, #dc2626);
}

:deep(.type-tag.el-tag--info) {
  background: linear-gradient(135deg, #6b7280, #4b5563);
}

/* 题库预览窗口中的标签样式 */
.question-header .el-tag {
  margin-left: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  transition: all 0.25s ease;
  font-weight: 500;
  border: none;
}

.question-header .el-tag:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  filter: brightness(1.05);
}

/* 题型标签 */
.question-header .el-tag[type="primary"] {
  background: linear-gradient(135deg, #3b82f6, #6366f1);
  color: white;
}

.question-header .el-tag[type="success"] {
  background: linear-gradient(135deg, #10b981, #059669);
  color: white;
}

.question-header .el-tag[type="warning"] {
  background: linear-gradient(135deg, #f59e0b, #d97706);
  color: white;
}

.question-header .el-tag[type="danger"] {
  background: linear-gradient(135deg, #ef4444, #dc2626);
  color: white;
}

.question-header .el-tag[type="info"] {
  background: linear-gradient(135deg, #6b7280, #4b5563);
  color: white;
}

/* 元数据标签样式 */
.question-meta .el-tag {
  margin-right: 6px;
  margin-bottom: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  border-radius: 6px;
  padding: 4px 8px;
  height: auto;
  transition: all 0.25s ease;
  font-weight: 500;
}

.question-meta .el-tag:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.question-meta .el-tag[effect="plain"] {
  background-color: #f5f7fb;
  padding: 4px 10px;
  border-radius: 6px;
  margin-right: 8px;
  transition: all 0.25s ease;
}

.question-meta .el-tag[effect="plain"][type="primary"] {
  color: #3b82f6;
  border: 1px solid #bfdbfe;
}

.question-meta .el-tag[effect="plain"][type="primary"]:hover {
  background-color: #eff6ff;
  transform: translateY(-2px);
}

.question-meta .el-tag[effect="plain"][type="success"] {
  color: #10b981;
  border: 1px solid #a7f3d0;
}

.question-meta .el-tag[effect="plain"][type="success"]:hover {
  background-color: #ecfdf5;
  transform: translateY(-2px);
}

.question-meta .el-tag[effect="plain"][type="info"] {
  color: #6b7280;
  border: 1px solid #d1d5db;
}

.question-meta .el-tag[effect="plain"][type="info"]:hover {
  background-color: #f3f4f6;
  transform: translateY(-2px);
}

/* 修复题库预览中的标签颜色 */
.question-meta .el-tag {
  border-radius: 6px;
  padding: 4px 8px;
  height: auto;
  line-height: 1.4;
  font-weight: 500;
  margin: 0 6px 4px 0;
  transition: all 0.25s ease;
}

.question-meta .el-tag:hover {
  transform: translateY(-2px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

/* 确保题目领域和测试指标标签显示更鲜明的颜色 */
.question-meta .el-tag[type="primary"]:not([effect="plain"]) {
  background: linear-gradient(135deg, #3b82f6, #6366f1);
  color: white;
  border: none;
}

.question-meta .el-tag[type="success"]:not([effect="plain"]) {
  background: linear-gradient(135deg, #10b981, #059669);
  color: white;
  border: none;
}

/* 版本内容值样式 */
.version-value {
  font-size: 1.02em;
  line-height: 1.6;
  display: inline-block;
  padding: 2px 0;
  border-radius: 4px;
  font-weight: 500;
}

/* 折叠标题美化 */
.original-q-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding: 0.75rem 1rem;
  background-color: #f9fafb;
  border-radius: 6px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.original-q-header span {
  color: #2d3748; /* 调整折叠标题文字颜色 */
  font-weight: 500; /* 调整字重 */
  font-size: 1.05em; /* 调整字体大小 */
  line-height: 1.5;
}

.original-q-header .el-tag {
  margin-left: 10px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  transition: all 0.25s ease;
  font-weight: 500;
  border: none;
}

.original-q-header .el-tag:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  filter: brightness(1.05);
}

/* 选项部分样式 */
.options-section {
  margin-top: 10px;
  padding-left: 20px;
}

.option-item {
  margin-bottom: 5px;
}

.option-key {
  font-weight: bold;
}

.option-text {
  margin-left: 10px;
}
</style> 
<template>
  <div class="question-transform">
    <div class="header">
      <h1>题库变形</h1>
      <div class="header-actions">
        <el-button type="primary" @click="showTransformDialog">
          <i class="fas fa-magic"></i> 创建变形任务
        </el-button>
        <div class="search-box">
          <input 
            type="text" 
            v-model="searchQuery" 
            placeholder="搜索变形任务..."
            @input="filterTasks"
          >
          <i class="fas fa-search"></i>
        </div>
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
            <i class="fas fa-calendar"></i>
            <span>创建时间：{{ formatDate(task.created_at) }}</span>
          </div>
          <div class="info-item">
            <i class="fas fa-question-circle"></i>
            <span>题目数量：{{ task.question_count }}</span>
          </div>
          <div class="info-item">
            <i class="fas fa-clock"></i>
            <span>完成时间：{{ task.completed_at ? formatDate(task.completed_at) : '进行中' }}</span>
          </div>
        </div>
        <div class="task-actions">
          <el-button-group>
            <el-button size="small" @click="viewTask(task)">
              <i class="fas fa-eye"></i> 查看详情
            </el-button>
            <el-button 
              size="small" 
              type="success" 
              :disabled="task.status !== 'completed'"
              @click="exportResults(task)"
            >
              <i class="fas fa-download"></i> 导出结果
            </el-button>
            <el-button 
              size="small" 
              type="danger" 
              :disabled="task.status === 'running'"
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
    >
      <el-form :model="taskForm" label-width="120px">
        <el-form-item label="任务名称">
          <el-input v-model="taskForm.name" placeholder="请输入任务名称" />
        </el-form-item>
        <el-form-item label="选择题目">
          <el-select
            v-model="taskForm.questionIds"
            multiple
            filterable
            placeholder="请选择要变形的题目"
            style="width: 100%"
          >
            <el-option
              v-for="question in questions"
              :key="question.id"
              :label="question.title"
              :value="question.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="变形类型">
          <el-select v-model="taskForm.transformType" placeholder="请选择变形类型">
            <el-option label="同义词替换" value="synonym" />
            <el-option label="句式转换" value="sentence" />
            <el-option label="上下文扩展" value="context" />
            <el-option label="难度调整" value="difficulty" />
          </el-select>
        </el-form-item>
        <el-form-item label="变形参数">
          <el-input-number 
            v-model="taskForm.parameters.count" 
            :min="1" 
            :max="10"
            label="每个题目变形数量"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitTask">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'

export default {
  name: 'QuestionTransform',
  setup() {
    const tasks = ref([])
    const questions = ref([])
    const searchQuery = ref('')
    const dialogVisible = ref(false)
    const taskForm = ref({
      name: '',
      questionIds: [],
      transformType: '',
      parameters: {
        count: 1
      }
    })

    const filteredTasks = computed(() => {
      if (!searchQuery.value) return tasks.value
      const query = searchQuery.value.toLowerCase()
      return tasks.value.filter(task => 
        task.name.toLowerCase().includes(query)
      )
    })

    const showTransformDialog = () => {
      taskForm.value = {
        name: '',
        questionIds: [],
        transformType: '',
        parameters: {
          count: 1
        }
      }
      dialogVisible.value = true
    }

    const viewTask = (task) => {
      // TODO: 实现查看任务详情
    }

    const exportResults = async (task) => {
      try {
        // TODO: 实现导出结果
        ElMessage.success('导出成功')
      } catch (error) {
        console.error('导出失败:', error)
      }
    }

    const deleteTask = async (task) => {
      try {
        await ElMessageBox.confirm('确定要删除这个变形任务吗？', '警告', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
        // TODO: 调用删除API
        ElMessage.success('删除成功')
      } catch (error) {
        console.error('删除失败:', error)
      }
    }

    const submitTask = async () => {
      try {
        // TODO: 调用创建任务API
        ElMessage.success('创建成功')
        dialogVisible.value = false
      } catch (error) {
        console.error('创建失败:', error)
      }
    }

    const getTaskStatusTag = (status) => {
      const statusMap = {
        pending: 'info',
        running: 'warning',
        completed: 'success',
        failed: 'danger'
      }
      return statusMap[status] || 'info'
    }

    const getTaskStatusText = (status) => {
      const statusMap = {
        pending: '等待中',
        running: '进行中',
        completed: '已完成',
        failed: '失败'
      }
      return statusMap[status] || status
    }

    const formatDate = (date) => {
      return new Date(date).toLocaleString()
    }

    return {
      tasks,
      questions,
      searchQuery,
      filteredTasks,
      dialogVisible,
      taskForm,
      showTransformDialog,
      viewTask,
      exportResults,
      deleteTask,
      submitTask,
      getTaskStatusTag,
      getTaskStatusText,
      formatDate
    }
  }
}
</script>

<style scoped>
.question-transform {
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

.tasks-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 1.5rem;
}

.task-card {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.task-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 12px rgba(0, 0, 0, 0.1);
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
}

.task-header h3 {
  margin: 0;
  color: #2d3748;
  font-size: 1.25rem;
}

.task-info {
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

.task-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
}
</style> 
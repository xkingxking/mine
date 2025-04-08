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
          <div v-if="isJsonContent" class="json-content">
            <template v-for="(value, key) in content" :key="key">
              <div class="section">
                <h3 class="section-title">{{ key }}</h3>
                <div v-if="key === '详细结果'" class="detailed-results">
                  <div v-for="(result, index) in value" :key="index" class="result-item">
                    <h4>问题 {{ result['问题ID'] }}</h4>
                    <div class="result-content">
                      <div class="result-field">
                        <span class="field-label">问题类型：</span>
                        <span class="field-value">{{ result['问题类型'] }}</span>
                      </div>
                      <div class="result-field">
                        <span class="field-label">领域：</span>
                        <span class="field-value">{{ result['领域'] }}</span>
                      </div>
                      <div class="result-field model-output">
                        <span class="field-label">模型输出：</span>
                        <pre class="field-value">{{ result['模型输出'] }}</pre>
                      </div>
                      <div class="result-field">
                        <span class="field-label">评估结果：</span>
                        <div class="evaluation-results">
                          <div class="eval-section">
                            <h5>安全性</h5>
                            <div>安全分数：{{ result['评估结果']['安全性']['安全分数'] }}</div>
                            <div>是否安全：{{ result['评估结果']['安全性']['是否安全'] }}</div>
                            <div>毒性等级：{{ result['评估结果']['安全性']['毒性等级'] }}</div>
                          </div>
                          <div class="eval-section">
                            <h5>准确性</h5>
                            <div>准确率分数：{{ result['评估结果']['准确性']['准确率分数'] }}</div>
                            <div>相似度等级：{{ result['评估结果']['准确性']['相似度等级'] }}</div>
                          </div>
                          <div class="eval-section">
                            <h5>总分</h5>
                            <div>{{ result['评估结果']['总分'] }}</div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                <div v-else class="key-value-pairs">
                  <div v-for="(subValue, subKey) in value" :key="subKey" class="field">
                    <span class="field-label">{{ subKey }}：</span>
                    <span class="field-value">{{ subValue }}</span>
                  </div>
                </div>
              </div>
            </template>
          </div>
          <pre v-else class="text-content">{{ content }}</pre>
        </div>
        <div v-else class="loading">
          <i class="fas fa-spinner fa-spin"></i>
          <span>加载中...</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue';

export default {
  name: 'ReportDialog',
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
      type: [Object, String],
      default: null
    }
  },
  emits: ['close'],
  setup(props, { emit }) {
    const isJsonContent = computed(() => {
      return typeof props.content === 'object' && props.content !== null;
    });

    const onClose = () => {
      emit('close');
    };

    return {
      onClose,
      isJsonContent
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
  max-height: calc(90vh - 4rem);
}

.content-wrapper {
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.section {
  padding: 1.5rem;
  border-bottom: 1px solid #e2e8f0;
}

.section:last-child {
  border-bottom: none;
}

.section-title {
  margin: 0 0 1rem;
  color: #2d3748;
  font-size: 1.25rem;
  font-weight: 600;
}

.key-value-pairs {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
}

.field {
  padding: 0.5rem;
  background: white;
  border-radius: 6px;
  border: 1px solid #e2e8f0;
}

.field-label {
  color: #4a5568;
  font-weight: 500;
}

.field-value {
  color: #2d3748;
}

.detailed-results .result-item {
  margin-bottom: 2rem;
  padding: 1rem;
  background: white;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.result-item h4 {
  margin: 0 0 1rem;
  color: #2d3748;
  font-size: 1.1rem;
  font-weight: 600;
}

.result-field {
  margin-bottom: 1rem;
}

.model-output pre {
  margin: 0.5rem 0;
  padding: 1rem;
  background: #f1f5f9;
  border-radius: 6px;
  font-size: 0.875rem;
  line-height: 1.6;
  white-space: pre-wrap;
}

.evaluation-results {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-top: 0.5rem;
}

.eval-section {
  padding: 1rem;
  background: #f1f5f9;
  border-radius: 6px;
}

.eval-section h5 {
  margin: 0 0 0.5rem;
  color: #4a5568;
  font-size: 0.875rem;
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

@media (max-width: 640px) {
  .report-dialog-content {
    width: 95%;
    max-height: 95vh;
  }

  .dialog-header h2 {
    font-size: 1.25rem;
  }

  .key-value-pairs {
    grid-template-columns: 1fr;
  }

  .evaluation-results {
    grid-template-columns: 1fr;
  }
}
</style> 
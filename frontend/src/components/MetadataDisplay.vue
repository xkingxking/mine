<template>
  <div class="metadata-level" :style="{ marginLeft: level * 18 + 'px' }">
    <template v-for="(value, key, index) in metadata" :key="key">
      <hr v-if="level === 0 && index > 0" class="top-level-divider" />
      
      <div class="metadata-item">
        <strong class="metadata-key">{{ formatKey(key) }}:</strong>

        <!-- Simple Value -->
        <span v-if="isSimpleValue(value)" class="metadata-value simple">
          {{ value }}
        </span>

        <!-- Array -->
        <div v-else-if="isArray(value)" class="metadata-value array">
          <el-tag 
            v-for="(item, idx) in value" 
            :key="idx" 
            size="small" 
            :type="getTagType(item, idx)" 
            effect="light" 
            class="array-item"
          >
            {{ item }}
          </el-tag>
        </div>

        <!-- Object (render as tags if suitable, else recurse) -->
        <div v-else-if="isObject(value)">
          <div v-if="isTagLikeObject(value)" class="metadata-value tags">
            <el-tag 
              v-for="(tagValue, tagName) in value" 
              :key="tagName" 
              size="small" 
              :type="getTagTypeForNamedTag(tagName)" 
              effect="dark" 
              class="tag-item"
            >
              {{ formatKey(tagName) }}: {{ tagValue }}
            </el-tag>
          </div>
          <!-- Recursive call -->
          <MetadataDisplay v-else :metadata="value" :level="level + 1" class="nested-object"/>
        </div>

      </div>
    </template>
  </div>
</template>

<script setup>
import { defineProps } from 'vue';
import { ElTag } from 'element-plus'; // Import ElTag if used directly in template

// Define props using defineProps with <script setup>
const props = defineProps({
  metadata: {
    type: Object,
    required: true
  },
  level: { // For indentation
    type: Number,
    default: 0
  }
});

// Helper functions
const formatKey = (key) => {
    // Simple conversion: split camelCase and capitalize, handle snake_case
    const words = key.replace(/([A-Z])/g, ' $1').split(/[_ ]+/);
    // Capitalize first letter of each word
    return words.map(word => word ? word.charAt(0).toUpperCase() + word.slice(1).toLowerCase() : '').join(' ').trim();
};

const isObject = (value) => typeof value === 'object' && value !== null && !Array.isArray(value);
const isArray = (value) => Array.isArray(value);
const isSimpleValue = (value) => !isObject(value) && !isArray(value);

const isTagLikeObject = (obj) => {
    // Heuristic: Check if all values are numbers or strings (suitable for tag display)
    return isObject(obj) && Object.values(obj).every(v => typeof v === 'number' || typeof v === 'string');
};

// Helper to get tag type for array items (cycles through types)
const getTagType = (item, index) => {
    const itemStr = String(item).toLowerCase();
    
    // 检查是否为类型标签
    if (itemStr === 'choice' || itemStr.includes('choice')) return 'primary';
    if (itemStr === 'short_answer' || itemStr.includes('short') || itemStr.includes('short answer')) return 'success';
    if (itemStr === 'true_false' || itemStr.includes('true') || itemStr.includes('false')) return 'warning';
    if (itemStr === 'translation' || itemStr.includes('translation')) return 'info';
    if (itemStr === 'code' || itemStr.includes('code')) return 'danger';
    if (itemStr === 'scenario' || itemStr.includes('scenario')) return 'info';
    
    // 检查是否为难度标签
    if (itemStr.includes('简单') || itemStr.includes('easy')) return 'success';
    if (itemStr.includes('中等') || itemStr.includes('medium')) return 'warning';
    if (itemStr.includes('困难') || itemStr.includes('hard')) return 'danger';
    
    // 使用循环颜色
    const types = ['info', 'success', 'warning', 'danger', 'primary'];
    return types[index % types.length];
};

// Helper to get specific tag types based on key name (e.g., for difficulty)
const getTagTypeForNamedTag = (tagName) => {
    const lowerTagName = String(tagName).toLowerCase();
    
    // 难度相关
    if (lowerTagName.includes('easy') || lowerTagName.includes('简单')) return 'success';
    if (lowerTagName.includes('medium') || lowerTagName.includes('中等')) return 'warning';
    if (lowerTagName.includes('hard') || lowerTagName.includes('困难')) return 'danger';
    
    // 题型相关
    if (lowerTagName.includes('choice')) return 'primary';
    if (lowerTagName.includes('short') || lowerTagName.includes('answer')) return 'success';
    if (lowerTagName.includes('true') || lowerTagName.includes('false')) return 'warning';
    if (lowerTagName.includes('translation')) return 'info';
    if (lowerTagName.includes('code')) return 'danger';
    if (lowerTagName.includes('scenario')) return 'info';
    
    // 能力维度相关
    if (lowerTagName.includes('能力') || lowerTagName.includes('ability')) return 'primary';
    if (lowerTagName.includes('知识') || lowerTagName.includes('knowledge')) return 'info';
    if (lowerTagName.includes('理解') || lowerTagName.includes('understand')) return 'success';
    if (lowerTagName.includes('分析') || lowerTagName.includes('analysis')) return 'warning';
    
    return 'info';
};

// No need to return anything in <script setup>
</script>

<style scoped>
/* Styles specific to MetadataDisplay */
.metadata-level {
  /* Indentation handled by inline style */
}

.top-level-divider {
  border: none;
  border-top: 1px solid #e5e7eb; /* 更新分隔线颜色 */
  margin: 16px 0; /* 增加分隔线间距 */
}

.metadata-item {
  margin-bottom: 14px; /* 增加项目间距 */
}

.metadata-key {
  color: #4b5563; /* 更新键颜色 */
  margin-right: 8px;
  display: block; 
  margin-bottom: 6px; 
  font-weight: 600; 
  font-size: 0.85em; /* 稍微缩小键字体 */
  letter-spacing: 0.5px;
  text-transform: uppercase;
  background: linear-gradient(90deg, #f3f4f6, #ffffff); /* 添加渐变背景 */
  padding: 4px 8px;
  border-radius: 4px;
}

.metadata-value {
  color: #1f2937; /* 更新值颜色 */
  word-break: break-all; 
  display: block; 
  font-size: 1em; 
  line-height: 1.6; /* 增加行高 */
}

.metadata-value.simple {
  padding: 6px 10px; /* 增加内边距 */
  background-color: #f9fafb; /* 添加背景色 */
  border-radius: 6px;
  border: 1px solid #e5e7eb;
  font-weight: 500;
}

.metadata-value.array,
.metadata-value.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px; /* 增加标签间距 */
  margin-top: 6px;
  padding: 10px 12px; /* 增加内边距 */
  background-color: #f9fafb; /* 添加背景色 */
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

/* 标签样式增强 */
:deep(.array-item),
:deep(.tag-item) {
  border-radius: 6px;
  padding: 6px 12px;
  height: auto;
  min-height: 28px;
  line-height: 1.4;
  font-weight: 500;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  transition: all 0.25s ease;
  margin: 2px;
  border: none;
}

:deep(.array-item:hover),
:deep(.tag-item:hover) {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  filter: brightness(1.05);
}

/* 类型标签样式定制 */
:deep(.el-tag--primary) {
  background: linear-gradient(135deg, #3b82f6, #6366f1);
  color: white;
}

:deep(.el-tag--success) {
  background: linear-gradient(135deg, #10b981, #059669);
  color: white;
}

:deep(.el-tag--warning) {
  background: linear-gradient(135deg, #f59e0b, #d97706);
  color: white;
}

:deep(.el-tag--danger) {
  background: linear-gradient(135deg, #ef4444, #dc2626);
  color: white;
}

:deep(.el-tag--info) {
  background: linear-gradient(135deg, #6b7280, #4b5563);
  color: white;
}

/* 为标签添加计数样式 */
:deep(.array-item)::after,
:deep(.tag-item)::after {
  content: attr(data-count);
  background-color: rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  padding: 0 4px;
  margin-left: 6px;
  font-size: 0.75em;
  display: none;
}

:deep(.array-item)[data-count],
:deep(.tag-item)[data-count] {
  padding-right: 8px;
}

:deep(.array-item)[data-count]::after,
:deep(.tag-item)[data-count]::after {
  display: inline-block;
}

.nested-object {
  margin-top: 10px; 
  border-left: 2px solid #3b82f6; /* 使用主题蓝色边框 */
  padding-left: 16px; 
  padding-top: 6px;
  padding-bottom: 6px;
  background: linear-gradient(90deg, rgba(59, 130, 246, 0.05), transparent); /* 添加渐变背景 */
  border-top-right-radius: 6px;
  border-bottom-right-radius: 6px;
}
</style> 
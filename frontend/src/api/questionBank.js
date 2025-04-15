import axios from 'axios';

const API_BASE_URL = '/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 3000000, // 从10秒增加到3000秒（50分钟）
  headers: {
    'Content-Type': 'application/json'
  }
});
// 统一数据格式化 - 基础题库
const formatBaseBankData = (bank) => ({
  ...bank,
  dimensions: Array.isArray(bank.dimensions) ? bank.dimensions.join(', ') : bank.dimensions,
  created_at: bank.created_at ? new Date(bank.created_at).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  }) : '未知日期'
});

// 统一数据格式化 - 变形题库
const formatTransformedBankData = (bank) => {
  // 从变形题库文件中提取所有变形方法
  const transformMethods = new Set();
  if (bank.questions && Array.isArray(bank.questions)) {
    bank.questions.forEach(question => {
      if (question.transformed_versions) {
        question.transformed_versions.forEach(version => {
          if (version.transform_method) {
            transformMethods.add(version.transform_method);
          }
        });
      }
    });
  }
  
  // 提取变形题库的原始源题库文件名
  const sourceFileName = bank.source_file?.replace('.json', '') || 'unknown';
  
  // 计算总题目数量，包括所有变形版本
  let totalQuestions = 0;
  if (bank.metadata?.total_transformed_versions) {
    // 使用元数据中的总变形版本数
    totalQuestions = bank.metadata.total_transformed_versions;
  } else if (bank.questions && Array.isArray(bank.questions)) {
    // 手动计算所有变形版本的数量
    bank.questions.forEach(question => {
      if (question.transformed_versions) {
        totalQuestions += question.transformed_versions.length;
      }
    });
  }
  
  return {
    ...bank,
    id: bank.id || sourceFileName,
    name: bank.taskName ? `变形题库-${bank.taskName}` : (bank.name || `变形题库-${sourceFileName}`),
    dimensions: '变形题库',
    transform_methods: Array.from(transformMethods),
    total: totalQuestions, // 使用计算后的总题目数
    created_at: bank.transformed_at || bank.created_at || '未知日期',
    // 添加额外信息以适应原先需要显示这些信息的UI组件
    total_transformed_versions: bank.metadata?.total_transformed_versions || 0
  };
};

export const fetchQuestionBanks = async () => {
  try {
    const response = await api.get('/question-banks');
    return {
      baseBanks: response.data.baseBanks.map(formatBaseBankData),
      transformedBanks: response.data.transformedBanks.map(formatTransformedBankData),
      lastUpdated: response.data.lastUpdated
    };
  } catch (error) {
    console.error('Error fetching question banks:', error);
    return { 
      baseBanks: [], 
      transformedBanks: [],
      lastUpdated: new Date().toISOString()
    };
  }
};
// 统一格式化题目数据
const formatQuestion = (question) => {
  if (question.transform_method) {
    // 变形题库题目
    return {
      ...question,
      '题目领域': '变形题库',
      '测试指标': question.transform_method,
      '难度级别': question.difficulty
    };
  }
  return question;
};

// 获取指定题库的前N道题目
export const fetchBankQuestions = async (bankId, limit = 5) => {
  try {
    const response = await api.get(`/question-banks/${bankId}/questions`);
    const questions = response.data.questions.map(formatQuestion);
    
    // 判断是否是变形题库
    const isTransformed = bankId.includes('transformed_');
    
    if (isTransformed) {
      // 对于变形题库，我们返回全部题目，但如果有limit限制则截取
      return limit === 'all' ? questions : questions.slice(0, limit);
    } else {
      // 对于原始题库，保持原有逻辑
      return limit === 'all' ? questions : questions.slice(0, limit);
    }
  } catch (error) {
    console.error('Error fetching bank questions:', error);
    return [];
  }
};

// 添加获取所有题目的函数（用于测试任务创建）
export const fetchAllBankQuestions = async (bankId) => {
  try {
    const response = await api.get(`/question-banks/${bankId}/questions?limit=all`);
    return response.data.questions.map(formatQuestion);
  } catch (error) {
    console.error('Error fetching all bank questions:', error);
    return [];
  }
};

//难度分布
export const generateQuestionBank = async (params) => {
  try {
    // 添加难度级别映射
    const difficultyMap = {
      'easy': '简单',
      'medium': '中等',
      'hard': '困难'
    };

    const response = await api.post('/generate-question-bank', {
      dimensions: params.dimensions,
      difficulties: params.difficulties,
      difficultyDistribution: params.distribution,
      count: params.count,
      name: params.name,
      easyPercent: params.easyPercent,
      mediumPercent: params.mediumPercent,
      hardPercent: params.hardPercent
    });
    
    // 添加延迟确保数据更新
    await new Promise(resolve => setTimeout(resolve, 1500));
    return response.data;
    
  } catch (error) {
    console.error('生成失败:', error);
    return {
      success: false,
      error: error.response?.data?.error || 
        `生成失败: ${error.message}`
    };
  }
};
<template>
  <div class="view-main-container">

    <!-- 主内容区域 -->
    <div class="content-container">
      <div class="home-container">
        <!-- 顶部动态展示区 -->
        <section class="hero-section">
          <el-carousel 
            height="600px" 
            :interval="5000" 
            arrow="always"
            indicator-position="none"
            motion-blur
          >
            <el-carousel-item v-for="(item, index) in carouselItems" :key="index">
              <div class="carousel-content" :style="{ backgroundImage: `url(${item.bg})` }">
                <div class="content-wrapper">
                  <h2 class="animate__animated animate__fadeInDown">{{ item.title }}</h2>
                  <p class="animate__animated animate__fadeInUp">{{ item.desc }}</p>
                </div>
              </div>
            </el-carousel-item>
          </el-carousel>
        </section>

        <!-- 向下滑动提示 -->
        <div class="scroll-down">
          <p>向下滑动查看更多信息</p>
          <i class="fas fa-chevron-down"></i>
        </div>

        <!-- 新增的文字展示区域 -->
        <section class="message-section">
          <p class="message" ref="messageRef">{{ displayText }}</p>
        </section>

        <!-- 模型测试模块 -->
        <section class="modules-section">
          <h2 class="cyberpunk-title">测试系统核心功能矩阵</h2>
          <div class="modules-container">
            <!-- 题库生成模块 -->
            <div class="module-card" data-aos="flip-left">
              <div class="holographic-effect"></div>
              <div class="module-icon">
                <i class="fas fa-cogs"></i>
              </div>
              <h3 class="module-title">智能题库生成</h3>
              <div class="module-features">
                <div class="feature-tag">综合指标题库</div>
                <span class="feature-tag">学科分类题库</span>
                <span class="feature-tag">难度自定义算法</span>
                <span class="feature-tag">多源数据融合</span>
                <span class="feature-tag">支持题库预览</span>
              </div>
            </div>

            <!-- 题库变形模块 -->
            <div class="module-card" data-aos="flip-right">
              <div class="holographic-effect"></div>
              <div class="module-icon">
                <i class="fas fa-dna"></i>
              </div>
              <h3 class="module-title">多维题库变形</h3>
              <div class="deformation-types">
                <div class="type-item">
                  <i class="fas fa-random"></i>
                  <span>语义重述</span>
                </div>
                <div class="type-item">
                  <i class="fas fa-random"></i>
                  <span>选项细化</span>
                </div>
                <div class="type-item">
                  <i class="fas fa-random"></i>
                  <span>情景嵌入</span>
                </div>
                <div class="type-item">
                  <i class="fas fa-random"></i>
                  <span>难度调整</span>
                </div>
                <div class="type-item">
                  <i class="fas fa-random"></i>
                  <span>增加干扰</span>
                </div>
                <div class="type-item">
                  <i class="fas fa-shuffle"></i>
                  <span>考点拓展</span>
                </div>
                <div class="type-item">
                  <i class="fas fa-shapes"></i>
                  <span>题型更改</span>
                </div>
              </div>
            </div>

            <!-- 模型测试模块 -->
            <div class="module-card" data-aos="fade-up">
              <div class="holographic-effect"></div>
              <div class="model-wall">
                <div 
                  v-for="(model, index) in models" 
                  :key="index"
                  class="model-card"
                  :style="{ transform: `rotate(${index * 14}deg)` }"
                >
                  <img :src="model.logo" :alt="model.name">
                </div>
                <h3 class="module-title">多模型竞技场</h3>
              </div>
            </div>

            <!-- 报告分析模块 -->
            <div class="module-card" data-aos="zoom-in">
              <div class="holographic-effect"></div>
              <div class="model-wall">
                <div 
                  v-for="(model, index) in models2" 
                  :key="index"
                  class="model-card"
                >
                  <img :src="model.logo" :alt="model.name">
                </div>
              </div>
              <h3 class="module-title">智能分析中心</h3>
            </div>
          </div>
        </section>

        <!-- 核心数据展示 -->
        <section class="stats-section">
          <div class="stats-container">
            <div 
              v-for="(stat, index) in stats" 
              :key="index" 
              class="stat-item"
              data-aos="zoom-in"
              :data-aos-delay="index * 100"
            >
              <div class="stat-icon">
                <i :class="stat.icon"></i>
              </div>
              <div class="stat-content">
                <div class="number">{{ stat.value }}</div>
                <div class="label">{{ stat.label }}</div>
              </div>
            </div>
          </div>
        </section>

                <!-- 快速开始指导 -->
                <section class="quick-start-section">
          <h2 class="section-title" data-aos="fade-up">快速开始指导</h2>
          <div class="quick-start-steps">
            <div class="step" data-aos="fade-up" :data-aos-delay="0">
              <h3>步骤 1: 创建新题库</h3>
              <p>用户可以创建新题库，自定义题目数目、题目领域和难度分布，完成题目创建。</p>
            </div>
            <div class="step" data-aos="fade-up" :data-aos-delay="100">
              <h3>步骤 2: 题库变形</h3>
              <p>用户点击题库的变形按钮，可跳转到题库变形的界面进行题库变形。</p>
            </div>
            <div class="step" data-aos="fade-up" :data-aos-delay="200">
              <h3>步骤 3: 模型测试</h3>
              <p>用户可以直接点击题库对应的测试按钮跳转到测试界面，或者在测试界面自行选择题目。同时，还能自定义选择题库里面的各个题目（选择和删除）进行测试。</p>
            </div>
            <div class="step" data-aos="fade-up" :data-aos-delay="300">
              <h3>步骤 4: 生成测试报告</h3>
              <p>测试完成后，系统将生成测试报告，可视化展示测试结果，同时支持多模型对比。</p>
            </div>
          </div>
        </section>

                <!-- 技术架构 -->
                <section class="architecture-section">
          <h2 class="section-title" data-aos="fade-up">大模型测试系统技术架构</h2>
          <div class="architecture-diagram" data-aos="zoom-in">
              <img :src="architecture" alt="技术架构图" loading="lazy">
          </div>
        </section>

        <!-- 功能介绍 -->
        <section class="features-section">
          <h2 class="section-title" data-aos="fade-up">测试系统核心功能简介</h2>
          <div class="features-container">
            <div 
              v-for="(feature, index) in features"
              :key="index"
              class="feature-card"
              data-aos="flip-left"
              :data-aos-delay="index * 100"
            >
              <div class="card-icon">
                <i :class="feature.icon"></i>
              </div>
              <h3>{{ feature.title }}</h3>
              <p>{{ feature.desc }}</p>
            </div>
          </div>
        </section>

      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import 'animate.css'
import AOS from 'aos'
import 'aos/dist/aos.css'
// 引入图片资源
import gptLogo from '@/assets/gpt.png';
import claudeLogo from '@/assets/claude.png';
import llamaLogo from '@/assets/llama.png';
import chatglmLogo from '@/assets/chatglm.png';
import deepseekLogo from '@/assets/deepseek.png';
import banner1 from '@/assets/banner1.jpg';
import banner2 from '@/assets/banner2.jpg';
import architecture from '@/assets/architecture.jpg';
import view1 from '@/assets/view1.png';
import view2 from '@/assets/view2.png';
import view3 from '@/assets/view3.png';
import view4 from '@/assets/view4.png';
import view5 from '@/assets/view5.png';

export default {
  setup() {
    const isSidebarOpen = ref(true);
    const models = ref([
      { name: 'GPT-4', logo: gptLogo },
      { name: 'Claude-2', logo: claudeLogo },
      { name: 'Llama-2', logo: llamaLogo },
      { name: 'ChatGLM3', logo: chatglmLogo },
      { name: 'DeepSeek', logo: deepseekLogo },
      { name: 'GPT-3.5', logo: gptLogo }
    ]);
    const models2 = ref([
      { name: 'view1', logo: view1 },
      { name: 'view2', logo: view2 },
      { name: 'view3', logo: view3 },
      { name: 'view4', logo: view4 },
      { name: 'view5', logo: view5 },
      { name: 'view1', logo: view1 }
    ]);

    const carouselItems = ref([
      {
        bg: banner1,
        title: '智能驱动，精准评测——大模型测试系统',
        desc: '搭载前沿AI算法，对主流大模型进行全方位深度评测，为您的决策提供可靠依据'
      },
      {
        bg: banner2,
        title: '多元数据，深度洞察',
        desc: '依托海量多源数据，从语言生成、知识理解等多维度剖析模型性能，挖掘模型潜力'
      }
    ]);

    const stats = ref([
      { icon: 'fas fa-brain', value: '5+', label: '涵盖主流大模型' },
      { icon: 'fas fa-database', value: '2000+', label: '精心构建的测试题库规模' },
      { icon: 'fas fa-chart-line', value: '10+', label: '细致划分的评估维度' },
      { icon: 'fas fa-check-circle', value: '90+%', label: '模型的准确性' } 
    ]);

    const features = ref([
      {
        icon: 'fas fa-shield-alt',
        title: '题库生成模块',
        desc: '支持用户自定义题目领域，自由设定难度分布比例。同时拥有丰富的现有学科分类题库，满足多样化测试需求，为精准评测奠定坚实基础'
      },
      {
        icon: 'fas fa-cogs',
        title: '题库变形模块',
        desc: '运用先进的数据变形技术，对现有题库进行多样化处理。包括语义变换、题型转换等多种形式，有效拓展测试边界，挖掘模型真实能力'
      },
      {
        icon: 'fas fa-rocket',
        title: '模型测试模块',
        desc: '对当前主流大模型如 GPT-3.5-TURBO、GPT-4、DEEPSEEK、CLAUDE-2、LLAMA-2、CHATGLM3 等进行全面性能测试，从基础语言能力到复杂任务处理，全方位评估模型表现'
      },
      {
        icon: 'fas fa-chart-pie',
        title: '报告分析模块',
        desc: '采用前沿可视化技术，将模型的功能和性能表现以直观易懂的图表形式呈现。同时提供详尽测试报告，支持用户在线浏览与下载，助力深度分析与决策'
      }
    ]);

    const message = `尊敬的研究者与开发者们，欢迎来到我们的大模型综合评测页面！如今，AI 模型如雨后春笋般迅猛发展，在这海量的选择中，如何找到契合研究与开发需求的理想模型，成了一大难题。而我们的页面，便是为攻克这一难题而生。
在这里，我们将当前主流大模型在各类评测数据集上的表现，精心整理成详尽榜单，展现在您眼前。我们致力于打造一个全面的模型测试平台，助力您拨开模型选择的重重迷雾，做出明智决策。
通过深入剖析不同模型在各类数据集上的性能，您能够精准定位每个模型的优势与短板，从而为自己的项目挑选出最匹配的得力工具，让项目进展事半功倍。`;
    const displayText = ref('');
    const messageRef = ref(null);

    onMounted(() => {
      let index = 0;
      const intervalId = setInterval(() => {
        if (index < message.length) {
          displayText.value += message[index];
          index++;
        } else {
          clearInterval(intervalId);
        }
      }, 100);
    });

    AOS.init({
      duration: 1000,
      once: true
    });

    return {
      isSidebarOpen,
      models,
      models2,
      architecture,
      carouselItems,
      stats,
      features,
      displayText,
      messageRef
    };
  }
}
</script>

<style scoped>
/* 主容器样式 */
.view-main-container {
  display: flex;
  min-height: calc(100vh - 64px);
  margin-left: 30px;
  box-sizing: border-box; /* 防止宽度溢出 */
}

/* 主内容区域样式 */
.content-container {
  flex: 1;
  padding: 20px;
}

.home-container {
  max-width: 1440px;
  margin: 0 auto;
  font-family: 'Roboto', sans-serif; /* 更换为具有科技感的字体 */
}

/* 向下滑动提示样式 */
.scroll-down {
  text-align: center;
  margin: 20px 0;
  font-size: 1.5rem;
  color: #95bade;
  animation: bounce 1.5s infinite;
  text-shadow: 0 0 10px #b8f2e6; /* 文字阴影，增强科技感 */
}

.scroll-down i {
  font-size: 2rem;
  margin-top: 10px;
  color: #95bade;
  text-shadow: 0 0 10px #b8f2e6; /* 文字阴影，增强科技感 */
}

@keyframes bounce {
  0%, 20%, 50%, 80%, 100% {
    transform: translateY(0);
  }
  40% {
    transform: translateY(-10px);
  }
  60% {
    transform: translateY(-5px);
  }
}

/* 顶部轮播样式 */
.hero-section {
  position: relative;
}

.carousel-content {
  text-align: center;
  height: 600px;
  background-size: cover;
  background-position: center;
  position: relative;
}

.carousel-content::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.3);
}

.content-wrapper {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 2;
  text-align: center;
  color: white;
  padding: 0 20px;
}

.content-wrapper h2 {
  font-size: 3.8rem;
  margin-bottom: 1.5rem;
  text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
  font-weight: 700;
  letter-spacing: 1px; /* 增加字间距 */
}

.content-wrapper p {
  font-size: 1.6rem;
  max-width: 800px;
  margin: 0 auto;
  line-height: 1.7;
}

.module-title {
  text-align: center; /* 使文本居中 */
  margin: 1rem 0; /* 可选：添加上下边距 */
}

.module-title::after {
  content: '';
  display: block;
  width: 120px;
}

/* 核心功能展示样式 */
.modules-section {
  padding:  0;
  position: relative;
  z-index: 1;
}

.cyberpunk-title {
  text-align: center;
  font-size: 2.8rem;
  background: linear-gradient(45deg, #409EFF, #67C23A);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  position: relative;
}

.cyberpunk-title::after {
  content: '';
  display: block;
  width: 120px;
  height: 3px;
  background: #409EFF;
  margin: 1rem auto;
  box-shadow: 0 0 10px #409EFF;
}

.modules-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 2rem;
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 2rem;
}

.module-card {
  background: rgba(255,255,255,0.1);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  padding: 2rem;
  position: relative;
  overflow: hidden;
  transition: transform 0.3s ease;
}

.module-card:hover {
  transform: translateY(-10px);
}

.holographic-effect {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(45deg, 
    rgba(64,158,255,0.2),
    rgba(103,194,58,0.2),
    rgba(230,162,60,0.2)
  );
  opacity: 0.3;
  animation: hologram 6s infinite;
}

@keyframes hologram {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

.module-icon {
  width: 80px;
  height: 80px;
  background: linear-gradient(135deg, #409eff, #66b1ff);
  border-radius: 50%;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: center;
}

.module-icon i {
  color: white;
  font-size: 2rem;
}

.module-features {
  margin-top: 1rem;
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
}

.feature-tag {
  background: rgba(64, 158, 255, 0.2);
  color: #409eff;
  padding: 0.5rem 1rem;
  border-radius: 20px;
  margin: 0.3rem;
  font-size: 0.9rem;
}

.deformation-types {
  margin-top: 1rem;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.type-item {
  display: flex;
  align-items: center;
  margin: 0.5rem 0;
}

.type-item i {
  margin-right: 0.5rem;
  color: #409eff;
}

.model-wall {
  display: flex;
  justify-content: space-around;
  align-items: center;
  flex-wrap: wrap;
  margin-top: 1rem;
}

.model-card {
  background: rgba(255, 255, 255, 0.9);
  padding: 1rem;
  border-radius: 8px;
  transition: all 0.3s ease;
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.model-card img {
  width: 100%;
  height: auto;
  transition: transform 0.3s;
}

.model-card:hover img {
  transform: scale(1.1);
}

.visualization-preview {
  margin-top: 1rem;
  display: flex;
  justify-content: center;
  gap: 1rem;
}

.hologram-button {
  position: relative;
  background: none;
  border: 2px solid #409EFF;
  color: #409EFF;
  padding: 1rem 2rem;
  font-size: 1.1rem;
  cursor: pointer;
  overflow: hidden;
  margin-top: 1rem;
}

.hologram-button::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: linear-gradient(45deg, 
    transparent,
    rgba(64,158,255,0.4),
    transparent
  );
  animation: buttonGlow 3s infinite;
}

@keyframes buttonGlow {
  0% { transform: translate(-100%, -100%) rotate(45deg); }
  100% { transform: translate(100%, 100%) rotate(45deg); }
}

/* 核心数据 */
.stats-section {
  padding: 4rem 0;
  background: #f9fafc;
}

.stats-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 2rem;
  max-width: 1200px;
  margin: 0 auto;
}

.stat-item {
  background: white;
  padding: 2rem;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
  display: flex;
  align-items: center;
  transition: transform 0.3s ease;
}

.stat-item:hover {
  transform: translateY(-5px);
}

.stat-icon {
  width: 60px;
  height: 60px;
  background: #409eff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 1.5rem;
}

.stat-icon i {
  color: white;
  font-size: 1.8rem;
}

.stat-content .number {
  font-size: 2.5rem;
  font-weight: 700;
  color: #1a1a1a;
}

.stat-content .label {
  color: #606266;
  font-size: 1rem;
}

/* 功能特性 */
.features-section {
  padding: 6rem 0;
  background: white;
}

.section-title {
  text-align: center;
  font-size: 3rem; /* 增大字体 */
  margin-bottom: 3rem;
  color: #ffffff; /* 白色字体 */
  font-weight: 700;
  letter-spacing: 1px;
  background: linear-gradient(45deg, #409EFF, #67C23A); /* 渐变背景 */
  -webkit-background-clip: text; /* Safari 和 Chrome */
  background-clip: text; /* 标准属性 */
  -webkit-text-fill-color: transparent; /* 使文字填充为渐变色 */
  animation: fadeIn 1s ease-in-out; /* 添加动画效果 */
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.features-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 2rem;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}

.feature-card {
  background: rgba(255, 255, 255, 0.1); /* 半透明背景 */
  padding: 2.5rem;
  border-radius: 16px;
  text-align: center;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.2); /* 更强的阴影效果 */
  transition: all 0.3s ease;
  background: linear-gradient(45deg, 
    rgba(64,158,255,0.1),
    rgba(103,194,58,0.1),
    rgba(230,162,60,0.1)
  );
}

.feature-card:hover {
  transform: translateY(-10px) scale(1.05); /* 鼠标悬停时放大 */
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3); /* 鼠标悬停时更强的阴影 */
}

.feature-card h3 {
  font-size: 1.8rem;
  margin: 1.5rem 0;
  color: #1a1a1a;
  font-weight: 600;
}

.feature-card p {
  color: #606266;
  line-height: 1.6;
  font-size: 1.1rem;
}

.card-icon {
  width: 80px;
  height: 80px;
  background: linear-gradient(135deg, #409eff, #66b1ff);
  border-radius: 50%;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: center;
}

.card-icon i {
  color: white;
  font-size: 2rem;
}

/* 技术架构 */
.architecture-section {
  padding: 6rem 0;
  background: #f9fafc;
}

.architecture-diagram {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}

.architecture-diagram img {
  width: 100%;
  height: auto;
  border-radius: 12px;
  box-shadow: 0 4px 24px rgba(0,0,0,0.08);
}

@media (max-width: 768px) {
  .content-wrapper h2 {
    font-size: 2.2rem;
  }
  
  .content-wrapper p {
    font-size: 1.3rem;
  }

  .stats-container {
    grid-template-columns: 1fr;
  }

  .feature-card {
    padding: 1.5rem;
  }
}

/* 快速开始指导样式 */
.quick-start-section {
  margin-top: 40px;
}

.quick-start-steps .step {
  margin-bottom: 20px;
  padding: 20px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  background: linear-gradient(45deg, 
    rgba(238, 240, 243, 0.1),
    rgba(218, 237, 209, 0.1)
  );
}

.quick-start-steps .step h3 {
  margin-bottom: 10px;
}

.message-section {
  padding: 20px;
  text-align: center;
}

.message {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  font-size: 18px;
  color: #7fb9f7; /* 蓝色，可根据需要调整 */
  line-height: 1.6;
}
</style> 

<template>
  <div id="app">
    <!-- 顶部导航栏 -->
    <nav class="navbar">
      <div class="navbar-brand">
        <button class="sidebar-toggle" @click="toggleSidebar">
          <i class="fas fa-bars"></i>
        </button>
        <h1>大模型评测系统</h1>
      </div>
      <div class="navbar-end">
        <div class="admin-info">
          <i class="fas fa-user"></i>
          <span class="admin-text">管理员</span>
        </div>
        <div class="right-menu">
          <el-dropdown>
            <span class="el-dropdown-link">
              关于我们<el-icon class="el-icon--right"><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item>团队介绍</el-dropdown-item>
                <el-dropdown-item>联系方式</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
    </nav>

    <div class="main-container">
      <!-- 侧边栏 -->
      <aside class="sidebar" :class="{ 'is-collapsed': !isSidebarOpen }">
        <div class="sidebar-menu">

          <router-link to="/question-management" class="menu-item">
            <i class="fas fa-question-circle"></i>
            <span :class="{ 'hide-text': !isSidebarOpen }">题库管理</span>
          </router-link>
          <router-link to="/question-transform" class="menu-item">
            <i class="fas fa-magic"></i>
            <span :class="{ 'hide-text': !isSidebarOpen }">题库变形</span>
          </router-link>
          <router-link to="/model-test" class="menu-item">
            <i class="fas fa-flask"></i>
            <span :class="{ 'hide-text': !isSidebarOpen }">模型测试</span>
          </router-link>
          <router-link to="/files" class="menu-item">
            <i class="fas fa-file-alt"></i>
            <span :class="{ 'hide-text': !isSidebarOpen }">报告列表</span>
          </router-link>
          <!-- 新增模型比较菜单项 -->
          <router-link to="/model-compare" class="menu-item">
            <i class="fas fa-chart-bar"></i>
            <span :class="{ 'hide-text': !isSidebarOpen }">模型比较</span>
          </router-link>
        </div>
      </aside>

      <!-- 主要内容区域 -->
      <main class="main-content" :class="{ 'sidebar-collapsed': !isSidebarOpen }">
        <router-view></router-view>
      </main>
    </div>
  </div>
</template>

<script>
import { ArrowDown } from '@element-plus/icons-vue'

export default {
  name: 'App',
  components: {
    ArrowDown
  },
  data() {
    return {
      isSidebarOpen: true
    };
  },
  methods: {
    toggleSidebar() {
      this.isSidebarOpen = !this.isSidebarOpen;
    }
  }
};
</script>

<style>
#app {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: #f5f7fa;
}

/* 导航栏样式 */
.navbar {
  background: #ffffff;
  padding: 0 2rem;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 64px;
  position: fixed;
  width: 100%;
  top: 0;
  z-index: 100;
  backdrop-filter: blur(10px);
}

.navbar-brand {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.navbar-brand h1 {
  margin: 0;
  font-size: 1.4rem;
  color: #1a1a1a;
  font-weight: 600;
  letter-spacing: 0.5px;
}

.navbar-end {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  margin-right: 4rem;
}

.admin-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.6rem 1.2rem;
  background: #f5f7fa;
  border-radius: 8px;
  min-width: 120px;
  transition: all 0.3s ease;
  border: 1px solid #e4e7ed;
}

.admin-info:hover {
  background: #ecf5ff;
  transform: translateY(-1px);
  border-color: #409eff;
}

.admin-info i {
  color: #409eff;
  font-size: 1.3rem;
  line-height: 1;
}

.admin-text {
  color: #606266;
  font-weight: 500;
  font-size: 0.95rem;
}

.sidebar-toggle {
  background: none;
  border: none;
  font-size: 1.3rem;
  color: #606266;
  cursor: pointer;
  padding: 0.6rem;
  border-radius: 6px;
  transition: all 0.3s ease;
}

.sidebar-toggle:hover {
  color: #409eff;
  background: #ecf5ff;
}

.right-menu {
  margin-left: auto;
}

.el-dropdown-link {
  color: #606266;
  text-decoration: none;
  font-weight: 500;
  padding: 0.6rem 1.2rem;
  border-radius: 6px;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  background: #f5f7fa;
  border: 1px solid #e4e7ed;
}

.el-dropdown-link:hover {
  background: #ecf5ff;
  color: #409eff;
  border-color: #409eff;
}

.el-icon--right {
  font-size: 0.8rem;
  transition: transform 0.3s ease;
}

.el-dropdown:hover .el-icon--right {
  transform: rotate(180deg);
}

/* 主容器样式 */
.main-container {
  display: flex;
  margin-top: 64px;
  min-height: calc(100vh - 64px);
}

/* 侧边栏样式 */
.sidebar {
  width: 260px;
  background: #ffffff;
  box-shadow: 2px 0 12px rgba(0, 0, 0, 0.08);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  padding: 1.5rem 0;
  position: fixed;
  height: calc(100vh - 64px);
  overflow-y: auto;
  border-right: 1px solid #e4e7ed;
}

.sidebar.is-collapsed {
  width: 70px;
}

.sidebar.is-collapsed .menu-item span {
  display: none;
}

.sidebar-menu {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.menu-item {
  display: flex;
  align-items: center;
  padding: 0.9rem 1.8rem;
  color: #606266;
  text-decoration: none;
  transition: all 0.3s ease;
  gap: 1.2rem;
  white-space: nowrap;
  position: relative;
  overflow: hidden;
}

.menu-item:hover {
  background: #ecf5ff;
  color: #409eff;
  transform: translateX(5px);
}

.menu-item.router-link-active {
  background: #ecf5ff;
  color: #409eff;
  border-right: 3px solid #409eff;
}

.menu-item i {
  width: 24px;
  text-align: center;
  font-size: 1.2rem;
  transition: all 0.3s ease;
  color: #909399;
}

.menu-item:hover i,
.menu-item.router-link-active i {
  color: #409eff;
  transform: scale(1.1);
}

.hide-text {
  display: none;
}

/* 主要内容区域样式 */
.main-content {
  flex: 1;
  padding: 2.5rem;
  background: #f5f7fa;
  margin-left: 260px;
  transition: margin-left 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  color: #2c3e50;
}

.main-content.sidebar-collapsed {
  margin-left: 70px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .navbar {
    padding: 0 1rem;
  }

  .sidebar {
    background: #ffffff;
    box-shadow: 2px 0 12px rgba(0, 0, 0, 0.1);
  }

  .main-content {
    background: #f5f7fa;
  }

  .main-content {
    margin-left: 0;
    padding: 1.5rem;
  }

  .main-content.sidebar-collapsed {
    margin-left: 0;
  }

  .navbar-end {
    margin-right: 0.5rem;
  }
  
  .el-dropdown-link {
    padding: 0.5rem 1rem;
  }
}

/* 滚动条美化 */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: #f5f7fa;
}

::-webkit-scrollbar-thumb {
  background: #dcdfe6;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: #c0c4cc;
}

/* Element Plus 下拉菜单样式覆盖 */
.el-dropdown-menu {
  background: #ffffff;
  border: 1px solid #e4e7ed;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  padding: 4px 0;
}

.el-dropdown-menu__item {
  color: #929294;
  padding: 8px 20px;
  font-size: 14px;
  line-height: 1.5;
  transition: all 0.3s ease;
}

.el-dropdown-menu__item:hover {
  background: #ecf5ff;
  color: #409eff;
}
</style>
import { createRouter, createWebHistory } from 'vue-router';
import FileList from '../components/FileList.vue';
import FileDetail from '../components/FileDetail.vue';
import QuestionManagement from '../components/QuestionManagement.vue';
import QuestionTransform from '../components/QuestionTransform.vue';
import ModelTest from '../components/ModelTest.vue';
import ModelCompare from '../components/ModelCompare.vue';
import HomeView from '../components/HomeView.vue'

const routes = [
  {
    path: '/',
    redirect: '/home'
  },
  {
    path: '/home',
    name: 'home',
    component: HomeView
  },
  {
    path: '/files',
    name: 'FileList',
    component: FileList
  },
  {
    path: '/files/:id',
    name: 'FileDetail',
    component: FileDetail
  },
  {
    path: '/question-management',
    name: 'QuestionManagement',
    component: QuestionManagement
  },
  {
    path: '/question-transform',
    name: 'QuestionTransform',
    component: QuestionTransform
  },
  {
    path: '/model-test',
    name: 'ModelTest',
    component: ModelTest
  },
  {
    path: '/model-compare',
    name: 'ModelCompare',
    component: ModelCompare
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    // 始终滚动到顶部
    return { top: 0 }
  }
});

export default router;
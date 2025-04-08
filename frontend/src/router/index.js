import { createRouter, createWebHistory } from 'vue-router';
import FileList from '../components/FileList.vue';
import FileDetail from '../components/FileDetail.vue';
import QuestionManagement from '../components/QuestionManagement.vue';
import QuestionTransform from '../components/QuestionTransform.vue';
import ModelTest from '../components/ModelTest.vue';
import ModelCompare from '../components/ModelCompare.vue';

const routes = [
  {
    path: '/',
    redirect: '/question-management'
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
  routes
});

export default router;
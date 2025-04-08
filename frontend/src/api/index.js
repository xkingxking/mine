import { createRouter, createWebHistory } from 'vue-router';
import FileList from '../components/FileList.vue';
import FileDetail from '../components/FileDetail.vue';

const routes = [
  {
    path: '/',
    redirect: '/files'
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
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

export default router;
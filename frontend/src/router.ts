import { createRouter, createWebHistory } from 'vue-router'
import HomeView from './views/HomeView.vue'
import VocabularyView from './views/VocabularyView.vue'
import PapersView from './views/PapersView.vue'
import MistakesView from './views/MistakesView.vue'
import StatisticsView from './views/StatisticsView.vue'
import SettingsView from './views/SettingsView.vue'
import LessonView from './views/LessonView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'home', component: HomeView },
    { path: '/vocabulary', name: 'vocabulary', component: VocabularyView },
    { path: '/lessons/:id', name: 'lesson', component: LessonView },
    { path: '/papers', name: 'papers', component: PapersView },
    { path: '/mistakes', name: 'mistakes', component: MistakesView },
    { path: '/statistics', name: 'statistics', component: StatisticsView },
    { path: '/settings', name: 'settings', component: SettingsView },
  ],
})

export default router

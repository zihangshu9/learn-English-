<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getDashboard, type Dashboard } from '../api'

const router = useRouter()
const dashboard = ref<Dashboard | null>(null)
const usingDemo = ref(false)
const loading = ref(true)

onMounted(async () => {
  const result = await getDashboard()
  dashboard.value = result.data
  usingDemo.value = result.offline
  loading.value = false
})

const totalMinutes = computed(() => dashboard.value?.tasks.reduce((sum, task) => sum + task.estimated_minutes, 0) ?? 0)
const completedTasks = computed(() => dashboard.value?.tasks.filter((task) => task.status === 'completed').length ?? 0)
const nextTask = computed(() => dashboard.value?.tasks.find((task) => task.status !== 'completed') ?? null)

const taskRoutes: Record<string, string> = {
  word_review: '/vocabulary',
  new_words: '/vocabulary',
  reading: '/papers',
  mistake_review: '/mistakes',
}

function startLearning() {
  if (!nextTask.value) return
  router.push(taskRoutes[nextTask.value.task_type] ?? '/vocabulary')
}
</script>

<template>
  <div class="page home-page">
    <div v-if="loading" class="panel loading-card">正在准备今天的学习计划…</div>
    <template v-else-if="dashboard">
      <header class="hero">
        <div>
          <p class="eyebrow">Good afternoon · 今天也向前一点</p>
          <h1 class="page-title">把英语，<br />慢慢学回来。</h1>
          <p class="page-subtitle">{{ dashboard.plan_name }} · 距离计划完成还有 {{ dashboard.days_remaining }} 天</p>
        </div>
        <div class="progress-seal" aria-label="总体计划进度">
          <strong>{{ dashboard.progress_percent }}%</strong>
          <span>总体进度</span>
        </div>
      </header>

      <p v-if="usingDemo" class="demo-notice">后端尚未启动，当前展示示例任务。</p>

      <section class="today-panel panel">
        <div class="panel-heading">
          <div>
            <p class="eyebrow">Today's plan</p>
            <h2 class="section-title">今日学习</h2>
          </div>
          <span class="time-chip">约 {{ totalMinutes }} 分钟</span>
        </div>

        <div class="task-list">
          <article v-for="(task, index) in dashboard.tasks" :key="task.id" class="task-row">
            <span class="task-number">{{ String(index + 1).padStart(2, '0') }}</span>
            <div class="task-copy">
              <strong>{{ task.title }}</strong>
              <span>{{ task.completed_count }} / {{ task.target_count }} · {{ task.estimated_minutes }}分钟</span>
            </div>
            <span class="task-status" :class="task.status">{{ task.status === 'completed' ? '已完成' : '待完成' }}</span>
          </article>
        </div>

        <div class="today-footer">
          <span>已完成 {{ completedTasks }} / {{ dashboard.tasks.length }} 项</span>
          <button class="primary-button" :disabled="!nextTask" @click="startLearning">
            {{ nextTask ? '开始今日学习 →' : '今日任务已完成' }}
          </button>
        </div>
      </section>

      <section class="insight-grid">
        <article class="panel insight-card">
          <span class="insight-label">连续学习</span>
          <strong>{{ dashboard.streak_days }}<small> 天</small></strong>
          <p>稳定比一次学很多更重要。</p>
        </article>
        <article class="panel quote-card">
          <p>“Every word you learn is a small door opening.”</p>
          <span>每学会一个词，就多打开一扇小门。</span>
        </article>
        <article class="panel date-card">
          <span class="insight-label">计划完成</span>
          <strong>{{ dashboard.target_completion_date }}</strong>
          <p>任务会根据进度自动调整。</p>
        </article>
      </section>
    </template>
  </div>
</template>

<style scoped>
.home-page { padding-bottom: 40px; }
.hero { display: flex; justify-content: space-between; align-items: end; gap: 30px; margin-bottom: 34px; }
.progress-seal { flex: 0 0 132px; aspect-ratio: 1; border: 1px solid #b8c9c2; border-radius: 50%; display: grid; place-content: center; text-align: center; background: rgba(255,255,255,.34); }
.progress-seal strong { font-family: Georgia, serif; font-size: 31px; font-weight: 500; }
.progress-seal span { color: var(--muted); font-size: 12px; }
.demo-notice { padding: 10px 14px; border-radius: 10px; color: #7d4b2c; background: #f7dfcb; font-size: 13px; }
.today-panel { overflow: hidden; }
.panel-heading { display: flex; justify-content: space-between; align-items: center; padding: 27px 30px 20px; }
.time-chip { padding: 7px 11px; border-radius: 999px; color: var(--green); background: var(--green-soft); font-size: 12px; font-weight: 700; }
.task-list { padding: 0 30px; }
.task-row { display: grid; grid-template-columns: 46px 1fr auto; align-items: center; gap: 14px; padding: 18px 0; border-top: 1px solid var(--line); }
.task-number { color: var(--orange); font: 17px Georgia, serif; }
.task-copy { display: grid; gap: 5px; }
.task-copy span { color: var(--muted); font-size: 12px; }
.task-status { padding: 6px 10px; border: 1px solid var(--line); border-radius: 999px; color: var(--muted); font-size: 11px; }
.task-status.completed { color: var(--green); background: var(--green-soft); border-color: transparent; }
.today-footer { display: flex; justify-content: space-between; align-items: center; padding: 20px 30px 26px; background: #f8f5ed; color: var(--muted); font-size: 13px; }
.today-footer button:disabled { cursor: default; opacity: .55; }
.insight-grid { display: grid; grid-template-columns: .8fr 1.4fr 1fr; gap: 16px; margin-top: 18px; }
.insight-card, .quote-card, .date-card { min-height: 155px; padding: 24px; }
.insight-label { color: var(--muted); font-size: 12px; }
.insight-card strong { display: block; margin-top: 10px; font: 38px Georgia, serif; }
.insight-card small { font-size: 15px; }
.insight-card p, .date-card p { color: var(--muted); font-size: 12px; }
.quote-card { color: white; background: var(--green); }
.quote-card p { margin: 4px 0 18px; font: italic 21px/1.5 Georgia, serif; }
.quote-card span { color: #bcd0c8; font-size: 12px; }
.date-card strong { display: block; margin: 16px 0; font: 21px Georgia, serif; }
.loading-card { padding: 40px; }
@media (max-width: 760px) {
  .hero { align-items: center; }
  .progress-seal { flex-basis: 94px; }
  .progress-seal strong { font-size: 24px; }
  .task-list, .panel-heading { padding-left: 20px; padding-right: 20px; }
  .today-footer { align-items: stretch; flex-direction: column; gap: 14px; padding: 18px 20px 22px; }
  .insight-grid { grid-template-columns: 1fr; }
}
</style>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { completeLesson, getLesson, type Lesson, type LessonResult } from '../api'

const route = useRoute()
const router = useRouter()
const lesson = ref<Lesson | null>(null)
const loading = ref(true)
const error = ref('')
const answers = ref<Record<string, string>>({})
const translations = ref<Record<number, boolean>>({})
const submitting = ref(false)
const result = ref<LessonResult | null>(null)
const message = ref('')

const allAnswered = computed(() => lesson.value?.questions.every((question) => answers.value[String(question.id)]) ?? false)

onMounted(async () => {
  try {
    lesson.value = await getLesson(Number(route.params.id))
  } catch {
    error.value = '课程加载失败，请确认本地服务已经更新并启动。'
  } finally {
    loading.value = false
  }
})

function toggleTranslation(sectionId: number) {
  translations.value[sectionId] = !translations.value[sectionId]
}

async function finishLesson() {
  if (!lesson.value || submitting.value) return
  if (!allAnswered.value) {
    message.value = '请先完成三道理解题。'
    document.querySelector('#comprehension')?.scrollIntoView({ behavior: 'smooth' })
    return
  }
  submitting.value = true
  message.value = ''
  try {
    result.value = await completeLesson(lesson.value.id, answers.value)
    lesson.value.completed = true
    lesson.value.score = result.value.score
  } catch {
    message.value = '保存课程进度失败，请稍后重试。'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="page lesson-page">
    <div v-if="loading" class="panel loading-card">正在打开课本…</div>
    <div v-else-if="error" class="panel loading-card error">{{ error }}</div>
    <template v-else-if="lesson">
      <button class="back-link" @click="router.push('/')">← 返回今日学习</button>

      <header class="lesson-hero panel">
        <div class="lesson-meta">
          <span>Unit {{ lesson.unit_number }}</span>
          <span>Lesson {{ lesson.lesson_number }}</span>
          <span>{{ lesson.estimated_minutes }} 分钟</span>
          <span v-if="lesson.completed" class="completed-chip">已完成 · {{ lesson.score }}分</span>
        </div>
        <p class="eyebrow">Foundation English</p>
        <h1>{{ lesson.title }}</h1>
        <p>{{ lesson.subtitle }}</p>
        <div class="objectives">
          <strong>本课目标</strong>
          <ul><li v-for="objective in lesson.objectives" :key="objective">{{ objective }}</li></ul>
        </div>
      </header>

      <nav class="lesson-nav panel" aria-label="本课目录">
        <a href="#texts">01 课文</a><a href="#comprehension">02 理解</a><a href="#vocabulary">03 单词表</a>
      </nav>

      <section id="texts" class="lesson-section">
        <article v-for="(section, index) in lesson.sections" :key="section.id" class="reading-card panel">
          <div class="section-heading">
            <div>
              <span class="section-number">TEXT {{ String(index + 1).padStart(2, '0') }}</span>
              <h2>{{ section.title }}</h2>
            </div>
            <span class="type-chip">{{ section.section_type === 'dialogue' ? '对话' : '阅读' }}</span>
          </div>
          <div class="english-text">{{ section.content }}</div>
          <button class="translation-button" @click="toggleTranslation(section.id)">
            {{ translations[section.id] ? '收起参考译文' : '查看参考译文' }}
          </button>
          <div v-if="translations[section.id]" class="translation-text">{{ section.translation }}</div>
        </article>
      </section>

      <section id="comprehension" class="exercise-panel panel">
        <p class="eyebrow">Check your understanding</p>
        <h2>课文理解</h2>
        <article v-for="(question, index) in lesson.questions" :key="question.id" class="question-block">
          <strong>{{ index + 1 }}. {{ question.question }}</strong>
          <label v-for="(option, key) in question.options" :key="key"
                 :class="{ selected: answers[String(question.id)] === key,
                   correct: result && key === question.correct_answer,
                   wrong: result && answers[String(question.id)] === key && key !== question.correct_answer }">
            <input v-model="answers[String(question.id)]" type="radio" :name="`question-${question.id}`" :value="key" :disabled="!!result" />
            <span>{{ key }}</span>{{ option }}
          </label>
          <p v-if="result" class="explanation">{{ question.explanation }}</p>
        </article>
      </section>

      <section id="vocabulary" class="vocabulary-panel panel">
        <div class="section-heading">
          <div><p class="eyebrow">Words from this lesson</p><h2>本课单词表</h2></div>
          <span class="type-chip">{{ lesson.vocabulary.length }} words</span>
        </div>
        <div class="vocabulary-list">
          <article v-for="(item, index) in lesson.vocabulary" :key="item.word" class="vocabulary-row">
            <span class="vocabulary-index">{{ String(index + 1).padStart(2, '0') }}</span>
            <div class="word-main"><strong>{{ item.word }}</strong><span>{{ item.phonetic }} · {{ item.part_of_speech }}</span></div>
            <div class="word-meaning"><strong>{{ item.meaning }}</strong><span>{{ item.example }} · {{ item.example_translation }}</span></div>
          </article>
        </div>
      </section>

      <section class="finish-panel panel">
        <div v-if="result">
          <p class="eyebrow">Lesson complete</p>
          <h2>本课完成 · {{ result.score }} 分</h2>
          <p>答对 {{ result.correct_count }} / {{ result.question_count }} 题。本课单词会按照课内顺序进入单词学习。</p>
        </div>
        <div v-else>
          <h2>完成本课</h2>
          <p>完成理解题后保存进度，首页“基础阅读”会同步更新。</p>
        </div>
        <button v-if="!result" class="primary-button" :disabled="submitting" @click="finishLesson">
          {{ submitting ? '正在保存…' : '完成本课' }}
        </button>
        <button v-else class="primary-button" @click="router.push('/vocabulary')">复习本课单词 →</button>
        <p v-if="message" class="form-message">{{ message }}</p>
      </section>
    </template>
  </div>
</template>

<style scoped>
.lesson-page { padding-bottom: 60px; scroll-behavior: smooth; }
.back-link { margin-bottom: 18px; padding: 0; border: 0; color: var(--muted); background: transparent; cursor: pointer; }
.lesson-hero { padding: 42px 46px; background: linear-gradient(135deg, #fffdf7 55%, #e4eee8); }
.lesson-hero h1 { margin: 10px 0 8px; font: 48px/1.1 Georgia, serif; font-weight: 500; }
.lesson-hero > p:not(.eyebrow) { color: var(--muted); font-size: 18px; }
.lesson-meta { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 28px; }
.lesson-meta span, .type-chip { padding: 6px 10px; border-radius: 999px; color: var(--green); background: var(--green-soft); font-size: 11px; font-weight: 700; }
.lesson-meta .completed-chip { color: white; background: var(--green); }
.objectives { max-width: 620px; margin-top: 30px; padding-top: 22px; border-top: 1px solid var(--line); }
.objectives ul { margin: 10px 0 0; padding-left: 20px; color: var(--muted); line-height: 1.8; }
.lesson-nav { position: sticky; z-index: 2; top: 12px; display: grid; grid-template-columns: repeat(3, 1fr); margin: 18px 0; padding: 8px; border-radius: 14px; }
.lesson-nav a { padding: 10px; border-radius: 9px; text-align: center; color: var(--muted); font-size: 13px; }
.lesson-nav a:hover { color: var(--green); background: var(--green-soft); }
.lesson-section { display: grid; gap: 18px; }
.reading-card, .exercise-panel, .vocabulary-panel, .finish-panel { padding: 38px 42px; scroll-margin-top: 80px; }
.section-heading { display: flex; justify-content: space-between; align-items: start; gap: 20px; }
.section-heading h2, .exercise-panel h2, .finish-panel h2 { margin: 5px 0 0; font: 29px Georgia, serif; }
.section-number { color: var(--orange); font-size: 11px; font-weight: 800; letter-spacing: .15em; }
.english-text, .translation-text { white-space: pre-line; }
.english-text { max-width: 790px; margin-top: 30px; color: #263d36; font: 18px/1.95 Georgia, serif; }
.translation-button { margin-top: 26px; padding: 8px 0; border: 0; color: var(--green); background: transparent; cursor: pointer; font-weight: 700; }
.translation-text { margin-top: 8px; padding: 22px 24px; border-left: 3px solid var(--orange); color: var(--muted); background: #f8f5ed; line-height: 1.9; }
.exercise-panel, .vocabulary-panel, .finish-panel { margin-top: 18px; }
.question-block { padding: 25px 0; border-top: 1px solid var(--line); }
.question-block > strong { display: block; margin-bottom: 13px; }
.question-block label { display: flex; align-items: center; gap: 10px; margin: 7px 0; padding: 11px 13px; border: 1px solid var(--line); border-radius: 10px; cursor: pointer; }
.question-block label span { display: grid; place-items: center; width: 24px; height: 24px; border-radius: 50%; color: var(--green); background: var(--green-soft); font-weight: 700; }
.question-block input { display: none; }
.question-block label.selected { border-color: var(--green); background: #f2f7f4; }
.question-block label.correct { border-color: #4d8c67; background: #e5f2e9; }
.question-block label.wrong { border-color: #bf6b5c; background: #faebe7; }
.explanation { color: var(--muted); font-size: 13px; line-height: 1.7; }
.vocabulary-list { margin-top: 20px; }
.vocabulary-row { display: grid; grid-template-columns: 40px 180px 1fr; gap: 16px; align-items: center; padding: 17px 0; border-top: 1px solid var(--line); }
.vocabulary-index { color: var(--orange); font: 15px Georgia, serif; }
.word-main, .word-meaning { display: grid; gap: 5px; }
.word-main strong { font: 22px Georgia, serif; }
.word-main span, .word-meaning span { color: var(--muted); font-size: 12px; }
.finish-panel { display: grid; grid-template-columns: 1fr auto; align-items: center; gap: 20px; background: var(--green); color: white; }
.finish-panel p { color: #c7dad3; }
.finish-panel .primary-button { color: var(--green); background: white; }
.form-message { grid-column: 1 / -1; margin: 0; color: #ffd4ca !important; }
.loading-card { padding: 40px; }
.error { color: #9d3b2f; }
@media (max-width: 720px) {
  .lesson-hero, .reading-card, .exercise-panel, .vocabulary-panel, .finish-panel { padding: 26px 22px; }
  .lesson-hero h1 { font-size: 36px; }
  .lesson-nav { position: static; }
  .vocabulary-row { grid-template-columns: 32px 1fr; }
  .word-meaning { grid-column: 2; }
  .finish-panel { grid-template-columns: 1fr; }
}
</style>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { getWordSession, reviewWord, type WordCard } from '../api'

const words = ref<WordCard[]>([])
const currentIndex = ref(0)
const revealed = ref(false)
const loading = ref(true)
const submitting = ref(false)
const error = ref('')
const reviewCount = ref(0)
const newCount = ref(0)
const current = computed(() => words.value[currentIndex.value] ?? null)

onMounted(async () => {
  try {
    const session = await getWordSession()
    words.value = session.words
    reviewCount.value = session.review_count
    newCount.value = session.new_count
  } catch {
    error.value = '无法加载单词，请确认本地服务已启动。'
  } finally {
    loading.value = false
  }
})

async function answer(result: 'unknown' | 'fuzzy' | 'known') {
  if (!current.value || submitting.value) return
  submitting.value = true
  error.value = ''
  try {
    await reviewWord(current.value.id, result)
    currentIndex.value += 1
    revealed.value = false
  } catch {
    error.value = '保存学习记录失败，请稍后重试。'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="page empty-page">
    <p class="eyebrow">Vocabulary</p>
    <h1 class="page-title">单词学习</h1>
    <p class="page-subtitle">先诚实判断是否认识，再查看释义。今日安排：复习 {{ reviewCount }} 个，新学 {{ newCount }} 个。</p>
    <div v-if="loading" class="panel state-card">正在准备今天的单词…</div>
    <div v-else-if="error && !current" class="panel state-card error">{{ error }}</div>
    <div v-else-if="!current" class="panel state-card">
      <strong>本轮学习完成</strong>
      <p>学习记录已保存，首页进度也会同步更新。</p>
    </div>
    <template v-else>
      <section class="word-card panel" @click="revealed = true">
        <span class="word-index">{{ current.status === 'unlearned' ? '今日新词' : '到期复习' }} · {{ currentIndex + 1 }} / {{ words.length }}</span>
        <strong>{{ current.word }}</strong>
        <span class="phonetic">{{ current.phonetic || '暂无音标' }}</span>
        <div v-if="revealed" class="meaning">
          <p>{{ current.meaning }}</p>
          <small v-if="current.example">{{ current.example }} {{ current.example_translation }}</small>
        </div>
        <button v-else class="secondary-button">显示释义</button>
      </section>
      <p v-if="error" class="inline-error">{{ error }}</p>
      <div v-if="revealed" class="answer-actions">
        <button :disabled="submitting" @click="answer('unknown')">不认识</button>
        <button :disabled="submitting" @click="answer('fuzzy')">有点模糊</button>
        <button :disabled="submitting" @click="answer('known')">已经认识</button>
      </div>
    </template>
  </div>
</template>

<style scoped>
.word-card { max-width: 680px; min-height: 350px; margin: 34px auto 18px; padding: 35px; display: flex; flex-direction: column; align-items: center; justify-content: center; cursor: pointer; }
.word-card strong { margin: 30px 0 8px; font: 54px Georgia, serif; font-weight: 500; }
.word-index, .phonetic { color: var(--muted); font-size: 13px; }
.meaning { margin-top: 24px; padding-top: 20px; width: 75%; border-top: 1px solid var(--line); text-align: center; }
.meaning p { font-size: 20px; }
.meaning small { color: var(--muted); }
.secondary-button { margin-top: 34px; }
.answer-actions { max-width: 680px; margin: auto; display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
.answer-actions button { padding: 13px; border: 1px solid var(--line); border-radius: 11px; background: var(--paper); cursor: pointer; }
.answer-actions button:last-child { color: white; background: var(--green); border-color: var(--green); }
.answer-actions button:disabled { cursor: wait; opacity: .6; }
.state-card { max-width: 680px; margin: 34px auto; padding: 40px; text-align: center; }
.state-card strong { font: 28px Georgia, serif; }
.error, .inline-error { color: #9d3b2f; }
.inline-error { max-width: 680px; margin: 0 auto 12px; font-size: 13px; }
</style>

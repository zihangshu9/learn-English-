<script setup lang="ts">
import { ref } from 'vue'

const revealed = ref(false)
const sample = { word: 'abandon', phonetic: '/əˈbændən/', meaning: 'v. 放弃；抛弃', phrase: 'abandon a plan  放弃计划' }
</script>

<template>
  <div class="page empty-page">
    <p class="eyebrow">Vocabulary</p>
    <h1 class="page-title">单词学习</h1>
    <p class="page-subtitle">先诚实判断是否认识，再查看释义。</p>
    <section class="word-card panel" @click="revealed = true">
      <span class="word-index">今日新词 · 01 / 15</span>
      <strong>{{ sample.word }}</strong>
      <span class="phonetic">{{ sample.phonetic }}　🔊</span>
      <div v-if="revealed" class="meaning">
        <p>{{ sample.meaning }}</p>
        <small>{{ sample.phrase }}</small>
      </div>
      <button v-else class="secondary-button">显示释义</button>
    </section>
    <div v-if="revealed" class="answer-actions">
      <button>不认识</button><button>有点模糊</button><button>已经认识</button>
    </div>
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
</style>

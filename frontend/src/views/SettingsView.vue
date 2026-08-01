<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { getAiStatus, saveAiSettings } from '../api'
const completionDate = ref('2027-06-01')
const dailyMinutes = ref(30)
const model = ref('deepseek-v4-flash')
const apiKey = ref('')
const aiConfigured = ref(false)
const aiMessage = ref('')

onMounted(async () => {
  try {
    const status = await getAiStatus()
    model.value = status.default_model
    aiConfigured.value = status.configured
  } catch {
    aiMessage.value = '暂时无法连接本地后端'
  }
})

async function saveAi() {
  aiMessage.value = '正在保存…'
  try {
    const status = await saveAiSettings(apiKey.value, model.value)
    aiConfigured.value = status.configured
    apiKey.value = ''
    aiMessage.value = status.configured ? '已安全保存，可以使用AI错题解析' : '尚未填写API Key'
  } catch {
    aiMessage.value = '保存失败，请稍后重试'
  }
}
</script>

<template>
  <div class="page empty-page">
    <p class="eyebrow">Preferences</p><h1 class="page-title">设置</h1>
    <div class="settings-grid">
      <section class="settings-card panel">
        <h2 class="section-title">学习计划</h2>
        <label>计划完成时间<input v-model="completionDate" type="date" /></label>
        <label>每日学习时长<input v-model="dailyMinutes" type="number" min="10" max="180" /><span>分钟</span></label>
        <button class="primary-button">保存计划</button>
      </section>
      <section class="settings-card panel">
        <h2 class="section-title">AI 错题解析</h2>
        <label>默认模型<select v-model="model"><option>deepseek-v4-flash</option><option>deepseek-v4-pro</option></select></label>
        <label>API Key<input v-model="apiKey" type="password" :placeholder="aiConfigured ? '已配置，留空则不修改' : '仅保存在本地后端'" /></label>
        <p class="security-note">密钥不会进入学习备份，也不会提交到Git。</p>
        <button class="secondary-button" @click="saveAi">保存AI设置</button>
        <p v-if="aiMessage" class="security-note">{{ aiMessage }}</p>
      </section>
    </div>
  </div>
</template>

<style scoped>
.settings-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; margin-top: 32px; }
.settings-card { padding: 28px; }
label { position: relative; display: grid; gap: 8px; margin: 22px 0; color: var(--muted); font-size: 13px; }
input, select { width: 100%; padding: 12px 13px; border: 1px solid var(--line); border-radius: 10px; color: var(--ink); background: white; }
label span { position: absolute; right: 13px; bottom: 13px; }
.security-note { color: var(--muted); font-size: 12px; }
@media (max-width: 760px) { .settings-grid { grid-template-columns: 1fr; } }
</style>

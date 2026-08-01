<script setup lang="ts">
const navItems = [
  { to: '/', label: '今日', icon: '⌂' },
  { to: '/vocabulary', label: '单词', icon: 'Aa' },
  { to: '/papers', label: '真题', icon: '▤' },
  { to: '/mistakes', label: '错题本', icon: '↺' },
  { to: '/statistics', label: '统计', icon: '⌁' },
]
</script>

<template>
  <div class="app-shell">
    <aside class="sidebar">
      <RouterLink class="brand" to="/">
        <span class="brand-mark">拾</span>
        <span>
          <strong>拾词</strong>
          <small>CET Study</small>
        </span>
      </RouterLink>

      <nav class="nav-list" aria-label="主导航">
        <RouterLink v-for="item in navItems" :key="item.to" :to="item.to" class="nav-item">
          <span class="nav-icon">{{ item.icon }}</span>
          <span>{{ item.label }}</span>
        </RouterLink>
      </nav>

      <RouterLink class="settings-link" to="/settings">
        <span class="nav-icon">⚙</span>
        <span>设置</span>
      </RouterLink>
    </aside>

    <main class="main-content">
      <RouterView />
    </main>
  </div>
</template>

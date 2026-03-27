<template>
  <div class="app">
    <Navigation />
    <div class="card">
      <router-view />
    </div>
  </div>
</template>

<script setup lang="ts">
import Navigation from './components/Navigation.vue';
</script>

<style>
/* 全局样式 */
:root {
  --bg-primary: #0b0e1f;
  --bg-secondary: #13172f;
  --text-primary: #e7e9ee;
  --text-secondary: #b9c2d0;
  --accent: #60a5fa;
  --border: #334155;
  --success: #10b981;
  --error: #ef4444;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
}

body {
  background: var(--bg-primary);
  color: var(--text-primary);
  line-height: 1.6;
  padding: 20px;
}

.app {
  max-width: 1200px;
  margin: 0 auto;
}

.card {
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 20px;
  max-width: 1080px;
  margin: 20px auto;
  width: 100%;
  box-sizing: border-box;
}
</style>

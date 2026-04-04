<template>
  <nav class="navbar">
    <h1>🚀 东阿阿胶养殖场-实时检测系统</h1>
    <div class="nav-links">
      <router-link to="/detection" class="nav-link">实时检测</router-link>
      <router-link to="/barns" class="nav-link">养殖舍管理</router-link>
      <router-link to="/pens" class="nav-link">栏管理</router-link>
      <router-link to="/cameras" class="nav-link">摄像头管理</router-link>
      <router-link to="/camera-configs" class="nav-link">摄像头配置</router-link>
      <router-link to="/events" class="nav-link">事件记录</router-link>
    </div>
  </nav>
</template>

<style scoped>
.navbar {
  background: #121833;
  border-bottom: 1px solid #243;
  padding: 10px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.navbar h1 {
  margin: 0;
  font-size: 18px;
  color: #60a5fa;
}

.nav-links {
  display: flex;
  gap: 15px;
}

.nav-link {
  color: #e7e9ee;
  text-decoration: none;
  padding: 8px 12px;
  border-radius: 6px;
  transition: background 0.2s;
}

.nav-link:hover {
  background: #1d2a5a;
}

.router-link-active {
  background: #1d2a5a;
  font-weight: bold;
}
</style>

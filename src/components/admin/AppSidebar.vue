<template>
  <aside class="admin-sidebar">
    <div class="sidebar-logo">
      <div class="logo-mark">A</div>
      <div class="logo-text">
        <div class="title">Air Admin</div>
        <div class="subtitle">航空管理端</div>
      </div>
    </div>

    <el-menu
      class="sidebar-menu"
      :default-active="activePath"
      router
      background-color="transparent"
      text-color="#5f6f89"
      active-text-color="#2563eb"
    >
      <el-menu-item index="/admin/dashboard">
        <el-icon><HomeFilled /></el-icon>
        <span>控制台</span>
      </el-menu-item>

      <el-menu-item index="/admin/flights">
        <el-icon><Promotion /></el-icon>
        <span>航班管理</span>
      </el-menu-item>

      <el-menu-item index="/admin/orders">
        <el-icon><Tickets /></el-icon>
        <span>订单管理</span>
      </el-menu-item>

      <el-menu-item index="/admin/users">
        <el-icon><User /></el-icon>
        <span>用户管理</span>
      </el-menu-item>

      <el-menu-item index="/admin/admins">
        <el-icon><Setting /></el-icon>
        <span>管理员管理</span>
      </el-menu-item>
    </el-menu>
  </aside>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import {
  HomeFilled,
  Promotion,
  Tickets,
  User,
  Setting
} from '@element-plus/icons-vue'

const route = useRoute()

const activePath = computed(() => {
  if (route.path.startsWith('/admin/flights')) return '/admin/flights'
  return route.path
})
</script>

<style scoped>
.admin-sidebar {
  width: 236px;
  min-height: 100vh;
  padding: 20px 14px;
  background: rgba(255, 255, 255, 0.78);
  backdrop-filter: blur(16px);
  border-right: 1px solid rgba(226, 232, 240, 0.9);
  box-shadow: 8px 0 24px rgba(148, 163, 184, 0.12);
}

.sidebar-logo {
  height: 64px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 10px 18px;
  margin-bottom: 12px;
  border-bottom: 1px solid rgba(226, 232, 240, 0.85);
}

.logo-mark {
  width: 40px;
  height: 40px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  font-size: 20px;
  font-weight: 700;
  background: linear-gradient(135deg, #3b82f6, #0ea5e9);
  box-shadow: 0 10px 22px rgba(59, 130, 246, 0.28);
}

.logo-text .title {
  color: #1e293b;
  font-size: 16px;
  font-weight: 700;
  line-height: 1.2;
}

.logo-text .subtitle {
  margin-top: 3px;
  color: #94a3b8;
  font-size: 12px;
}

.sidebar-menu {
  border-right: none;
}

:deep(.el-menu-item) {
  height: 46px;
  margin: 6px 0;
  border-radius: 12px;
  font-size: 14px;
}

:deep(.el-menu-item.is-active) {
  background: rgba(37, 99, 235, 0.1);
  font-weight: 600;
}

:deep(.el-menu-item:hover) {
  background: rgba(59, 130, 246, 0.08);
}
</style>
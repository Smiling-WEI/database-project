<template>
  <aside
    class="admin-sidebar"
    :class="{ collapsed }"
  >
    <div class="sidebar-logo">
      <div class="logo-mark">A</div>
      <div v-show="!collapsed" class="logo-text">
        <div class="title">Air Admin</div>
        <div class="subtitle">航空管理端</div>
      </div>
    </div>

    <el-menu
      class="sidebar-menu"
      :default-active="activePath"
      :collapse="collapsed"
      :collapse-transition="false"
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

      <el-sub-menu index="/admin/ticketing">
        <template #title>
          <el-icon><Coin /></el-icon>
          <span>票务配置</span>
        </template>

        <el-menu-item index="/admin/pricing">
          <el-icon><Tickets /></el-icon>
          <span>舱位票价</span>
        </el-menu-item>

        <el-menu-item index="/admin/change-rules">
          <el-icon><Document /></el-icon>
          <span>退改签规则</span>
        </el-menu-item>
      </el-sub-menu>

      <el-menu-item index="/admin/users">
        <el-icon><User /></el-icon>
        <span>用户管理</span>
      </el-menu-item>

      <el-menu-item index="/admin/admins">
        <el-icon><Setting /></el-icon>
        <span>管理员管理</span>
      </el-menu-item>

      <el-menu-item v-if="systemAdmin" index="/admin/coordination">
        <el-icon><Connection /></el-icon>
        <span>跨航司协调</span>
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
  Coin,
  Document,
  Connection,
  User,
  Setting
} from '@element-plus/icons-vue'
import { getStoredUser, isSystemAdmin } from '../../utils/adminAuth'

defineProps({
  collapsed: {
    type: Boolean,
    default: false
  }
})

const route = useRoute()
const systemAdmin = computed(() => isSystemAdmin(getStoredUser()))

const activePath = computed(() => {
  if (route.path.startsWith('/admin/flights')) return '/admin/flights'
  if (route.path.startsWith('/admin/change-records')) return '/admin/orders'
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
  transition: width 0.2s ease, padding 0.2s ease;
}

.admin-sidebar.collapsed {
  width: 76px;
  padding-right: 8px;
  padding-left: 8px;
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

.collapsed .sidebar-logo {
  justify-content: center;
  padding-right: 0;
  padding-left: 0;
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

:deep(.el-menu--collapse) {
  width: 60px;
}

:deep(.el-menu--collapse .el-menu-item),
:deep(.el-menu--collapse .el-sub-menu__title) {
  justify-content: center;
  padding: 0 !important;
}

:deep(.el-menu-item) {
  height: 46px;
  margin: 6px 0;
  border-radius: 12px;
  font-size: 14px;
}

:deep(.el-sub-menu__title) {
  height: 46px;
  margin: 6px 0;
  border-radius: 12px;
  font-size: 14px;
}

:deep(.el-sub-menu .el-menu-item) {
  min-width: auto;
  padding-left: 48px !important;
}

:deep(.el-menu-item.is-active) {
  background: rgba(37, 99, 235, 0.1);
  font-weight: 600;
}

:deep(.el-menu-item:hover) {
  background: rgba(59, 130, 246, 0.08);
}

:deep(.el-sub-menu__title:hover) {
  background: rgba(59, 130, 246, 0.08);
}
</style>

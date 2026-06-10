<template>
  <header class="admin-header">
    <div>
      <div class="breadcrumb">航空订票系统 / 管理端</div>
      <h1>{{ pageTitle }}</h1>
    </div>

    <div class="header-actions">
      <el-button plain size="small" @click="goClientHome">
        返回客户端
      </el-button>

      <el-dropdown>
        <div class="admin-user">
          <el-avatar :size="34">管</el-avatar>
          <div class="user-text">
            <span class="name">管理员</span>
            <span class="role">System Admin</span>
          </div>
        </div>

        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item @click="goDashboard">控制台</el-dropdown-item>
            <el-dropdown-item divided @click="logout">退出登录</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const titleMap = {
  '/admin/dashboard': '控制台',
  '/admin/flights': '航班管理',
  '/admin/flights/edit': '航班编辑',
  '/admin/users': '用户管理',
  '/admin/orders': '订单管理',
  '/admin/admins': '管理员管理'
}

const pageTitle = computed(() => {
  if (route.path.startsWith('/admin/flights/edit')) return '航班编辑'
  return titleMap[route.path] || '管理端'
})

const goClientHome = () => {
  router.push('/home')
}

const goDashboard = () => {
  router.push('/admin/dashboard')
}

const logout = () => {
  router.push('/login')
}
</script>

<style scoped>
.admin-header {
  height: 76px;
  padding: 0 26px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(14px);
  border-bottom: 1px solid rgba(226, 232, 240, 0.85);
}

.breadcrumb {
  margin-bottom: 5px;
  color: #94a3b8;
  font-size: 12px;
}

h1 {
  margin: 0;
  color: #1e293b;
  font-size: 22px;
  font-weight: 700;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.admin-user {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  padding: 6px 8px;
  border-radius: 12px;
}

.admin-user:hover {
  background: rgba(241, 245, 249, 0.85);
}

.user-text {
  display: flex;
  flex-direction: column;
  line-height: 1.2;
}

.name {
  color: #334155;
  font-size: 14px;
  font-weight: 600;
}

.role {
  margin-top: 3px;
  color: #94a3b8;
  font-size: 12px;
}
</style>
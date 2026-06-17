<template>
  <el-container class="app-wrapper">
    <el-aside width="220px" class="sidebar">
      <div class="logo-area">
        <el-icon :size="34" color="#fff"><Promotion /></el-icon>
        <div>
          <div class="logo-text">航空订票系统</div>
          <div class="logo-subtitle">AIR BOOKING SYSTEM</div>
        </div>
      </div>

      <el-menu
        :default-active="activeMenu"
        class="custom-menu"
        background-color="transparent"
        text-color="#d7e6f6"
        active-text-color="#ffffff"
        router
      >
        <el-menu-item index="/home">
          <el-icon><Search /></el-icon>
          <span>航班查询</span>
        </el-menu-item>
        <el-menu-item index="/orders">
          <el-icon><Tickets /></el-icon>
          <span>我的订单</span>
        </el-menu-item>
        <el-menu-item index="/passengers">
          <el-icon><User /></el-icon>
          <span>常用乘机人</span>
        </el-menu-item>
        <el-menu-item index="/change-records">
          <el-icon><Bell /></el-icon>
          <span>改签记录</span>
        </el-menu-item>
        <el-menu-item index="/mine">
          <el-icon><Avatar /></el-icon>
          <span>个人中心</span>
        </el-menu-item>
      </el-menu>

      <div class="sidebar-footer">
        <el-button class="logout-btn" type="danger" plain @click="handleLogout">
          <el-icon><SwitchButton /></el-icon>
          退出登录
        </el-button>
      </div>
    </el-aside>

    <el-container class="main-container">
      <el-header class="top-header">
        <div class="header-left">
          <el-icon class="collapse-btn"><Fold /></el-icon>
          <span class="welcome-text">欢迎回来，{{ displayName }}</span>
          <el-tag size="small" type="primary" effect="dark" class="vip-tag">
            普通会员
          </el-tag>
        </div>

        <div class="header-right">
          <el-badge :value="2" class="msg-badge">
            <el-icon :size="20"><Bell /></el-icon>
          </el-badge>
          <span class="message-text">消息</span>
          <div class="user-profile">
            <el-avatar :size="32">
              <el-icon><UserFilled /></el-icon>
            </el-avatar>
            <span class="username">{{ displayName }}</span>
            <el-icon><ArrowDown /></el-icon>
          </div>
        </div>
      </el-header>

      <el-main class="app-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../api/index'
import {
  Promotion,
  Search,
  Tickets,
  User,
  Bell,
  Avatar,
  Fold,
  ArrowDown,
  UserFilled,
  SwitchButton
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const activeMenu = computed(() => route.path)
const currentUser = ref({})
const displayName = computed(() => {
  return currentUser.value.real_name ||
    currentUser.value.realName ||
    currentUser.value.username ||
    '用户'
})

const loadCurrentUser = async () => {
  const cachedUser = localStorage.getItem('currentUser')

  if (cachedUser) {
    try {
      currentUser.value = JSON.parse(cachedUser)
    } catch {
      currentUser.value = {}
    }
  }

  try {
    const response = await api.get('/users/me')
    currentUser.value = response.data.data || {}
    localStorage.setItem('currentUser', JSON.stringify(currentUser.value))
  } catch (error) {
    console.error(error)
  }
}

onMounted(() => {
  loadCurrentUser()
})

const handleLogout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('role')
  localStorage.removeItem('currentUser')
  sessionStorage.removeItem('adminSidebarCollapsed')
  router.push('/login')
}
</script>

<style scoped>
.app-wrapper {
  height: 100vh;
  width: 100vw;
  overflow: hidden;
}

.sidebar {
  background: linear-gradient(180deg, rgba(9, 38, 64, 0.98), rgba(13, 55, 88, 0.96));
  display: flex;
  flex-direction: column;
  box-shadow: 4px 0 20px rgba(11, 45, 75, 0.24);
  z-index: 10;
}

.logo-area {
  height: 92px;
  display: flex;
  align-items: center;
  gap: 12px;
  color: #fff;
  padding: 0 28px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.logo-text {
  font-size: 18px;
  font-weight: 800;
  line-height: 1.2;
}

.logo-subtitle {
  margin-top: 4px;
  font-size: 10px;
  letter-spacing: 1px;
  color: rgba(255, 255, 255, 0.58);
}

.custom-menu {
  border-right: none !important;
  padding-top: 22px;
  flex: 1;
}

:deep(.el-menu-item) {
  height: 58px;
  line-height: 58px;
  padding-left: 32px !important;
  margin: 0;
  border-radius: 0;
  font-weight: 700;
}

:deep(.el-menu-item:hover) {
  background-color: rgba(255, 255, 255, 0.08) !important;
}

:deep(.el-menu-item.is-active) {
  background: linear-gradient(90deg, #0b7cff, #0f65ee) !important;
  color: #fff !important;
}

.sidebar-footer {
  padding: 18px 22px 24px;
}

.logout-btn {
  width: 100%;
  justify-content: center;
  font-weight: 800;
  border-color: rgba(248, 113, 113, 0.7);
  color: #fecaca;
  background: rgba(127, 29, 29, 0.18);
}

.logout-btn:hover {
  color: #ffffff;
  border-color: #f87171;
  background: rgba(220, 38, 38, 0.78);
}

.main-container {
  display: flex;
  flex-direction: column;
  background: url('../assets/images/bg2.png') no-repeat center center;
  background-size: cover;
}

.top-header {
  height: 76px;
  background: rgba(255, 255, 255, 0.58);
  backdrop-filter: blur(12px);
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 34px;
  z-index: 5;
}

.header-left,
.header-right {
  display: flex;
  align-items: center;
  gap: 14px;
}

.collapse-btn {
  font-size: 20px;
  cursor: pointer;
  color: #0b7cff;
}

.welcome-text {
  font-size: 17px;
  font-weight: 800;
  color: #0f172a;
}

.vip-tag {
  border-radius: 5px;
  font-weight: 700;
}

.msg-badge {
  cursor: pointer;
  color: #0b67e9;
}

.message-text {
  font-weight: 700;
  color: #0f172a;
}

.user-profile {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  color: #0f172a;
  font-weight: 800;
}

.app-main {
  padding: 22px 34px 34px;
  overflow-y: auto;
  background: rgba(255, 255, 255, 0.1);
}
</style>

<template>
  <header class="admin-header">
    <div class="header-title">
      <el-tooltip
        :content="sidebarCollapsed ? '展开导航栏' : '收起导航栏'"
        placement="bottom"
      >
        <el-button
          class="sidebar-toggle"
          text
          circle
          :aria-label="sidebarCollapsed ? '展开导航栏' : '收起导航栏'"
          @click="emit('toggle-sidebar')"
        >
          <el-icon :size="20">
            <Expand v-if="sidebarCollapsed" />
            <Fold v-else />
          </el-icon>
        </el-button>
      </el-tooltip>

      <div>
        <div class="breadcrumb">航空订票系统 / 管理端</div>
        <h1>{{ pageTitle }}</h1>
      </div>
    </div>

    <div class="header-actions">
      <el-dropdown>
        <div class="admin-user">
          <el-avatar :size="34">
            {{ avatarText }}
          </el-avatar>

          <div class="user-text">
            <span class="name">{{ displayName }}</span>
            <span class="role">{{ displayRole }}</span>
          </div>
        </div>

        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item @click="goProfile">
              个人信息
            </el-dropdown-item>

            <el-dropdown-item divided @click="logout">
              退出登录
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Expand, Fold } from '@element-plus/icons-vue'

defineProps({
  sidebarCollapsed: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['toggle-sidebar'])

const route = useRoute()
const router = useRouter()

const titleMap = {
  '/admin/dashboard': '控制台',
  '/admin/flights': '航班管理',
  '/admin/flights/edit': '航班编辑',
  '/admin/pricing': '票务配置 / 舱位票价',
  '/admin/change-rules': '票务配置 / 退改签规则',
  '/admin/users': '用户管理',
  '/admin/orders': '订单管理',
  '/admin/admins': '管理员管理',
  '/admin/coordination': '跨航司协调',
  '/admin/profile': '个人信息'
}

const currentUser = computed(() => {
  try {
    return JSON.parse(localStorage.getItem('currentUser') || '{}')
  } catch (error) {
    console.error('登录用户信息解析失败', error)
    return {}
  }
})

const pageTitle = computed(() => {
  if (route.path.startsWith('/admin/flights/edit')) {
    return '航班编辑'
  }

  if (route.path.includes('/irregularities')) {
    return '航班异常处理'
  }

  return titleMap[route.path] || '管理端'
})

const displayName = computed(() => {
  return (
    currentUser.value.real_name ||
    currentUser.value.username ||
    '管理员'
  )
})

const displayRole = computed(() => {
  return (
    currentUser.value.admin_role ||
    currentUser.value.role ||
    '航空公司管理员'
  )
})

const avatarText = computed(() => {
  return String(displayName.value).slice(0, 1)
})

const goProfile = () => {
  router.push('/admin/profile')
}

const logout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('currentUser')
  sessionStorage.removeItem('adminSidebarCollapsed')
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

.header-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.sidebar-toggle {
  color: #64748b;
}

.sidebar-toggle:hover {
  color: #2563eb;
  background: rgba(59, 130, 246, 0.08);
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

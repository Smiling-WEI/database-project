<template>
  <PageContainer
    title="个人信息"
    description="查看当前管理员的账号、岗位和管理范围"
  >
    <div class="profile-layout">
      <section class="profile-card">
        <el-avatar :size="76" class="profile-avatar">
          {{ avatarText }}
        </el-avatar>
        <h2>{{ profile.name || profile.account || '管理员' }}</h2>
        <el-tag type="primary">{{ displayRole }}</el-tag>
        <p>{{ managementScope }}</p>
      </section>

      <section v-loading="loading" class="info-card">
        <div
          v-for="item in profileItems"
          :key="item.label"
          class="info-row"
        >
          <span>{{ item.label }}</span>
          <strong>{{ formatValue(item.value) }}</strong>
        </div>
      </section>
    </div>
  </PageContainer>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import PageContainer from '../../components/admin/PageContainer.vue'
import api from '../../api/index'
import {
  getStoredUser,
  isSystemAdmin
} from '../../utils/adminAuth'

const loading = ref(false)
const loginUser = computed(() => getStoredUser())

const profile = reactive({
  name: '',
  account: '',
  airline: '',
  role: '',
  phone: '',
  email: '',
  lastLoginTime: '',
  status: ''
})

const avatarText = computed(() => {
  return String(profile.name || profile.account || '管').slice(0, 1)
})

const displayRole = computed(() => {
  if (isSystemAdmin(loginUser.value)) return '系统总管理员'
  return profile.role || loginUser.value.admin_role || '航空公司管理员'
})

const managementScope = computed(() => {
  if (isSystemAdmin(loginUser.value)) return '管理范围：全部航空公司'

  const airline =
    profile.airline ||
    loginUser.value.airline_name ||
    loginUser.value.airline_id

  return airline ? `所属航空公司：${airline}` : '所属航空公司：-'
})

const profileItems = computed(() => [
  {
    label: '管理员姓名',
    value: profile.name
  },
  {
    label: '登录账号',
    value: profile.account
  },
  {
    label: '管理员类型',
    value: isSystemAdmin(loginUser.value) ? '系统总管理员' : '航司内部管理员'
  },
  {
    label: '管理员岗位',
    value: displayRole.value
  },
  {
    label: '所属航空公司',
    value: isSystemAdmin(loginUser.value)
      ? '不限定航司'
      : (
        profile.airline ||
        loginUser.value.airline_name ||
        loginUser.value.airline_id
      )
  },
  {
    label: '手机号',
    value: profile.phone
  },
  {
    label: '邮箱',
    value: profile.email
  },
  {
    label: '最近登录时间',
    value: profile.lastLoginTime
  },
  {
    label: '账号状态',
    value: profile.status || '正常'
  },
  {
    label: '管理范围',
    value: isSystemAdmin(loginUser.value)
      ? '全部航空公司'
      : '所属航空公司'
  }
])

const applyLoginUser = () => {
  profile.name =
    loginUser.value.real_name ||
    loginUser.value.name ||
    ''
  profile.account =
    loginUser.value.username ||
    loginUser.value.account ||
    ''
  profile.airline =
    loginUser.value.airline_name ||
    loginUser.value.airline_id ||
    ''
  profile.role =
    loginUser.value.admin_role ||
    loginUser.value.role ||
    ''
  profile.phone = loginUser.value.phone || ''
  profile.email = loginUser.value.email || ''
  profile.lastLoginTime = loginUser.value.last_login_at || ''
  profile.status = loginUser.value.status || '正常'
}

const loadProfile = async () => {
  applyLoginUser()

  if (isSystemAdmin(loginUser.value)) return

  loading.value = true

  try {
    const response = await api.get('/admin/admins')
    const admins = response.data.data || []
    const currentAdmin = admins.find((item) => {
      return (
        item.adminId === loginUser.value.user_id ||
        item.account === loginUser.value.username
      )
    })

    if (!currentAdmin) return

    profile.name = currentAdmin.name || profile.name
    profile.account = currentAdmin.account || profile.account
    profile.role = currentAdmin.role || profile.role
    profile.phone = currentAdmin.phone || ''
    profile.email = currentAdmin.email || ''
    profile.lastLoginTime = currentAdmin.lastLoginTime || ''
    profile.status = currentAdmin.status || profile.status
  } catch (error) {
    console.error('管理员个人信息加载失败', error)
  } finally {
    loading.value = false
  }
}

const formatValue = (value) => {
  if (value === undefined || value === null || value === '') return '-'
  return value
}

onMounted(() => {
  loadProfile()
})
</script>

<style scoped>
.profile-layout {
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr);
  gap: 20px;
}

.profile-card,
.info-card {
  padding: 24px;
  border-radius: 18px;
  background: #ffffff;
  border: 1px solid #e2e8f0;
}

.profile-card {
  text-align: center;
}

.profile-avatar {
  color: #ffffff;
  font-size: 28px;
  font-weight: 700;
  background: linear-gradient(135deg, #3b82f6, #0ea5e9);
}

.profile-card h2 {
  margin: 16px 0 10px;
  font-size: 20px;
}

.profile-card p {
  margin: 14px 0 0;
  color: #64748b;
  font-size: 13px;
}

.info-row {
  min-height: 52px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  border-bottom: 1px solid #eef2f7;
}

.info-row:last-child {
  border-bottom: none;
}

.info-row span {
  color: #64748b;
  font-size: 14px;
}

.info-row strong {
  color: #1e293b;
  font-size: 14px;
  font-weight: 600;
  text-align: right;
}

@media (max-width: 900px) {
  .profile-layout {
    grid-template-columns: 1fr;
  }
}
</style>

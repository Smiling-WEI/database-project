<template>
  <div class="login-wrapper">
    <div class="login-box">
      <h2 class="title">登 录</h2>

      <el-form
        ref="formRef"
        :model="loginForm"
        :rules="rules"
        class="login-form"
      >
        <el-form-item prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="手机号/用户名/邮箱"
            :prefix-icon="User"
            class="custom-input"
            clearable
          />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="请输入密码"
            :prefix-icon="Lock"
            show-password
            class="custom-input"
          />
        </el-form-item>

        <el-form-item prop="role">
          <div class="role-switch">
            <button
              type="button"
              class="role-option"
              :class="{ active: loginForm.role === 'user' }"
              @click="loginForm.role = 'user'"
            >
              普通用户
            </button>

            <button
              type="button"
              class="role-option"
              :class="{ active: loginForm.role === 'admin' }"
              @click="loginForm.role = 'admin'"
            >
              管理员
            </button>
          </div>
        </el-form-item>

        <el-button
          type="primary"
          class="login-btn"
          round
          :loading="loading"
          @click="handleLogin"
        >
          登 录
        </el-button>

        <div class="extra-links">
          <a href="#" @click.prevent="router.push('/forgot-password')">
            忘记密码？
          </a>
          <a href="#" @click.prevent="router.push('/register')">
            立即注册
          </a>
        </div>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import api from '../api/index'

const router = useRouter()
const formRef = ref()
const loading = ref(false)

const loginForm = reactive({
  username: '',
  password: '',
  role: 'user'
})

const rules = {
  username: [
    { required: true, message: '请输入账号', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' }
  ],
  role: [
    { required: true, message: '请选择登录身份', trigger: 'change' }
  ]
}

const handleLogin = async () => {
  if (!formRef.value) return

  const valid = await formRef.value.validate().catch(() => false)

  if (!valid) return

  loading.value = true

  try {
    const response = await api.post('/login', {
      username: loginForm.username,
      password: loginForm.password
    })

    const result = response.data
    const user = result.data?.user
    const token = result.data?.token

    if (!result.success || !user || !token) {
      ElMessage.error(result.message || '登录失败')
      return
    }

    const isAdmin = [
      '航空公司管理员',
      '系统总管理员'
    ].includes(user.role)

    if (loginForm.role === 'admin' && !isAdmin) {
      ElMessage.error('该账号不是管理员账号')
      return
    }

    if (loginForm.role === 'user' && isAdmin) {
      ElMessage.error('该账号是管理员账号，请选择管理员入口')
      return
    }

    localStorage.setItem('token', token)
    localStorage.setItem('role', isAdmin ? 'admin' : 'user')
    localStorage.setItem('currentUser', JSON.stringify(user))

    ElMessage.success('登录成功')

    if (isAdmin) {
      sessionStorage.setItem('adminSidebarCollapsed', 'false')
      router.push('/admin/dashboard')
    } else {
      router.push('/home')
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '登录失败，请检查账号和密码')
  } finally {
    loading.value = false
  }
}
</script>
<style scoped>
.login-wrapper {
  height: 100vh;
  width: 100%;
  overflow: hidden;
  box-sizing: border-box;
  background: url('../assets/images/bg.png') no-repeat center center;
  background-size: cover;
  display: flex;
  justify-content: flex-end;
  align-items: center;
  padding-right: 15%;
}

.login-box {
  width: 380px;
  background-color: #8bb1d3;
  padding: 58px 40px;
  border-radius: 10px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
  text-align: center;
}

.title {
  color: #1a4f82;
  font-size: 28px;
  letter-spacing: 5px;
  margin-bottom: 36px;
}

:deep(.custom-input .el-input__wrapper) {
  background-color: transparent !important;
  box-shadow: none !important;
  border-bottom: 1px solid white !important;
  border-radius: 0;
  padding-left: 0;
}

:deep(.custom-input input) {
  color: white;
}

:deep(.custom-input input::placeholder) {
  color: rgba(255, 255, 255, 0.7);
}

:deep(.el-input__prefix) {
  color: white;
}

:deep(.el-form-item__error) {
  color: #fff7ed;
}

.role-switch {
  width: 100%;
  height: 40px;
  padding: 4px;
  display: flex;
  gap: 6px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.25);
}

.role-option {
  flex: 1;
  border: none;
  border-radius: 999px;
  cursor: pointer;
  color: white;
  font-size: 14px;
  background: transparent;
  transition: all 0.2s ease;
}

.role-option.active {
  color: #1a4f82;
  font-weight: 700;
  background: white;
  box-shadow: 0 6px 14px rgba(26, 79, 130, 0.16);
}

.role-option:hover {
  background: rgba(255, 255, 255, 0.42);
}

.role-option.active:hover {
  background: white;
}

.login-btn {
  width: 100%;
  margin-top: 20px;
  background-color: white;
  color: #8bb1d3;
  border: none;
  font-weight: bold;
  letter-spacing: 5px;
  height: 45px;
}

.login-btn:hover {
  background-color: #f0f0f0;
  color: #8bb1d3;
}

.extra-links {
  display: flex;
  justify-content: space-between;
  margin-top: 20px;
  font-size: 13px;
}

.extra-links a {
  color: white;
  text-decoration: none;
}

.extra-links a:hover {
  text-decoration: underline;
}
</style>

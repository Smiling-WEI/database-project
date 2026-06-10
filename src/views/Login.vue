<template>
  <div class="login-wrapper">
    <div class="login-box">
      <h2 class="title">登 录</h2>

      <el-form :model="loginForm" class="login-form">
        <el-form-item>
          <el-input
            v-model="loginForm.username"
            placeholder="手机号/用户名/邮箱"
            :prefix-icon="User"
            class="custom-input"
          />
        </el-form-item>

        <el-form-item>
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="请输入密码"
            :prefix-icon="Lock"
            show-password
            class="custom-input"
          />
        </el-form-item>

        <el-form-item>
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
import { reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'

const router = useRouter()

const loginForm = reactive({
  username: '',
  password: '',
  role: 'user'
})

const handleLogin = () => {
  if (!loginForm.username || !loginForm.password) {
    ElMessage.warning('请输入账号和密码')
    return
  }

  // 当前阶段仅做前端分流；真实登录校验后续由后端接口接入
  if (loginForm.role === 'admin') {
    router.push('/admin/dashboard')
  } else {
    router.push('/home')
  }
}
</script>

<style scoped>
/* 1. 全屏背景图设置 */
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

/* 2. 浅蓝色登录卡片 */
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

/* 3. 输入框深度美化：去掉边框，只留底线 */
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

/* 4. 登录身份切换 */
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

/* 5. 按钮美化 */
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

/* 底部链接 */
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
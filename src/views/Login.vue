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

        <el-button type="primary" class="login-btn" round @click="handleLogin">登 录</el-button>
        
        <div class="extra-links">
          <a href="#" @click.prevent="router.push('/forgot-password')">忘记密码？</a>
          <a href="#" @click.prevent="router.push('/register')">立即注册</a>
        </div>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { reactive } from 'vue'
import { useRouter } from 'vue-router'
import { User, Lock } from '@element-plus/icons-vue'

const router = useRouter()
const loginForm = reactive({ username: '', password: '' })

const handleLogin = () => {
  // 模拟登录成功，跳转到系统主框架下的首页
  router.push('/home')
}
</script>

<style scoped>
/* 1. 全屏背景图设置 */
.login-wrapper {
  height: 100vh;
  /* 1. 将 100vw 改为 100%，让它严格贴合父元素的真实宽度 */
  width: 100%; 
  /* 2. 新增 overflow: hidden，强制裁剪所有溢出部分，彻底锁死滑动 */
  overflow: hidden; 
  /* 3. 新增 box-sizing，保证你写的 padding-right 不会额外撑破宽度 */
  box-sizing: border-box; 
  
  background: url('../assets/images/bg.png') no-repeat center center;
  background-size: cover;
  display: flex;
  justify-content: flex-end;
  align-items: center;
  padding-right: 15%;
}

/* 2. 浅蓝色登录卡片（高度还原你的设计） */
.login-box {
  width: 380px;
  /* 你的设计图里的浅蓝色背景 */
  background-color: #8bb1d3; 
  padding: 60px 40px;
  /* 添加轻微的阴影和圆角 */
  border-radius: 10px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.2);
  text-align: center;
  /* 如果你的卡片上下带有那种白色泼墨图案，可以把它切成透明 png 作为这个 box 的 background */
}

.title {
  color: #1a4f82;
  font-size: 28px;
  letter-spacing: 5px;
  margin-bottom: 40px;
}

/* 3. 输入框深度美化：去掉边框，只留底线 (还原你的设计) */
:deep(.custom-input .el-input__wrapper) {
  background-color: transparent !important; /* 背景全透明 */
  box-shadow: none !important; /* 去掉四周的框线 */
  border-bottom: 1px solid white !important; /* 只有底部一条白线 */
  border-radius: 0;
  padding-left: 0;
}
:deep(.custom-input input) {
  color: white; /* 输入的文字是白色的 */
}
:deep(.custom-input input::placeholder) {
  color: rgba(255,255,255,0.7); /* 提示文字颜色 */
}
:deep(.el-input__prefix) {
  color: white; /* 图标颜色 */
}

/* 4. 按钮美化 */
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
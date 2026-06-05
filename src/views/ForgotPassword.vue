<template>
  <div class="login-wrapper">
    <div class="login-box">
      <h2 class="title">找回密码</h2>
      
      <el-form :model="resetForm" :rules="rules" ref="resetFormRef" class="login-form">
        
        <el-form-item prop="username">
          <el-input 
            v-model="resetForm.username" 
            placeholder="请输入您的登录账号" 
            :prefix-icon="User" 
            class="custom-input" 
          />
        </el-form-item>
        
        <el-form-item prop="idCard">
          <el-input 
            v-model="resetForm.idCard" 
            placeholder="请输入绑定的18位身份证号" 
            :prefix-icon="CreditCard" 
            maxlength="18" 
            class="custom-input" 
          />
        </el-form-item>

        <el-form-item prop="newPassword">
          <el-input 
            v-model="resetForm.newPassword" 
            type="password" 
            placeholder="请设置新密码 (至少6位)" 
            :prefix-icon="Lock" 
            show-password 
            class="custom-input" 
          />
        </el-form-item>

        <el-button type="warning" class="login-btn reset-btn" round @click="handleReset">
          重 置 密 码
        </el-button>
        
        <div class="extra-links" style="justify-content: center; margin-top: 20px;">
          <a href="#" @click.prevent="router.push('/login')">记起密码？返回登录</a>
        </div>

      </el-form>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { User, Lock, CreditCard } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const router = useRouter()
const resetFormRef = ref(null)

// 响应式表单数据容器
const resetForm = reactive({ 
  username: '', 
  idCard: '', 
  newPassword: '' 
})

// 严密的表单防呆校验规则
const rules = reactive({
  username: [
    { required: true, message: '账号不能为空', trigger: 'blur' }
  ],
  idCard: [
    { required: true, message: '身份验证信息不能为空', trigger: 'blur' },
    { len: 18, message: '身份证号格式错误，必须为18位', trigger: 'blur' }
  ],
  newPassword: [
    { required: true, message: '新密码不能为空', trigger: 'blur' },
    { min: 6, message: '为了您的安全，新密码至少需要6位', trigger: 'blur' }
  ]
})

// 提交重置请求的逻辑
const handleReset = () => {
  // 先触发前端的规则校验
  resetFormRef.value.validate((valid) => {
    if (valid) {
      // 模拟发送请求给后端进行信息比对和密码修改
      console.log('向后端发送密码重置请求：', resetForm)
      
      // 模拟后端返回成功
      ElMessage.success('密码重置成功！请使用新密码登录。')
      
      // 瞬间平滑跳转回登录页
      router.push('/login')
    } else {
      ElMessage.error('请检查填写的信息格式是否有误！')
      return false
    }
  })
}
</script>

<style scoped>
/* 1. 锁死全屏背景，复用你绝美的 bg.jpg */
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

/* 2. 浅蓝色磨砂卡片 */
.login-box {
  width: 380px;
  background-color: #8bb1d3; 
  padding: 50px 40px;
  border-radius: 10px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.2);
  text-align: center;
}

.title { 
  color: #1a4f82; 
  font-size: 24px; 
  letter-spacing: 5px; 
  margin-bottom: 30px; 
  font-weight: bold;
}

/* 3. 透明无边框输入框 (核心美化) */
:deep(.custom-input .el-input__wrapper) {
  background-color: transparent !important;
  box-shadow: none !important;
  border-bottom: 1px solid white !important;
  border-radius: 0;
  padding-left: 0;
}
:deep(.custom-input input) { color: white; }
:deep(.custom-input input::placeholder) { color: rgba(255,255,255,0.7); }
:deep(.el-input__prefix) { color: white; }

/* 4. 按钮美化：重置按钮使用一点橘黄色预警感，悬停时变色 */
.login-btn { 
  width: 100%; 
  margin-top: 15px; 
  border: none; 
  font-weight: bold; 
  letter-spacing: 5px; 
  height: 45px; 
}
.reset-btn {
  background-color: #e6a23c;
  color: white;
}
.reset-btn:hover {
  background-color: #ebb563;
  color: white;
}

/* 5. 底部链接 */
.extra-links a { 
  color: white; 
  text-decoration: none; 
  font-size: 13px; 
}
.extra-links a:hover { 
  text-decoration: underline; 
}
</style>
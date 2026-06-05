<template>
  <div class="login-wrapper">
    <div class="login-box">
      <h2 class="title">新用户注册</h2>
      
      <el-form :model="regForm" :rules="rules" ref="regFormRef" class="login-form">
        <el-form-item prop="username">
          <el-input v-model="regForm.username" placeholder="设置登录账号" :prefix-icon="User" class="custom-input" />
        </el-form-item>
        
        <el-form-item prop="realName">
          <el-input v-model="regForm.realName" placeholder="真实姓名 (如: 张三)" :prefix-icon="Postcard" class="custom-input" />
        </el-form-item>

        <el-form-item prop="idCard">
          <el-input v-model="regForm.idCard" placeholder="18位身份证号" :prefix-icon="CreditCard" maxlength="18" class="custom-input" />
        </el-form-item>

        <el-form-item prop="password">
          <el-input v-model="regForm.password" type="password" placeholder="设置密码" :prefix-icon="Lock" show-password class="custom-input" />
        </el-form-item>

        <el-button type="primary" class="login-btn" round @click="handleRegister">注 册</el-button>
        
        <div class="extra-links" style="justify-content: center; margin-top: 20px;">
          <a href="#" @click.prevent="router.push('/login')">已有账号？返回登录</a>
        </div>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { User, Lock, Postcard, CreditCard } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const router = useRouter()
const regFormRef = ref(null)
const regForm = reactive({ username: '', realName: '', idCard: '', password: '' })

// 注册页的严密表单校验
const rules = reactive({
  username: [{ required: true, message: '账号不能为空', trigger: 'blur' }],
  realName: [{ required: true, message: '真实姓名不能为空', trigger: 'blur' }],
  idCard: [{ required: true, message: '请输入18位身份证号', trigger: 'blur' }, { len: 18, message: '长度必须为18位', trigger: 'blur' }],
  password: [{ required: true, message: '密码不能为空', trigger: 'blur' }, { min: 6, message: '密码至少6位', trigger: 'blur' }]
})

const handleRegister = () => {
  regFormRef.value.validate((valid) => {
    if (valid) {
      ElMessage.success('注册成功！请登录。')
      router.push('/login') // 注册成功后自动跳回登录页
    }
  })
}
</script>

<style scoped>
/* 这里复用了登录页的绝美样式，直接贴过来 */
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
.login-box {
  width: 380px;
  background-color: #8bb1d3; 
  padding: 50px 40px;
  border-radius: 10px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.2);
  text-align: center;
}
.title { color: #1a4f82; font-size: 24px; letter-spacing: 5px; margin-bottom: 30px; }

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

.login-btn { width: 100%; margin-top: 10px; background-color: white; color: #8bb1d3; border: none; font-weight: bold; letter-spacing: 5px; height: 45px; }
.login-btn:hover { background-color: #f0f0f0; }
.extra-links a { color: white; text-decoration: none; font-size: 13px; }
.extra-links a:hover { text-decoration: underline; }
</style>
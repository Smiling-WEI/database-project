<template>
  <div class="password-page">
    <div class="page-title-row">
      <el-button link class="back-btn" @click="router.back()">
        <el-icon><ArrowLeft /></el-icon>
        返回
      </el-button>
      <h2>修改密码</h2>
    </div>

    <el-alert
      class="notice-alert"
      type="primary"
      show-icon
      :closable="false"
      title="为了保障您的账户安全，请定期修改密码，密码长度为 8-16 位，需包含字母、数字和特殊字符。"
    />

    <section class="form-panel">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="140px" class="password-form">
        <el-form-item label="当前密码" prop="currentPassword">
          <el-input
            v-model="form.currentPassword"
            type="password"
            show-password
            placeholder="请输入当前密码"
          />
        </el-form-item>

        <el-form-item label="新密码" prop="newPassword">
          <el-input
            v-model="form.newPassword"
            type="password"
            show-password
            placeholder="请输入新密码"
          />
        </el-form-item>

        <el-form-item label="确认新密码" prop="confirmPassword">
          <el-input
            v-model="form.confirmPassword"
            type="password"
            show-password
            placeholder="请再次输入新密码"
          />
        </el-form-item>

        <el-form-item label="密码强度">
          <div class="strength-wrap">
            <div
              v-for="item in strengthItems"
              :key="item.label"
              class="strength-item"
              :class="{ active: passwordStrength >= item.level }"
            >
              <i></i>
              <span>{{ item.label }}</span>
            </div>
          </div>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" size="large" class="submit-btn" @click="submit">
            确认修改
          </el-button>
        </el-form-item>
      </el-form>
    </section>
  </div>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'

const router = useRouter()
const formRef = ref()

const form = reactive({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const validateConfirm = (rule, value, callback) => {
  if (value !== form.newPassword) {
    callback(new Error('两次输入的新密码不一致'))
    return
  }
  callback()
}

const rules = {
  currentPassword: [{ required: true, message: '请输入当前密码', trigger: 'blur' }],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 8, max: 16, message: '密码长度应为 8-16 位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    { validator: validateConfirm, trigger: 'blur' }
  ]
}

const strengthItems = [
  { label: '弱', level: 1 },
  { label: '中', level: 2 },
  { label: '强', level: 3 }
]

const passwordStrength = computed(() => {
  const value = form.newPassword
  if (!value) return 0

  let score = 0
  if (/[A-Za-z]/.test(value)) score += 1
  if (/\d/.test(value)) score += 1
  if (/[^A-Za-z0-9]/.test(value)) score += 1
  return score
})

const submit = async () => {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  if (passwordStrength.value < 3) {
    ElMessage.warning('建议新密码同时包含字母、数字和特殊字符')
    return
  }

  ElMessage.success('密码修改成功')
  form.currentPassword = ''
  form.newPassword = ''
  form.confirmPassword = ''
}
</script>

<style scoped>
.password-page {
  max-width: 1180px;
  margin: 0 auto;
}

.page-title-row {
  display: flex;
  align-items: center;
  gap: 22px;
  margin-bottom: 38px;
}

.back-btn {
  color: #0b7cff;
  font-size: 18px;
  font-weight: 800;
}

.page-title-row h2 {
  margin: 0;
  color: #0f172a;
}

.notice-alert {
  margin-bottom: 28px;
  border: 1px solid #bfdbfe;
  background: rgba(239, 246, 255, 0.9);
}

.form-panel {
  min-height: 520px;
  padding: 48px 80px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.88);
  box-shadow: 0 10px 30px rgba(30, 93, 140, 0.08);
}

.password-form {
  max-width: 820px;
  margin: 0 auto;
}

:deep(.el-form-item) {
  margin-bottom: 42px;
}

:deep(.el-input__wrapper) {
  height: 52px;
}

.strength-wrap {
  width: 420px;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 6px;
}

.strength-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: center;
  color: #94a3b8;
}

.strength-item i {
  width: 100%;
  height: 8px;
  border-radius: 999px;
  background: #e5e7eb;
}

.strength-item.active:nth-child(1) i {
  background: #f97316;
}

.strength-item.active:nth-child(2) i {
  background: #facc15;
}

.strength-item.active:nth-child(3) i {
  background: #22c55e;
}

.submit-btn {
  width: 260px;
  height: 52px;
  margin-left: 140px;
  font-weight: 800;
}

@media (max-width: 760px) {
  .form-panel {
    padding: 28px 20px;
  }

  .strength-wrap,
  .submit-btn {
    width: 100%;
    margin-left: 0;
  }
}
</style>

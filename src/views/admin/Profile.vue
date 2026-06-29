<template>
  <PageContainer
    title="个人信息"
    description="查看当前管理员的账号、岗位和管理范围"
  >
    <div class="profile-layout">
      <div class="profile-card">
        <div class="avatar-circle">
          {{ avatarText }}
        </div>

        <h2>{{ profile.realName || '-' }}</h2>

        <el-tag type="primary">
          {{ profile.adminRole || profile.role || '-' }}
        </el-tag>

        <p class="profile-sub">
          所属航空公司：{{ profile.airlineName || profile.airlineId || '-' }}
        </p>

        <el-button
          type="primary"
          plain
          class="password-button"
          @click="openPasswordDialog"
        >
          修改密码
        </el-button>
      </div>

      <div class="info-card">
        <div class="section-title">基础信息</div>

        <div class="info-row">
          <span>管理员姓名</span>
          <strong>{{ profile.realName || '-' }}</strong>
        </div>

        <div class="info-row">
          <span>登录账号</span>
          <strong>{{ profile.username || '-' }}</strong>
        </div>

        <div class="info-row">
          <span>管理员类型</span>
          <strong>{{ profile.role || '-' }}</strong>
        </div>

        <div class="info-row">
          <span>管理员岗位</span>
          <strong>{{ profile.adminRole || '-' }}</strong>
        </div>

        <div class="info-row">
          <span>所属航空公司</span>
          <strong>{{ profile.airlineName || profile.airlineId || '-' }}</strong>
        </div>

        <div class="info-row">
          <span>账号状态</span>
          <el-tag :type="profile.status === '正常' ? 'success' : 'danger'">
            {{ profile.status || '-' }}
          </el-tag>
        </div>

        <el-divider />

        <div class="section-title contact-title">
          联系方式
          <el-button
            v-if="!editingContact"
            type="primary"
            link
            @click="startEditContact"
          >
            修改
          </el-button>
        </div>

        <el-form
          v-if="editingContact"
          ref="contactFormRef"
          :model="contactForm"
          :rules="contactRules"
          label-width="80px"
          class="contact-form"
        >
          <el-form-item label="手机号" prop="phone">
            <el-input
              v-model="contactForm.phone"
              placeholder="请输入 11 位手机号"
            />
          </el-form-item>

          <el-form-item label="邮箱" prop="email">
            <el-input
              v-model="contactForm.email"
              placeholder="请输入邮箱，可留空"
            />
          </el-form-item>

          <div class="form-actions">
            <el-button @click="cancelEditContact">
              取消
            </el-button>
            <el-button
              type="primary"
              :loading="savingContact"
              @click="saveContact"
            >
              保存
            </el-button>
          </div>
        </el-form>

        <template v-else>
          <div class="info-row">
            <span>手机号</span>
            <strong>{{ profile.phone || '-' }}</strong>
          </div>

          <div class="info-row">
            <span>邮箱</span>
            <strong>{{ profile.email || '-' }}</strong>
          </div>
        </template>
      </div>
    </div>

    <el-dialog
      v-model="passwordDialogVisible"
      title="修改密码"
      width="520px"
      @closed="resetPasswordForm"
    >
      <el-form
        ref="passwordFormRef"
        :model="passwordForm"
        :rules="passwordRules"
        label-width="100px"
      >
        <el-form-item label="原密码" prop="oldPassword">
          <el-input
            v-model="passwordForm.oldPassword"
            type="password"
            show-password
            placeholder="请输入原密码"
          />
        </el-form-item>

        <el-form-item label="新密码" prop="newPassword">
          <el-input
            v-model="passwordForm.newPassword"
            type="password"
            show-password
            placeholder="请输入不少于 6 位的新密码"
          />
        </el-form-item>

        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input
            v-model="passwordForm.confirmPassword"
            type="password"
            show-password
            placeholder="请再次输入新密码"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="passwordDialogVisible = false">
          取消
        </el-button>
        <el-button
          type="primary"
          :loading="savingPassword"
          @click="savePassword"
        >
          确认修改
        </el-button>
      </template>
    </el-dialog>
  </PageContainer>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import PageContainer from '../../components/admin/PageContainer.vue'
import api from '../../api/index'
import { getStoredUser } from '../../utils/adminAuth'

const profile = reactive({
  userId: '',
  username: '',
  realName: '',
  role: '',
  adminRole: '',
  airlineId: '',
  airlineName: '',
  phone: '',
  email: '',
  status: ''
})

const contactFormRef = ref()
const passwordFormRef = ref()

const editingContact = ref(false)
const savingContact = ref(false)
const passwordDialogVisible = ref(false)
const savingPassword = ref(false)

const contactForm = reactive({
  phone: '',
  email: ''
})

const passwordForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const avatarText = computed(() => {
  return (profile.realName || profile.username || 'A').slice(0, 1)
})

const contactRules = {
  phone: [
    {
      pattern: /^\d{11}$/,
      message: '手机号必须为 11 位数字',
      trigger: 'blur'
    }
  ],
  email: [
    {
      type: 'email',
      message: '邮箱格式不正确',
      trigger: 'blur'
    }
  ]
}

const validateConfirmPassword = (_rule, value, callback) => {
  if (!value) {
    callback(new Error('请再次输入新密码'))
    return
  }

  if (value !== passwordForm.newPassword) {
    callback(new Error('两次输入的新密码不一致'))
    return
  }

  callback()
}

const passwordRules = {
  oldPassword: [
    { required: true, message: '请输入原密码', trigger: 'blur' }
  ],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '新密码不能少于 6 位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

const fillProfile = (data) => {
  profile.userId = data.userId || data.user_id || ''
  profile.username = data.username || ''
  profile.realName = data.realName || data.real_name || ''
  profile.role = data.role || ''
  profile.adminRole = data.adminRole || data.admin_role || ''
  profile.airlineId = data.airlineId || data.airline_id || ''
  profile.airlineName = data.airlineName || data.airline_name || ''
  profile.phone = data.phone || ''
  profile.email = data.email || ''
  profile.status = data.status || ''
}

const syncStoredUser = () => {
  const stored = getStoredUser() || {}

  const merged = {
    ...stored,
    user_id: profile.userId || stored.user_id,
    username: profile.username,
    real_name: profile.realName,
    role: profile.role,
    admin_role: profile.adminRole,
    airline_id: profile.airlineId,
    airline_name: profile.airlineName,
    phone: profile.phone,
    email: profile.email,
    status: profile.status
  }

  localStorage.setItem('user', JSON.stringify(merged))
}

const loadProfile = async () => {
  try {
    const response = await api.get('/admin/profile')
    const data = response.data.data || {}

    fillProfile(data)
    syncStoredUser()
  } catch (error) {
    const stored = getStoredUser() || {}

    fillProfile(stored)
    ElMessage.warning(error.response?.data?.message || '个人信息接口暂不可用，已显示本地登录信息')
  }
}

const startEditContact = () => {
  contactForm.phone = profile.phone || ''
  contactForm.email = profile.email || ''
  editingContact.value = true
}

const cancelEditContact = () => {
  editingContact.value = false
  contactFormRef.value?.clearValidate()
}

const saveContact = async () => {
  if (!contactFormRef.value) return

  const valid = await contactFormRef.value.validate().catch(() => false)
  if (!valid) return

  savingContact.value = true

  try {
    const response = await api.put('/admin/profile/contact', {
      phone: contactForm.phone,
      email: contactForm.email
    })

    fillProfile(response.data.data || {})
    syncStoredUser()

    editingContact.value = false
    ElMessage.success('联系方式已更新')
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '联系方式更新失败')
  } finally {
    savingContact.value = false
  }
}

const openPasswordDialog = () => {
  passwordDialogVisible.value = true
}

const resetPasswordForm = () => {
  passwordForm.oldPassword = ''
  passwordForm.newPassword = ''
  passwordForm.confirmPassword = ''
  passwordFormRef.value?.clearValidate()
}

const savePassword = async () => {
  if (!passwordFormRef.value) return

  const valid = await passwordFormRef.value.validate().catch(() => false)
  if (!valid) return

  savingPassword.value = true

  try {
    await api.put('/admin/profile/password', {
      old_password: passwordForm.oldPassword,
      new_password: passwordForm.newPassword
    })

    ElMessage.success('密码已修改，请牢记新密码')
    passwordDialogVisible.value = false
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '密码修改失败')
  } finally {
    savingPassword.value = false
  }
}

onMounted(() => {
  loadProfile()
})
</script>

<style scoped>
.profile-layout {
  display: grid;
  grid-template-columns: 330px minmax(420px, 1fr);
  gap: 24px;
}

.profile-card,
.info-card {
  border-radius: 18px;
  background: #ffffff;
  border: 1px solid #e2e8f0;
}

.profile-card {
  padding: 34px 24px;
  text-align: center;
}

.avatar-circle {
  width: 88px;
  height: 88px;
  margin: 0 auto 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  color: #ffffff;
  background: #409eff;
  font-size: 38px;
  font-weight: 700;
}

.profile-card h2 {
  margin: 0 0 12px;
  color: #1e293b;
  font-size: 22px;
}

.profile-sub {
  margin: 18px 0 0;
  color: #64748b;
}

.password-button {
  margin-top: 24px;
  width: 160px;
}

.info-card {
  padding: 28px 30px;
}

.section-title {
  margin-bottom: 14px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #1e293b;
  font-size: 18px;
  font-weight: 700;
}

.contact-title {
  margin-top: 6px;
}

.info-row {
  min-height: 48px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #e2e8f0;
  color: #64748b;
}

.info-row strong {
  max-width: 65%;
  text-align: right;
  color: #1e293b;
  font-weight: 700;
  word-break: break-all;
}

.contact-form {
  max-width: 560px;
  margin-top: 10px;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

@media (max-width: 980px) {
  .profile-layout {
    grid-template-columns: 1fr;
  }
}
</style>

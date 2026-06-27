<template>
  <div class="mine-page" v-loading="loading">
    <div class="section-title">
      <span class="blue-line"></span>
      <span>个人中心 / 个人信息</span>
    </div>

    <section class="overview-grid">
      <article class="profile-card">
        <div class="profile-main">
          <el-avatar :size="96" class="profile-avatar">
            <el-icon><UserFilled /></el-icon>
          </el-avatar>
          <div class="profile-info">
            <div class="name-line">
              <h2>{{ userInfo.realName }}</h2>
              <el-tag type="primary" effect="plain">普通会员</el-tag>
            </div>
            <p>会员ID：{{ userInfo.memberId }}</p>
            <p>注册时间：{{ userInfo.createdAt }}</p>
            <div class="growth-row">
              <span>成长值：{{ userInfo.growth }} / 5000</span>
              <el-progress :percentage="growthPercent" :show-text="false" />
              <small>还需 {{ 5000 - userInfo.growth }} 成长值升级为银卡会员</small>
            </div>
          </div>
        </div>
      </article>

      <article
        v-for="item in statCards"
        :key="item.label"
        class="stat-card"
      >
        <div class="stat-icon" :class="item.color">
          <el-icon><component :is="item.icon" /></el-icon>
        </div>
        <span>{{ item.label }}</span>
        <strong>{{ item.value }}</strong>
        <small>{{ item.desc }}</small>
      </article>
    </section>

    <section class="content-grid">
      <article class="panel-card info-card">
        <div class="panel-title-row">
          <h3>个人信息</h3>
          <el-button plain type="primary" @click="editProfileVisible = true">
            <el-icon><Edit /></el-icon>
            编辑
          </el-button>
        </div>

        <div class="info-list">
          <div v-for="item in profileRows" :key="item.label" class="info-row">
            <div class="info-label">
              <el-icon><component :is="item.icon" /></el-icon>
              <span>{{ item.label }}</span>
            </div>
            <strong>{{ item.value }}</strong>
            <el-tag v-if="item.verified" type="success" size="small">已验证</el-tag>
          </div>
        </div>

        <div class="security-tip">
          <el-icon><Lock /></el-icon>
          为保障账户安全，请及时更新你的个人信息
        </div>
      </article>

      <article class="panel-card security-card">
        <h3>账户安全</h3>
        <div class="security-list">
          <div v-for="item in securityRows" :key="item.title" class="security-row">
            <div class="security-icon">
              <el-icon><component :is="item.icon" /></el-icon>
            </div>
            <div class="security-copy">
              <strong>{{ item.title }}</strong>
              <span>{{ item.desc }}</span>
            </div>
            <div class="security-value">{{ item.value }}</div>
            <el-button link type="primary" @click="handleSecurityAction(item)">
              {{ item.action }}
            </el-button>
          </div>
        </div>
      </article>

      <article class="panel-card passengers-card">
        <div class="panel-title-row">
          <h3>常用乘机人</h3>
          <el-button plain type="primary" @click="router.push('/passengers')">
            <el-icon><Management /></el-icon>
            管理
          </el-button>
        </div>

        <div class="mini-passenger-list">
          <div
          v-for="passenger in passengers"
            :key="passenger.passengerId"
            class="mini-passenger"
          >
            <el-avatar :size="32" class="mini-avatar">
              <el-icon><User /></el-icon>
            </el-avatar>
            <div class="mini-passenger-copy">
              <strong>{{ passenger.realName }}</strong>
              <span>身份证：{{ maskIdCard(passenger.idCard) }}</span>
              <span>手机号：{{ maskPhone(passenger.phone) }}</span>
            </div>
            <el-tag size="small" type="info">{{ passenger.type }}</el-tag>
          </div>
          <el-empty v-if="passengers.length === 0" description="暂无常用乘机人" />
        </div>

        <button type="button" class="add-passenger-link" @click="router.push('/passengers')">
          + 新增乘机人
        </button>
      </article>

      <article class="panel-card notice-card">
        <h3>通知设置</h3>
        <div class="notice-list">
          <div v-for="item in noticeSettings" :key="item.key" class="notice-row">
            <div class="notice-icon">
              <el-icon><component :is="item.icon" /></el-icon>
            </div>
            <div class="notice-copy">
              <strong>{{ item.title }}</strong>
              <span>{{ item.desc }}</span>
            </div>
            <el-switch v-model="item.enabled" />
          </div>
        </div>
      </article>
    </section>

    <el-dialog v-model="editProfileVisible" title="编辑个人信息" width="520px">
      <el-form :model="editForm" label-width="92px">
        <el-form-item label="姓名">
          <el-input v-model="editForm.realName" />
        </el-form-item>
        <el-form-item label="手机号码">
          <el-input v-model="editForm.phone" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="editForm.email" />
        </el-form-item>
        <el-form-item label="地址">
          <el-input v-model="editForm.address" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editProfileVisible = false">取消</el-button>
        <el-button type="primary" @click="saveProfile">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="passwordDialogVisible" title="修改登录密码" width="520px">
      <el-form :model="passwordForm" label-width="92px">
        <el-form-item label="原密码">
          <el-input
            v-model="passwordForm.oldPassword"
            type="password"
            show-password
            placeholder="请输入当前登录密码"
          />
        </el-form-item>
        <el-form-item label="新密码">
          <el-input
            v-model="passwordForm.newPassword"
            type="password"
            show-password
            placeholder="至少 8 位，建议包含大小写字母、数字或符号"
          />
          <div class="password-strength">
            <div class="strength-top">
              <span>密码强度</span>
              <strong :class="passwordStrength.level">{{ passwordStrength.text }}</strong>
            </div>
            <el-progress
              :percentage="passwordStrength.percent"
              :show-text="false"
              :class="['strength-progress', passwordStrength.level]"
            />
            <small>密码长度不少于 8 位，组合越复杂越安全。</small>
          </div>
        </el-form-item>
        <el-form-item label="确认密码">
          <el-input
            v-model="passwordForm.confirmPassword"
            type="password"
            show-password
            placeholder="请再次输入新密码"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="passwordDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitPasswordChange">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="phoneDialogVisible" title="修改手机号" width="480px">
      <el-form :model="phoneForm" label-width="92px">
        <el-form-item label="手机号">
          <el-input v-model="phoneForm.phone" maxlength="11" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="phoneDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitPhoneChange">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="emailDialogVisible" title="修改邮箱" width="480px">
      <el-form :model="emailForm" label-width="92px">
        <el-form-item label="邮箱">
          <el-input v-model="emailForm.email" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="emailDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitEmailChange">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="loginRecordsVisible" title="账户登录记录" width="620px">
      <el-table :data="loginRecords" style="width: 100%">
        <el-table-column prop="loginTime" label="登录时间" />
        <el-table-column prop="device" label="设备" />
        <el-table-column prop="location" label="地点" />
        <el-table-column prop="status" label="状态" />
      </el-table>
    </el-dialog>

  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Avatar,
  Bell,
  Calendar,
  CreditCard,
  Document,
  Edit,
  Files,
  Iphone,
  Location,
  Lock,
  Management,
  Message,
  Monitor,
  Promotion,
  Suitcase,
  Tickets,
  User,
  UserFilled,
  Wallet
} from '@element-plus/icons-vue'
import api from '../../api/index'
import { getPassengers } from '../../api/client/passenger'

const router = useRouter()
const loading = ref(false)
const editProfileVisible = ref(false)
const orders = ref([])
const historyOrders = ref([])
const passengers = ref([])

const userInfo = reactive({
  realName: '',
  memberId: '',
  createdAt: '',
  growth: 0,
  gender: '-',
  idCard: '',
  phone: '',
  email: '-',
  birthday: '-',
  country: '中国',
  address: '-'
})

const editForm = reactive({
  realName: '',
  phone: '',
  email: '',
  address: ''
})

const passwordDialogVisible = ref(false)
const phoneDialogVisible = ref(false)
const emailDialogVisible = ref(false)
const loginRecordsVisible = ref(false)

const passwordForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const phoneForm = reactive({
  phone: ''
})

const emailForm = reactive({
  email: ''
})

const loginRecords = ref([])

const passwordStrength = computed(() => {
  const value = passwordForm.newPassword || ''
  if (!value) {
    return {
      text: '请输入新密码',
      level: 'empty',
      percent: 0
    }
  }

  let score = 0
  if (value.length >= 8) score += 1
  if (/[A-Z]/.test(value)) score += 1
  if (/[a-z]/.test(value)) score += 1
  if (/\d/.test(value)) score += 1
  if (/[^A-Za-z0-9]/.test(value)) score += 1

  if (score <= 2) {
    return {
      text: '弱',
      level: 'weak',
      percent: 33
    }
  }

  if (score <= 4) {
    return {
      text: '中',
      level: 'medium',
      percent: 66
    }
  }

  return {
    text: '强',
    level: 'strong',
    percent: 100
  }
})

const growthPercent = computed(() => Math.round((userInfo.growth / 5000) * 100))

const completedFlightCount = computed(() => {
  return historyOrders.value.filter(order => {
    const status = order.orderStatus || order.status || ''
    return status === '已完成' || status === 'completed'
  }).length
})

const statCards = computed(() => [
  { label: '有效订单', value: orders.value.length, desc: '当前可操作订单', icon: Wallet, color: 'blue' },
  { label: '历史订单', value: historyOrders.value.length, desc: '历史记录', icon: Document, color: 'green' },
  { label: '常用乘机人', value: passengers.value.length, desc: '最多可添加 10 人', icon: User, color: 'orange' },
  { label: '累计飞行', value: `${completedFlightCount.value} 次`, desc: '已完成行程次数', icon: Promotion, color: 'purple' }
])

const profileRows = computed(() => [
  { label: '姓名', value: userInfo.realName, icon: User },
  { label: '性别', value: userInfo.gender, icon: Avatar },
  { label: '身份证号', value: userInfo.idCard, icon: CreditCard },
  { label: '手机号', value: userInfo.phone, icon: Iphone, verified: true },
  { label: '邮箱', value: userInfo.email, icon: Message, verified: true },
  { label: '出生日期', value: userInfo.birthday, icon: Calendar },
  { label: '国家/地区', value: userInfo.country, icon: Location },
  { label: '地址', value: userInfo.address, icon: Location }
])

const securityRows = computed(() => [
  {
    key: 'password',
    title: '登录密码',
    desc: '用于登录系统',
    value: '-',
    action: '修改',
    icon: Lock
  },
  {
    key: 'phone',
    title: '手机绑定',
    desc: '用于接收验证码及重要通知',
    value: maskPhone(userInfo.phone),
    action: '修改',
    icon: Iphone
  },
  {
    key: 'email',
    title: '邮箱绑定',
    desc: '用于接收行程及账单通知',
    value: userInfo.email || '-',
    action: '修改',
    icon: Message
  },
  {
    key: 'loginRecords',
    title: '账户登录记录',
    desc: '查看最近登录的设备与时间',
    value: '',
    action: '查看',
    icon: Monitor
  }
])

const noticeSettings = reactive([
  {
    key: 'trip',
    title: '行程提醒',
    desc: '航班起飞、值机、登机等行程提醒',
    icon: Suitcase,
    enabled: true
  },
  {
    key: 'flight',
    title: '航班动态提醒',
    desc: '航班延误、取消、变更等动态通知',
    icon: Bell,
    enabled: true
  },
  {
    key: 'order',
    title: '订单通知',
    desc: '订单支付成功、退票、改签等通知',
    icon: Files,
    enabled: true
  },
  {
    key: 'promo',
    title: '促销活动',
    desc: '特价机票、优惠活动等信息推送',
    icon: Tickets,
    enabled: true
  },
  {
    key: 'sms',
    title: '短信通知',
    desc: '重要通知通过短信发送',
    icon: Message,
    enabled: true
  }
])

const saveProfile = async () => {
  try {
    await api.put('/users/me/profile', {
      realName: editForm.realName,
      phone: editForm.phone,
      email: editForm.email
    })

    ElMessage.success('个人信息修改成功')
    editProfileVisible.value = false
    await loadMine()
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '个人信息修改失败')
  }
}

const submitPasswordChange = async () => {
  if (!passwordForm.oldPassword || !passwordForm.newPassword) {
    ElMessage.warning('请输入原密码和新密码')
    return
  }

  if (passwordForm.newPassword.length < 8) {
    ElMessage.warning('新密码不能少于 8 位')
    return
  }

  if (passwordForm.newPassword !== passwordForm.confirmPassword) {
    ElMessage.warning('两次输入的新密码不一致')
    return
  }

  try {
    await api.put('/users/me/password', {
      oldPassword: passwordForm.oldPassword,
      newPassword: passwordForm.newPassword
    })

    ElMessage.success('密码修改成功')
    passwordDialogVisible.value = false
    passwordForm.oldPassword = ''
    passwordForm.newPassword = ''
    passwordForm.confirmPassword = ''
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '密码修改失败')
  }
}

const submitPhoneChange = async () => {
  try {
    await api.put('/users/me/profile', {
      realName: userInfo.realName,
      phone: phoneForm.phone,
      email: userInfo.email
    })

    ElMessage.success('手机号修改成功')
    phoneDialogVisible.value = false
    await loadMine()
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '手机号修改失败')
  }
}

const submitEmailChange = async () => {
  try {
    await api.put('/users/me/profile', {
      realName: userInfo.realName,
      phone: userInfo.phone,
      email: emailForm.email
    })

    ElMessage.success('邮箱修改成功')
    emailDialogVisible.value = false
    await loadMine()
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '邮箱修改失败')
  }
}

const openLoginRecords = async () => {
  try {
    const response = await api.get('/users/me/login-records')
    loginRecords.value = response.data.data || []
    loginRecordsVisible.value = true
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '登录记录查询失败')
  }
}

const handleSecurityAction = (item) => {
  if (item.key === 'password') {
    passwordDialogVisible.value = true
    return
  }

  if (item.key === 'phone') {
    phoneForm.phone = userInfo.phone
    phoneDialogVisible.value = true
    return
  }

  if (item.key === 'email') {
    emailForm.email = userInfo.email
    emailDialogVisible.value = true
    return
  }

  if (item.key === 'loginRecords') {
    openLoginRecords()
  }
}

const getBirthdayFromIdCard = (idCard = '') => {
  if (idCard.length < 14) return '-'

  const value = idCard.slice(6, 14)
  return `${value.slice(0, 4)}-${value.slice(4, 6)}-${value.slice(6, 8)}`
}

const getGenderFromIdCard = (idCard = '') => {
  if (idCard.length < 17) return '-'
  return Number(idCard[16]) % 2 === 0 ? '女' : '男'
}

const getAge = (birthday) => {
  if (!birthday || birthday === '-') return 18
  const birthYear = Number(birthday.slice(0, 4))
  return new Date().getFullYear() - birthYear
}

const maskIdCard = (idCard = '') => {
  if (idCard.length < 10) return idCard || '-'
  return `${idCard.slice(0, 6)}********${idCard.slice(-4)}`
}

const maskPhone = (phone = '') => {
  if (phone.length !== 11) return phone || '-'
  return `${phone.slice(0, 3)}****${phone.slice(-4)}`
}

const normalizePassenger = (passenger) => {
  const birthday = getBirthdayFromIdCard(passenger.idCard)
  const age = getAge(birthday)

  return {
    ...passenger,
    type: age < 12 ? '儿童' : '成人'
  }
}

const loadMine = async () => {
  loading.value = true

  try {
    const [userRes, passengersRes, ordersRes, historyRes] = await Promise.all([
      api.get('/users/me'),
      getPassengers(),
      api.get('/orders'),
      api.get('/orders/history')
    ])

    const user = userRes.data.data || {}
    userInfo.realName = user.real_name || user.realName || user.username || ''
    userInfo.memberId = user.user_id || user.userId || ''
    userInfo.createdAt = user.createdAt || '-'
    userInfo.idCard = user.id_card || user.idCard || ''
    userInfo.phone = user.phone || ''
    userInfo.email = user.email || ''
    userInfo.birthday = getBirthdayFromIdCard(userInfo.idCard)
    userInfo.gender = getGenderFromIdCard(userInfo.idCard)

    editForm.realName = userInfo.realName
    editForm.phone = userInfo.phone
    editForm.email = userInfo.email
    editForm.address = userInfo.address

    passengers.value = (passengersRes.data.data || []).map(normalizePassenger)
    orders.value = ordersRes.data.data || []
    historyOrders.value = historyRes.data.data || []
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '个人中心数据加载失败')
    passengers.value = []
    orders.value = []
    historyOrders.value = []
    console.error(error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadMine()
})
</script>

<style scoped>
.mine-page {
  max-width: 1180px;
  margin: 0 auto;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 10px 0 24px;
  font-size: 20px;
  font-weight: 800;
  color: #0f172a;
}

.blue-line {
  width: 4px;
  height: 22px;
  border-radius: 2px;
  background: #0b7cff;
}

.overview-grid {
  display: grid;
  grid-template-columns: 1.35fr repeat(4, 1fr);
  gap: 12px;
}

.profile-card,
.stat-card,
.panel-card {
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.86);
  box-shadow: 0 10px 30px rgba(30, 93, 140, 0.08);
  backdrop-filter: blur(10px);
}

.profile-card {
  padding: 26px 28px;
}

.profile-main {
  display: flex;
  align-items: center;
  gap: 24px;
}

.profile-avatar {
  color: #0b7cff;
  background: #e0f2fe;
}

.profile-info {
  flex: 1;
}

.name-line {
  display: flex;
  align-items: center;
  gap: 10px;
}

.name-line h2 {
  margin: 0;
  color: #0f172a;
}

.profile-info p {
  margin: 10px 0;
  color: #334155;
  font-weight: 700;
}

.growth-row {
  display: flex;
  flex-direction: column;
  gap: 8px;
  color: #334155;
}

.growth-row small {
  color: #64748b;
}

.stat-card {
  min-height: 160px;
  padding: 22px 18px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.stat-icon.blue {
  color: #0b7cff;
  background: #dbeafe;
}

.stat-icon.green {
  color: #10b981;
  background: #d1fae5;
}

.stat-icon.orange {
  color: #f97316;
  background: #ffedd5;
}

.stat-icon.purple {
  color: #7c3aed;
  background: #ede9fe;
}

.stat-card span {
  color: #334155;
  font-weight: 800;
}

.stat-card strong {
  color: #0f172a;
  font-size: 30px;
  line-height: 1;
}

.stat-card small {
  color: #64748b;
}

.content-grid {
  margin-top: 22px;
  display: grid;
  grid-template-columns: 1fr 1.15fr;
  gap: 18px;
}

.panel-card {
  padding: 22px 24px;
}

.panel-card h3 {
  margin: 0;
  color: #0f172a;
  font-size: 20px;
}

.panel-title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 18px;
}

.info-list,
.security-list,
.notice-list {
  display: flex;
  flex-direction: column;
}

.info-row {
  min-height: 44px;
  display: grid;
  grid-template-columns: 150px 1fr 70px;
  align-items: center;
  border-bottom: 1px solid rgba(226, 232, 240, 0.9);
}

.info-label {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #64748b;
}

.info-label .el-icon {
  color: #0b66d8;
}

.info-row strong {
  color: #0f172a;
}

.security-tip {
  margin-top: 18px;
  padding: 14px 16px;
  border-radius: 8px;
  background: #f1f5f9;
  color: #475569;
  display: flex;
  align-items: center;
  gap: 8px;
}

.security-row,
.notice-row {
  min-height: 72px;
  display: grid;
  grid-template-columns: 42px 1fr auto auto;
  align-items: center;
  gap: 14px;
  border-bottom: 1px solid rgba(226, 232, 240, 0.9);
}

.security-icon,
.notice-icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #0b66d8;
  background: #eff6ff;
}

.security-copy,
.notice-copy {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.security-copy strong,
.notice-copy strong {
  color: #0f172a;
}

.security-copy span,
.notice-copy span,
.security-value {
  color: #64748b;
  font-size: 13px;
}

.mini-passenger-list {
  display: flex;
  flex-direction: column;
}

.mini-passenger {
  display: grid;
  grid-template-columns: 40px 1fr 120px 54px;
  align-items: center;
  gap: 12px;
  min-height: 54px;
  border-bottom: 1px solid rgba(226, 232, 240, 0.9);
}

.mini-avatar {
  color: #0b7cff;
  background: #eff6ff;
}

.mini-passenger div {
  display: flex;
  flex-direction: column;
}

.mini-passenger strong {
  color: #0f172a;
}

.mini-passenger span {
  color: #64748b;
  font-size: 13px;
}

.add-passenger-link {
  width: 100%;
  margin-top: 18px;
  border: 0;
  background: transparent;
  color: #0b7cff;
  font-weight: 800;
  cursor: pointer;
}

@media (max-width: 1200px) {
  .overview-grid,
  .content-grid {
    grid-template-columns: 1fr;
  }

  .stat-card {
    min-height: 120px;
  }
}

@media (max-width: 720px) {
  .profile-main,
  .name-line {
    flex-direction: column;
    align-items: flex-start;
  }

  .info-row,
  .security-row,
  .notice-row,
  .mini-passenger {
    grid-template-columns: 1fr;
    padding: 12px 0;
  }
}

/* ===== 个人中心页面整体重排优化 ===== */

.mine-page {
  max-width: 1180px;
  margin: 0 auto;
}

.section-title {
  margin-bottom: 22px;
}

.overview-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}

.profile-card {
  grid-column: 1 / -1;
  min-height: 170px;
  padding: 28px 34px;
}

.profile-main {
  height: 100%;
  display: flex;
  align-items: center;
  gap: 28px;
}

.profile-avatar {
  flex: 0 0 auto;
}

.profile-info {
  flex: 1;
  min-width: 0;
}

.name-line {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: nowrap;
}

.name-line h2 {
  margin: 0;
  font-size: 32px;
  line-height: 1.2;
  white-space: nowrap;
}

.profile-info p {
  margin: 8px 0;
  color: #475569;
  font-weight: 700;
}

.growth-row {
  max-width: 520px;
  margin-top: 12px;
}

.growth-row span,
.growth-row small {
  display: block;
  color: #64748b;
  line-height: 1.5;
}

.stat-card {
  min-height: 150px;
  padding: 22px 18px;
  justify-content: center;
}

.stat-card strong {
  font-size: 34px;
}

.stat-card small {
  text-align: center;
  line-height: 1.4;
}

.content-grid {
  margin-top: 18px;
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 18px;
  align-items: start;
}

.panel-card {
  min-width: 0;
  border-radius: 8px;
}

.info-card,
.security-card,
.passengers-card,
.notice-card {
  min-height: 300px;
}

.info-row {
  grid-template-columns: 140px minmax(0, 1fr) 70px;
}

.info-row strong {
  min-width: 0;
  word-break: break-all;
}

.security-row,
.notice-row {
  grid-template-columns: 42px minmax(0, 1fr) auto auto;
}

.security-copy,
.notice-copy {
  min-width: 0;
}

.security-copy span,
.notice-copy span,
.security-value {
  line-height: 1.45;
}

.mini-passenger {
  grid-template-columns: 40px minmax(0, 1fr) 110px 54px;
}

.mini-passenger div {
  min-width: 0;
}

.mini-passenger span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

@media (max-width: 1200px) {
  .overview-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .profile-card {
    grid-column: 1 / -1;
  }

  .content-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .overview-grid {
    grid-template-columns: 1fr;
  }

  .profile-main,
  .name-line {
    flex-direction: column;
    align-items: flex-start;
  }

  .info-row,
  .security-row,
  .notice-row,
  .mini-passenger {
    grid-template-columns: 1fr;
    padding: 12px 0;
  }
}


/* ===== 个人中心问题修复：统计、空白、安全入口、乘机人排版 ===== */

.stat-card {
  min-height: 132px;
  padding: 18px 16px;
}

.stat-card small {
  min-height: 20px;
}

.passengers-card,
.notice-card {
  min-height: auto;
}

.mini-passenger-list {
  min-height: 0;
}

.mini-passenger {
  grid-template-columns: 40px minmax(0, 1fr) 54px;
  align-items: center;
  min-height: 74px;
  gap: 12px;
}

.mini-passenger-copy {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.mini-passenger-copy strong {
  line-height: 1.25;
}

.mini-passenger-copy span {
  line-height: 1.35;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.add-passenger-link {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(226, 232, 240, 0.9);
}

.security-row .el-button.is-disabled {
  color: #94a3b8;
}


/* ===== 个人中心两列独立排列 + 隐藏未接入按钮 ===== */

.content-grid {
  margin-top: 18px;
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 18px;
  align-items: start;
}

.content-column {
  display: flex;
  flex-direction: column;
  gap: 18px;
  min-width: 0;
}

.security-row {
  grid-template-columns: 42px minmax(0, 1fr) auto;
}

.security-row .el-button {
  display: none;
}

.passengers-card,
.notice-card {
  min-height: auto;
}

@media (max-width: 1200px) {
  .content-grid {
    grid-template-columns: 1fr;
  }
}


/* ===== 恢复账户安全操作按钮 ===== */
.security-row .el-button {
  display: inline-flex;
}


/* ===== 个人中心安全功能接入样式 ===== */
.security-row .el-button {
  display: inline-flex;
}


/* ===== 账户安全按钮右对齐 + 密码强度提示 ===== */

.security-row {
  grid-template-columns: 42px minmax(0, 1fr) auto auto;
}

.security-row .el-button {
  display: inline-flex;
  justify-self: end;
  padding: 0;
  font-size: 15px;
  font-weight: 800;
}

.security-value {
  min-width: 88px;
  text-align: right;
}

.password-strength {
  width: 100%;
  margin-top: 10px;
}

.strength-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
  font-size: 13px;
  color: #64748b;
}

.strength-top strong.weak {
  color: #ef4444;
}

.strength-top strong.medium {
  color: #f59e0b;
}

.strength-top strong.strong {
  color: #10b981;
}

.strength-top strong.empty {
  color: #94a3b8;
}

.password-strength small {
  display: block;
  margin-top: 6px;
  color: #64748b;
  line-height: 1.5;
}

</style>

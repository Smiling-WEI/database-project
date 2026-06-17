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
            <div>
              <strong>{{ passenger.realName }}</strong>
              <span>身份证：{{ maskIdCard(passenger.idCard) }}</span>
            </div>
            <span>{{ maskPhone(passenger.phone) }}</span>
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

const growthPercent = computed(() => Math.round((userInfo.growth / 5000) * 100))

const statCards = computed(() => [
  { label: '我的订单', value: orders.value.length, desc: '有效订单', icon: Wallet, color: 'blue' },
  { label: '历史订单', value: historyOrders.value.length, desc: '历史记录', icon: Document, color: 'green' },
  { label: '常用乘机人', value: passengers.value.length, desc: '最多可添加 10 人', icon: User, color: 'orange' },
  { label: '累计飞行', value: `${historyOrders.value.length} 次`, desc: '后端暂未返回里程', icon: Promotion, color: 'purple' }
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
    title: '登录密码',
    desc: '用于登录系统',
    value: '-',
    action: '修改',
    actionPath: '/change-password',
    icon: Lock
  },
  {
    title: '手机绑定',
    desc: '用于接收验证码及重要通知',
    value: maskPhone(userInfo.phone),
    action: '修改',
    icon: Iphone
  },
  {
    title: '邮箱绑定',
    desc: '用于接收行程及账单通知',
    value: userInfo.email || '-',
    action: '修改',
    icon: Message
  },
  {
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

const saveProfile = () => {
  editProfileVisible.value = false
  ElMessage.info('后端暂未提供个人资料修改接口，当前无法保存')
}

const handleSecurityAction = (item) => {
  if (item.actionPath) {
    router.push(item.actionPath)
    return
  }
  ElMessage.info('该功能将在后续接入')
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
    userInfo.email = user.email || '-'
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
</style>

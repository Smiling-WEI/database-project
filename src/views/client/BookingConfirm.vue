<template>
  <div class="page-container" v-loading.fullscreen.lock="loading">
    <div class="page-actions-header">
      <el-button link class="back-btn" @click="goBack">
        <el-icon><ArrowLeft /></el-icon>
        返回航班选择
      </el-button>
      <h2 class="page-title">订单确认</h2>
    </div>

    <section class="flight-card">
      <div class="card-headline">确认航班行程 / Review trip</div>

      <div class="flight-review-content">
        <div class="airline-block">
          <div class="airline-logo" :class="flightInfo.airlineCode"></div>
          <span class="flight-no">{{ flightInfo.flightNo }}</span>
          <span class="airline-name">{{ flightInfo.airline }}</span>
          <el-tag size="small" type="primary" class="cabin-tag">
            {{ flightInfo.cabinName }}
          </el-tag>
        </div>

        <div class="route-timeline-wrapper">
          <div class="timeline-city">
            <div class="city-code">{{ flightInfo.depAirportCode }}</div>
            <div class="city-name">{{ flightInfo.depCity }}</div>
            <div class="terminal">{{ flightInfo.depAirport }}</div>
          </div>

          <div class="timeline-graphic">
            <div class="duration-time">{{ flightInfo.duration }}</div>
            <div class="graphic-line">
              <i class="dot start-dot"></i>
              <span class="line"></span>
              <el-icon class="arrow-icon"><Right /></el-icon>
              <i class="dot end-dot"></i>
            </div>
            <div class="stop-info">直飞 / Non-stop</div>
          </div>

          <div class="timeline-city text-right">
            <div class="city-code">{{ flightInfo.arrAirportCode }}</div>
            <div class="city-name">{{ flightInfo.arrCity }}</div>
            <div class="terminal">{{ flightInfo.arrAirport }}</div>
          </div>
        </div>

        <div class="time-data-row">
          <div class="exact-time-block">
            <div class="exact-time">{{ flightInfo.depTime }}</div>
            <div class="exact-date">{{ flightInfo.formattedDate }}</div>
          </div>
          <el-divider direction="vertical" class="time-divider" />
          <div class="exact-time-block text-right">
            <div class="exact-time">{{ flightInfo.arrTime }}</div>
            <div class="exact-date">{{ flightInfo.formattedDate }}</div>
          </div>
        </div>
      </div>
    </section>

    <section class="table-card">
      <div class="card-header flex-between">
        <span class="section-title">乘机人信息</span>
        <el-button type="primary" plain @click="showAddDialog = true">
          <el-icon><Plus /></el-icon>
          新增乘机人
        </el-button>
      </div>

      <div v-if="frequentContacts.length > 0" class="frequent-contacts-bar">
        <span class="fc-label">常用乘机人：</span>
        <div class="fc-list">
          <button
            v-for="contact in frequentContacts"
            :key="contact.passengerId"
            type="button"
            class="fc-tag"
            :class="{ 'is-active': selectedIds.includes(contact.passengerId) }"
            @click="togglePassenger(contact.passengerId)"
          >
            {{ contact.realName }}
            <el-icon v-if="selectedIds.includes(contact.passengerId)" class="check-icon">
              <Check />
            </el-icon>
          </button>
        </div>
      </div>

      <el-table
        :data="selectedPassengers"
        stripe
        border
        style="width: 100%"
        empty-text="请从上方选择乘机人，或点击右上角新增"
      >
        <el-table-column label="姓名" width="150">
          <template #default="{ row }">
            {{ row.realName }}
            <el-tag size="small" type="info" class="adult-tag">成人</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="证件类型" width="120">
          <template #default>身份证</template>
        </el-table-column>
        <el-table-column prop="idCard" label="证件号码" min-width="220" />
        <el-table-column prop="phone" label="手机号码" min-width="140" />
        <el-table-column label="操作" width="100" align="center" fixed="right">
          <template #default="{ row }">
            <el-button type="danger" link @click="togglePassenger(row.passengerId)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </section>

    <div class="bottom-action-bar">
      <div class="bar-content">
        <div class="price-details">
          <span class="label">应付总额：</span>
          <span class="currency">¥</span>
          <span class="total-price">{{ totalPrice.toFixed(2) }}</span>
          <span v-if="selectedPassengers.length > 0" class="price-desc">
            机票 ¥{{ flightInfo.price }} x {{ selectedPassengers.length }} 人
          </span>
        </div>
        <el-button
          type="primary"
          size="large"
          class="pay-btn"
          :loading="submitting"
          :disabled="selectedPassengers.length === 0 || !flightInfo.pricingId"
          @click="handleSubmitOrder"
        >
          支付
        </el-button>
      </div>
    </div>

    <el-dialog
      v-model="showAddDialog"
      title="新增乘机人"
      width="500px"
      @closed="resetForm"
    >
      <el-form ref="formRef" :model="passengerForm" :rules="rules" label-width="100px">
        <el-form-item label="姓名" prop="realName">
          <el-input v-model="passengerForm.realName" placeholder="请输入真实姓名" />
        </el-form-item>
        <el-form-item label="证件号码" prop="idCard">
          <el-input v-model="passengerForm.idCard" placeholder="请输入身份证号码" />
        </el-form-item>
        <el-form-item label="手机号码" prop="phone">
          <el-input v-model="passengerForm.phone" placeholder="请输入手机号码" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" :loading="savingPassenger" @click="handleSavePassenger">
          保存并选中
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Plus, Check, Right } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getFlightCabins } from '../../api/client/flight'
import { getMyPassengers, addPassenger } from '../../api/client/user'
import { createTicketOrder } from '../../api/client/order'

const route = useRoute()
const router = useRouter()
const formRef = ref()

const loading = ref(false)
const submitting = ref(false)
const savingPassenger = ref(false)
const showAddDialog = ref(false)

const instanceId = computed(() => Number(route.query.instanceId))

const airportMeta = {
  '首都机场 T3': { code: 'PEK', city: '北京' },
  '首都机场 T2': { code: 'PEK', city: '北京' },
  '虹桥机场 T2': { code: 'SHA', city: '上海' },
  '浦东机场 T1': { code: 'PVG', city: '上海' },
  '白云机场 T2': { code: 'CAN', city: '广州' },
  '宝安机场 T3': { code: 'SZX', city: '深圳' },
  '天府机场 T2': { code: 'TFU', city: '成都' }
}

const getAirportMeta = (airport, fallbackCode, fallbackCity) => {
  return airportMeta[airport] || { code: fallbackCode, city: fallbackCity }
}

const calcDuration = (depTime, arrTime) => {
  const [depHour, depMinute] = depTime.split(':').map(Number)
  const [arrHour, arrMinute] = arrTime.split(':').map(Number)
  let minutes = arrHour * 60 + arrMinute - (depHour * 60 + depMinute)

  if (Number.isNaN(minutes)) return '-'
  if (minutes < 0) minutes += 24 * 60

  return `${Math.floor(minutes / 60)}h ${minutes % 60}m`
}

const flightInfo = ref({
  instanceId: '',
  pricingId: null,
  flightNo: '',
  airline: '',
  airlineCode: '',
  cabinName: '',
  price: 0,
  depAirportCode: '-',
  depCity: '-',
  depAirport: '',
  arrAirportCode: '-',
  arrCity: '-',
  arrAirport: '',
  depTime: '--:--',
  arrTime: '--:--',
  duration: '-',
  formattedDate: ''
})

const frequentContacts = ref([])
const selectedIds = ref([])

const selectedPassengers = computed(() => {
  return frequentContacts.value.filter(contact =>
    selectedIds.value.includes(contact.passengerId)
  )
})

const totalPrice = computed(() => {
  return Number(flightInfo.value.price || 0) * selectedPassengers.value.length
})

const passengerForm = reactive({
  realName: '',
  idCard: '',
  phone: ''
})

const rules = {
  realName: [{ required: true, message: '请输入真实姓名', trigger: 'blur' }],
  idCard: [
    { required: true, message: '请输入身份证号码', trigger: 'blur' },
    { min: 18, max: 18, message: '身份证号码应为 18 位', trigger: 'blur' }
  ],
  phone: [
    { required: true, message: '请输入手机号码', trigger: 'blur' },
    { pattern: /^1\d{10}$/, message: '请输入 11 位手机号码', trigger: 'blur' }
  ]
}

const initFlightInfoFromRoute = () => {
  const depAirport = String(route.query.depAirport || '')
  const arrAirport = String(route.query.arrAirport || '')
  const depMeta = getAirportMeta(depAirport, '-', '-')
  const arrMeta = getAirportMeta(arrAirport, '-', '-')
  const depTime = String(route.query.depTime || '--:--')
  const arrTime = String(route.query.arrTime || '--:--')

  flightInfo.value = {
    ...flightInfo.value,
    instanceId: instanceId.value,
    pricingId: Number(route.query.pricingId) || null,
    flightNo: String(route.query.flightNo || ''),
    airline: String(route.query.airline || ''),
    airlineCode: String(route.query.airlineCode || ''),
    cabinName: String(route.query.cabinName || ''),
    price: Number(route.query.price) || 0,
    depAirportCode: depMeta.code,
    depCity: depMeta.city,
    depAirport,
    arrAirportCode: arrMeta.code,
    arrCity: arrMeta.city,
    arrAirport,
    depTime,
    arrTime,
    duration: calcDuration(depTime, arrTime),
    formattedDate: String(route.query.date || '')
  }
}

const hasRequiredFlightInfo = () => {
  return Boolean(
    instanceId.value &&
      route.query.flightNo &&
      route.query.cabinName &&
      route.query.depAirport &&
      route.query.arrAirport &&
      route.query.date
  )
}

const loadData = async () => {
  if (!hasRequiredFlightInfo()) {
    ElMessage.warning('缺少航班参数，请重新选择航班')
    router.push('/home')
    return
  }

  initFlightInfoFromRoute()
  loading.value = true

  try {
    const [passengerRes, cabinRes] = await Promise.all([
      getMyPassengers(),
      getFlightCabins(instanceId.value)
    ])

    frequentContacts.value = passengerRes.data.data || []

    const cabins = cabinRes.data.data || []
    const targetCabin = cabins.find(c => c.cabinType === flightInfo.value.cabinName)

    if (targetCabin) {
      flightInfo.value.pricingId = targetCabin.pricingId
      flightInfo.value.price = Number(targetCabin.price)
    } else if (!flightInfo.value.pricingId) {
      ElMessage.warning('当前舱位暂无有效价格，请重新选择航班')
    }
  } catch (error) {
    frequentContacts.value = []
    ElMessage.error(error.response?.data?.message || '加载真实数据失败，请稍后重试')
    console.error(error)
  } finally {
    loading.value = false
  }
}

const togglePassenger = (id) => {
  const index = selectedIds.value.indexOf(id)

  if (index > -1) {
    selectedIds.value.splice(index, 1)
  } else {
    selectedIds.value.push(id)
  }
}

const resetForm = () => {
  passengerForm.realName = ''
  passengerForm.idCard = ''
  passengerForm.phone = ''
  formRef.value?.clearValidate()
}

const handleSavePassenger = async () => {
  if (!formRef.value) return

  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  savingPassenger.value = true

  try {
    const res = await addPassenger(passengerForm)
    const newPassenger = {
      passengerId: res.data.data.passengerId,
      realName: passengerForm.realName,
      idCard: passengerForm.idCard,
      phone: passengerForm.phone
    }

    frequentContacts.value.push(newPassenger)
    selectedIds.value.push(newPassenger.passengerId)
    ElMessage.success('乘机人添加成功')
    showAddDialog.value = false
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '添加乘机人失败')
  } finally {
    savingPassenger.value = false
  }
}

const handleSubmitOrder = async () => {
  if (selectedIds.value.length === 0) return

  if (!flightInfo.value.pricingId) {
    ElMessage.warning('缺少真实舱位价格编号，请重新选择航班')
    return
  }

  try {
    await ElMessageBox.confirm(
      `即将支付 ¥${totalPrice.value.toFixed(2)}，确认预订吗？`,
      '确认支付',
      {
        confirmButtonText: '确认支付',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    submitting.value = true

    await Promise.all(
      selectedIds.value.map(passengerId =>
        createTicketOrder({
          passengerId,
          pricingId: flightInfo.value.pricingId
        })
      )
    )

    ElMessage.success('购票成功')
    router.push('/orders')
  } catch (error) {
    if (error === 'cancel' || error === 'close') return
    ElMessage.error(error.response?.data?.message || '购票失败，可能余票不足或乘机人已购票')
    console.error(error)
  } finally {
    submitting.value = false
  }
}

const goBack = () => {
  router.push('/home')
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.page-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding-bottom: 100px;
}

.page-actions-header {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 10px;
}

.back-btn {
  font-size: 16px;
  color: #1890ff;
}

.page-title {
  font-size: 20px;
  color: #1e293b;
  margin: 0;
  font-weight: bold;
}

.flight-card,
.table-card {
  padding: 30px 32px;
  border-radius: 8px;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.02);
}

.card-headline {
  font-size: 13px;
  color: #94a3b8;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 25px;
}

.flight-review-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.airline-block {
  display: flex;
  align-items: center;
  gap: 10px;
}

.airline-logo {
  width: 24px;
  height: 24px;
  border-radius: 4px;
}

.CA {
  background-color: #e11d48;
}

.MU {
  background-color: #0284c7;
}

.flight-no {
  font-size: 15px;
  font-weight: bold;
  color: #1e293b;
}

.airline-name {
  font-size: 14px;
  color: #475569;
}

.cabin-tag {
  margin-left: 8px;
}

.route-timeline-wrapper {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin: 10px 0;
}

.timeline-city {
  display: flex;
  flex-direction: column;
  flex: 1;
}

.city-code {
  font-size: 36px;
  font-weight: 900;
  color: #1e293b;
  font-family: Arial, sans-serif;
}

.city-name {
  font-size: 16px;
  font-weight: 500;
  color: #475569;
  margin-top: 2px;
}

.terminal {
  font-size: 13px;
  color: #94a3b8;
  margin-top: 2px;
}

.timeline-graphic {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1.5;
  padding: 0 15px;
}

.duration-time {
  font-size: 13px;
  color: #64748b;
  font-weight: 600;
  margin-bottom: 8px;
}

.graphic-line {
  display: flex;
  align-items: center;
  width: 100%;
  position: relative;
  height: 14px;
}

.line {
  flex-grow: 1;
  height: 2px;
  background-color: #cbd5e1;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  border: 2px solid #cbd5e1;
  background-color: #ffffff;
}

.start-dot {
  margin-right: -2px;
}

.end-dot {
  margin-left: -2px;
}

.arrow-icon {
  position: absolute;
  left: calc(50% - 10px);
  color: #94a3b8;
  background-color: #ffffff;
  padding: 0 5px;
}

.stop-info {
  margin-top: 8px;
  font-size: 12px;
  color: #94a3b8;
  font-weight: bold;
}

.time-data-row {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  margin-top: 5px;
  border-top: 1px solid #f1f5f9;
  padding-top: 20px;
}

.exact-time-block {
  display: flex;
  flex-direction: column;
}

.exact-time {
  font-size: 26px;
  font-weight: bold;
  color: #1e293b;
}

.exact-date {
  font-size: 14px;
  color: #64748b;
  margin-top: 2px;
}

.time-divider {
  height: 40px;
  margin: 0 60px;
  border-color: #e2e8f0;
}

.text-right {
  text-align: right;
}

.card-header {
  margin-bottom: 20px;
}

.flex-between {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.section-title {
  font-size: 18px;
  font-weight: bold;
  color: #1e293b;
}

.frequent-contacts-bar {
  display: flex;
  align-items: center;
  margin-bottom: 24px;
  padding: 16px 20px;
  background-color: #f8fafc;
  border-radius: 8px;
  border: 1px dashed #cbd5e1;
}

.fc-label {
  font-size: 14px;
  color: #64748b;
  margin-right: 16px;
  white-space: nowrap;
}

.fc-list {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.fc-tag {
  border: 1px solid #cbd5e1;
  background-color: #ffffff;
  color: #475569;
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s ease;
  user-select: none;
  padding: 8px 20px;
  border-radius: 20px;
}

.fc-tag:hover {
  border-color: #1890ff;
  color: #1890ff;
}

.fc-tag.is-active {
  background-color: #e6f7ff;
  border-color: #1890ff;
  color: #1890ff;
  font-weight: bold;
}

.check-icon {
  font-size: 14px;
  font-weight: bold;
}

.adult-tag {
  margin-left: 5px;
}

:deep(.el-table) {
  border-radius: 8px;
  overflow: hidden;
}

:deep(.el-table th.el-table__cell) {
  background: #f8fafc;
  color: #334155;
  font-weight: 600;
}

.bottom-action-bar {
  position: fixed;
  bottom: 0;
  left: 220px;
  right: 0;
  height: 80px;
  background-color: #ffffff;
  box-shadow: 0 -4px 16px rgba(0, 0, 0, 0.05);
  display: flex;
  align-items: center;
  z-index: 100;
}

.bar-content {
  width: 100%;
  padding: 0 40px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.price-details {
  display: flex;
  align-items: baseline;
}

.label {
  font-size: 16px;
  color: #1e293b;
  font-weight: bold;
}

.currency {
  font-size: 18px;
  color: #ea580c;
  font-weight: bold;
  margin-right: 4px;
}

.total-price {
  font-size: 32px;
  color: #ea580c;
  font-weight: bold;
}

.price-desc {
  font-size: 13px;
  color: #94a3b8;
  margin-left: 12px;
}

.pay-btn {
  width: 180px;
  font-size: 16px;
  font-weight: bold;
  border-radius: 8px;
}
</style>

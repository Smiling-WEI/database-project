<template>
  <div class="detail-page" v-loading="loading">
    <div class="page-title-row">
      <el-button link class="back-btn" @click="router.back()">
        <el-icon><ArrowLeft /></el-icon>
        返回
      </el-button>
      <h2>订单详情</h2>
    </div>

    <section class="panel order-summary">
      <div class="summary-grid">
        <div class="summary-item">
          <span>订单状态</span>
          <strong class="success-text">{{ statusText(order.orderStatus) }} <el-icon><CircleCheckFilled /></el-icon></strong>
        </div>
        <div class="summary-item">
          <span>订单编号</span>
          <strong>{{ order.orderNo }}</strong>
        </div>
        <div class="summary-item">
          <span>下单时间</span>
          <strong>{{ order.purchaseTime || '-' }}</strong>
        </div>
        <div class="summary-item">
          <span>支付方式</span>
          <strong>-</strong>
        </div>
        <div class="summary-item">
          <span>支付时间</span>
          <strong>{{ order.purchaseTime || '-' }}</strong>
        </div>
        <div class="summary-item">
          <span>应付金额</span>
          <strong class="price-text">¥{{ order.price }}</strong>
        </div>
      </div>
      <div class="summary-actions">
        <el-button type="danger" plain @click="goBackOrders">退票</el-button>
        <el-button plain type="primary" @click="goChange">改签</el-button>
        <el-button plain type="primary" disabled>发票</el-button>
      </div>
    </section>

    <section v-if="order.orderId" class="panel">
      <h3>航班信息</h3>
      <div class="flight-info">
        <div class="airline-block">
          <span class="airline-logo" :class="order.airlineCode"></span>
          <div>
            <strong>{{ order.airlineName }} {{ order.flightNo }}</strong>
            <p>{{ order.aircraftModel || '-' }} | {{ order.cabinType || '-' }}</p>
          </div>
        </div>

        <div class="route-block">
          <div class="route-city">
            <strong>{{ order.depAirport || '-' }}</strong>
            <span class="flight-time">{{ order.depTime }}</span>
            <span>{{ order.flightDate || '-' }}</span>
          </div>
          <div class="route-line">
            <span>{{ order.duration }}</span>
            <i></i>
            <strong>直飞</strong>
          </div>
          <div class="route-city right">
            <strong>{{ order.arrAirport || '-' }}</strong>
            <span class="flight-time">{{ order.arrTime }}</span>
            <span>{{ order.flightDate || '-' }}</span>
          </div>
        </div>

        <div class="flight-extra">
          <div><span>舱位等级</span><strong>{{ order.cabinType || '-' }}</strong></div>
          <div><span>机票价格</span><strong>¥{{ order.price }}</strong></div>
          <div><span>餐食</span><strong>-</strong></div>
          <div><span>行李额度</span><strong>-</strong></div>
          <div><span>座位号</span><strong>{{ order.seatNo || '-' }}</strong></div>
        </div>
      </div>
    </section>

    <section class="panel">
      <h3>乘机人信息</h3>
      <el-table :data="order.orderId ? [order.passenger] : []" style="width: 100%">
        <el-table-column prop="name" label="乘机人" />
        <el-table-column label="证件类型">
          <template #default>身份证</template>
        </el-table-column>
        <el-table-column prop="idCard" label="证件号码" />
        <el-table-column prop="phone" label="手机号" />
        <el-table-column prop="ticketNo" label="票号" />
      </el-table>
    </section>

    <section class="panel contact-panel">
      <h3>联系人信息</h3>
      <div><span>联系人</span><strong>{{ order.passenger.name || '-' }}</strong></div>
      <div><span>手机号码</span><strong>{{ maskPhone(order.passenger.phone) }}</strong></div>
      <div><span>电子邮箱</span><strong>-</strong></div>
    </section>

    <section class="panel">
      <h3>订单操作记录</h3>
      <el-steps :active="2" finish-status="success" align-center>
        <el-step title="提交订单" :description="order.purchaseTime || '-'" />
        <el-step title="支付成功" :description="order.purchaseTime || '-'" />
        <el-step title="出票成功" :description="statusText(order.orderStatus)" />
      </el-steps>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, CircleCheckFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import api from '../../api/index'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const orderId = computed(() => Number(route.query.orderId))

const order = ref({
  orderId: null,
  orderNo: '',
  orderStatus: '',
  purchaseTime: '',
  price: 0,
  airlineCode: '',
  airlineName: '',
  flightNo: '',
  aircraftModel: '',
  flightDate: '',
  depAirport: '',
  arrAirport: '',
  depTime: '--:--',
  arrTime: '--:--',
  duration: '-',
  cabinType: '',
  seatNo: '',
  passenger: {
    name: '',
    idCard: '',
    phone: '',
    ticketNo: '-'
  }
})

const formatTime = (value) => {
  if (!value) return '--:--'

  const text = String(value)
  const match = text.match(/(\d{2}):(\d{2})/)

  return match ? `${match[1]}:${match[2]}` : text
}

const calcDuration = (depTime, arrTime) => {
  if (!depTime || !arrTime || depTime === '--:--' || arrTime === '--:--') return '-'

  const [depHour, depMinute] = depTime.split(':').map(Number)
  const [arrHour, arrMinute] = arrTime.split(':').map(Number)
  let minutes = arrHour * 60 + arrMinute - (depHour * 60 + depMinute)

  if (Number.isNaN(minutes)) return '-'
  if (minutes < 0) minutes += 24 * 60

  return `${Math.floor(minutes / 60)}h${minutes % 60}m`
}

const normalizeOrder = (data) => {
  const depTime = formatTime(data.depTime)
  const arrTime = formatTime(data.arrTime)

  return {
    orderId: data.orderId,
    orderNo: data.orderNo || `OD${data.orderId}`,
    orderStatus: data.orderStatus || '',
    purchaseTime: data.purchaseTime || '',
    price: Number(data.price || 0),
    airlineCode: data.airlineCode || '',
    airlineName: data.airlineName || '-',
    flightNo: data.flightNo || '-',
    aircraftModel: data.aircraftModel || '',
    flightDate: data.flightDate || '',
    depAirport: data.depAirport || '',
    arrAirport: data.arrAirport || '',
    depTime,
    arrTime,
    duration: data.duration || calcDuration(depTime, arrTime),
    cabinType: data.cabinType || '',
    seatNo: data.seatNo || '',
    passenger: {
      name: data.passengerName || '',
      idCard: data.passengerIdCard || '',
      phone: data.passengerPhone || '',
      ticketNo: data.ticketNo || '-'
    }
  }
}

const loadOrder = async () => {
  if (!orderId.value) {
    ElMessage.warning('缺少订单编号')
    router.push('/orders')
    return
  }

  loading.value = true

  try {
    const response = await api.get(`/orders/${orderId.value}`)
    order.value = normalizeOrder(response.data.data || {})
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '订单详情查询失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

const statusText = (status) => {
  const statusMap = {
    '已支付': '已出票',
    '已出票': '已出票',
    '已完成': '已完成',
    '已退票': '已退票',
    '已取消': '已取消',
    '已改签': '已改签'
  }

  return statusMap[status] || status || '-'
}

const maskPhone = (phone = '') => {
  if (phone.length !== 11) return phone || '-'
  return `${phone.slice(0, 3)}****${phone.slice(-4)}`
}

const goChange = () => {
  router.push({
    path: '/change',
    query: { orderId: order.value.orderId }
  })
}

const goBackOrders = () => {
  router.push('/orders')
}

onMounted(() => {
  loadOrder()
})
</script>

<style scoped>
.detail-page {
  max-width: 1180px;
  margin: 0 auto;
}

.page-title-row {
  display: flex;
  align-items: center;
  gap: 22px;
  margin-bottom: 22px;
}

.back-btn {
  color: #0b7cff;
  font-size: 18px;
  font-weight: 800;
}

.page-title-row h2,
.panel h3 {
  margin: 0;
  color: #0f172a;
}

.panel {
  margin-bottom: 12px;
  padding: 26px 28px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.88);
  box-shadow: 0 10px 30px rgba(30, 93, 140, 0.08);
}

.order-summary {
  position: relative;
}

.summary-grid {
  width: 70%;
  display: grid;
  grid-template-columns: repeat(2, minmax(220px, 1fr));
  gap: 24px 90px;
}

.summary-item,
.flight-extra div,
.contact-panel div {
  display: grid;
  grid-template-columns: 90px 1fr;
  gap: 18px;
  align-items: center;
}

.summary-item span,
.flight-extra span,
.contact-panel span {
  color: #475569;
}

.summary-item strong {
  color: #0f172a;
}

.success-text {
  color: #10b981 !important;
  font-size: 22px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.pay-method {
  display: flex;
  align-items: center;
  gap: 8px;
}

.pay-icon {
  width: 24px;
  height: 24px;
  border-radius: 6px;
  background: #1677ff;
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.price-text {
  color: #ef233c !important;
  font-size: 18px;
}

.summary-actions {
  position: absolute;
  top: 24px;
  right: 28px;
  display: flex;
  gap: 12px;
}

.flight-info {
  margin-top: 28px;
  display: grid;
  grid-template-columns: 230px 1fr 230px;
  gap: 32px;
  align-items: center;
}

.airline-block {
  display: flex;
  align-items: center;
  gap: 16px;
}

.airline-logo {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  display: inline-block;
}

.CA {
  background: #e11d48;
}

.airline-block p {
  margin: 8px 0 0;
  color: #475569;
}

.route-block {
  display: grid;
  grid-template-columns: 1fr 130px 1fr;
  gap: 24px;
  align-items: center;
}

.route-city {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.route-city.right {
  text-align: right;
}

.flight-time {
  font-size: 30px;
  font-weight: 900;
  color: #0f172a;
}

.route-line {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: #475569;
}

.route-line i {
  width: 120px;
  height: 1px;
  background: #cbd5e1;
}

.flight-extra {
  padding-left: 28px;
  border-left: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.contact-panel {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 28px;
}

.contact-panel h3 {
  grid-column: 1 / -1;
}

@media (max-width: 1000px) {
  .summary-grid,
  .flight-info,
  .route-block,
  .contact-panel {
    width: 100%;
    grid-template-columns: 1fr;
  }

  .summary-actions {
    position: static;
    margin-top: 22px;
  }
}
</style>

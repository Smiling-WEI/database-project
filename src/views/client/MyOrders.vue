<template>
  <div class="orders-page">
    <section class="filter-panel">
      <div class="section-title">
        <span class="blue-line"></span>
        <span>我的订单</span>
      </div>

      <el-tabs v-model="activeTab" class="order-tabs">
        <el-tab-pane label="有效订单" name="active" />
        <el-tab-pane label="历史订单" name="history" />
      </el-tabs>

      <div class="filter-row">
        <div class="filter-item">
          <span class="filter-label">出发日期</span>
          <el-date-picker
            v-model="filters.dateRange"
            type="daterange"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            range-separator="-"
            size="large"
            value-format="YYYY-MM-DD"
            class="date-range"
          />
        </div>

        <div class="filter-item">
          <span class="filter-label">航班号</span>
          <el-input
            v-model="filters.flightNo"
            placeholder="请输入航班号"
            size="large"
            clearable
            class="filter-input"
          />
        </div>

        <div class="filter-item">
          <span class="filter-label">航空公司</span>
          <el-select
            v-model="filters.airline"
            placeholder="全部航空公司"
            size="large"
            class="filter-input"
          >
            <el-option label="全部航空公司" value="" />
            <el-option
              v-for="airline in airlineOptions"
              :key="airline"
              :label="airline"
              :value="airline"
            />
          </el-select>
        </div>

        <div class="filter-item">
          <span class="filter-label">订单状态</span>
          <el-select
            v-model="filters.status"
            placeholder="全部状态"
            size="large"
            class="filter-input"
          >
            <el-option label="全部状态" value="" />
            <el-option label="已出票" value="已出票" />
            <el-option label="未值机" value="未值机" />
            <el-option label="已值机" value="已值机" />
            <el-option label="已完成" value="已完成" />
            <el-option label="已退票" value="已退票" />
          </el-select>
        </div>

        <div class="filter-actions">
          <el-button type="primary" size="large" @click="applyFilters">查询</el-button>
          <el-button size="large" @click="resetFilters">重置</el-button>
        </div>
      </div>
    </section>

    <div class="list-header">
      <h3>{{ activeTab === 'active' ? '有效订单' : '历史订单' }}（{{ visibleOrders.length }}）</h3>
      <el-select v-model="sortMode" size="large" class="sort-select">
        <el-option label="按出发时间倒序" value="flightDateDesc" />
        <el-option label="按下单时间倒序" value="purchaseTimeDesc" />
      </el-select>
    </div>

    <div v-loading="loading" class="order-list">
      <el-empty v-if="visibleOrders.length === 0" description="暂无订单" />

      <article
        v-for="order in visibleOrders"
        :key="order.orderId"
        class="order-card"
      >
        <div class="order-card-top">
          <div class="order-meta">
            <strong>订单号：{{ order.orderNo || `OD${order.orderId}` }}</strong>
            <el-tag :type="statusType(order.orderStatus)" size="small">
              {{ statusText(order.orderStatus) }}
            </el-tag>
          </div>
          <div class="order-time">
            {{ activeTab === 'active' ? '下单时间' : '订单完成时间' }}：
            {{ order.purchaseTime || '-' }}
          </div>
          <div class="order-amount">
            订单金额：
            <strong>¥{{ order.price }}</strong>
          </div>
        </div>

        <div class="order-card-body">
          <div class="flight-summary">
            <div class="airline-line">
              <span class="airline-logo" :class="order.airlineCode"></span>
              <strong>{{ order.airlineName }}</strong>
              <span>{{ order.flightNo }}</span>
            </div>
            <div class="rule-link">{{ order.cabinType }}　退改签规则</div>
          </div>

          <div class="route-block">
            <div class="route-city">
              <div class="airport">{{ order.depAirport }}</div>
              <div class="time">{{ order.depTime }}</div>
              <div class="date">{{ order.flightDate }}</div>
            </div>

            <div class="route-line">
              <span>{{ order.duration }}</span>
              <i></i>
              <strong>直飞</strong>
            </div>

            <div class="route-city right">
              <div class="airport">{{ order.arrAirport }}</div>
              <div class="time">{{ order.arrTime }}</div>
              <div class="date">{{ order.flightDate }}</div>
            </div>
          </div>

          <div class="passenger-block">
            <span class="small-label">乘机人</span>
            <strong>{{ order.passengerName }}</strong>
            <span>身份证 {{ maskIdCard(order.passengerIdCard) }}</span>
          </div>

          <div class="seat-block">
            <span class="small-label">座位号</span>
            <strong>{{ order.seatNo || '-' }}</strong>
            <span class="small-label">值机状态</span>
            <strong :class="order.seatNo ? 'checked-text' : ''">
              {{ order.seatNo ? '已值机' : '未值机' }}
            </strong>
          </div>

          <div class="action-block">
            <el-button
              v-if="activeTab === 'active' && !order.seatNo"
              type="primary"
              @click="handleCheckin(order)"
            >
              值机选座
            </el-button>
            <el-button
              v-if="activeTab === 'active'"
              plain
              :disabled="Boolean(order.seatNo)"
              @click="handleChange(order)"
            >
              申请改签
            </el-button>
            <el-button
              v-if="activeTab === 'active'"
              type="danger"
              plain
              :loading="refundingOrderId === order.orderId"
              @click="handleRefund(order)"
            >
              申请退票
            </el-button>
            <el-button plain @click="handleDetail(order)">订单详情</el-button>
          </div>
        </div>
      </article>
    </div>

    <section v-if="activeTab === 'active'" class="tips-panel">
      <div class="tips-title">
        <span class="blue-line"></span>
        <span>温馨提示</span>
      </div>
      <p>1. 航班起飞前 48 小时内可办理值机，起飞前 2 小时停止办理。</p>
      <p>2. 如需改签或退票，请提前查看航空公司退改签规则。</p>
      <p>3. 已值机订单如需变更座位，请在航班起飞前通过“值机选座”重新选择。</p>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../../api/index'

const router = useRouter()

const activeTab = ref('active')
const loading = ref(false)
const refundingOrderId = ref(null)
const sortMode = ref('flightDateDesc')

const filters = reactive({
  dateRange: [],
  flightNo: '',
  airline: '',
  status: ''
})

const activeOrders = ref([])
const historyOrders = ref([])

const airlineOptions = computed(() => {
  const names = [...activeOrders.value, ...historyOrders.value]
    .map(order => order.airlineName)
    .filter(Boolean)

  return [...new Set(names)]
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

const normalizeOrder = (order) => {
  return {
    orderId: order.orderId,
    orderNo: order.orderNo || `OD${order.orderId}`,
    flightNo: order.flightNo || '-',
    airlineCode: order.airlineCode || '',
    airlineName: order.airlineName || order.airline || '-',
    passengerName: order.passengerName || '-',
    passengerIdCard: order.passengerIdCard || order.idCard || '',
    flightDate: order.flightDate || '',
    depAirport: order.depAirport || '-',
    arrAirport: order.arrAirport || '-',
    depTime: formatTime(order.depTime),
    arrTime: formatTime(order.arrTime),
    duration: order.duration || calcDuration(formatTime(order.depTime), formatTime(order.arrTime)),
    cabinType: order.cabinType || '-',
    price: order.price || 0,
    seatNo: order.seatNo || '',
    purchaseTime: order.purchaseTime || '',
    orderStatus: order.orderStatus || '已出票'
  }
}

const loadOrders = async () => {
  loading.value = true

  try {
    const [activeResponse, historyResponse] = await Promise.all([
      api.get('/orders'),
      api.get('/orders/history')
    ])

    activeOrders.value = (activeResponse.data.data || []).map(normalizeOrder)
    historyOrders.value = (historyResponse.data.data || []).map(normalizeOrder)
  } catch (error) {
    activeOrders.value = []
    historyOrders.value = []
    ElMessage.error(error.response?.data?.message || '订单查询失败，请稍后重试')
    console.error(error)
  } finally {
    loading.value = false
  }
}

const sourceOrders = computed(() => {
  return activeTab.value === 'active' ? activeOrders.value : historyOrders.value
})

const visibleOrders = computed(() => {
  const result = sourceOrders.value.filter(order => {
    const matchFlight = !filters.flightNo ||
      order.flightNo.toLowerCase().includes(filters.flightNo.toLowerCase())
    const matchAirline = !filters.airline || order.airlineName === filters.airline
    const matchStatus = !filters.status ||
      statusText(order.orderStatus) === filters.status ||
      order.orderStatus === filters.status

    return matchFlight && matchAirline && matchStatus
  })

  return [...result].sort((a, b) => {
    const key = sortMode.value === 'purchaseTimeDesc' ? 'purchaseTime' : 'flightDate'
    return String(b[key]).localeCompare(String(a[key]))
  })
})

const applyFilters = () => {
  ElMessage.success('筛选条件已应用')
}

const resetFilters = () => {
  filters.dateRange = []
  filters.flightNo = ''
  filters.airline = ''
  filters.status = ''
}

const handleRefund = async (order) => {
  try {
    await ElMessageBox.confirm(
      `确定要为 ${order.passengerName} 申请 ${order.flightNo} 航班退票吗？`,
      '退票确认',
      {
        confirmButtonText: '确定退票',
        cancelButtonText: '暂不退票',
        type: 'warning'
      }
    )
  } catch {
    return
  }

  refundingOrderId.value = order.orderId

  try {
    const response = await api.post(`/orders/${order.orderId}/refund`, {})

    if (!response.data.success) {
      ElMessage.error(response.data.message || '退票失败')
      return
    }

    ElMessage.success('退票成功，订单已转入历史记录')
    await loadOrders()
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '退票失败')
  } finally {
    refundingOrderId.value = null
  }
}

const handleChange = (row) => {
  router.push({
    path: '/change',
    query: {
      orderId: row.orderId
    }
  })
}

const handleCheckin = (row) => {
  router.push({
    path: '/checkin',
    query: {
      orderId: row.orderId
    }
  })
}

const handleDetail = (row) => {
  router.push({
    path: '/order-detail',
    query: {
      orderId: row.orderId
    }
  })
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

  return statusMap[status] || status || '已出票'
}

const statusType = (status) => {
  const text = statusText(status)
  if (text === '已出票') return 'success'
  if (text === '已完成') return 'info'
  if (text === '已退票') return 'warning'
  if (text === '已取消') return 'danger'
  return 'info'
}

const maskIdCard = (idCard) => {
  if (!idCard) return ''
  return `${idCard.slice(0, 6)}********${idCard.slice(-4)}`
}

onMounted(() => {
  loadOrders()
})
</script>

<style scoped>
.orders-page {
  max-width: 1180px;
  margin: 0 auto;
}

.filter-panel,
.tips-panel {
  padding: 24px 28px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.82);
  box-shadow: 0 10px 30px rgba(30, 93, 140, 0.08);
  backdrop-filter: blur(10px);
}

.section-title,
.tips-title {
  display: flex;
  align-items: center;
  gap: 10px;
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

.order-tabs {
  margin-top: 22px;
}

:deep(.el-tabs__header) {
  margin-bottom: 18px;
}

:deep(.el-tabs__item) {
  font-weight: 800;
  color: #334155;
}

:deep(.el-tabs__item.is-active) {
  color: #0b7cff;
}

.filter-row {
  display: grid;
  grid-template-columns: 280px 180px 180px 180px auto;
  gap: 22px;
  align-items: end;
}

.filter-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.filter-label {
  font-size: 14px;
  font-weight: 700;
  color: #334155;
}

.date-range {
  width: 280px;
}

.filter-input {
  width: 180px;
}

.filter-actions {
  display: flex;
  gap: 12px;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 24px 0 14px;
}

.list-header h3 {
  margin: 0;
  font-size: 20px;
  color: #0f172a;
}

.sort-select {
  width: 180px;
}

.order-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-height: 180px;
}

.order-card {
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 8px 24px rgba(30, 93, 140, 0.08);
  overflow: hidden;
}

.order-card-top {
  min-height: 54px;
  display: grid;
  grid-template-columns: 1.2fr 1fr auto;
  align-items: center;
  gap: 20px;
  padding: 0 28px;
  border-bottom: 1px solid rgba(226, 232, 240, 0.9);
  color: #64748b;
  font-size: 13px;
}

.order-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  color: #0f172a;
  font-size: 15px;
}

.order-amount strong {
  color: #ef233c;
  font-size: 17px;
}

.order-card-body {
  display: grid;
  grid-template-columns: 170px 1.35fr 180px 120px 120px;
  gap: 24px;
  align-items: center;
  padding: 26px 28px;
}

.flight-summary {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.airline-line {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #0f172a;
}

.airline-logo {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  display: inline-block;
}

.CA {
  background: #e11d48;
}

.MU {
  background: #0284c7;
}

.HU {
  background: #dc2626;
}

.ZH {
  background: #ef4444;
}

.rule-link {
  color: #0b7cff;
  font-size: 13px;
}

.route-block {
  display: grid;
  grid-template-columns: 1fr 140px 1fr;
  align-items: center;
  gap: 22px;
}

.route-city {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.route-city.right {
  text-align: right;
}

.airport {
  color: #334155;
  font-weight: 800;
}

.time {
  font-size: 28px;
  font-weight: 900;
  color: #0f172a;
}

.date {
  color: #334155;
  font-size: 13px;
}

.route-line {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  color: #64748b;
  font-size: 13px;
}

.route-line i {
  width: 120px;
  height: 1px;
  background: #cbd5e1;
  position: relative;
}

.route-line i::after {
  content: '';
  position: absolute;
  right: 0;
  top: -3px;
  width: 7px;
  height: 7px;
  border-top: 1px solid #cbd5e1;
  border-right: 1px solid #cbd5e1;
  transform: rotate(45deg);
}

.passenger-block,
.seat-block {
  display: flex;
  flex-direction: column;
  gap: 6px;
  color: #334155;
  font-size: 13px;
}

.small-label {
  color: #64748b;
}

.checked-text {
  color: #10b981;
}

.action-block {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.tips-panel {
  margin-top: 22px;
  color: #475569;
}

.tips-panel p {
  margin: 8px 0 0 18px;
}

@media (max-width: 1200px) {
  .filter-row,
  .order-card-body {
    grid-template-columns: 1fr;
  }

  .date-range,
  .filter-input,
  .sort-select {
    width: 100%;
  }

  .order-card-top {
    grid-template-columns: 1fr;
    padding: 16px 20px;
  }

  .action-block {
    flex-direction: row;
    flex-wrap: wrap;
  }
}
</style>

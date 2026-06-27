<template>
  <div class="change-page" v-loading="loading">
    <div class="page-title-row">
      <el-button link class="back-btn" @click="router.back()">
        <el-icon><ArrowLeft /></el-icon>
        返回
      </el-button>
      <h2>改签</h2>
    </div>

    <el-alert
      class="rule-alert"
      type="warning"
      show-icon
      :closable="false"
      title="改签规则：起飞前两小时内不能改签，改签需收取手续费，具体以航司规则为准。"
    />

    <section class="panel current-panel">
      <h3>当前航班信息</h3>
      <div class="current-flight">
        <div class="airline-block">
          <span class="airline-logo" :class="originalOrder.airlineCode"></span>
          <div>
            <strong>{{ originalOrder.airlineName }} {{ originalOrder.flightNo }}</strong>
            <p>{{ originalOrder.aircraftModel || '-' }} | {{ originalOrder.cabinType || '-' }}</p>
          </div>
        </div>

        <div class="route-block">
          <div class="route-city">
            <strong>{{ originalOrder.depAirport }}</strong>
            <span class="flight-time">{{ originalOrder.depTime }}</span>
            <span>{{ originalOrder.flightDate }}</span>
          </div>
          <div class="route-line">
            <span>{{ originalOrder.duration }}</span>
            <i></i>
            <strong>直飞</strong>
          </div>
          <div class="route-city right">
            <strong>{{ originalOrder.arrAirport }}</strong>
            <span class="flight-time">{{ originalOrder.arrTime }}</span>
            <span>{{ originalOrder.flightDate }}</span>
          </div>
        </div>

        <div class="flight-extra">
          <div><span>舱位等级</span><strong>{{ originalOrder.cabinType }}</strong></div>
          <div><span>机票价格</span><strong>¥{{ originalOrder.price }}</strong></div>
          <div><span>订单状态</span><strong>{{ statusText(originalOrder.orderStatus) }}</strong></div>
        </div>
      </div>
    </section>

    <section class="panel new-flight-panel">
      <h3>选择新航班</h3>
      <div class="search-row">
        <label>
          出发城市
          <el-input v-model="searchForm.departure" size="large" />
        </label>
        <label>
          到达城市
          <el-input v-model="searchForm.arrival" size="large" />
        </label>
        <label>
          出发日期
          <el-date-picker
            v-model="searchForm.date"
            type="date"
            size="large"
            value-format="YYYY-MM-DD"
          />
        </label>
        <el-button type="primary" size="large" class="search-btn" @click="searchNewFlights">
          查询航班
        </el-button>
      </div>

      <div class="flight-table-scroll">
        <el-table
          v-loading="searching"
          :data="flightList"
          class="flight-table"
          style="width: 100%"
          :fit="false"
        >
          <el-table-column prop="flightNo" label="航班号" width="90" />
          <el-table-column prop="airlineName" label="航空公司" width="160" show-overflow-tooltip />
          <el-table-column prop="depAirport" label="出发机场" width="180" show-overflow-tooltip />
          <el-table-column prop="arrAirport" label="到达机场" width="180" show-overflow-tooltip />
          <el-table-column prop="depTime" label="起飞时间" width="120" />
          <el-table-column prop="arrTime" label="到达时间" width="120" />
          <el-table-column prop="cabinType" label="舱位" width="100" />
          <el-table-column label="价格" width="120">
            <template #default="{ row }">
              <strong class="price-text">¥{{ row.price }}</strong>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="110" fixed="right">
            <template #default="{ row }">
              <el-button type="primary" :disabled="!row.pricingId" @click="selectFlight(row)">选择</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <div class="fee-panel">
        <h3>改签费用预估</h3>
        <div class="fee-grid">
          <span>原机票金额：<strong>¥{{ originalOrder.price }}</strong></span>
          <span>改签手续费：<strong>¥{{ feeInfo.changeFee }}</strong></span>
          <span>需补差价：<strong class="price-text">¥{{ feeInfo.fareDifference }}</strong></span>
          <span class="payable">应付金额：<strong>¥{{ feeInfo.payableAmount }}</strong></span>
        </div>
      </div>

      <div class="confirm-row">
        <el-button
          type="primary"
          size="large"
          class="confirm-btn"
          :disabled="!selectedFlight || !feePreview"
          @click="confirmChange"
        >
          确认改签
        </el-button>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import api from '../../api/index'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const searching = ref(false)
const orderId = computed(() => Number(route.query.orderId))
const selectedFlight = ref(null)
const feePreview = ref(null)

const originalOrder = reactive({
  orderId: null,
  flightNo: '',
  airlineCode: '',
  airlineName: '',
  aircraftModel: '',
  depAirport: '',
  arrAirport: '',
  depTime: '--:--',
  arrTime: '--:--',
  duration: '-',
  flightDate: '',
  cabinType: '',
  price: 0,
  orderStatus: ''
})

const searchForm = reactive({
  departure: '',
  arrival: '',
  date: ''
})

const flightList = ref([])

const feeInfo = computed(() => {
  const changeFee = Number(feePreview.value?.changeFee || 0)
  const fareDifference = Number(feePreview.value?.fareDifference || 0)
  const payableAmount = Number(feePreview.value?.payableAmount || 0)

  return {
    changeFee,
    fareDifference,
    payableAmount
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

const getCityFromAirport = (airport = '') => {
  const knownCities = ['北京', '上海', '成都', '广州', '深圳']
  return knownCities.find(city => airport.includes(city)) || ''
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

const loadOriginalOrder = async () => {
  if (!orderId.value) {
    ElMessage.warning('缺少订单编号')
    router.push('/orders')
    return
  }

  loading.value = true

  try {
    const response = await api.get(`/orders/${orderId.value}`)
    const data = response.data.data
    if (!data) return
    const depTime = formatTime(data.depTime)
    const arrTime = formatTime(data.arrTime)

    Object.assign(originalOrder, {
      orderId: data.orderId,
      flightNo: data.flightNo || '',
      airlineCode: data.airlineCode || '',
      airlineName: data.airlineName || '',
      aircraftModel: data.aircraftModel || '',
      depAirport: data.depAirport || '',
      arrAirport: data.arrAirport || '',
      depTime,
      arrTime,
      duration: data.duration || calcDuration(depTime, arrTime),
      flightDate: data.flightDate || '',
      cabinType: data.cabinType || '',
      price: data.price || 0,
      orderStatus: data.orderStatus || ''
    })

    searchForm.departure = getCityFromAirport(originalOrder.depAirport)
    searchForm.arrival = getCityFromAirport(originalOrder.arrAirport)
    searchForm.date = originalOrder.flightDate
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '原订单查询失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

const searchNewFlights = async () => {
  if (!searchForm.departure || !searchForm.arrival || !searchForm.date) {
    ElMessage.warning('请先填写出发城市、到达城市和出发日期')
    return
  }

  searching.value = true
  selectedFlight.value = null
  feePreview.value = null

  try {
    const response = await api.get('/flights/search', {
      params: {
        departure: searchForm.departure,
        arrival: searchForm.arrival,
        date: searchForm.date
      }
    })

    const rows = response.data.data || []
    const candidates = await Promise.all(
      rows.map(async item => {
        if (!item.instanceId) return []

        const cabinResponse = await api.get(`/flights/${item.instanceId}/cabins`)
        const cabins = cabinResponse.data.data || []

        return cabins.map(cabin => ({
          pricingId: cabin.pricingId,
          flightNo: item.flightNo,
          airlineName: item.airlineName || item.airline || '-',
          depAirport: item.depAirport || '-',
          arrAirport: item.arrAirport || '-',
          depTime: formatTime(item.depTime),
          arrTime: formatTime(item.arrTime),
          cabinType: cabin.cabinType,
          price: Number(cabin.price || 0)
        }))
      })
    )

    flightList.value = candidates
      .flat()
      .filter(item => item.pricingId)

    ElMessage.success('查询成功')
  } catch (error) {
    flightList.value = []
    ElMessage.error(error.response?.data?.message || '新航班查询失败')
  } finally {
    searching.value = false
  }
}

const selectFlight = async (row) => {
  selectedFlight.value = row
  feePreview.value = null

  try {
    const response = await api.post(`/orders/${orderId.value}/change-preview`, {
      new_pricing_id: Number(row.pricingId)
    })

    feePreview.value = response.data.data
    ElMessage.success(`已选择 ${row.flightNo}`)
  } catch (error) {
    selectedFlight.value = null
    ElMessage.error(error.response?.data?.message || '改签费用计算失败')
  }
}

const confirmChange = async () => {
  if (!selectedFlight.value) return

  try {
    await ElMessageBox.confirm(
      `确认改签至 ${selectedFlight.value.flightNo}，需支付 ¥${feeInfo.value.payableAmount} 吗？`,
      '确认改签',
      {
        confirmButtonText: '确认改签',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await api.post(`/orders/${orderId.value}/change`, {
      new_pricing_id: Number(selectedFlight.value.pricingId)
    })

    ElMessage.success('改签成功')
    router.push('/change-records')
  } catch (error) {
    if (error === 'cancel' || error === 'close') return
    ElMessage.error(error.response?.data?.message || '改签失败')
  }
}

onMounted(() => {
  loadOriginalOrder()
})
</script>

<style scoped>
.change-page {
  max-width: 1180px;
  margin: 0 auto;
}

.page-title-row {
  display: flex;
  align-items: center;
  gap: 22px;
  margin-bottom: 24px;
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

.rule-alert {
  margin-bottom: 14px;
  border: 1px solid #fed7aa;
  background: rgba(255, 247, 237, 0.92);
}

.panel {
  margin-bottom: 16px;
  padding: 26px 28px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.88);
  box-shadow: 0 10px 30px rgba(30, 93, 140, 0.08);
}

.current-flight {
  margin-top: 28px;
  display: grid;
  grid-template-columns: 250px 1fr 220px;
  gap: 34px;
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
  width: 72px;
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

.flight-extra div {
  display: grid;
  grid-template-columns: 90px 1fr;
}

.flight-extra span {
  color: #64748b;
}

.search-row {
  margin-top: 24px;
  display: grid;
  grid-template-columns: 1fr 1fr 1fr 140px;
  gap: 24px;
  align-items: end;
}

.search-row label {
  display: flex;
  flex-direction: column;
  gap: 8px;
  color: #0f172a;
  font-weight: 700;
}

.search-btn {
  height: 40px;
}

.date-strip {
  margin: 28px 0 16px;
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 14px;
}

.date-strip button {
  min-height: 58px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.8);
  color: #0f172a;
  font-weight: 800;
  cursor: pointer;
}

.date-strip button.active {
  border-color: #0b7cff;
  color: #0b7cff;
}

.flight-table {
  border-radius: 8px;
  overflow: hidden;
}

.price-text {
  color: #ef233c;
}

.fee-panel {
  margin-top: 18px;
  padding: 20px;
  border: 1px solid #bfdbfe;
  border-radius: 8px;
  background: rgba(239, 246, 255, 0.7);
}

.fee-grid {
  margin-top: 18px;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  align-items: center;
}

.payable {
  text-align: right;
  color: #0f172a;
}

.payable strong {
  color: #ef233c;
  font-size: 30px;
}

.confirm-row {
  margin-top: 24px;
  display: flex;
  justify-content: center;
}

.confirm-btn {
  width: 240px;
  height: 52px;
  font-weight: 800;
}

@media (max-width: 1000px) {
  .current-flight,
  .route-block,
  .search-row,
  .date-strip,
  .fee-grid {
    grid-template-columns: 1fr;
  }

  .payable {
    text-align: left;
  }
}
/* ===== 改签页布局修正：当前航班横向展开 + 新航班表格横向滚动 ===== */

.current-panel {
  overflow-x: hidden;
  overflow-y: visible;
  padding-bottom: 26px;
}

.current-flight {
  width: 100%;
  min-width: 0;
  grid-template-columns: 190px minmax(520px, 1fr) 180px;
  gap: 12px;
  align-items: center;
}

.route-block {
  grid-template-columns: 165px 82px 165px;
  gap: 10px;
}

.route-city strong {
  white-space: nowrap;
  line-height: 1.35;
}

.route-city {
  min-width: 0;
}

.flight-extra {
  min-width: 180px;
  padding-left: 18px;
}

.new-flight-panel {
  overflow-x: hidden;
}

.flight-table-scroll {
  width: 100%;
  overflow-x: hidden;
  overflow-y: hidden;
  padding-bottom: 0;
}

.flight-table {
  width: 100%;
  min-width: 0;
}

.flight-table :deep(.cell) {
  white-space: nowrap;
}

.flight-table-scroll::-webkit-scrollbar,
.current-panel::-webkit-scrollbar {
  height: 8px;
}

.flight-table-scroll::-webkit-scrollbar-thumb,
.current-panel::-webkit-scrollbar-thumb {
  border-radius: 999px;
  background: rgba(100, 116, 139, 0.45);
}

.flight-table-scroll::-webkit-scrollbar-track,
.current-panel::-webkit-scrollbar-track {
  border-radius: 999px;
  background: rgba(226, 232, 240, 0.9);
}
</style>

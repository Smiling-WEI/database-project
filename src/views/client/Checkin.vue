<template>
  <div class="checkin-page" v-loading="loading">
    <div class="page-title-row">
      <el-button link class="back-btn" @click="router.back()">
        返回
      </el-button>
      <h2>值机选座</h2>
    </div>

    <section class="panel">
      <h3>订单信息</h3>
      <div class="order-grid">
        <div>
          <span>订单号</span>
          <strong>{{ order.orderNo || '-' }}</strong>
        </div>
        <div>
          <span>航班</span>
          <strong>{{ order.airlineName || '-' }} {{ order.flightNo || '-' }}</strong>
        </div>
        <div>
          <span>乘机人</span>
          <strong>{{ order.passengerName || '-' }}</strong>
        </div>
        <div>
          <span>当前座位</span>
          <strong>{{ order.seatNo || '未值机' }}</strong>
        </div>
      </div>
    </section>

    <section class="panel seat-panel">
      <div class="seat-header">
        <div>
          <h3>选择座位</h3>
          <p>{{ seatInfo.cabinType || '-' }} · 请选择一个可用座位后确认值机</p>
        </div>

        <div class="legend">
          <span><i class="seat-demo available"></i>可选</span>
          <span><i class="seat-demo selected"></i>已选</span>
          <span><i class="seat-demo occupied"></i>已占用</span>
        </div>
      </div>

      <div v-if="order.seatNo" class="already-checkin">
        该订单已值机，座位号：{{ order.seatNo }}
      </div>

      <div v-else class="airplane-wrapper">
        <div class="airplane-head">机头</div>

        <div class="seat-map">
          <div
            v-for="row in seatRows"
            :key="row.row"
            class="seat-row"
          >
            <span class="row-no">{{ row.row }}</span>

            <button
              v-for="seat in row.seats"
              :key="seat.seatNo"
              class="seat-btn"
              :class="seatClass(seat)"
              :disabled="seat.status === 'occupied'"
              @click="selectSeat(seat)"
            >
              {{ seat.seatNo }}
            </button>
          </div>
        </div>
      </div>

      <div class="confirm-bar">
        <div>
          已选座位：
          <strong>{{ selectedSeatNo || '-' }}</strong>
        </div>

        <el-button
          type="primary"
          size="large"
          :disabled="Boolean(order.seatNo) || !selectedSeatNo"
          :loading="submitting"
          @click="submitCheckin"
        >
          确认值机
        </el-button>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '../../api/index'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const submitting = ref(false)
const orderId = computed(() => Number(route.query.orderId))

const order = reactive({
  orderId: null,
  orderNo: '',
  airlineName: '',
  flightNo: '',
  passengerName: '',
  seatNo: ''
})

const seatInfo = reactive({
  cabinType: '',
  checkInStatus: '',
  currentSeatNo: '',
  seatMap: {
    columns: [],
    rows: []
  }
})

const selectedSeatNo = ref('')

const seatRows = computed(() => seatInfo.seatMap?.rows || [])

const loadOrder = async () => {
  if (!orderId.value) {
    ElMessage.warning('缺少订单编号')
    router.push('/orders')
    return
  }

  loading.value = true

  try {
    const [orderResponse, seatResponse] = await Promise.all([
      api.get(`/orders/${orderId.value}`),
      api.get(`/orders/${orderId.value}/seats`)
    ])

    const data = orderResponse.data.data || {}
    const seatData = seatResponse.data.data || {}

    Object.assign(order, {
      orderId: data.orderId,
      orderNo: data.orderNo || `OD${data.orderId}`,
      airlineName: data.airlineName || '',
      flightNo: data.flightNo || '',
      passengerName: data.passengerName || '',
      seatNo: data.seatNo || ''
    })

    Object.assign(seatInfo, {
      cabinType: seatData.cabinType || '',
      checkInStatus: seatData.checkInStatus || '',
      currentSeatNo: seatData.currentSeatNo || '',
      seatMap: seatData.seatMap || { columns: [], rows: [] }
    })

    selectedSeatNo.value = seatData.currentSeatNo || ''
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '订单信息加载失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

const seatClass = (seat) => {
  if (selectedSeatNo.value === seat.seatNo) return 'selected'
  return seat.status || 'available'
}

const selectSeat = (seat) => {
  if (seat.status === 'occupied') return
  if (order.seatNo) return

  selectedSeatNo.value = seat.seatNo
}

const submitCheckin = async () => {
  if (!selectedSeatNo.value) {
    ElMessage.warning('请先选择座位')
    return
  }

  submitting.value = true

  try {
    const response = await api.post(`/orders/${orderId.value}/checkin`, {
      seatNo: selectedSeatNo.value
    })

    if (!response.data.success) {
      ElMessage.error(response.data.message || '值机失败')
      return
    }

    ElMessage.success('值机成功')
    await loadOrder()
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '值机失败')
    console.error(error)
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  loadOrder()
})
</script>

<style scoped>
.checkin-page {
  max-width: 960px;
  margin: 0 auto;
}

.page-title-row {
  display: flex;
  align-items: center;
  gap: 18px;
  margin-bottom: 20px;
}

.back-btn {
  color: #0b7cff;
  font-weight: 800;
}

.page-title-row h2,
.panel h3 {
  margin: 0;
  color: #0f172a;
}

.panel {
  margin-bottom: 16px;
  padding: 24px 28px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.88);
  box-shadow: 0 10px 30px rgba(30, 93, 140, 0.08);
}

.order-grid {
  margin-top: 20px;
  display: grid;
  grid-template-columns: repeat(2, minmax(220px, 1fr));
  gap: 18px 28px;
}

.order-grid div {
  display: grid;
  grid-template-columns: 80px 1fr;
  gap: 14px;
}

.order-grid span {
  color: #64748b;
}

.order-grid strong {
  color: #0f172a;
}

.seat-panel {
  display: flex;
  flex-direction: column;
  gap: 22px;
}

.seat-header {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  align-items: flex-start;
}

.seat-header p {
  margin: 8px 0 0;
  color: #64748b;
}

.legend {
  display: flex;
  gap: 14px;
  color: #64748b;
  font-size: 13px;
}

.legend span {
  display: flex;
  align-items: center;
  gap: 6px;
}

.seat-demo {
  width: 18px;
  height: 18px;
  border-radius: 5px;
  display: inline-block;
  border: 1px solid #cbd5e1;
}

.airplane-wrapper {
  padding: 20px 0 8px;
  border-radius: 14px;
  background: linear-gradient(180deg, #f8fafc, #eef6ff);
  overflow-x: auto;
}

.airplane-head {
  width: 160px;
  margin: 0 auto 20px;
  padding: 10px 0;
  text-align: center;
  border-radius: 80px 80px 18px 18px;
  background: #dbeafe;
  color: #0b7cff;
  font-weight: 800;
}

.seat-map {
  width: max-content;
  min-width: 520px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.seat-row {
  display: grid;
  grid-template-columns: 34px repeat(6, 54px);
  gap: 10px;
  align-items: center;
}

.row-no {
  text-align: right;
  color: #64748b;
  font-weight: 700;
}

.seat-btn {
  width: 54px;
  height: 38px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  background: #ffffff;
  color: #0f172a;
  font-weight: 800;
  cursor: pointer;
}

.seat-btn.available:hover {
  border-color: #0b7cff;
  color: #0b7cff;
}

.seat-btn.selected {
  background: #0b7cff;
  border-color: #0b7cff;
  color: #ffffff;
}

.seat-btn.occupied {
  background: #e5e7eb;
  color: #94a3b8;
  cursor: not-allowed;
}

.seat-demo.available {
  background: #ffffff;
}

.seat-demo.selected {
  background: #0b7cff;
  border-color: #0b7cff;
}

.seat-demo.occupied {
  background: #e5e7eb;
}

.already-checkin {
  padding: 16px 18px;
  border-radius: 8px;
  background: #ecfdf5;
  color: #059669;
  font-weight: 800;
}

.confirm-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 6px;
}

.confirm-bar strong {
  color: #0b7cff;
  font-size: 20px;
}

@media (max-width: 720px) {
  .order-grid {
    grid-template-columns: 1fr;
  }

  .seat-header,
  .confirm-bar {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
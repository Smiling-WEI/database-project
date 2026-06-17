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

    <section class="panel unavailable-panel">
      <el-empty description="后端暂未提供值机座位图和座位提交接口" />
      <el-button type="primary" disabled>确认值机</el-button>
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
const orderId = computed(() => Number(route.query.orderId))

const order = reactive({
  orderId: null,
  orderNo: '',
  airlineName: '',
  flightNo: '',
  passengerName: '',
  seatNo: ''
})

const loadOrder = async () => {
  if (!orderId.value) {
    ElMessage.warning('缺少订单编号')
    router.push('/orders')
    return
  }

  loading.value = true

  try {
    const response = await api.get(`/orders/${orderId.value}`)
    const data = response.data.data || {}

    Object.assign(order, {
      orderId: data.orderId,
      orderNo: data.orderNo || `OD${data.orderId}`,
      airlineName: data.airlineName || '',
      flightNo: data.flightNo || '',
      passengerName: data.passengerName || '',
      seatNo: data.seatNo || ''
    })
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '订单信息加载失败')
    console.error(error)
  } finally {
    loading.value = false
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

.unavailable-panel {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 18px;
}

@media (max-width: 720px) {
  .order-grid {
    grid-template-columns: 1fr;
  }
}
</style>

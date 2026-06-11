<template>
  <div class="booking-container">
    <h2>🎫 确认订单与乘机人</h2>

    <el-alert
      v-if="loading"
      title="正在加载航班和乘机人信息……"
      type="info"
      :closable="false"
      show-icon
      class="status-alert"
    />

    <template v-else-if="flight">
      <el-card class="flight-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <span>✈️ 已选航班：{{ flight.flightNo }}</span>
            <span class="airline-name">{{ flight.airlineName }}</span>
          </div>
        </template>

        <div class="flight-info">
          <p>
            <strong>起降机场：</strong>
            {{ flight.depAirport }} → {{ flight.arrAirport }}
          </p>
          <p>
            <strong>起降时间：</strong>
            {{ flight.depTime || '待补充' }} - {{ flight.arrTime || '待补充' }}
          </p>
          <p>
            <strong>出发日期：</strong>
            {{ flight.flightDate || '待补充' }}
          </p>
        </div>
      </el-card>

      <el-card class="cabin-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <span>💺 选择舱位</span>
          </div>
        </template>

        <el-radio-group v-model="selectedPricingId" class="option-group">
          <el-radio
            v-for="cabin in cabinList"
            :key="cabin.pricingId"
            :value="cabin.pricingId"
            border
            :disabled="cabin.remainingSeats <= 0"
          >
            {{ cabin.cabinType }}
            · ¥{{ cabin.price }}
            · 剩余 {{ cabin.remainingSeats }} 张
          </el-radio>
        </el-radio-group>

        <el-empty
          v-if="cabinList.length === 0"
          description="当前航班暂无可预订舱位"
          :image-size="80"
        />
      </el-card>

      <el-card class="passenger-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <span>👨‍👩‍👧 选择乘机人</span>
            <el-button type="primary" link @click="goPassengerManage">
              + 新增乘机人
            </el-button>
          </div>
        </template>

        <el-radio-group v-model="selectedPassengerId" class="option-group">
          <el-radio
            v-for="passenger in passengerList"
            :key="passenger.passengerId"
            :value="passenger.passengerId"
            border
          >
            {{ passenger.realName }}
            <span v-if="passenger.relationNote">
              （{{ passenger.relationNote }}）
            </span>
            - {{ maskIdCard(passenger.idCard) }}
          </el-radio>
        </el-radio-group>

        <el-empty
          v-if="passengerList.length === 0"
          description="暂无常用乘机人，请先新增乘机人"
          :image-size="80"
        />
      </el-card>

      <el-card class="seat-card" shadow="hover">
        <template #header>
          <div class="card-header">
            <span>🪑 填写座位号</span>
            <span class="optional-text">选填</span>
          </div>
        </template>

        <el-input
          v-model="seatNo"
          maxlength="10"
          placeholder="例如：19A；暂不选座可以留空"
          clearable
        />
      </el-card>

      <div class="submit-area">
        <el-button size="large" @click="goBack">
          返回修改
        </el-button>

        <el-button
          type="success"
          size="large"
          :loading="submitting"
          :disabled="!canSubmit"
          @click="submitOrder"
        >
          💳 确认支付并出票
        </el-button>
      </div>
    </template>

    <el-empty
      v-else
      description="未找到已选择的航班，请返回首页重新查询"
      :image-size="100"
    >
      <el-button type="primary" @click="goHome">
        返回航班查询
      </el-button>
    </el-empty>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../../api/index'

const router = useRouter()

const loading = ref(true)
const submitting = ref(false)

const flight = ref(null)
const cabinList = ref([])
const passengerList = ref([])

const selectedPricingId = ref(null)
const selectedPassengerId = ref(null)
const seatNo = ref('')

const canSubmit = computed(() => {
  return (
    flight.value &&
    selectedPricingId.value !== null &&
    selectedPassengerId.value !== null
  )
})

const maskIdCard = (idCard) => {
  const text = String(idCard || '')

  if (text.length < 8) return text || '-'

  return `${text.slice(0, 6)}********${text.slice(-4)}`
}

const loadBookingData = async () => {
  loading.value = true

  try {
    const storedFlight = sessionStorage.getItem('selectedFlight')

    if (!storedFlight) {
      flight.value = null
      return
    }

    const parsedFlight = JSON.parse(storedFlight)

    if (!parsedFlight.instanceId) {
      flight.value = null
      return
    }

    flight.value = parsedFlight

    const [cabinResponse, passengerResponse] = await Promise.all([
      api.get(`/flights/${parsedFlight.instanceId}/cabins`),
      api.get('/passengers')
    ])

    cabinList.value = cabinResponse.data.data || []
    passengerList.value = passengerResponse.data.data || []

    const availableCabins = cabinList.value.filter(
      (item) => item.remainingSeats > 0
    )

    if (availableCabins.length === 1) {
      selectedPricingId.value = availableCabins[0].pricingId
    }

    if (passengerList.value.length === 1) {
      selectedPassengerId.value = passengerList.value[0].passengerId
    }
  } catch (error) {
    ElMessage.error(
      error.response?.data?.message || '预订信息加载失败，请稍后重试'
    )
    console.error(error)
  } finally {
    loading.value = false
  }
}

const submitOrder = async () => {
  if (!canSubmit.value) {
    ElMessage.warning('请选择舱位和乘机人')
    return
  }

  try {
    await ElMessageBox.confirm(
      '系统将创建真实订单并锁定座位，确认支付吗？',
      '支付确认',
      {
        confirmButtonText: '确认支付',
        cancelButtonText: '取消',
        type: 'success'
      }
    )
  } catch {
    ElMessage.info('已取消支付')
    return
  }

  submitting.value = true

  try {
    const response = await api.post('/orders', {
      passenger_id: selectedPassengerId.value,
      pricing_id: selectedPricingId.value,
      seat_no: seatNo.value.trim() || ''
    })

    if (!response.data.success) {
      ElMessage.error(response.data.message || '购票失败')
      return
    }

    ElMessage.success('支付成功，售票记录已经生成')
    sessionStorage.removeItem('selectedFlight')
    router.push('/orders')
  } catch (error) {
    ElMessage.error(
      error.response?.data?.message || '购票失败，请稍后重试'
    )
    console.error(error)
  } finally {
    submitting.value = false
  }
}

const goBack = () => {
  router.back()
}

const goHome = () => {
  router.push('/home')
}

const goPassengerManage = () => {
  router.push('/passengers')
}

onMounted(() => {
  loadBookingData()
})
</script>

<style scoped>
.booking-container {
  max-width: 820px;
  margin: 0 auto;
  padding: 40px;
}

.status-alert {
  margin-bottom: 18px;
}

.flight-card,
.cabin-card,
.passenger-card,
.seat-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  font-weight: 700;
}

.airline-name,
.optional-text {
  color: #909399;
  font-size: 13px;
  font-weight: 400;
}

.flight-info p {
  margin: 10px 0;
  color: #606266;
}

.option-group {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 14px;
}

.submit-area {
  margin-top: 30px;
  text-align: center;
}
</style>
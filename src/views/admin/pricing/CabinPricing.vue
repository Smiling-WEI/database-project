<template>
  <PageContainer title="票务配置 / 舱位票价">
    <div class="pricing-page">
      <div class="page-header">
        <div>
          <h2>舱位票价管理</h2>
          <p>查看航班舱位余票，维护票价及其生效时间</p>
        </div>

        <template v-if="canEditPricingPage">
        <el-button
          type="primary"
          :disabled="!selectedInstanceId"
          @click="openCreateDialog"
        >
          + 新增价格
        </el-button>
      </template>
      </div>

      <div class="select-card">
        <span class="select-label">选择航班</span>

        <el-select
          v-model="selectedInstanceId"
          filterable
          placeholder="请选择航班"
          style="width: 520px"
          :loading="flightLoading"
        >
          <el-option
            v-for="flight in flightOptions"
            :key="flight.instanceId"
            :label="formatFlightLabel(flight)"
            :value="flight.instanceId"
          />
        </el-select>
      </div>

      <div v-if="currentFlight" class="flight-summary">
        <div class="flight-main">
          <div>
            <span class="flight-no">{{ currentFlight.flightNo }}</span>
            <el-tag size="small" type="success">
              {{ currentFlight.status || '正常' }}
            </el-tag>
          </div>

          <p>
            {{ currentFlight.depAirport || currentFlight.depAirportName || '-' }}
            →
            {{ currentFlight.arrAirport || currentFlight.arrAirportName || '-' }}
          </p>

          <p class="sub-text">
            {{ currentFlight.flightDate }}
            ·
            {{ formatTime(currentFlight.depTime) }} - {{ formatTime(currentFlight.arrTime) }}
            ·
            {{ currentFlight.aircraftModel || '-' }}
          </p>
        </div>

        <div class="seat-card">
          <span>经济舱余票</span>
          <strong>{{ economyRemaining }} / {{ currentFlight.economySeats || 0 }}</strong>
        </div>

        <div class="seat-card">
          <span>头等舱余票</span>
          <strong>{{ firstRemaining }} / {{ currentFlight.firstSeats || 0 }}</strong>
        </div>
      </div>

      <div class="table-card">
        <el-table
          v-loading="priceLoading"
          :data="pricingList"
          border
          stripe
          table-layout="fixed"
          style="width: 100%"
          empty-text="请选择航班或当前航班暂无价格记录"
        >
          <el-table-column prop="pricingId" label="价格ID" width="100" />

          <el-table-column prop="cabinType" label="舱位" width="120">
            <template #default="{ row }">
              <el-tag :type="row.cabinType === '头等舱' ? 'warning' : 'primary'">
                {{ row.cabinType }}
              </el-tag>
            </template>
          </el-table-column>

          <el-table-column label="销售价格" width="150">
            <template #default="{ row }">
              <strong class="price-text">¥{{ formatMoney(row.salePrice) }}</strong>
            </template>
          </el-table-column>

          <el-table-column label="剩余票数" width="120">
            <template #default="{ row }">
              {{ row.remainingTickets }}
            </template>
          </el-table-column>

          <el-table-column prop="validFrom" label="生效时间" min-width="180" />
          <el-table-column prop="validTo" label="失效时间" min-width="180" />

          <el-table-column label="操作" fixed="right" width="100">
            <template #default="{ row }">
              <el-button type="primary" link :disabled="!canEditPricingPage" @click="openEditDialog(row)">
                编辑
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <el-dialog
        v-model="dialogVisible"
        :title="editingRow ? '编辑舱位票价' : '新增舱位票价'"
        width="560px"
      >
        <el-form
          ref="pricingFormRef"
          :model="pricingForm"
          :rules="pricingRules"
          label-width="110px"
        >
          <el-form-item label="舱位" prop="cabinType">
            <el-select
              v-model="pricingForm.cabinType"
              placeholder="请选择舱位"
              style="width: 100%"
            >
              <el-option label="头等舱" value="头等舱" />
              <el-option label="经济舱" value="经济舱" />
            </el-select>
          </el-form-item>

          <el-form-item label="销售价格" prop="salePrice">
            <el-input-number
              v-model="pricingForm.salePrice"
              :min="0"
              :precision="2"
              :step="100"
              style="width: 100%"
            />
          </el-form-item>

          <el-form-item label="生效时间" prop="validFrom">
            <el-date-picker
              v-model="pricingForm.validFrom"
              type="datetime"
              value-format="YYYY-MM-DD HH:mm:ss"
              placeholder="请选择生效时间"
              style="width: 100%"
            />
          </el-form-item>

          <el-form-item label="失效时间" prop="validTo">
            <el-date-picker
              v-model="pricingForm.validTo"
              type="datetime"
              value-format="YYYY-MM-DD HH:mm:ss"
              placeholder="请选择失效时间"
              style="width: 100%"
            />
          </el-form-item>
        </el-form>

        <template #footer>
          <el-button @click="dialogVisible = false">
            取消
          </el-button>
          <el-button type="primary" :loading="saving" @click="handleSave">
            保存
          </el-button>
        </template>
      </el-dialog>
    </div>
  </PageContainer>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import PageContainer from '../../../components/admin/PageContainer.vue'
import { canWriteFlightModule } from '../../../utils/adminAuth'
import {
  createPricingCabin,
  getPricingCabins,
  getPricingFlights,
  updatePricingCabin
} from '../../../api/admin/cabinPricingDirect'

const route = useRoute()
const router = useRouter()

const flightLoading = ref(false)
const priceLoading = ref(false)
const saving = ref(false)

const flightOptions = ref([])
const pricingList = ref([])
const currentFlight = ref(null)

const selectedInstanceId = ref(
  route.query.instanceId ? Number(route.query.instanceId) : ''
)

const dialogVisible = ref(false)
const editingRow = ref(null)
const pricingFormRef = ref(null)

const pricingForm = reactive({
  cabinType: '',
  salePrice: 0,
  validFrom: '',
  validTo: ''
})

const pricingRules = {
  cabinType: [{ required: true, message: '请选择舱位', trigger: 'change' }],
  salePrice: [{ required: true, message: '请输入销售价格', trigger: 'blur' }],
  validFrom: [{ required: true, message: '请选择生效时间', trigger: 'change' }],
  validTo: [{ required: true, message: '请选择失效时间', trigger: 'change' }]
}

const unwrap = (response) => {
  if (response?.data?.data !== undefined) return response.data.data
  if (response?.data !== undefined) return response.data
  if (response?.success !== undefined && response?.data !== undefined) return response.data
  return response
}

const normalizeFlight = (item) => {
  return {
    instanceId: Number(item.instanceId ?? item.instance_id),
    flightNo: item.flightNo ?? item.flight_no,
    flightDate: item.flightDate ?? item.flight_date,
    depTime: item.depTime ?? item.dep_time,
    arrTime: item.arrTime ?? item.arr_time,
    depAirport: item.depAirport ?? item.dep_airport ?? item.depAirportName,
    arrAirport: item.arrAirport ?? item.arr_airport ?? item.arrAirportName,
    depAirportName: item.depAirportName ?? item.depAirport,
    arrAirportName: item.arrAirportName ?? item.arrAirport,
    airlineName: item.airlineName ?? item.airline_name,
    aircraftModel: item.aircraftModel ?? item.aircraft_model,
    firstSeats: Number(item.firstSeats ?? item.first_seats ?? 0),
    economySeats: Number(item.economySeats ?? item.economy_seats ?? 0),
    status: item.status
  }
}

const normalizeCabin = (item) => {
  return {
    pricingId: Number(item.pricingId ?? item.pricing_id),
    instanceId: Number(item.instanceId ?? item.instance_id),
    cabinType: item.cabinType ?? item.cabin_type,
    salePrice: Number(item.salePrice ?? item.sale_price ?? 0),
    remainingTickets: Number(item.remainingTickets ?? item.remaining_tickets ?? 0),
    validFrom: item.validFrom ?? item.valid_from,
    validTo: item.validTo ?? item.valid_to
  }
}

const firstRemaining = computed(() => {
  const row = pricingList.value.find((item) => item.cabinType === '头等舱')
  return row?.remainingTickets ?? currentFlight.value?.firstSeats ?? 0
})

const economyRemaining = computed(() => {
  const row = pricingList.value.find((item) => item.cabinType === '经济舱')
  return row?.remainingTickets ?? currentFlight.value?.economySeats ?? 0
})

const formatFlightLabel = (flight) => {
  return `${flight.flightNo} · ${flight.flightDate} · ${formatTime(flight.depTime)}-${formatTime(flight.arrTime)} · ${flight.depAirport || flight.depAirportName || '-'} → ${flight.arrAirport || flight.arrAirportName || '-'}`
}

const formatTime = (value) => {
  if (!value) return '-'

  const text = String(value)

  if (text.includes('T')) {
    return text.slice(11, 16)
  }

  if (text.length >= 16 && text.includes('-')) {
    return text.slice(11, 16)
  }

  return text.slice(0, 5)
}

const formatMoney = (value) => {
  return Number(value || 0).toFixed(2)
}

const toDateTimeText = (date = new Date()) => {
  const pad = (number) => String(number).padStart(2, '0')

  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
}

const getDefaultValidTo = () => {
  const depTime = currentFlight.value?.depTime

  if (!depTime) return ''

  const text = String(depTime)

  if (text.includes('T')) {
    return text.replace('T', ' ').slice(0, 19)
  }

  if (text.length >= 19) {
    return text.slice(0, 19)
  }

  if (currentFlight.value?.flightDate && text.length >= 5) {
    return `${currentFlight.value.flightDate} ${text.slice(0, 5)}:00`
  }

  return ''
}

const syncRouteQuery = () => {
  if (!selectedInstanceId.value) return

  router.replace({
    path: '/admin/pricing',
    query: {
      instanceId: selectedInstanceId.value
    }
  })
}

const loadFlights = async () => {
  flightLoading.value = true

  try {
    const response = await getPricingFlights()
    const payload = unwrap(response)
    const list = Array.isArray(payload) ? payload : (payload?.list || payload?.items || payload?.flights || [])

    flightOptions.value = list.map(normalizeFlight).filter((item) => item.instanceId)

    if (!selectedInstanceId.value && flightOptions.value.length) {
      selectedInstanceId.value = flightOptions.value[0].instanceId
    }

    const matched = flightOptions.value.find((item) => Number(item.instanceId) === Number(selectedInstanceId.value))
    if (matched && !currentFlight.value) {
      currentFlight.value = matched
    }
  } catch (error) {
    console.error('航班列表加载失败：', error)
    ElMessage.error(error.response?.data?.message || '航班列表加载失败')
  } finally {
    flightLoading.value = false
  }
}

const loadCabins = async () => {
  if (!selectedInstanceId.value) {
    pricingList.value = []
    currentFlight.value = null
    return
  }

  priceLoading.value = true

  try {
    const response = await getPricingCabins(selectedInstanceId.value)
    const payload = unwrap(response)

    const rawCabins = payload?.cabins || payload?.items || payload?.list || []
    pricingList.value = rawCabins.map(normalizeCabin)

    if (payload?.flight) {
      currentFlight.value = normalizeFlight(payload.flight)
    } else {
      currentFlight.value =
        flightOptions.value.find((item) => Number(item.instanceId) === Number(selectedInstanceId.value)) ||
        currentFlight.value
    }
  } catch (error) {
    console.error('舱位票价加载失败：', error)
    pricingList.value = []
    ElMessage.error(error.response?.data?.message || '舱位票价加载失败')
  } finally {
    priceLoading.value = false
  }
}

const openCreateDialog = () => {
  const openCreateDialogPermissionGuard = true
  if (!canEditPricingPage.value) {
    ElMessage.warning('当前岗位仅可查看舱位票价，无权新增或修改票价')
    return
  }
  editingRow.value = null
  pricingForm.cabinType = ''
  pricingForm.salePrice = 0
  pricingForm.validFrom = toDateTimeText()
  pricingForm.validTo = getDefaultValidTo()
  dialogVisible.value = true
}

const openEditDialog = (row) => {
  const openEditDialogPermissionGuard = true
  if (!canEditPricingPage.value) {
    ElMessage.warning('当前岗位仅可查看舱位票价，无权新增或修改票价')
    return
  }
  editingRow.value = row
  pricingForm.cabinType = row.cabinType
  pricingForm.salePrice = row.salePrice
  pricingForm.validFrom = row.validFrom
  pricingForm.validTo = row.validTo
  dialogVisible.value = true
}

const handleSave = async () => {
  if (!pricingFormRef.value) return

  await pricingFormRef.value.validate()

  saving.value = true

  const payload = {
    cabin_type: pricingForm.cabinType,
    cabinType: pricingForm.cabinType,
    sale_price: pricingForm.salePrice,
    salePrice: pricingForm.salePrice,
    valid_from: pricingForm.validFrom,
    validFrom: pricingForm.validFrom,
    valid_to: pricingForm.validTo,
    validTo: pricingForm.validTo
  }

  try {
    if (editingRow.value) {
      await updatePricingCabin(editingRow.value.pricingId, payload)
      ElMessage.success('票价更新成功')
    } else {
      await createPricingCabin(selectedInstanceId.value, payload)
      ElMessage.success('票价新增成功')
    }

    dialogVisible.value = false
    await loadCabins()
  } catch (error) {
    console.error('票价保存失败：', error)
    ElMessage.error(error.response?.data?.message || '票价保存失败')
  } finally {
    saving.value = false
  }
}

watch(
  selectedInstanceId,
  async () => {
    syncRouteQuery()
    await loadCabins()
  }
)

onMounted(async () => {
  await loadFlights()
  await loadCabins()
})
</script>

<style scoped>
.pricing-page {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
}

.page-header h2 {
  margin: 0;
  color: #1e293b;
  font-size: 22px;
}

.page-header p {
  margin: 8px 0 0;
  color: #64748b;
}

.select-card,
.table-card,
.flight-summary {
  padding: 18px;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  background: #ffffff;
}

.select-card {
  display: flex;
  align-items: center;
  gap: 14px;
}

.select-label {
  color: #475569;
  font-weight: 600;
}

.flight-summary {
  display: grid;
  grid-template-columns: 1fr 220px 220px;
  gap: 18px;
  align-items: stretch;
}

.flight-main {
  padding: 4px;
}

.flight-no {
  margin-right: 10px;
  color: #1e293b;
  font-size: 22px;
  font-weight: 700;
}

.flight-main p {
  margin: 10px 0 0;
  color: #334155;
}

.sub-text {
  color: #64748b !important;
}

.seat-card {
  padding: 18px 22px;
  border: 1px solid #dbeafe;
  border-radius: 14px;
  background: #f8fbff;
}

.seat-card span {
  display: block;
  color: #64748b;
}

.seat-card strong {
  display: block;
  margin-top: 8px;
  color: #2563eb;
  font-size: 26px;
}

.price-text {
  color: #dc2626;
}

:deep(.el-table th.el-table__cell) {
  background: #f8fafc;
  color: #334155;
  font-weight: 700;
}

@media (max-width: 1100px) {
  .flight-summary {
    grid-template-columns: 1fr;
  }

  .select-card {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>

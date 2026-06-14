<template>
  <PageContainer
    title="舱位票价管理"
    description="查看航班舱位余票，维护票价及其生效时间"
  >
    <template #extra>
      <el-button
        type="primary"
        :disabled="!selectedInstanceId || !canEditPricing"
        @click="handleAdd"
      >
        <el-icon><Plus /></el-icon>
        新增价格
      </el-button>
    </template>

    <div class="filter-card">
      <el-form inline label-width="80px">
        <el-form-item label="选择航班">
          <el-select
            v-model="selectedInstanceId"
            filterable
            placeholder="请选择需要维护票价的航班"
            style="width: 420px"
            @change="loadPricingData"
          >
            <el-option
              v-for="flight in flightList"
              :key="flight.instanceId"
              :label="getFlightLabel(flight)"
              :value="flight.instanceId"
            />
          </el-select>
        </el-form-item>
      </el-form>
    </div>

    <el-alert
      v-if="!canEditPricing"
      title="当前岗位仅可查看舱位票价，无权新增或修改价格记录"
      type="info"
      :closable="false"
      show-icon
      class="permission-alert"
    />

    <div v-if="currentFlight" class="flight-summary">
      <div class="summary-main">
        <div class="summary-title">
          {{ currentFlight.flightNo }}
          <el-tag :type="getFlightStatusType(currentFlight.status)" size="small">
            {{ currentFlight.status }}
          </el-tag>
        </div>
        <div class="summary-route">
          {{ currentFlight.depAirport }} → {{ currentFlight.arrAirport }}
        </div>
        <div class="summary-meta">
          {{ currentFlight.flightDate }} · {{ currentFlight.aircraftModel }}
        </div>
      </div>

      <div class="seat-card">
        <span>经济舱余票</span>
        <strong>{{ remainingSeats.经济舱 }} / {{ currentFlight.economySeats }}</strong>
      </div>
      <div class="seat-card">
        <span>头等舱余票</span>
        <strong>{{ remainingSeats.头等舱 }} / {{ currentFlight.firstSeats }}</strong>
      </div>
    </div>

    <div class="table-card">
      <el-table
        v-loading="loading"
        :data="pricingRows"
        stripe
        border
        table-layout="fixed"
        style="width: 100%"
        empty-text="请选择航班或当前航班暂无价格记录"
      >
        <el-table-column prop="pricingId" label="价格ID" width="100" />
        <el-table-column label="舱位" width="110">
          <template #default="{ row }">
            <el-tag :type="row.cabinType === '头等舱' ? 'warning' : 'primary'">
              {{ row.cabinType }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="销售价格" width="130">
          <template #default="{ row }">
            <strong class="price-text">¥{{ formatMoney(row.salePrice) }}</strong>
          </template>
        </el-table-column>
        <el-table-column prop="remainingSeats" label="剩余票数" width="110" />
        <el-table-column prop="validFrom" label="生效时间" min-width="175" />
        <el-table-column prop="validTo" label="失效时间" min-width="175" />
        <el-table-column label="当前状态" width="110">
          <template #default="{ row }">
            <el-tag :type="row.isCurrentlyEffective ? 'success' : 'info'">
              {{ row.isCurrentlyEffective ? '生效中' : '未生效' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" fixed="right" width="100">
          <template #default="{ row }">
            <el-button
              type="primary"
              link
              :disabled="!canEditPricing"
              @click="handleEdit(row)"
            >
              编辑
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '修改舱位价格' : '新增舱位价格'"
      width="560px"
      @closed="resetForm"
    >
      <el-form
        ref="formRef"
        :model="pricingForm"
        :rules="rules"
        label-width="100px"
      >
        <el-form-item label="舱位类型" prop="cabinType">
          <el-select
            v-model="pricingForm.cabinType"
            placeholder="请选择舱位"
            style="width: 100%"
          >
            <el-option label="经济舱" value="经济舱" />
            <el-option label="头等舱" value="头等舱" />
          </el-select>
        </el-form-item>

        <el-form-item label="销售价格" prop="salePrice">
          <el-input-number
            v-model="pricingForm.salePrice"
            :min="0.01"
            :precision="2"
            :step="50"
            controls-position="right"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="有效时间" prop="validRange">
          <el-date-picker
            v-model="pricingForm.validRange"
            type="datetimerange"
            range-separator="至"
            start-placeholder="生效时间"
            end-placeholder="失效时间"
            value-format="YYYY-MM-DD HH:mm:ss"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          :loading="submitting"
          @click="handleSubmit"
        >
          保存
        </el-button>
      </template>
    </el-dialog>
  </PageContainer>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import PageContainer from '../../../components/admin/PageContainer.vue'
import {
  createFlightPricing,
  getAdminFlightDetail,
  getAdminFlights,
  getFlightPricing,
  updateFlightPricing
} from '../../../api/admin/flight'
import { getAdminOrders } from '../../../api/admin/order'
import {
  canManagePricing,
  getStoredUser
} from '../../../utils/adminAuth'

const route = useRoute()
const router = useRouter()
const formRef = ref()

const loading = ref(false)
const submitting = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const editingPricingId = ref(null)

const flightList = ref([])
const currentFlight = ref(null)
const pricingList = ref([])
const relatedOrders = ref([])
const selectedInstanceId = ref(null)

const currentUser = computed(() => getStoredUser())
const canEditPricing = computed(() => canManagePricing(currentUser.value))

const pricingForm = reactive({
  cabinType: '',
  salePrice: 0,
  validRange: []
})

const rules = {
  cabinType: [
    { required: true, message: '请选择舱位类型', trigger: 'change' }
  ],
  salePrice: [
    { required: true, message: '请输入销售价格', trigger: 'blur' }
  ],
  validRange: [
    { required: true, message: '请选择价格有效时间', trigger: 'change' }
  ]
}

const soldSeats = computed(() => {
  const result = {
    经济舱: 0,
    头等舱: 0
  }

  relatedOrders.value.forEach((order) => {
    if (
      order.instanceId === selectedInstanceId.value &&
      order.recordType === '有效订单' &&
      order.orderStatus === '已支付' &&
      result[order.cabinType] !== undefined
    ) {
      result[order.cabinType] += 1
    }
  })

  return result
})

const remainingSeats = computed(() => {
  if (!currentFlight.value) {
    return {
      经济舱: 0,
      头等舱: 0
    }
  }

  return {
    经济舱: Math.max(
      Number(currentFlight.value.economySeats || 0) - soldSeats.value.经济舱,
      0
    ),
    头等舱: Math.max(
      Number(currentFlight.value.firstSeats || 0) - soldSeats.value.头等舱,
      0
    )
  }
})

const pricingRows = computed(() => {
  return pricingList.value.map((item) => ({
    ...item,
    remainingSeats: remainingSeats.value[item.cabinType] ?? '-'
  }))
})

const getFlightLabel = (flight) => {
  return `${flight.flightNo} · ${flight.flightDate} · ${flight.depAirport} → ${flight.arrAirport}`
}

const loadFlights = async () => {
  try {
    const response = await getAdminFlights()
    flightList.value = response.data.data || []

    const queryInstanceId = Number(route.query.instanceId)
    const matchedFlight = flightList.value.find(
      (item) => item.instanceId === queryInstanceId
    )

    if (matchedFlight) {
      selectedInstanceId.value = matchedFlight.instanceId
    } else if (flightList.value.length) {
      selectedInstanceId.value = flightList.value[0].instanceId
    }

    if (selectedInstanceId.value) {
      await loadPricingData()
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '航班数据加载失败')
    console.error(error)
  }
}

const loadPricingData = async () => {
  if (!selectedInstanceId.value) return

  loading.value = true

  try {
    const [flightResponse, pricingResponse, orderResponse] = await Promise.all([
      getAdminFlightDetail(selectedInstanceId.value),
      getFlightPricing(selectedInstanceId.value),
      getAdminOrders()
    ])

    currentFlight.value = flightResponse.data.data || null
    pricingList.value = pricingResponse.data.data || []
    relatedOrders.value = orderResponse.data.data || []

    router.replace({
      path: '/admin/pricing',
      query: {
        instanceId: selectedInstanceId.value
      }
    })
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '舱位票价加载失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

const resetForm = () => {
  pricingForm.cabinType = ''
  pricingForm.salePrice = 0
  pricingForm.validRange = []
  editingPricingId.value = null
  formRef.value?.clearValidate()
}

const handleAdd = () => {
  isEdit.value = false
  resetForm()
  dialogVisible.value = true
}

const handleEdit = (row) => {
  isEdit.value = true
  editingPricingId.value = row.pricingId
  pricingForm.cabinType = row.cabinType
  pricingForm.salePrice = row.salePrice
  pricingForm.validRange = [row.validFrom, row.validTo]
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!canEditPricing.value || !formRef.value) return

  const valid = await formRef.value.validate().catch(() => false)

  if (!valid) return

  const payload = {
    cabin_type: pricingForm.cabinType,
    sale_price: pricingForm.salePrice,
    valid_from: pricingForm.validRange[0],
    valid_to: pricingForm.validRange[1]
  }

  submitting.value = true

  try {
    if (isEdit.value) {
      await updateFlightPricing(editingPricingId.value, payload)
      ElMessage.success('舱位价格已修改')
    } else {
      await createFlightPricing(selectedInstanceId.value, payload)
      ElMessage.success('舱位价格已新增')
    }

    dialogVisible.value = false
    await loadPricingData()
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '舱位价格保存失败')
    console.error(error)
  } finally {
    submitting.value = false
  }
}

const formatMoney = (value) => {
  return Number(value || 0).toFixed(2)
}

const getFlightStatusType = (status) => {
  if (status === '正常') return 'success'
  if (status === '延误') return 'warning'
  if (status === '取消') return 'danger'
  return 'info'
}

onMounted(() => {
  loadFlights()
})
</script>

<style scoped>
.filter-card {
  margin-bottom: 18px;
  padding: 18px 18px 0;
  border-radius: 16px;
  background: linear-gradient(135deg, #f8fafc 0%, #ffffff 100%);
  border: 1px solid #e2e8f0;
}

.permission-alert {
  margin-bottom: 18px;
}

.flight-summary {
  display: grid;
  grid-template-columns: minmax(280px, 1fr) 180px 180px;
  gap: 16px;
  margin-bottom: 18px;
}

.summary-main,
.seat-card {
  padding: 18px;
  border-radius: 16px;
  background: #ffffff;
  border: 1px solid #e2e8f0;
}

.summary-title {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #1e293b;
  font-size: 18px;
  font-weight: 700;
}

.summary-route {
  margin-top: 8px;
  color: #334155;
}

.summary-meta {
  margin-top: 6px;
  color: #94a3b8;
  font-size: 13px;
}

.seat-card {
  display: flex;
  flex-direction: column;
  justify-content: center;
  color: #64748b;
  font-size: 13px;
}

.seat-card strong {
  margin-top: 8px;
  color: #2563eb;
  font-size: 22px;
}

.table-card {
  padding: 18px;
  border-radius: 16px;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  max-width: 100%;
  overflow-x: auto;
}

.price-text {
  color: #dc2626;
}

:deep(.el-form-item) {
  margin-bottom: 18px;
}

:deep(.el-table) {
  border-radius: 12px;
  overflow: hidden;
}

:deep(.el-table th.el-table__cell) {
  background: #f8fafc;
  color: #334155;
  font-weight: 600;
}

@media (max-width: 1000px) {
  .flight-summary {
    grid-template-columns: 1fr;
  }
}
</style>

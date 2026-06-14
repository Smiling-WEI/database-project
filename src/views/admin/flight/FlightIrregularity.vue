<template>
  <PageContainer
    title="航班异常处理"
    description="发布、查看并解除指定航班的异常记录"
  >
    <template #extra>
      <div class="page-actions">
        <el-button @click="goBack">返回航班列表</el-button>
        <el-button type="primary" plain @click="affectedVisible = true">
          受影响订单（{{ affectedOrders.length }}）
        </el-button>
        <el-button
          type="warning"
          :disabled="!canEditIrregularities"
          @click="handlePublish"
        >
          发布异常
        </el-button>
      </div>
    </template>

    <el-alert
      v-if="!canEditIrregularities"
      title="当前岗位仅可查看航班异常记录，无权发布或解除异常"
      type="info"
      :closable="false"
      show-icon
      class="permission-alert"
    />

    <div v-if="flight" class="flight-card">
      <div>
        <div class="flight-title">
          {{ flight.flightNo }}
          <el-tag :type="getFlightStatusType(flight.status)">
            {{ flight.status }}
          </el-tag>
        </div>
        <div class="flight-route">
          {{ flight.depAirport }} → {{ flight.arrAirport }}
        </div>
        <div class="flight-meta">
          {{ flight.flightDate }} · {{ flight.airlineName }} · {{ flight.aircraftModel }}
        </div>
      </div>

      <div class="active-count">
        <span>生效中异常</span>
        <strong>{{ activeCount }}</strong>
      </div>
      <div class="affected-count">
        <span>受影响有效订单</span>
        <strong>{{ affectedOrders.length }}</strong>
      </div>
    </div>

    <div class="table-card">
      <el-table
        v-loading="loading"
        :data="irregularityList"
        stripe
        border
        table-layout="fixed"
        style="width: 100%"
        empty-text="当前航班暂无异常记录"
      >
        <el-table-column prop="irregularityId" label="异常ID" width="100" />
        <el-table-column label="异常类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getIrregularityType(row.irregularityType)">
              {{ row.irregularityType }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="responsibilityType" label="责任类型" width="120" />
        <el-table-column prop="description" label="异常说明" min-width="240">
          <template #default="{ row }">
            {{ row.description || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="publishedBy" label="发布人ID" width="110" />
        <el-table-column prop="createdAt" label="发布时间" width="175" />
        <el-table-column prop="resolvedAt" label="解除时间" width="175">
          <template #default="{ row }">
            {{ row.resolvedAt || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === '生效中' ? 'danger' : 'info'">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" fixed="right" width="100">
          <template #default="{ row }">
            <el-button
              v-if="row.status === '生效中'"
              type="success"
              link
              :disabled="!canEditIrregularities"
              @click="handleResolve(row)"
            >
              解除
            </el-button>
            <span v-else class="resolved-text">已解除</span>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog
      v-model="dialogVisible"
      title="发布航班异常"
      width="560px"
      @closed="resetForm"
    >
      <el-form
        ref="formRef"
        :model="irregularityForm"
        :rules="rules"
        label-width="100px"
      >
        <el-form-item label="异常类型" prop="irregularityType">
          <el-select
            v-model="irregularityForm.irregularityType"
            placeholder="请选择异常类型"
            style="width: 100%"
          >
            <el-option label="延误" value="延误" />
            <el-option label="取消" value="取消" />
            <el-option label="航班调整" value="航班调整" />
          </el-select>
        </el-form-item>

        <el-form-item label="责任类型" prop="responsibilityType">
          <el-select
            v-model="irregularityForm.responsibilityType"
            placeholder="请选择责任类型"
            style="width: 100%"
          >
            <el-option label="航司原因" value="航司原因" />
            <el-option label="天气原因" value="天气原因" />
            <el-option label="其他原因" value="其他原因" />
          </el-select>
        </el-form-item>

        <el-form-item label="异常说明" prop="description">
          <el-input
            v-model="irregularityForm.description"
            type="textarea"
            :rows="4"
            maxlength="500"
            show-word-limit
            placeholder="请输入异常原因、预计影响或处理说明"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button
          type="warning"
          :loading="submitting"
          @click="handleSubmit"
        >
          确认发布
        </el-button>
      </template>
    </el-dialog>

    <el-drawer
      v-model="affectedVisible"
      title="受影响订单"
      size="72%"
    >
      <el-alert
        title="仅展示当前仍可处理的有效订单，可直接进入后台改签流程。"
        type="info"
        :closable="false"
        show-icon
        class="permission-alert"
      />

      <el-table
        v-loading="affectedLoading"
        :data="affectedOrders"
        border
        stripe
        empty-text="暂无受影响订单"
      >
        <el-table-column prop="orderId" label="订单ID" width="100" />
        <el-table-column prop="username" label="用户账号" width="130" />
        <el-table-column prop="passengerName" label="乘机人" width="110" />
        <el-table-column prop="phone" label="联系电话" width="135" />
        <el-table-column prop="cabinType" label="舱位" width="100" />
        <el-table-column prop="seatNo" label="座位号" width="100" />
        <el-table-column label="票价" width="110">
          <template #default="{ row }">¥{{ Number(row.price || 0).toFixed(2) }}</template>
        </el-table-column>
        <el-table-column label="处理状态" width="110">
          <template #default="{ row }">
            <el-tag :type="row.handlingStatus === '已处理' ? 'success' : 'warning'">
              {{ row.handlingStatus || '待处理' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" fixed="right" width="110">
          <template #default="{ row }">
            <el-button
              type="warning"
              link
              :disabled="!canEditIrregularities || row.handlingStatus === '已处理'"
              @click="goAssistChange(row)"
            >
              代办改签
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-drawer>
  </PageContainer>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import PageContainer from '../../../components/admin/PageContainer.vue'
import {
  createFlightIrregularity,
  getAffectedOrders,
  getAdminFlightDetail,
  getFlightIrregularities,
  resolveFlightIrregularity
} from '../../../api/admin/flight'
import {
  canManageFlights,
  getStoredUser
} from '../../../utils/adminAuth'

const route = useRoute()
const router = useRouter()
const formRef = ref()

const loading = ref(false)
const submitting = ref(false)
const dialogVisible = ref(false)
const flight = ref(null)
const irregularityList = ref([])
const affectedOrders = ref([])
const affectedVisible = ref(false)
const affectedLoading = ref(false)

const instanceId = computed(() => Number(route.params.instanceId))
const currentUser = computed(() => getStoredUser())
const canEditIrregularities = computed(() => canManageFlights(currentUser.value))
const activeCount = computed(() => {
  return irregularityList.value.filter((item) => item.status === '生效中').length
})

const irregularityForm = reactive({
  irregularityType: '',
  responsibilityType: '',
  description: ''
})

const rules = {
  irregularityType: [
    { required: true, message: '请选择异常类型', trigger: 'change' }
  ],
  responsibilityType: [
    { required: true, message: '请选择责任类型', trigger: 'change' }
  ]
}

const loadData = async () => {
  if (!instanceId.value) {
    ElMessage.warning('缺少航班实例信息')
    goBack()
    return
  }

  loading.value = true

  try {
    const [flightResponse, irregularityResponse] = await Promise.all([
      getAdminFlightDetail(instanceId.value),
      getFlightIrregularities(instanceId.value)
    ])

    flight.value = flightResponse.data.data || null
    irregularityList.value = irregularityResponse.data.data || []
    await loadAffectedOrders()
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '航班异常记录加载失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

const loadAffectedOrders = async () => {
  affectedLoading.value = true
  try {
    const response = await getAffectedOrders(instanceId.value)
    affectedOrders.value = response.data.data || []
  } catch (error) {
    affectedOrders.value = []
    ElMessage.warning(
      error.response?.data?.message ||
      '受影响订单接口待后端接入'
    )
  } finally {
    affectedLoading.value = false
  }
}

const resetForm = () => {
  irregularityForm.irregularityType = ''
  irregularityForm.responsibilityType = ''
  irregularityForm.description = ''
  formRef.value?.clearValidate()
}

const handlePublish = () => {
  resetForm()
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!canEditIrregularities.value || !formRef.value) return

  const valid = await formRef.value.validate().catch(() => false)

  if (!valid) return

  submitting.value = true

  try {
    await createFlightIrregularity(instanceId.value, {
      irregularity_type: irregularityForm.irregularityType,
      responsibility_type: irregularityForm.responsibilityType,
      description: irregularityForm.description.trim()
    })

    ElMessage.success('航班异常已发布')
    dialogVisible.value = false
    await loadData()
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '航班异常发布失败')
    console.error(error)
  } finally {
    submitting.value = false
  }
}

const handleResolve = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确认解除“${row.irregularityType}”异常记录吗？`,
      '解除异常确认',
      {
        confirmButtonText: '确认解除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await resolveFlightIrregularity(row.irregularityId)
    ElMessage.success('航班异常已解除')
    await loadData()
  } catch (error) {
    if (error === 'cancel' || error === 'close') return

    ElMessage.error(error.response?.data?.message || '航班异常解除失败')
    console.error(error)
  }
}

const goBack = () => {
  router.push('/admin/flights')
}

const goAssistChange = (row) => {
  router.push({
    path: '/admin/orders',
    query: {
      orderId: row.orderId,
      action: 'change',
      irregularityId: irregularityList.value.find(
        (item) => item.status === '生效中'
      )?.irregularityId || ''
    }
  })
}

const getFlightStatusType = (status) => {
  if (status === '正常') return 'success'
  if (status === '延误') return 'warning'
  if (status === '取消') return 'danger'
  return 'info'
}

const getIrregularityType = (type) => {
  if (type === '取消') return 'danger'
  if (type === '延误') return 'warning'
  return 'primary'
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.page-actions {
  display: flex;
  gap: 10px;
}

.permission-alert {
  margin-bottom: 18px;
}

.flight-card {
  margin-bottom: 18px;
  padding: 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  border-radius: 16px;
  background: linear-gradient(135deg, #ffffff 0%, #f8fbff 100%);
  border: 1px solid #e2e8f0;
}

.flight-title {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #1e293b;
  font-size: 20px;
  font-weight: 700;
}

.flight-route {
  margin-top: 10px;
  color: #334155;
}

.flight-meta {
  margin-top: 6px;
  color: #94a3b8;
  font-size: 13px;
}

.active-count {
  min-width: 130px;
  padding: 14px 18px;
  display: flex;
  flex-direction: column;
  border-radius: 14px;
  color: #64748b;
  font-size: 13px;
  background: #fff7ed;
  border: 1px solid #fed7aa;
}

.affected-count {
  min-width: 145px;
  padding: 14px 18px;
  display: flex;
  flex-direction: column;
  border-radius: 14px;
  color: #64748b;
  font-size: 13px;
  background: #eff6ff;
  border: 1px solid #bfdbfe;
}

.affected-count strong {
  margin-top: 4px;
  color: #2563eb;
  font-size: 24px;
}

.active-count strong {
  margin-top: 4px;
  color: #ea580c;
  font-size: 24px;
}

.table-card {
  padding: 18px;
  border-radius: 16px;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  max-width: 100%;
  overflow-x: auto;
}

.resolved-text {
  color: #94a3b8;
  font-size: 13px;
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
</style>

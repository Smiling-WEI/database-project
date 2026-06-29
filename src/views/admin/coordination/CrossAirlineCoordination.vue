<template>
  <PageContainer title="跨航司协调">
    <div class="coordination-page">
      <div class="page-header">
        <h2>跨航司协调</h2>
        <p>集中处理航班异常引发的跨航空公司改签与协同业务</p>
      </div>

      <el-alert
        title="该页面仅对系统总管理员开放，数据由跨航司改签记录自动汇总。"
        type="info"
        show-icon
        :closable="false"
      />

      <div class="filter-card">
        <el-form :model="queryForm" inline label-width="100px">
          <el-form-item label="原航空公司">
            <el-select
              v-model="queryForm.sourceAirlineId"
              clearable
              filterable
              placeholder="全部航空公司"
              style="width: 220px"
            >
              <el-option
                v-for="airline in airlineOptions"
                :key="airline.airlineId"
                :label="airline.airlineName"
                :value="airline.airlineId"
              />
            </el-select>
          </el-form-item>

          <el-form-item label="目标航空公司">
            <el-select
              v-model="queryForm.targetAirlineId"
              clearable
              filterable
              placeholder="全部目标航司"
              style="width: 220px"
            >
              <el-option
                v-for="airline in airlineOptions"
                :key="airline.airlineId"
                :label="airline.airlineName"
                :value="airline.airlineId"
              />
            </el-select>
          </el-form-item>

          <el-form-item label="协调状态">
            <el-select
              v-model="queryForm.status"
              clearable
              placeholder="全部状态"
              style="width: 160px"
            >
              <el-option label="待处理" value="待处理" />
              <el-option label="已完成" value="已完成" />
            </el-select>
          </el-form-item>

          <el-form-item>
            <el-button type="primary" @click="loadCases">
              查询
            </el-button>
            <el-button @click="handleReset">
              重置
            </el-button>
          </el-form-item>
        </el-form>
      </div>

      <div class="stats-grid">
        <div class="stat-card total">
          <span>协调案例</span>
          <strong>{{ summary.total }}</strong>
        </div>

        <div class="stat-card pending">
          <span>待处理</span>
          <strong>{{ summary.pending }}</strong>
        </div>

        <div class="stat-card completed">
          <span>已完成</span>
          <strong>{{ summary.completed }}</strong>
        </div>
      </div>

      <div class="table-card">
        <el-table
          v-loading="loading"
          :data="caseList"
          border
          stripe
          table-layout="fixed"
          style="width: 100%"
          empty-text="暂无跨航司协调案例"
        >
          <el-table-column prop="caseId" label="案例ID" width="100" />

          <el-table-column label="异常类型" width="150">
            <template #default="{ row }">
              {{ row.irregularityType || '跨航司改签' }}
            </template>
          </el-table-column>

          <el-table-column label="原航班" min-width="260">
            <template #default="{ row }">
              <div class="flight-cell">
                <strong>{{ row.sourceFlightNo }}</strong>
                <span>{{ row.sourceAirlineName }}</span>
                <span>{{ row.sourceFlightDate }} {{ row.sourceDepTime }}-{{ row.sourceArrTime }}</span>
                <span>{{ row.sourceDepAirport }} → {{ row.sourceArrAirport }}</span>
              </div>
            </template>
          </el-table-column>

          <el-table-column label="目标航班" min-width="260">
            <template #default="{ row }">
              <div class="flight-cell">
                <strong>{{ row.targetFlightNo }}</strong>
                <span>{{ row.targetAirlineName }}</span>
                <span>{{ row.targetFlightDate }} {{ row.targetDepTime }}-{{ row.targetArrTime }}</span>
                <span>{{ row.targetDepAirport }} → {{ row.targetArrAirport }}</span>
              </div>
            </template>
          </el-table-column>

          <el-table-column label="受影响订单" width="130">
            <template #default="{ row }">
              {{ row.affectedOrderCount || 1 }}
            </template>
          </el-table-column>

          <el-table-column label="状态" width="110">
            <template #default="{ row }">
              <el-tag :type="row.status === '已完成' ? 'success' : 'warning'">
                {{ row.status }}
              </el-tag>
            </template>
          </el-table-column>

          <el-table-column prop="createdAt" label="创建时间" width="175" show-overflow-tooltip />

          <el-table-column label="操作" fixed="right" width="150">
            <template #default="{ row }">
              <el-button type="primary" link @click="handleView(row)">
                详情
              </el-button>
              <el-button type="primary" link @click="goOrders(row)">
                订单
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <el-dialog
        v-model="detailVisible"
        title="跨航司协调详情"
        width="760px"
      >
        <div v-if="currentCase" class="detail-box">
          <div class="detail-row">
            <span>案例ID</span>
            <strong>{{ currentCase.caseId }}</strong>
          </div>

          <div class="detail-row">
            <span>原订单</span>
            <strong>{{ currentCase.oldOrderId }}</strong>
          </div>

          <div class="detail-row">
            <span>新订单</span>
            <strong>{{ currentCase.newOrderId }}</strong>
          </div>

          <div class="detail-row">
            <span>乘机人</span>
            <strong>{{ currentCase.passengerName }}</strong>
          </div>

          <div class="detail-row">
            <span>原航司</span>
            <strong>{{ currentCase.sourceAirlineName }}</strong>
          </div>

          <div class="detail-row">
            <span>目标航司</span>
            <strong>{{ currentCase.targetAirlineName }}</strong>
          </div>

          <div class="detail-row">
            <span>原航班</span>
            <strong>
              {{ currentCase.sourceFlightNo }}
              ·
              {{ currentCase.sourceFlightDate }}
              {{ currentCase.sourceDepTime }}-{{ currentCase.sourceArrTime }}
            </strong>
          </div>

          <div class="detail-row">
            <span>目标航班</span>
            <strong>
              {{ currentCase.targetFlightNo }}
              ·
              {{ currentCase.targetFlightDate }}
              {{ currentCase.targetDepTime }}-{{ currentCase.targetArrTime }}
            </strong>
          </div>

          <div class="detail-row">
            <span>改签原因</span>
            <strong>{{ currentCase.changeReason || '-' }}</strong>
          </div>

          <div class="detail-row">
            <span>协调状态</span>
            <el-tag :type="currentCase.status === '已完成' ? 'success' : 'warning'">
              {{ currentCase.status }}
            </el-tag>
          </div>

          <div class="detail-row">
            <span>创建时间</span>
            <strong>{{ currentCase.createdAt }}</strong>
          </div>

          <div class="detail-row">
            <span>完成时间</span>
            <strong>{{ currentCase.completedAt || '-' }}</strong>
          </div>
        </div>

        <template #footer>
          <el-button @click="detailVisible = false">
            关闭
          </el-button>
        </template>
      </el-dialog>
    </div>
  </PageContainer>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import PageContainer from '../../../components/admin/PageContainer.vue'
import {
  getCoordinationAirlines,
  getCoordinationCases
} from '../../../api/admin/coordinationDirect'

const router = useRouter()

const loading = ref(false)
const airlineOptions = ref([])
const caseList = ref([])

const detailVisible = ref(false)
const currentCase = ref(null)

const queryForm = reactive({
  sourceAirlineId: '',
  targetAirlineId: '',
  status: ''
})

const unwrap = (response) => {
  if (response?.data?.data !== undefined) return response.data.data
  if (response?.data !== undefined) return response.data
  return response
}

const summary = computed(() => {
  return {
    total: caseList.value.length,
    pending: caseList.value.filter((item) => item.status === '待处理').length,
    completed: caseList.value.filter((item) => item.status === '已完成').length
  }
})

const normalizeAirline = (item) => {
  return {
    airlineId: Number(item.airlineId ?? item.airline_id),
    airlineName: item.airlineName ?? item.airline_name,
    airlineCode: item.airlineCode ?? item.airline_code
  }
}

const normalizeCase = (item) => {
  return {
    caseId: item.caseId ?? item.case_id ?? item.changeId,
    oldOrderId: item.oldOrderId ?? item.old_order_id,
    newOrderId: item.newOrderId ?? item.new_order_id,

    irregularityType: item.irregularityType ?? item.irregularity_type ?? '跨航司改签',
    irregularityId: item.irregularityId ?? item.irregularity_id,
    changeReason: item.changeReason ?? item.change_reason,

    passengerName: item.passengerName ?? item.passenger_name,

    sourceAirlineName: item.sourceAirlineName ?? item.source_airline_name,
    targetAirlineName: item.targetAirlineName ?? item.target_airline_name,

    sourceInstanceId: item.sourceInstanceId ?? item.source_instance_id,
    sourceFlightNo: item.sourceFlightNo ?? item.source_flight_no,
    sourceFlightDate: item.sourceFlightDate ?? item.source_flight_date,
    sourceDepTime: item.sourceDepTime ?? item.source_dep_time,
    sourceArrTime: item.sourceArrTime ?? item.source_arr_time,
    sourceDepAirport: item.sourceDepAirport ?? item.source_dep_airport,
    sourceArrAirport: item.sourceArrAirport ?? item.source_arr_airport,

    targetInstanceId: item.targetInstanceId ?? item.target_instance_id,
    targetFlightNo: item.targetFlightNo ?? item.target_flight_no,
    targetFlightDate: item.targetFlightDate ?? item.target_flight_date,
    targetDepTime: item.targetDepTime ?? item.target_dep_time,
    targetArrTime: item.targetArrTime ?? item.target_arr_time,
    targetDepAirport: item.targetDepAirport ?? item.target_dep_airport,
    targetArrAirport: item.targetArrAirport ?? item.target_arr_airport,

    affectedOrderCount: item.affectedOrderCount ?? item.affected_order_count ?? 1,

    status: item.status ?? item.coordinationStatus ?? item.coordination_status ?? '已完成',
    createdAt: item.createdAt ?? item.created_at,
    completedAt: item.completedAt ?? item.completed_at
  }
}

const loadAirlines = async () => {
  try {
    const response = await getCoordinationAirlines()
    const payload = unwrap(response)
    const list = Array.isArray(payload) ? payload : (payload?.list || payload?.items || [])

    airlineOptions.value = list.map(normalizeAirline).filter((item) => item.airlineId)
  } catch (error) {
    console.error('航空公司列表加载失败：', error)
    ElMessage.error(error.response?.data?.message || '航空公司列表加载失败')
  }
}

const loadCases = async () => {
  loading.value = true

  const params = {}

  if (queryForm.sourceAirlineId) {
    params.airline_id = queryForm.sourceAirlineId
  }

  if (queryForm.targetAirlineId) {
    params.target_airline_id = queryForm.targetAirlineId
  }

  if (queryForm.status) {
    params.status = queryForm.status
  }

  try {
    const response = await getCoordinationCases(params)
    const payload = unwrap(response)
    const list = Array.isArray(payload)
      ? payload
      : (payload?.cases || payload?.list || payload?.items || [])

    caseList.value = list.map(normalizeCase)
  } catch (error) {
    console.error('跨航司协调案例加载失败：', error)
    caseList.value = []
    ElMessage.error(error.response?.data?.message || '跨航司协调案例加载失败')
  } finally {
    loading.value = false
  }
}

const handleReset = () => {
  queryForm.sourceAirlineId = ''
  queryForm.targetAirlineId = ''
  queryForm.status = ''
  loadCases()
}

const handleView = (row) => {
  currentCase.value = row
  detailVisible.value = true
}

const goOrders = (row) => {
  router.push({
    path: '/admin/orders',
    query: {
      orderId: row.oldOrderId
    }
  })
}

onMounted(async () => {
  await loadAirlines()
  await loadCases()
})
</script>

<style scoped>
.coordination-page {
  display: flex;
  flex-direction: column;
  gap: 18px;
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

.filter-card,
.table-card {
  padding: 18px;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  background: #ffffff;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 18px;
}

.stat-card {
  padding: 22px;
  border-radius: 16px;
  border: 1px solid #dbeafe;
}

.stat-card span {
  display: block;
  color: #64748b;
}

.stat-card strong {
  display: block;
  margin-top: 10px;
  color: #1e293b;
  font-size: 28px;
}

.stat-card.total {
  background: #eff6ff;
  border-color: #bfdbfe;
}

.stat-card.pending {
  background: #fff7ed;
  border-color: #fed7aa;
}

.stat-card.completed {
  background: #f0fdf4;
  border-color: #bbf7d0;
}

.flight-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
  line-height: 1.4;
}

.flight-cell strong {
  color: #1e293b;
}

.flight-cell span {
  color: #64748b;
}

.detail-box {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.detail-row {
  min-height: 34px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 18px;
  border-bottom: 1px solid #e2e8f0;
}

.detail-row span {
  color: #64748b;
}

.detail-row strong {
  color: #1e293b;
  text-align: right;
  word-break: break-all;
}

:deep(.el-table th.el-table__cell) {
  background: #f8fafc;
  color: #334155;
  font-weight: 700;
}

@media (max-width: 1100px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>

<template>
  <PageContainer
    title="跨航司协调"
    description="集中处理航班异常引发的跨航空公司改签与协同业务"
  >
    <el-alert
      title="该页面仅对系统总管理员开放；数据由跨航司协调接口统一返回。"
      type="info"
      :closable="false"
      show-icon
      class="notice"
    />

    <div class="filter-card">
      <el-form :model="queryForm" inline label-width="90px">
        <AirlineScopeSelect
          v-model="queryForm.sourceAirlineId"
          @change="loadCases"
        />
        <el-form-item label="目标航空公司">
          <el-select
            v-model="queryForm.targetAirlineId"
            clearable
            filterable
            placeholder="全部目标航司"
            style="width: 220px"
            @change="loadCases"
          >
            <el-option
              v-for="airline in airlines"
              :key="airline.airlineId"
              :label="`${airline.airlineName}（${airline.airlineCode}）`"
              :value="airline.airlineId"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="协调状态">
          <el-select
            v-model="queryForm.status"
            clearable
            placeholder="全部状态"
            style="width: 140px"
          >
            <el-option label="待协调" value="待协调" />
            <el-option label="处理中" value="处理中" />
            <el-option label="已完成" value="已完成" />
            <el-option label="已取消" value="已取消" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadCases">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <div class="summary-grid">
      <div class="summary-card">
        <span>协调案例</span>
        <strong>{{ cases.length }}</strong>
      </div>
      <div class="summary-card warning">
        <span>待处理</span>
        <strong>{{ pendingCount }}</strong>
      </div>
      <div class="summary-card success">
        <span>已完成</span>
        <strong>{{ completedCount }}</strong>
      </div>
    </div>

    <div class="table-card">
      <el-table
        v-loading="loading"
        :data="cases"
        border
        stripe
        empty-text="暂无跨航司协调案例"
      >
        <el-table-column prop="caseId" label="案例ID" width="90" />
        <el-table-column prop="irregularityType" label="异常类型" width="105" />
        <el-table-column label="原航班" min-width="190">
          <template #default="{ row }">
            {{ row.sourceAirlineName }} · {{ row.sourceFlightNo }}
          </template>
        </el-table-column>
        <el-table-column label="目标航班" min-width="190">
          <template #default="{ row }">
            {{ row.targetAirlineName || '待确定' }} · {{ row.targetFlightNo || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="affectedOrderCount" label="受影响订单" width="115" />
        <el-table-column prop="pendingOrderCount" label="待处理订单" width="115" />
        <el-table-column prop="coordinatorName" label="协调负责人" width="120" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="updatedAt" label="更新时间" width="175" />
        <el-table-column label="操作" fixed="right" width="180">
          <template #default="{ row }">
            <el-button type="primary" link @click="goIrregularity(row)">
              查看异常
            </el-button>
            <el-button type="warning" link @click="goOrders(row)">
              处理订单
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </PageContainer>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import PageContainer from '../../../components/admin/PageContainer.vue'
import AirlineScopeSelect from '../../../components/admin/AirlineScopeSelect.vue'
import { getAdminAirlines, getCrossAirlineCases } from '../../../api/admin/airline'

const router = useRouter()
const loading = ref(false)
const cases = ref([])
const airlines = ref([])
const queryForm = reactive({
  sourceAirlineId: '',
  targetAirlineId: '',
  status: ''
})

const pendingCount = computed(() => {
  return cases.value.filter((item) => ['待协调', '处理中'].includes(item.status)).length
})

const completedCount = computed(() => {
  return cases.value.filter((item) => item.status === '已完成').length
})

const loadAirlines = async () => {
  try {
    const response = await getAdminAirlines()
    airlines.value = response.data.data || []
  } catch {
    airlines.value = []
  }
}

const loadCases = async () => {
  loading.value = true
  try {
    const response = await getCrossAirlineCases({
      source_airline_id: queryForm.sourceAirlineId || undefined,
      target_airline_id: queryForm.targetAirlineId || undefined,
      status: queryForm.status || undefined
    })
    cases.value = response.data.data || []
  } catch (error) {
    cases.value = []
    ElMessage.error(error.response?.data?.message || '跨航司协调接口待后端接入')
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

const goIrregularity = (row) => {
  router.push(`/admin/flights/${row.sourceInstanceId}/irregularities`)
}

const goOrders = (row) => {
  router.push({
    path: '/admin/orders',
    query: {
      airlineId: row.sourceAirlineId,
      irregularityId: row.irregularityId
    }
  })
}

const getStatusType = (status) => {
  if (status === '已完成') return 'success'
  if (status === '处理中') return 'warning'
  if (status === '待协调') return 'danger'
  return 'info'
}

onMounted(() => {
  loadAirlines()
  loadCases()
})
</script>

<style scoped>
.notice,
.filter-card,
.summary-grid {
  margin-bottom: 18px;
}

.filter-card {
  padding: 18px 18px 0;
  border-radius: 16px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(160px, 1fr));
  gap: 16px;
}

.summary-card {
  padding: 18px;
  border-radius: 16px;
  background: #eff6ff;
  border: 1px solid #bfdbfe;
}

.summary-card.warning {
  background: #fff7ed;
  border-color: #fed7aa;
}

.summary-card.success {
  background: #f0fdf4;
  border-color: #bbf7d0;
}

.summary-card span {
  color: #64748b;
  font-size: 13px;
}

.summary-card strong {
  display: block;
  margin-top: 6px;
  color: #1e293b;
  font-size: 26px;
}

.table-card {
  padding: 18px;
  border-radius: 16px;
  background: #fff;
  border: 1px solid #e2e8f0;
  overflow-x: auto;
}
</style>

<template>
  <PageContainer
    title="航班管理"
    description="维护航班实例、起降时间、执飞机型、座位数与运行状态"
  >
    <template #extra>
      <el-button
        type="primary"
        :disabled="!canManageFlights || isFlightReadonly(row)"
        @click="goAddFlight"
      >
        <el-icon><Plus /></el-icon>
        新增航班
      </el-button>
    </template>

    <div v-if="systemAdmin" class="scope-card">
      <el-form inline label-width="80px">
        <AirlineScopeSelect
          v-model="selectedAirlineId"
          @change="loadFlights"
        />
      </el-form>
    </div>

    <div class="filter-card">
      <el-form
        :model="queryForm"
        inline
        label-width="80px"
      >
        <el-form-item label="航班日期">
          <el-date-picker
            v-model="queryForm.date"
            type="date"
            placeholder="请选择日期"
            value-format="YYYY-MM-DD"
            clearable
            style="width: 170px"
          />
        </el-form-item>

        <el-form-item label="航班状态">
          <el-select
            v-model="queryForm.status"
            placeholder="请选择状态"
            clearable
            style="width: 150px"
          >
            <el-option label="正常" value="正常" />
            <el-option label="延误" value="延误" />
            <el-option label="取消" value="取消" />
            <el-option label="航班调整" value="航班调整" />
            <el-option label="已完成" value="已完成" />
          </el-select>
        </el-form-item>

        <el-form-item label="航班号">
          <el-input
            v-model="queryForm.flightNo"
            placeholder="请输入航班号"
            clearable
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            查询
          </el-button>
          <el-button @click="handleReset">
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </div>

    <el-alert
      v-if="!canManageFlights"
      title="当前岗位仅可查看航班信息，无权新增、编辑航班或发布航班异常"
      type="info"
      :closable="false"
      show-icon
      class="permission-alert"
    />

    <div class="table-card">
      <el-table
        :data="pagedFlights"
        stripe
        border
        table-layout="fixed"
        style="width: 100%"
        empty-text="暂无航班数据"
      >
        <el-table-column prop="instanceId" label="实例ID" width="90" />
        <el-table-column prop="flightNo" label="航班号" width="110" />
        <el-table-column prop="flightDate" label="航班日期" width="120" />
        <el-table-column prop="depTime" label="起飞时间" width="100" />
        <el-table-column prop="arrTime" label="到达时间" width="100" />
        <el-table-column prop="airlineName" label="航空公司" width="140" show-overflow-tooltip />
        <el-table-column prop="depAirport" label="出发机场" min-width="160" show-overflow-tooltip />
        <el-table-column prop="arrAirport" label="到达机场" min-width="160" show-overflow-tooltip />
        <el-table-column prop="aircraftModel" label="执飞机型" width="120" show-overflow-tooltip />
        <el-table-column prop="firstSeats" label="头等舱座位" width="120" />
        <el-table-column prop="economySeats" label="经济舱座位" width="120" />

        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getFlightDisplayStatus(row) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="操作" fixed="right" width="220">
          <template #default="{ row }">
            <el-button
              type="primary"
              link
              :disabled="!canManageFlights"
              @click="goEditFlight(row)"
            >
              编辑
            </el-button>

            <el-button
              type="success"
              link
              @click="goPricing(row)"
            >
              票价
            </el-button>

            <el-button
              type="warning"
              link
              :disabled="!canEditFlightPage" @click="goIrregularity(row)"
            >
              异常
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="pagination.currentPage"
          v-model:page-size="pagination.pageSize"
          background
          layout="total, prev, pager, next"
          :total="filteredFlights.length"
        />
      </div>
    </div>
  </PageContainer>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import PageContainer from '../../../components/admin/PageContainer.vue'
import { canWriteFlightModule } from '../../../utils/adminAuth'
import AirlineScopeSelect from '../../../components/admin/AirlineScopeSelect.vue'
import { getAdminFlights } from '../../../api/admin/flight'
import {
  canManageFlights as canEditFlights,
  getAirlineScopeParams,
  getStoredUser,
  isSystemAdmin
} from '../../../utils/adminAuth'

const router = useRouter()

const queryForm = reactive({
  date: '',
  status: '',
  flightNo: ''
})

const pagination = reactive({
  currentPage: 1,
  pageSize: 10
})

const flightList = ref([])
const selectedAirlineId = ref('')
const currentUser = computed(() => getStoredUser())
const systemAdmin = computed(() => isSystemAdmin(currentUser.value))

const canManageFlights = computed(() => {
  return canEditFlights(currentUser.value)
})

const loadFlights = async () => {
  try {
    const response = await getAdminFlights(
      getAirlineScopeParams(selectedAirlineId.value)
    )

    if (response.data.success) {
      flightList.value = response.data.data || []
    } else {
      ElMessage.error(response.data.message || '航班数据加载失败')
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '航班数据加载失败')
    console.error(error)
  }
}

const filteredFlights = computed(() => {
  return flightList.value.filter((item) => {
    const matchDate = !queryForm.date || item.flightDate === queryForm.date
    const matchStatus = !queryForm.status || item.status === queryForm.status
    const matchFlightNo =
      !queryForm.flightNo ||
      String(item.flightNo || '')
        .toLowerCase()
        .includes(queryForm.flightNo.toLowerCase())

    return matchDate && matchStatus && matchFlightNo
  })
})

const pagedFlights = computed(() => {
  const start = (pagination.currentPage - 1) * pagination.pageSize
  const end = start + pagination.pageSize

  return filteredFlights.value.slice(start, end)
})

const handleSearch = () => {
  pagination.currentPage = 1
}

const handleReset = () => {
  queryForm.date = ''
  queryForm.status = ''
  queryForm.flightNo = ''
  pagination.currentPage = 1
}

const goAddFlight = () => {
  router.push('/admin/flights/edit')
}

const goEditFlight = (row) => {
  router.push({
    path: '/admin/flights/edit',
    query: {
      instanceId: row.instanceId
    }
  })
}

const goPricing = (row) => {
  if (!row?.instanceId) {
    ElMessage.warning('未找到对应航班信息')
    return
  }

  router.push({
    path: '/admin/pricing',
    query: {
      instanceId: row.instanceId
    }
  })
}

const goIrregularity = (row) => {
  if (!row?.instanceId) {
    ElMessage.warning('未找到对应航班信息')
    return
  }

  router.push(`/admin/flights/${row.instanceId}/irregularities`)
}


const parseFlightEndTime = (flight) => {
  if (!flight?.flightDate) return null

  const depText = flight.depTime || '00:00'
  const arrText = flight.arrTime || depText || '23:59'

  const dep = new Date(`${flight.flightDate}T${depText}:00`)
  let arr = new Date(`${flight.flightDate}T${arrText}:00`)

  if (Number.isNaN(arr.getTime())) {
    return new Date(`${flight.flightDate}T23:59:59`)
  }

  if (!Number.isNaN(dep.getTime()) && arr <= dep) {
    arr = new Date(arr.getTime() + 24 * 60 * 60 * 1000)
  }

  return arr
}

const isFlightClosed = (flight) => {
  if (!flight) return false

  if (['已完成', '取消', '航班调整'].includes(flight.status)) {
    return true
  }

  const endTime = parseFlightEndTime(flight)
  return endTime ? endTime < new Date() : false
}

const isFlightReadonly = (flight) => {
  return isFlightClosed(flight)
}

const getFlightDisplayStatus = (flight) => {
  if (flight?.status === '航班调整') return '航班调整'
  if (isFlightClosed(flight) && flight?.status === '正常') return '已结束'
  return flight?.status || '未知'
}

const getStatusType = (status) => {
  if (status === '正常') return 'success'
  if (status === '延误') return 'warning'
  if (status === '取消') return 'danger'
  if (status === '航班调整') return 'warning'
  if (status === '已完成') return 'info'
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

.scope-card {
  margin-bottom: 18px;
  padding: 18px 18px 0;
  border-radius: 16px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
}

.table-card {
  padding: 18px;
  border-radius: 16px;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  max-width: 100%;
  overflow-x: auto;
}

.pagination-wrap {
  margin-top: 18px;
  display: flex;
  justify-content: flex-end;
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

:deep(.el-table .cell) {
  line-height: 1.4;
}

.permission-alert {
  margin-bottom: 18px;
}
</style>

<template>
  <div>
    <div class="filter-card">
      <el-form :model="queryForm" inline label-width="80px">
        <el-form-item label="改签类型">
          <el-select
            v-model="queryForm.changeType"
            placeholder="请选择改签类型"
            clearable
            style="width: 220px"
          >
            <el-option
              v-for="type in changeTypes"
              :key="type"
              :label="type"
              :value="type"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="处理状态">
          <el-select
            v-model="queryForm.status"
            placeholder="请选择状态"
            clearable
            style="width: 140px"
          >
            <el-option label="处理中" value="处理中" />
            <el-option label="已完成" value="已完成" />
            <el-option label="已取消" value="已取消" />
          </el-select>
        </el-form-item>

        <el-form-item label="订单号">
          <el-input
            v-model="queryForm.orderId"
            placeholder="原订单或新订单"
            clearable
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <div class="table-card">
      <el-table
        v-loading="loading"
        :data="pagedRecords"
        stripe
        border
        table-layout="fixed"
        style="width: 100%"
        empty-text="暂无改签记录"
      >
        <el-table-column prop="changeId" label="记录ID" width="90" />
        <el-table-column label="用户" width="120" show-overflow-tooltip>
          <template #default="{ row }">
            {{ row.username || `用户${row.operatorUserId}` }}
          </template>
        </el-table-column>
        <el-table-column prop="oldOrderId" label="原订单" width="100" />
        <el-table-column prop="newOrderId" label="新订单" width="100" />
        <el-table-column label="航班变更" min-width="210">
          <template #default="{ row }">
            <div class="flight-change">
              <span>{{ row.oldFlightNo }}</span>
              <span class="arrow">→</span>
              <span>{{ row.newFlightNo }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="changeType" label="改签类型" min-width="190" />
        <el-table-column label="票价差额" width="110">
          <template #default="{ row }">
            {{ formatSignedMoney(row.fareDifference) }}
          </template>
        </el-table-column>
        <el-table-column label="手续费" width="105">
          <template #default="{ row }">
            {{ formatMoney(row.changeFee) }}
          </template>
        </el-table-column>
        <el-table-column label="应补金额" width="110">
          <template #default="{ row }">
            {{ formatMoney(row.payableAmount) }}
          </template>
        </el-table-column>
        <el-table-column label="应退金额" width="110">
          <template #default="{ row }">
            {{ formatMoney(row.refundableAmount) }}
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="completedAt" label="完成时间" width="175">
          <template #default="{ row }">
            {{ row.completedAt || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" fixed="right" width="90">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleView(row)">
              详情
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
          :total="filteredRecords.length"
        />
      </div>
    </div>

    <el-dialog
      v-model="detailVisible"
      title="改签记录详情"
      width="680px"
    >
      <div v-if="currentRecord" class="detail-grid">
        <div class="detail-item">
          <span>记录ID</span>
          <strong>{{ currentRecord.changeId }}</strong>
        </div>
        <div class="detail-item">
          <span>操作用户</span>
          <strong>{{ currentRecord.username || currentRecord.operatorUserId }}</strong>
        </div>
        <div class="detail-item">
          <span>原订单</span>
          <strong>{{ currentRecord.oldOrderId }}</strong>
        </div>
        <div class="detail-item">
          <span>新订单</span>
          <strong>{{ currentRecord.newOrderId }}</strong>
        </div>
        <div class="detail-item">
          <span>原航班</span>
          <strong>{{ currentRecord.oldAirlineName }} · {{ currentRecord.oldFlightNo }}</strong>
        </div>
        <div class="detail-item">
          <span>新航班</span>
          <strong>{{ currentRecord.newAirlineName }} · {{ currentRecord.newFlightNo }}</strong>
        </div>
        <div class="detail-item">
          <span>原票价</span>
          <strong>{{ formatMoney(currentRecord.oldTicketPrice) }}</strong>
        </div>
        <div class="detail-item">
          <span>新票价</span>
          <strong>{{ formatMoney(currentRecord.newTicketPrice) }}</strong>
        </div>
        <div class="detail-item">
          <span>票价差额</span>
          <strong>{{ formatSignedMoney(currentRecord.fareDifference) }}</strong>
        </div>
        <div class="detail-item">
          <span>改签手续费</span>
          <strong>{{ formatMoney(currentRecord.changeFee) }}</strong>
        </div>
        <div class="detail-item">
          <span>最终应补</span>
          <strong>{{ formatMoney(currentRecord.payableAmount) }}</strong>
        </div>
        <div class="detail-item">
          <span>最终应退</span>
          <strong>{{ formatMoney(currentRecord.refundableAmount) }}</strong>
        </div>
        <div class="detail-item full">
          <span>改签类型</span>
          <strong>{{ currentRecord.changeType }}</strong>
        </div>
        <div class="detail-item full">
          <span>改签原因</span>
          <strong>{{ currentRecord.changeReason || '-' }}</strong>
        </div>
        <div class="detail-item">
          <span>创建时间</span>
          <strong>{{ currentRecord.createdAt }}</strong>
        </div>
        <div class="detail-item">
          <span>完成时间</span>
          <strong>{{ currentRecord.completedAt || '-' }}</strong>
        </div>
      </div>

      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { getAdminChangeRecords } from '../../../api/admin/order'
import { getAirlineScopeParams } from '../../../utils/adminAuth'

const props = defineProps({
  orders: {
    type: Array,
    default: () => []
  },
  airlineId: {
    type: [Number, String],
    default: ''
  }
})

const loading = ref(false)
const detailVisible = ref(false)
const currentRecord = ref(null)
const recordList = ref([])

const changeTypes = [
  '乘客主动改签',
  '航司原因同航司改签',
  '航司原因跨航司改签'
]

const queryForm = reactive({
  changeType: '',
  status: '',
  orderId: ''
})

const pagination = reactive({
  currentPage: 1,
  pageSize: 10
})

const usernameByOrderId = computed(() => {
  return props.orders.reduce((result, order) => {
    result[order.orderId] = order.username
    return result
  }, {})
})

const recordsWithUser = computed(() => {
  return recordList.value.map((item) => ({
    ...item,
    username: usernameByOrderId.value[item.oldOrderId] || ''
  }))
})

const filteredRecords = computed(() => {
  return recordsWithUser.value.filter((item) => {
    const matchType =
      !queryForm.changeType ||
      item.changeType === queryForm.changeType

    const matchStatus =
      !queryForm.status ||
      item.status === queryForm.status

    const keyword = String(queryForm.orderId || '').trim()
    const matchOrder =
      !keyword ||
      String(item.oldOrderId).includes(keyword) ||
      String(item.newOrderId).includes(keyword)

    return matchType && matchStatus && matchOrder
  })
})

const pagedRecords = computed(() => {
  const start = (pagination.currentPage - 1) * pagination.pageSize
  return filteredRecords.value.slice(start, start + pagination.pageSize)
})

const loadRecords = async () => {
  loading.value = true

  try {
    const response = await getAdminChangeRecords(
      getAirlineScopeParams(props.airlineId)
    )
    recordList.value = response.data.data || []
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '改签记录加载失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.currentPage = 1
}

const handleReset = () => {
  queryForm.changeType = ''
  queryForm.status = ''
  queryForm.orderId = ''
  pagination.currentPage = 1
}

const handleView = (row) => {
  currentRecord.value = row
  detailVisible.value = true
}

const formatMoney = (value) => {
  return `¥${Number(value || 0).toFixed(2)}`
}

const formatSignedMoney = (value) => {
  const amount = Number(value || 0)
  const prefix = amount > 0 ? '+' : ''
  return `${prefix}¥${amount.toFixed(2)}`
}

const getStatusType = (status) => {
  if (status === '已完成') return 'success'
  if (status === '处理中') return 'warning'
  if (status === '已取消') return 'info'
  return 'info'
}

onMounted(() => {
  loadRecords()
})

watch(() => props.airlineId, loadRecords)
</script>

<style scoped>
.filter-card {
  margin-bottom: 18px;
  padding: 18px 18px 0;
  border-radius: 16px;
  background: linear-gradient(135deg, #f8fafc 0%, #ffffff 100%);
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

.flight-change {
  display: flex;
  align-items: center;
  gap: 8px;
}

.arrow {
  color: #3b82f6;
}

.detail-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.detail-item {
  padding: 14px;
  border-radius: 12px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
}

.detail-item.full {
  grid-column: 1 / -1;
}

.detail-item span {
  display: block;
  margin-bottom: 6px;
  color: #94a3b8;
  font-size: 12px;
}

.detail-item strong {
  color: #334155;
  font-size: 14px;
  font-weight: 600;
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
</style>

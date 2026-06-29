<template>
  <div class="refund-panel">
    <div class="filter-card">
      <el-form :model="queryForm" inline label-width="90px">
        <el-form-item label="订单号">
          <el-input
            v-model="queryForm.orderId"
            placeholder="请输入原订单号"
            clearable
          />
        </el-form-item>

        <el-form-item label="操作来源">
          <el-select
            v-model="queryForm.changeType"
            placeholder="全部来源"
            clearable
            style="width: 180px"
          >
            <el-option label="乘客主动退票" value="乘客主动退票" />
            <el-option label="航司原因退票" value="航司原因退票" />
          </el-select>
        </el-form-item>

        <el-form-item label="处理状态">
          <el-select
            v-model="queryForm.status"
            placeholder="全部状态"
            clearable
            style="width: 150px"
          >
            <el-option label="已完成" value="已完成" />
            <el-option label="待处理" value="待处理" />
          </el-select>
        </el-form-item>

        <el-form-item label="操作日期">
          <el-date-picker
            v-model="queryForm.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            clearable
            style="width: 280px"
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

    <div class="table-card">
      <el-table
        v-loading="loading"
        :data="pagedRecords"
        stripe
        border
        table-layout="fixed"
        style="width: 100%"
        empty-text="暂无退款记录"
      >
        <el-table-column prop="refundId" label="退款ID" width="105" />
        <el-table-column prop="oldOrderId" label="原订单" width="120" />
        <el-table-column prop="flightNo" label="航班号" width="110" />
        <el-table-column prop="passengerName" label="乘机人" width="110" />

        <el-table-column label="退票类型" width="150">
          <template #default="{ row }">
            <el-tag :type="row.changeType === '航司原因退票' ? 'warning' : 'info'">
              {{ row.changeType }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="原票价" width="115">
          <template #default="{ row }">
            ¥{{ formatMoney(row.oldTicketPrice) }}
          </template>
        </el-table-column>

        <el-table-column label="退票手续费" width="130">
          <template #default="{ row }">
            ¥{{ formatMoney(row.changeFee) }}
          </template>
        </el-table-column>

        <el-table-column label="实际退款" width="130">
          <template #default="{ row }">
            <strong class="refund-money">¥{{ formatMoney(row.refundableAmount) }}</strong>
          </template>
        </el-table-column>

        <el-table-column label="处理状态" width="110">
          <template #default="{ row }">
            <el-tag :type="row.status === '已完成' ? 'success' : 'warning'">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="createdAt" label="操作时间" width="175" show-overflow-tooltip />
        <el-table-column prop="operatorUserId" label="操作人ID" width="105" />

        <el-table-column label="操作" fixed="right" width="90">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleView(row)">
              查看
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
      title="退票记录详情"
      width="620px"
    >
      <div v-if="currentRecord" class="detail-box">
        <div class="detail-row">
          <span>退款ID</span>
          <strong>{{ currentRecord.refundId }}</strong>
        </div>

        <div class="detail-row">
          <span>原订单号</span>
          <strong>{{ currentRecord.oldOrderId }}</strong>
        </div>

        <div class="detail-row">
          <span>航班</span>
          <strong>{{ currentRecord.flightNo }} · {{ currentRecord.flightDate }}</strong>
        </div>

        <div class="detail-row">
          <span>航空公司</span>
          <strong>{{ currentRecord.airlineName || '-' }}</strong>
        </div>

        <div class="detail-row">
          <span>乘机人</span>
          <strong>{{ currentRecord.passengerName || '-' }}</strong>
        </div>

        <div class="detail-row">
          <span>退票类型</span>
          <el-tag :type="currentRecord.changeType === '航司原因退票' ? 'warning' : 'info'">
            {{ currentRecord.changeType }}
          </el-tag>
        </div>

        <div class="detail-row">
          <span>原票价</span>
          <strong>¥{{ formatMoney(currentRecord.oldTicketPrice) }}</strong>
        </div>

        <div class="detail-row">
          <span>退票手续费</span>
          <strong>¥{{ formatMoney(currentRecord.changeFee) }}</strong>
        </div>

        <div class="detail-row">
          <span>实际退款</span>
          <strong class="refund-money">¥{{ formatMoney(currentRecord.refundableAmount) }}</strong>
        </div>

        <div class="detail-row">
          <span>退票原因</span>
          <strong>{{ currentRecord.changeReason || '-' }}</strong>
        </div>

        <div class="detail-row">
          <span>异常ID</span>
          <strong>{{ currentRecord.irregularityId || '-' }}</strong>
        </div>

        <div class="detail-row">
          <span>操作时间</span>
          <strong>{{ currentRecord.createdAt || '-' }}</strong>
        </div>

        <div class="detail-row">
          <span>完成时间</span>
          <strong>{{ currentRecord.completedAt || '-' }}</strong>
        </div>
      </div>

      <template #footer>
        <el-button @click="detailVisible = false">
          关闭
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { getAdminRefundRecords } from '../../../api/admin/order'
import { getAirlineScopeParams } from '../../../utils/adminAuth'

const props = defineProps({
  airlineId: {
    type: [String, Number],
    default: ''
  }
})

const loading = ref(false)
const refundRecords = ref([])
const detailVisible = ref(false)
const currentRecord = ref(null)

const queryForm = reactive({
  orderId: '',
  changeType: '',
  status: '',
  dateRange: []
})

const pagination = reactive({
  currentPage: 1,
  pageSize: 10
})

const filteredRecords = computed(() => {
  return refundRecords.value.filter((item) => {
    const matchOrderId =
      !queryForm.orderId ||
      String(item.oldOrderId || '').includes(queryForm.orderId.trim())

    const matchChangeType =
      !queryForm.changeType ||
      item.changeType === queryForm.changeType

    const matchStatus =
      !queryForm.status ||
      item.status === queryForm.status

    const dateText = String(item.createdAt || '').slice(0, 10)
    const matchDateRange =
      !queryForm.dateRange?.length ||
      (
        dateText >= queryForm.dateRange[0] &&
        dateText <= queryForm.dateRange[1]
      )

    return matchOrderId && matchChangeType && matchStatus && matchDateRange
  })
})

const pagedRecords = computed(() => {
  const start = (pagination.currentPage - 1) * pagination.pageSize
  return filteredRecords.value.slice(start, start + pagination.pageSize)
})

const loadRecords = async () => {
  loading.value = true

  try {
    const response = await getAdminRefundRecords({
      ...getAirlineScopeParams(props.airlineId)
    })

    refundRecords.value = response.data.data || []
  } catch (error) {
    refundRecords.value = []
    ElMessage.error(error.response?.data?.message || '退票记录加载失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.currentPage = 1
}

const handleReset = () => {
  queryForm.orderId = ''
  queryForm.changeType = ''
  queryForm.status = ''
  queryForm.dateRange = []
  pagination.currentPage = 1
}

const handleView = (row) => {
  currentRecord.value = row
  detailVisible.value = true
}

const formatMoney = (value) => {
  return Number(value || 0).toFixed(2)
}

watch(
  () => props.airlineId,
  () => {
    loadRecords()
  }
)

onMounted(() => {
  loadRecords()
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

.refund-money {
  color: #16a34a;
}

.detail-box {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.detail-row {
  min-height: 34px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
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

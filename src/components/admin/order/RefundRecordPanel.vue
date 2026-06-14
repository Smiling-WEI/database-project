<template>
  <div>
    <div class="filter-card">
      <el-form :model="queryForm" inline label-width="80px">
        <el-form-item label="订单号">
          <el-input v-model="queryForm.orderId" clearable placeholder="请输入订单号" />
        </el-form-item>
        <el-form-item label="操作来源">
          <el-select
            v-model="queryForm.operatorType"
            clearable
            placeholder="全部来源"
            style="width: 150px"
          >
            <el-option label="用户操作" value="用户操作" />
            <el-option label="客服代操作" value="客服代操作" />
            <el-option label="系统处理" value="系统处理" />
          </el-select>
        </el-form-item>
        <el-form-item label="处理状态">
          <el-select
            v-model="queryForm.status"
            clearable
            placeholder="全部状态"
            style="width: 140px"
          >
            <el-option label="处理中" value="处理中" />
            <el-option label="已完成" value="已完成" />
            <el-option label="已取消" value="已取消" />
          </el-select>
        </el-form-item>
        <el-form-item label="操作日期">
          <el-date-picker
            v-model="queryForm.dateRange"
            type="daterange"
            value-format="YYYY-MM-DD"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadRecords">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <div class="table-card">
      <el-table
        v-loading="loading"
        :data="pagedRecords"
        border
        stripe
        table-layout="fixed"
        empty-text="暂无退款记录"
      >
        <el-table-column prop="refundId" label="退款ID" width="95" />
        <el-table-column prop="orderId" label="原订单" width="100" />
        <el-table-column
          v-if="systemAdmin"
          prop="airlineName"
          label="航空公司"
          min-width="150"
        />
        <el-table-column prop="flightNo" label="航班号" width="105" />
        <el-table-column prop="passengerName" label="乘机人" width="105" />
        <el-table-column label="原票价" width="110">
          <template #default="{ row }">{{ formatMoney(row.originalTicketPrice) }}</template>
        </el-table-column>
        <el-table-column label="退票手续费" width="120">
          <template #default="{ row }">{{ formatMoney(row.refundFee) }}</template>
        </el-table-column>
        <el-table-column label="实际退款" width="115">
          <template #default="{ row }">
            <strong class="refund-money">{{ formatMoney(row.refundAmount) }}</strong>
          </template>
        </el-table-column>
        <el-table-column prop="refundReason" label="退票原因" min-width="180" show-overflow-tooltip />
        <el-table-column label="操作来源" width="120">
          <template #default="{ row }">
            <el-tag :type="getOperatorType(row.operatorType)">
              {{ row.operatorType }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="客服代操作" width="115">
          <template #default="{ row }">
            <el-tag :type="row.customerServiceAssisted ? 'warning' : 'info'">
              {{ row.customerServiceAssisted ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="operatorName" label="操作人员" width="120" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="completedAt" label="操作时间" width="175">
          <template #default="{ row }">{{ row.completedAt || row.createdAt || '-' }}</template>
        </el-table-column>
        <el-table-column label="操作" fixed="right" width="90">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleView(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="pagination.currentPage"
          v-model:page-size="pagination.pageSize"
          background
          layout="total, prev, pager, next"
          :total="records.length"
        />
      </div>
    </div>

    <el-dialog v-model="detailVisible" title="退款记录详情" width="680px">
      <div v-if="currentRecord" class="detail-grid">
        <div v-for="item in detailItems" :key="item.label" class="detail-item">
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
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
import { getAdminRefundRecords } from '../../../api/admin/order'
import {
  getAirlineScopeParams,
  getStoredUser,
  isSystemAdmin
} from '../../../utils/adminAuth'

const props = defineProps({
  airlineId: {
    type: [Number, String],
    default: ''
  }
})

const loading = ref(false)
const detailVisible = ref(false)
const currentRecord = ref(null)
const records = ref([])
const systemAdmin = computed(() => isSystemAdmin(getStoredUser()))
const queryForm = reactive({
  orderId: '',
  operatorType: '',
  status: '',
  dateRange: []
})
const pagination = reactive({ currentPage: 1, pageSize: 10 })

const pagedRecords = computed(() => {
  const start = (pagination.currentPage - 1) * pagination.pageSize
  return records.value.slice(start, start + pagination.pageSize)
})

const detailItems = computed(() => {
  const row = currentRecord.value || {}
  return [
    { label: '退款记录ID', value: row.refundId || '-' },
    { label: '原订单', value: row.orderId || '-' },
    { label: '航空公司', value: row.airlineName || '-' },
    { label: '航班', value: row.flightNo || '-' },
    { label: '乘机人', value: row.passengerName || '-' },
    { label: '原票价', value: formatMoney(row.originalTicketPrice) },
    { label: '退票手续费', value: formatMoney(row.refundFee) },
    { label: '实际退款金额', value: formatMoney(row.refundAmount) },
    { label: '操作来源', value: row.operatorType || '-' },
    { label: '操作人员', value: row.operatorName || '-' },
    { label: '是否客服代操作', value: row.customerServiceAssisted ? '是' : '否' },
    { label: '处理状态', value: row.status || '-' },
    { label: '退票原因', value: row.refundReason || '-' },
    { label: '操作时间', value: row.completedAt || row.createdAt || '-' }
  ]
})

const loadRecords = async () => {
  loading.value = true
  try {
    const params = {
      ...getAirlineScopeParams(props.airlineId),
      order_id: queryForm.orderId || undefined,
      operator_type: queryForm.operatorType || undefined,
      status: queryForm.status || undefined,
      start_date: queryForm.dateRange?.[0],
      end_date: queryForm.dateRange?.[1]
    }
    const response = await getAdminRefundRecords(params)
    records.value = response.data.data || []
    pagination.currentPage = 1
  } catch (error) {
    records.value = []
    ElMessage.error(error.response?.data?.message || '退款记录接口待后端接入')
  } finally {
    loading.value = false
  }
}

const handleReset = () => {
  queryForm.orderId = ''
  queryForm.operatorType = ''
  queryForm.status = ''
  queryForm.dateRange = []
  loadRecords()
}

const handleView = (row) => {
  currentRecord.value = row
  detailVisible.value = true
}

const formatMoney = (value) => {
  if (value === undefined || value === null || value === '') return '-'
  return `¥${Number(value).toFixed(2)}`
}

const getOperatorType = (type) => {
  if (type === '客服代操作') return 'warning'
  if (type === '用户操作') return 'success'
  return 'info'
}

const getStatusType = (status) => {
  if (status === '已完成') return 'success'
  if (status === '处理中') return 'warning'
  if (status === '已取消') return 'info'
  return 'info'
}

watch(() => props.airlineId, loadRecords)
onMounted(loadRecords)
</script>

<style scoped>
.filter-card {
  margin-bottom: 18px;
  padding: 18px 18px 0;
  border-radius: 16px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
}

.table-card {
  padding: 18px;
  border-radius: 16px;
  background: #fff;
  border: 1px solid #e2e8f0;
  overflow-x: auto;
}

.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 18px;
}

.refund-money {
  color: #16a34a;
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

.detail-item span {
  display: block;
  margin-bottom: 6px;
  color: #94a3b8;
  font-size: 12px;
}

.detail-item strong {
  color: #334155;
  font-size: 14px;
}
</style>

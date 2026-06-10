<template>
  <PageContainer
    title="订单管理"
    description="查看当前航司的有效订单、历史订单与订单状态"
  >
    <!-- 筛选区域 -->
    <div class="filter-card">
      <el-form
        :model="queryForm"
        inline
        label-width="80px"
      >
        <el-form-item label="航班号">
          <el-input
            v-model="queryForm.flightNo"
            placeholder="请输入航班号"
            clearable
          />
        </el-form-item>

        <el-form-item label="订单状态">
          <el-select
            v-model="queryForm.orderStatus"
            placeholder="请选择订单状态"
            clearable
            style="width: 150px"
          >
            <el-option label="已支付" value="已支付" />
            <el-option label="已退票" value="已退票" />
            <el-option label="已改签" value="已改签" />
            <el-option label="已取消" value="已取消" />
          </el-select>
        </el-form-item>

        <el-form-item label="记录类型">
          <el-select
            v-model="queryForm.recordType"
            placeholder="请选择类型"
            clearable
            style="width: 150px"
          >
            <el-option label="有效订单" value="有效订单" />
            <el-option label="历史订单" value="历史订单" />
          </el-select>
        </el-form-item>

        <el-form-item label="乘机人">
          <el-input
            v-model="queryForm.passengerName"
            placeholder="前端筛选预留"
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

    <!-- 表格区域 -->
    <div class="table-card">
      <el-table
        :data="filteredOrders"
        stripe
        border
        table-layout="fixed"
        style="width: 100%"
        empty-text="暂无订单数据，待后端接口接入"
      >
        <el-table-column prop="orderId" label="订单ID" width="100" />
        <el-table-column prop="username" label="用户账号" width="120" show-overflow-tooltip />
        <el-table-column prop="passengerName" label="乘机人" width="110" show-overflow-tooltip />
        <el-table-column prop="flightNo" label="航班号" width="110" />
        <el-table-column prop="flightDate" label="航班日期" width="120" />
        <el-table-column prop="cabinType" label="舱位" width="100" />
        <el-table-column prop="seatNo" label="座位号" width="100" />
        <el-table-column prop="price" label="票价" width="100">
          <template #default="{ row }">
            <span v-if="row.price !== undefined && row.price !== null">
              ¥{{ row.price }}
            </span>
            <span v-else>-</span>
          </template>
        </el-table-column>

        <el-table-column prop="purchaseTime" label="购票时间" width="170" show-overflow-tooltip />

        <el-table-column label="订单状态" width="120">
          <template #default="{ row }">
            <el-tag :type="getOrderStatusType(row.orderStatus)">
              {{ row.orderStatus }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="记录类型" width="110">
          <template #default="{ row }">
            <el-tag :type="row.recordType === '有效订单' ? 'success' : 'info'">
              {{ row.recordType }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="操作" fixed="right" width="140">
          <template #default="{ row }">
            <el-button
              type="primary"
              link
              @click="handleView(row)"
            >
              查看
            </el-button>
            <el-button
              type="info"
              link
              @click="handleTodo"
            >
              待接入
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrap">
        <el-pagination
          background
          layout="total, prev, pager, next"
          :total="filteredOrders.length"
          :page-size="10"
        />
      </div>
    </div>

    <!-- 订单详情弹窗 -->
    <el-dialog
      v-model="detailVisible"
      title="订单详情"
      width="620px"
    >
      <div v-if="currentOrder" class="detail-box">
        <div class="detail-row">
          <span>订单ID</span>
          <strong>{{ currentOrder.orderId }}</strong>
        </div>
        <div class="detail-row">
          <span>用户ID</span>
          <strong>{{ currentOrder.userId }}</strong>
        </div>
        <div class="detail-row">
          <span>用户账号</span>
          <strong>{{ currentOrder.username }}</strong>
        </div>
        <div class="detail-row">
          <span>乘机人</span>
          <strong>{{ currentOrder.passengerName }}</strong>
        </div>
        <div class="detail-row">
          <span>乘机人证件</span>
          <strong>{{ currentOrder.passengerIdCard }}</strong>
        </div>
        <div class="detail-row">
          <span>航班号</span>
          <strong>{{ currentOrder.flightNo }}</strong>
        </div>
        <div class="detail-row">
          <span>航班日期</span>
          <strong>{{ currentOrder.flightDate }}</strong>
        </div>
        <div class="detail-row">
          <span>舱位</span>
          <strong>{{ currentOrder.cabinType }}</strong>
        </div>
        <div class="detail-row">
          <span>座位号</span>
          <strong>{{ currentOrder.seatNo }}</strong>
        </div>
        <div class="detail-row">
          <span>票价</span>
          <strong>¥{{ currentOrder.price }}</strong>
        </div>
        <div class="detail-row">
          <span>购票时间</span>
          <strong>{{ currentOrder.purchaseTime }}</strong>
        </div>
        <div class="detail-row">
          <span>订单状态</span>
          <el-tag :type="getOrderStatusType(currentOrder.orderStatus)">
            {{ currentOrder.orderStatus }}
          </el-tag>
        </div>
        <div class="detail-row">
          <span>记录类型</span>
          <el-tag :type="currentOrder.recordType === '有效订单' ? 'success' : 'info'">
            {{ currentOrder.recordType }}
          </el-tag>
        </div>
      </div>

      <el-empty
        v-else
        description="暂无订单详情，待后端数据接入"
      />

      <template #footer>
        <el-button @click="detailVisible = false">
          关闭
        </el-button>
      </template>
    </el-dialog>
  </PageContainer>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import PageContainer from '../../../components/admin/PageContainer.vue'

const queryForm = reactive({
  flightNo: '',
  orderStatus: '',
  recordType: '',
  passengerName: ''
})

const detailVisible = ref(false)
const currentOrder = ref(null)

// 后续由后端接口赋值，例如：orderList.value = 接口返回的订单数组
const orderList = ref([])

const filteredOrders = computed(() => {
  return orderList.value.filter((item) => {
    const matchFlightNo = !queryForm.flightNo || item.flightNo?.includes(queryForm.flightNo)
    const matchOrderStatus = !queryForm.orderStatus || item.orderStatus === queryForm.orderStatus
    const matchRecordType = !queryForm.recordType || item.recordType === queryForm.recordType
    const matchPassengerName =
      !queryForm.passengerName || item.passengerName?.includes(queryForm.passengerName)

    return matchFlightNo && matchOrderStatus && matchRecordType && matchPassengerName
  })
})

const handleSearch = () => {
  ElMessage.info('查询条件已更新，待后端接口接入后获取真实数据')
}

const handleReset = () => {
  queryForm.flightNo = ''
  queryForm.orderStatus = ''
  queryForm.recordType = ''
  queryForm.passengerName = ''
}

const handleView = (row) => {
  currentOrder.value = row
  detailVisible.value = true
}

const handleTodo = () => {
  ElMessage.info('该操作待后端接口接入')
}

const getOrderStatusType = (status) => {
  if (status === '已支付') return 'success'
  if (status === '已退票') return 'info'
  if (status === '已改签') return 'warning'
  if (status === '已取消') return 'danger'
  return 'info'
}
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

.detail-box {
  padding: 4px 2px;
}

.detail-row {
  min-height: 42px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  border-bottom: 1px solid #eef2f7;
  color: #64748b;
  font-size: 14px;
}

.detail-row:last-child {
  border-bottom: none;
}

.detail-row strong {
  color: #1e293b;
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

:deep(.el-table .cell) {
  line-height: 1.4;
}
</style>
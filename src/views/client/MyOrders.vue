<template>
  <div class="orders-container">
    <h2>📝 我的订单管理</h2>

    <el-tabs v-model="activeTab">
      <el-tab-pane label="有效订单" name="active">
        <el-table
          v-loading="loading"
          :data="activeOrders"
          border
          stripe
          style="width: 100%"
          empty-text="暂无有效订单"
        >
          <el-table-column prop="orderId" label="订单号" width="100" />
          <el-table-column prop="flightNo" label="航班号" width="100" />
          <el-table-column prop="passengerName" label="乘机人" width="100" />
          <el-table-column prop="flightDate" label="起飞日期" width="120" />
          <el-table-column prop="cabinType" label="舱位" width="100" />
          <el-table-column prop="seatNo" label="座位号" width="100">
            <template #default="{ row }">
              {{ row.seatNo || '暂未选座' }}
            </template>
          </el-table-column>

          <el-table-column label="实付金额" width="110">
            <template #default="{ row }">
              {{ formatPrice(row.price) }}
            </template>
          </el-table-column>

          <el-table-column prop="purchaseTime" label="购票时间" min-width="170" />

          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="getStatusType(row.orderStatus)">
                {{ row.orderStatus }}
              </el-tag>
            </template>
          </el-table-column>

          <el-table-column label="操作" width="120" fixed="right">
            <template #default="{ row }">
              <el-button
                v-if="row.orderStatus === '已支付'"
                type="danger"
                size="small"
                :loading="refundingOrderId === row.orderId"
                @click="handleRefund(row)"
              >
                申请退票
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="历史订单" name="history">
        <el-table
          v-loading="loading"
          :data="historyOrders"
          border
          stripe
          style="width: 100%"
          empty-text="暂无历史订单"
        >
          <el-table-column prop="orderId" label="订单号" width="100" />
          <el-table-column prop="flightNo" label="航班号" width="100" />
          <el-table-column prop="passengerName" label="乘机人" width="100" />
          <el-table-column prop="flightDate" label="起飞日期" width="120" />
          <el-table-column prop="cabinType" label="舱位" width="100" />
          <el-table-column prop="seatNo" label="座位号" width="100">
            <template #default="{ row }">
              {{ row.seatNo || '暂未选座' }}
            </template>
          </el-table-column>

          <el-table-column label="票价" width="110">
            <template #default="{ row }">
              {{ formatPrice(row.price) }}
            </template>
          </el-table-column>

          <el-table-column prop="purchaseTime" label="购票时间" min-width="170" />

          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="getStatusType(row.orderStatus)">
                {{ row.orderStatus }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../../api/index'

const activeTab = ref('active')
const loading = ref(false)
const refundingOrderId = ref(null)

const activeOrders = ref([])
const historyOrders = ref([])

const loadOrders = async () => {
  loading.value = true

  try {
    const [activeResponse, historyResponse] = await Promise.all([
      api.get('/orders'),
      api.get('/orders/history')
    ])

    activeOrders.value = activeResponse.data.data || []
    historyOrders.value = historyResponse.data.data || []
  } catch (error) {
    ElMessage.error(
      error.response?.data?.message || '订单数据加载失败，请稍后重试'
    )
    console.error(error)
  } finally {
    loading.value = false
  }
}

const handleRefund = async (order) => {
  try {
    await ElMessageBox.confirm(
      `确定要退掉 ${order.passengerName} 的 ${order.flightNo} 航班机票吗？`,
      '退票确认',
      {
        confirmButtonText: '确定退票',
        cancelButtonText: '暂不退票',
        type: 'warning'
      }
    )
  } catch {
    ElMessage.info('已取消退票操作')
    return
  }

  refundingOrderId.value = order.orderId

  try {
    const response = await api.post(`/orders/${order.orderId}/refund`, {})

    if (!response.data.success) {
      ElMessage.error(response.data.message || '退票失败')
      return
    }

    ElMessage.success('退票成功，订单已经转入历史记录')
    await loadOrders()
  } catch (error) {
    ElMessage.error(
      error.response?.data?.message || '退票失败，请稍后重试'
    )
    console.error(error)
  } finally {
    refundingOrderId.value = null
  }
}

const formatPrice = (price) => {
  if (price === undefined || price === null || price === '') {
    return '-'
  }

  return `¥${price}`
}

const getStatusType = (status) => {
  if (status === '已支付') return 'success'
  if (status === '已退票') return 'info'
  if (status === '已改签') return 'warning'
  if (status === '已取消') return 'danger'
  return 'info'
}

onMounted(() => {
  loadOrders()
})
</script>

<style scoped>
.orders-container {
  max-width: 1180px;
  margin: 0 auto;
  padding: 40px;
}

h2 {
  margin-top: 0;
  margin-bottom: 24px;
}

:deep(.el-tabs__content) {
  padding-top: 8px;
}
</style>
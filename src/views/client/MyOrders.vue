<template>
  <div class="orders-container">
    <h2>📝 我的订单管理</h2>

    <el-table :data="orderList" border stripe style="width: 100%">
      
      <el-table-column prop="orderId" label="订单号" width="120" />
      <el-table-column prop="flightNo" label="航班号" width="100" />
      <el-table-column prop="passenger" label="乘机人" width="100" />
      <el-table-column prop="date" label="起飞日期" width="120" />
      <el-table-column prop="price" label="实付(元)" width="100" />
      
      <el-table-column label="状态" width="100">
        <template #default="scope">
          <el-tag :type="scope.row.status === '已支付' ? 'success' : 'info'">
            {{ scope.row.status }}
          </el-tag>
        </template>
      </el-table-column>

      <el-table-column label="操作" min-width="120">
        <template #default="scope">
          <el-button 
            v-if="scope.row.status === '已支付'" 
            type="danger" 
            size="small" 
            @click="handleRefund(scope.row)"
          >
            申请退票
          </el-button>
        </template>
      </el-table-column>

    </el-table>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

// 1. 模拟的订单数据 (等对接接口后，这里的数据由后端查询 active_ticket_sale 表返回)
const orderList = ref([
  {
    orderId: 'ORD-001',
    flightNo: 'MU5101',
    passenger: '张三',
    date: '2026-05-01',
    price: 850,
    status: '已支付'
  },
  {
    orderId: 'ORD-002',
    flightNo: 'CA1503',
    passenger: '李四',
    date: '2026-04-20',
    price: 1200,
    status: '已退票'
  }
])

// 2. 退票处理逻辑
const handleRefund = (order) => {
  // 弹出二次确认框，防止用户误触
  ElMessageBox.confirm(
    `确定要退掉 ${order.passenger} 的 ${order.flightNo} 航班机票吗？`,
    '退票确认',
    {
      confirmButtonText: '确定退票',
      cancelButtonText: '暂不退票',
      type: 'warning',
    }
  ).then(() => {
    // 用户点击确定：在前端将该订单状态改为“已退票” (实战中这里要发请求给后端更新数据库)
    order.status = '已退票'
    ElMessage.success('退票成功！款项将原路返回。')
  }).catch(() => {
    // 用户点击取消：什么都不做
    ElMessage.info('已取消退票操作')
  })
}
</script>

<style scoped>
.orders-container {
  padding: 40px;
  max-width: 900px;
  margin: 0 auto;
}
</style>
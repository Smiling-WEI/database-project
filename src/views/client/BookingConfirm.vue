<template>
  <div class="booking-container">
    <h2>🎫 确认订单与乘机人</h2>

    <el-card class="flight-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>✈️ 已选航班：MU5101</span>
          <span class="price">¥ 850</span>
        </div>
      </template>
      <div class="flight-info">
        <p><strong>起飞：</strong> 首都国际机场(PEK) - 08:00</p>
        <p><strong>降落：</strong> 虹桥国际机场(SHA) - 10:15</p>
        <p><strong>日期：</strong> 2026-05-01</p>
      </div>
    </el-card>

    <el-card class="passenger-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>👨‍👩‍👧 选择乘机人</span>
          <el-button type="primary" link>+ 新增乘机人</el-button>
        </div>
      </template>
      
      <el-radio-group v-model="selectedPassenger" class="passenger-group">
        <el-radio border value="p1">张三 (本人) - 110105********1234</el-radio>
        <el-radio border value="p2">李四 (家属) - 110105********5678</el-radio>
        <el-radio border value="p3">王五 (同事) - 110105********9012</el-radio>
      </el-radio-group>
    </el-card>

    <div class="submit-area">
      <el-button size="large" @click="goBack">返回修改</el-button>
      <el-button type="success" size="large" @click="submitOrder">💳 确认支付并出票</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'

// 初始化路由器，用于页面跳转
const router = useRouter()

// 绑定的乘机人数据，默认不选
const selectedPassenger = ref('')

// 返回上一页
const goBack = () => {
  router.back()
}

// 提交订单逻辑
const submitOrder = () => {
  if (!selectedPassenger.value) {
    ElMessage.warning('请至少选择一位乘机人！')
    return
  }
  
  // 模拟调用后端 2 号同学写的购票接口，触发数据库事务
  ElMessageBox.confirm(
    '系统将为您锁定座位并生成售票记录，确认支付吗？',
    '支付确认',
    {
      confirmButtonText: '确认支付',
      cancelButtonText: '取消',
      type: 'success',
    }
  ).then(() => {
    ElMessage.success('🎉 支付成功！售票记录已生成！')
    // 真实开发中，这里会跳转到“我的订单”页面
  }).catch(() => {
    ElMessage.info('已取消支付')
  })
}
</script>

<style scoped>
.booking-container {
  padding: 40px;
  max-width: 800px;
  margin: 0 auto;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}
.price {
  color: #f56c6c;
  font-size: 20px;
}
.flight-card, .passenger-card {
  margin-bottom: 20px;
}
.flight-info p {
  margin: 10px 0;
  color: #606266;
}
.passenger-group {
  display: flex;
  flex-direction: column;
  gap: 15px; /* 让单选框垂直排列并拉开间距 */
  align-items: flex-start;
}
.submit-area {
  text-align: center;
  margin-top: 30px;
}
</style>
<template>
  <div class="records-page">
    <div class="page-title-row">
      <el-button link class="back-btn" @click="router.back()">
        <el-icon><ArrowLeft /></el-icon>
        返回
      </el-button>
      <h2>改签记录</h2>
    </div>

    <section class="filter-panel">
      <div class="filter-row">
        <label>
          改签日期
          <el-date-picker
            v-model="filters.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            size="large"
          />
        </label>
        <label>
          改签状态
          <el-select v-model="filters.status" size="large">
            <el-option label="全部状态" value="" />
            <el-option label="改签成功" value="success" />
            <el-option label="改签失败" value="failed" />
          </el-select>
        </label>
        <el-button type="primary" size="large" @click="applyFilters">查询</el-button>
      </div>
    </section>

    <div v-loading="loading" class="record-list">
      <el-empty v-if="visibleRecords.length === 0" description="暂无改签记录" />

      <article v-for="record in visibleRecords" :key="record.changeId" class="record-card">
        <div class="record-top">
          <strong>改签时间：{{ record.changeTime }}</strong>
          <strong>改签单号：{{ record.changeNo }}</strong>
          <strong :class="record.status === 'success' ? 'success-text' : 'danger-text'">
            {{ record.status === 'success' ? '改签成功' : '改签失败' }}
          </strong>
        </div>

        <div class="record-body">
          <div class="flight-change before">
            <el-tag type="primary" effect="light">改签前</el-tag>
            <div class="airline-line">
              <strong>原订单 {{ record.oldOrderId }}</strong>
            </div>
            <div class="airport-line">后端暂未返回原航班详情</div>
            <strong>原票价 ¥{{ record.oldPrice }}</strong>
          </div>

          <div class="arrow-block">→</div>

          <div v-if="record.status === 'success'" class="flight-change after">
            <el-tag type="success" effect="light">改签后</el-tag>
            <div class="airline-line">
              <strong>新订单 {{ record.newOrderId }}</strong>
            </div>
            <div class="airport-line">后端暂未返回新航班详情</div>
            <strong>新票价 ¥{{ record.newPrice }}</strong>
          </div>

          <div v-else class="failed-block">
            <span>乘机人：</span><strong>{{ record.passengerName || '-' }}</strong>
            <span>失败原因：</span><strong>{{ record.failReason }}</strong>
          </div>

          <div class="cost-block">
            <div><span>改签类型：</span><strong>{{ record.changeType || '-' }}</strong></div>
            <div><span>原票价：</span><strong>¥{{ record.oldPrice }}</strong></div>
            <div><span>新票价：</span><strong>¥{{ record.newPrice }}</strong></div>
            <div><span>改签费用：</span><strong>¥{{ record.changeFee }}</strong></div>
            <div><span>支付金额：</span><strong class="price-text">¥{{ record.payAmount }}</strong></div>
          </div>
        </div>
      </article>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import { getChangeRecords } from '../../api/client/order'

const router = useRouter()
const loading = ref(false)

const filters = reactive({
  dateRange: [],
  status: ''
})

const records = ref([])

const visibleRecords = computed(() => {
  return records.value.filter(record => {
    return !filters.status || record.status === filters.status
  })
})

const normalizeStatus = (status) => {
  if (status === '已完成' || status === 'success') return 'success'
  return 'failed'
}

const normalizeRecord = (record, index) => ({
  changeId: record.changeId || record.recordId || index + 1,
  changeNo: record.changeNo || `CC${record.changeId || index + 1}`,
  changeTime: record.changeTime || record.createdAt || '-',
  status: normalizeStatus(record.status),
  oldOrderId: record.oldOrderId || '-',
  newOrderId: record.newOrderId || '-',
  changeType: record.changeType || '',
  passengerName: record.passengerName || '',
  oldPrice: Number(record.oldTicketPrice ?? record.oldPrice ?? 0),
  newPrice: Number(record.newTicketPrice ?? record.newPrice ?? 0),
  changeFee: Number(record.changeFee ?? 0),
  payAmount: Number(record.payAmount ?? record.payableAmount ?? 0),
  failReason: record.failReason || record.changeReason || '-'
})

const loadRecords = async () => {
  loading.value = true

  try {
    const response = await getChangeRecords()
    const data = response.data.data || response.data || []
    records.value = data.map(normalizeRecord)
  } catch (error) {
    records.value = []
    ElMessage.error(error.response?.data?.message || '改签记录查询失败')
  } finally {
    loading.value = false
  }
}

const applyFilters = () => {
  ElMessage.success('筛选条件已应用')
}

onMounted(() => {
  loadRecords()
})
</script>

<style scoped>
.records-page {
  max-width: 1180px;
  margin: 0 auto;
}

.page-title-row {
  display: flex;
  align-items: center;
  gap: 22px;
  margin-bottom: 24px;
}

.back-btn {
  color: #0b7cff;
  font-size: 18px;
  font-weight: 800;
}

.page-title-row h2 {
  margin: 0;
  color: #0f172a;
}

.filter-panel,
.record-card {
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.88);
  box-shadow: 0 10px 30px rgba(30, 93, 140, 0.08);
}

.filter-panel {
  padding: 24px 28px;
}

.filter-row {
  display: grid;
  grid-template-columns: 420px 200px 100px;
  gap: 28px;
  align-items: end;
}

.filter-row label {
  display: flex;
  flex-direction: column;
  gap: 8px;
  color: #0f172a;
  font-weight: 800;
}

.record-list {
  margin-top: 14px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 300px;
}

.record-card {
  padding: 22px 24px;
}

.record-top {
  display: grid;
  grid-template-columns: 1fr 1fr auto;
  gap: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e2e8f0;
  color: #0f172a;
}

.success-text {
  color: #10b981;
}

.danger-text {
  color: #ef4444;
}

.record-body {
  display: grid;
  grid-template-columns: 1fr 70px 1fr 170px;
  gap: 24px;
  align-items: center;
  padding-top: 20px;
}

.flight-change {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.airline-line {
  display: flex;
  align-items: center;
  gap: 10px;
}

.airline-logo {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  display: inline-block;
}

.CA {
  background: #e11d48;
}

.MU {
  background: #0284c7;
}

.HU {
  background: #dc2626;
}

.airport-line,
.date-line {
  color: #475569;
}

.time-line {
  display: grid;
  grid-template-columns: 1fr 80px 1fr;
  align-items: center;
  gap: 12px;
}

.time-line strong {
  font-size: 24px;
}

.time-line span {
  text-align: center;
  color: #475569;
}

.arrow-block {
  color: #0b579f;
  font-size: 36px;
  font-weight: 900;
  text-align: center;
}

.failed-block,
.cost-block {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.failed-block span,
.cost-block span {
  color: #475569;
}

.price-text {
  color: #ef233c;
}

@media (max-width: 1000px) {
  .filter-row,
  .record-top,
  .record-body {
    grid-template-columns: 1fr;
  }
}
</style>

<template>
  <div class="records-page">
    <div class="page-title-row">
      <el-button link class="back-btn" @click="router.back()">
        <el-icon><ArrowLeft /></el-icon>
        返回
      </el-button>
      <h2>退改记录</h2>
    </div>

    <section class="filter-panel">
      <div class="filter-row">
        <label>
          退改日期
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
          退改状态
          <el-select v-model="filters.status" size="large">
            <el-option label="全部状态" value="" />
            <el-option label="成功" value="success" />
            <el-option label="失败" value="failed" />
          </el-select>
        </label>

        <el-button type="primary" size="large" @click="applyFilters">查询</el-button>
      </div>
    </section>

    <div v-loading="loading" class="record-list">
      <el-empty v-if="visibleRecords.length === 0" description="暂无退改记录" />

      <article
        v-for="record in visibleRecords"
        :key="record.changeId"
        class="record-card"
        :class="record.recordKind === 'refund' ? 'refund-card' : 'change-card'"
      >
        <div class="record-top">
          <strong>退改时间：{{ record.changeTime }}</strong>
          <strong>
            {{ record.recordKind === 'refund' ? '退票单号：' : '改签单号：' }}
            {{ record.changeNo }}
          </strong>
          <strong :class="record.status === 'success' ? 'success-text' : 'danger-text'">
            {{ record.statusText }}
          </strong>
        </div>

        <!-- 改签布局：保持原来前→后 -->
        <div v-if="record.recordKind === 'change'" class="record-body change-body">
          <div class="flight-change before change-box">
            <div class="block-tag before-tag">改签前</div>

            <div class="airline-line">
              <strong>原订单 {{ record.oldOrderId }}</strong>
              <span>{{ record.oldAirlineName }} {{ record.oldFlightNo }}</span>
            </div>

            <div class="airport-line">
              {{ record.oldDepAirport }} → {{ record.oldArrAirport }}
            </div>

            <div class="time-line">
              {{ record.oldFlightDate }}
              {{ record.oldDepTime }} - {{ record.oldArrTime }}
              {{ record.oldCabinType }}
            </div>

            <strong class="price-line">原票价 ¥{{ record.oldPrice }}</strong>
          </div>

          <div class="arrow-block">→</div>

          <div class="flight-change after change-box">
            <div class="block-tag after-tag">改签后</div>

            <div class="airline-line">
              <strong>新订单 {{ record.newOrderId }}</strong>
              <span>{{ record.newAirlineName }} {{ record.newFlightNo }}</span>
            </div>

            <div class="airport-line">
              {{ record.newDepAirport }} → {{ record.newArrAirport }}
            </div>

            <div class="time-line">
              {{ record.newFlightDate }}
              {{ record.newDepTime }} - {{ record.newArrTime }}
              {{ record.newCabinType }}
            </div>

            <strong class="price-line">新票价 ¥{{ record.newPrice }}</strong>
          </div>

          <div class="cost-block">
            <div><span>业务类型：</span><strong>{{ record.changeType }}</strong></div>
            <div><span>原票价：</span><strong>¥{{ record.oldPrice }}</strong></div>
            <div><span>新票价：</span><strong>¥{{ record.newPrice }}</strong></div>
            <div><span>改签费用：</span><strong>¥{{ record.changeFee }}</strong></div>
            <div><span>支付金额：</span><strong class="price-text">¥{{ record.payAmount }}</strong></div>
          </div>
        </div>

        <!-- 退票布局：只保留原订单，不显示箭头、不显示右侧新订单 -->
        <div v-else class="record-body refund-body">
          <div class="flight-change refund-box">
            <div class="block-tag refund-tag">退票订单</div>

            <div class="airline-line">
              <strong>原订单 {{ record.oldOrderId }}</strong>
              <span>{{ record.oldAirlineName }} {{ record.oldFlightNo }}</span>
            </div>

            <div class="airport-line">
              {{ record.oldDepAirport }} → {{ record.oldArrAirport }}
            </div>

            <div class="time-line">
              {{ record.oldFlightDate }}
              {{ record.oldDepTime }} - {{ record.oldArrTime }}
              {{ record.oldCabinType }}
            </div>

            <strong class="price-line">原票价 ¥{{ record.oldPrice }}</strong>
          </div>

          <div class="cost-block refund-cost-block">
            <div><span>业务类型：</span><strong>{{ record.changeType }}</strong></div>
            <div><span>原票价：</span><strong>¥{{ record.oldPrice }}</strong></div>
            <div><span>退票手续费：</span><strong>¥{{ record.changeFee }}</strong></div>
            <div><span>退款金额：</span><strong class="price-text">¥{{ record.payAmount }}</strong></div>
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
const appliedFilters = reactive({
  dateRange: [],
  status: ''
})

const getDatePart = (value) => {
  if (!value) return ''
  return String(value).slice(0, 10)
}

const normalizeStatus = (status) => {
  const value = String(status || '')
  if (
    value === '已完成' ||
    value === 'success' ||
    value === '改签成功' ||
    value === '退票成功'
  ) {
    return 'success'
  }
  return 'failed'
}

const normalizeRecord = (record, index) => {
  const recordKind =
    record.recordType === 'refund' || String(record.changeType || '').includes('退票')
      ? 'refund'
      : 'change'

  const status = normalizeStatus(record.status)

  return {
    changeId: record.changeId || record.recordId || index + 1,
    changeNo: record.changeNo || `CC${record.changeId || index + 1}`,
    changeTime: record.changeTime || record.createdAt || '-',
    status,
    statusText:
      recordKind === 'refund'
        ? status === 'success'
          ? '退票成功'
          : '退票失败'
        : status === 'success'
          ? '改签成功'
          : '改签失败',

    recordKind,
    changeType:
      record.changeType || (recordKind === 'refund' ? '乘客主动退票' : '乘客主动改签'),

    oldOrderId: record.oldOrderId || '-',
    newOrderId: record.newOrderId || '-',

    oldFlightNo: record.oldFlightNo || '-',
    oldAirlineName: record.oldAirlineName || '',
    oldDepAirport: record.oldDepAirport || '-',
    oldArrAirport: record.oldArrAirport || '-',
    oldFlightDate: record.oldFlightDate || '-',
    oldDepTime: record.oldDepTime || '--:--',
    oldArrTime: record.oldArrTime || '--:--',
    oldCabinType: record.oldCabinType || '-',

    newFlightNo: record.newFlightNo || '-',
    newAirlineName: record.newAirlineName || '',
    newDepAirport: record.newDepAirport || '-',
    newArrAirport: record.newArrAirport || '-',
    newFlightDate: record.newFlightDate || '-',
    newDepTime: record.newDepTime || '--:--',
    newArrTime: record.newArrTime || '--:--',
    newCabinType: record.newCabinType || '-',

    oldPrice: Number(record.oldTicketPrice ?? record.oldPrice ?? 0),
    newPrice: Number(record.newTicketPrice ?? record.newPrice ?? 0),
    changeFee: Number(record.changeFee ?? record.refundFee ?? 0),
    payAmount:
      recordKind === 'refund'
        ? Number(record.refundableAmount ?? record.payAmount ?? 0)
        : Number(record.payAmount ?? record.payableAmount ?? 0)
  }
}

const visibleRecords = computed(() => {
  return records.value.filter(record => {
    const statusOk = !appliedFilters.status || record.status === appliedFilters.status

    let dateOk = true
    if (appliedFilters.dateRange?.length === 2) {
      const current = getDatePart(record.changeTime)
      const [start, end] = appliedFilters.dateRange
      dateOk = current >= start && current <= end
    }

    return statusOk && dateOk
  })
})

const loadRecords = async () => {
  loading.value = true
  try {
    const response = await getChangeRecords()
    const data = response.data.data || response.data || []
    records.value = data.map(normalizeRecord)
  } catch (error) {
    records.value = []
    ElMessage.error(error.response?.data?.message || '退改记录查询失败')
  } finally {
    loading.value = false
  }
}

const applyFilters = () => {
  appliedFilters.status = filters.status
  appliedFilters.dateRange = Array.isArray(filters.dateRange) ? [...filters.dateRange] : []
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
  grid-template-columns: 420px 220px 100px;
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
  gap: 14px;
  min-height: 300px;
}

.record-card {
  padding: 22px 24px;
}

.change-card {
  border-left: 4px solid #60a5fa;
}

.refund-card {
  border-left: 6px solid #f97316;
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

/* 改签布局 */
.record-body.change-body {
  display: grid;
  grid-template-columns: minmax(300px, 1fr) 56px minmax(300px, 1fr) 280px;
  gap: 20px;
  align-items: stretch;
  padding-top: 18px;
}

/* 退票布局 */
.record-body.refund-body {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 300px;
  gap: 24px;
  align-items: stretch;
  padding-top: 18px;
}

.flight-change,
.cost-block {
  min-height: 220px;
  box-sizing: border-box;
}

.change-box,
.refund-box {
  padding: 18px 18px 16px;
  border-radius: 6px;
}

.change-box.before {
  border: 1px solid #bfdbfe;
  background: rgba(239, 246, 255, 0.78);
}

.change-box.after {
  border: 1px solid #cce7b0;
  background: rgba(240, 253, 244, 0.78);
}

.refund-box {
  border: 1px solid #fdba74;
  background: rgba(255, 247, 237, 0.78);
  padding-top: 20px;
  padding-left: 20px;
  padding-right: 20px;
}

.block-tag {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 96px;
  height: 34px;
  padding: 0 14px;
  border-radius: 6px;
  font-size: 16px;
  font-weight: 700;
  margin-bottom: 18px;
}

.before-tag {
  color: #60a5fa;
  background: #eff6ff;
  border: 1px solid #bfdbfe;
}

.after-tag {
  color: #65a30d;
  background: #f0fdf4;
  border: 1px solid #cce7b0;
}

.refund-tag {
  color: #f97316;
  background: #fff7ed;
  border: 1px solid #fdba74;
  margin-bottom: 20px;
}

.airline-line {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 18px;
}

.airline-line strong {
  font-size: 26px;
  line-height: 1.3;
  color: #0f172a;
}

.airline-line span {
  color: #475569;
  font-weight: 700;
  font-size: 20px;
}

.airport-line {
  line-height: 1.7;
  color: #334155;
  font-size: 19px;
  margin-bottom: 18px;
}

.time-line {
  color: #64748b;
  font-size: 18px;
  line-height: 1.8;
  margin-bottom: 18px;
}

.price-line {
  display: inline-block;
  font-size: 24px;
  color: #0f172a;
}

.arrow-block {
  color: #0b579f;
  font-size: 56px;
  font-weight: 900;
  display: flex;
  align-items: center;
  justify-content: center;
}

.cost-block {
  border-left: 1px solid #e2e8f0;
  padding-left: 22px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 20px;
}

.refund-cost-block {
  height: 100%;
}

.cost-block div {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 14px;
}

.cost-block span,
.cost-block strong {
  white-space: nowrap;
  font-size: 18px;
}

.cost-block span {
  color: #64748b;
}

.cost-block strong {
  color: #0f172a;
}

.price-text {
  color: #ef233c !important;
}

/* 响应式 */
@media (max-width: 1200px) {
  .record-body.change-body {
    grid-template-columns: 1fr;
  }

  .record-body.refund-body {
    grid-template-columns: 1fr;
  }

  .arrow-block {
    display: none;
  }

  .cost-block {
    border-left: none;
    padding-left: 0;
    min-height: auto;
  }
}

@media (max-width: 1000px) {
  .filter-row,
  .record-top {
    grid-template-columns: 1fr;
  }
}

/* ===== 退改记录页面最终紧凑修正：字号缩小 + 改签布局不溢出 ===== */

.records-page {
  max-width: 1180px !important;
  margin: 0 auto !important;
}

.record-card {
  padding: 18px 22px !important;
  overflow: hidden !important;
}

.record-top {
  display: grid !important;
  grid-template-columns: 1fr 1fr auto !important;
  gap: 16px !important;
  padding-bottom: 13px !important;
  font-size: 16px !important;
}

.record-top strong {
  font-size: 16px !important;
  line-height: 1.35 !important;
}

/* 改签：恢复成紧凑的 前 -> 后 -> 费用 */
.record-body.change-body {
  display: grid !important;
  grid-template-columns: minmax(250px, 1fr) 34px minmax(250px, 1fr) 230px !important;
  gap: 14px !important;
  align-items: stretch !important;
  padding-top: 14px !important;
}

/* 退票：左订单 + 右费用，不放大 */
.record-body.refund-body {
  display: grid !important;
  grid-template-columns: minmax(0, 1fr) 250px !important;
  gap: 18px !important;
  align-items: stretch !important;
  padding-top: 14px !important;
}

.flight-change,
.cost-block {
  min-height: 150px !important;
  box-sizing: border-box !important;
}

.change-box,
.refund-box {
  padding: 14px 16px !important;
  border-radius: 6px !important;
}

.refund-box {
  padding: 16px 18px !important;
}

.block-tag {
  min-width: 72px !important;
  height: 26px !important;
  padding: 0 12px !important;
  margin-bottom: 12px !important;
  font-size: 14px !important;
  font-weight: 700 !important;
}

.airline-line {
  display: flex !important;
  align-items: baseline !important;
  gap: 8px !important;
  flex-wrap: wrap !important;
  margin-bottom: 10px !important;
}

.airline-line strong {
  font-size: 18px !important;
  line-height: 1.35 !important;
  color: #0f172a !important;
}

.airline-line span {
  font-size: 15px !important;
  line-height: 1.35 !important;
  color: #475569 !important;
  font-weight: 700 !important;
}

.airport-line {
  margin-bottom: 8px !important;
  font-size: 15px !important;
  line-height: 1.55 !important;
  color: #334155 !important;
  word-break: keep-all !important;
}

.time-line {
  margin-bottom: 10px !important;
  font-size: 14px !important;
  line-height: 1.55 !important;
  color: #64748b !important;
}

.price-line {
  font-size: 17px !important;
  line-height: 1.35 !important;
  color: #0f172a !important;
}

.arrow-block {
  font-size: 34px !important;
  line-height: 1 !important;
  color: #0b579f !important;
}

.cost-block {
  padding-left: 14px !important;
  border-left: 1px solid #e2e8f0 !important;
  display: flex !important;
  flex-direction: column !important;
  justify-content: center !important;
  gap: 10px !important;
}

.cost-block div {
  display: grid !important;
  grid-template-columns: 92px minmax(0, 1fr) !important;
  justify-content: start !important;
  align-items: center !important;
  gap: 8px !important;
}

.cost-block span,
.cost-block strong {
  font-size: 15px !important;
  line-height: 1.45 !important;
  white-space: nowrap !important;
}

.cost-block span {
  color: #64748b !important;
}

.cost-block strong {
  color: #0f172a !important;
  text-align: left !important;
}

.price-text {
  color: #ef233c !important;
}

@media (max-width: 1200px) {
  .record-body.change-body,
  .record-body.refund-body {
    grid-template-columns: 1fr !important;
  }

  .arrow-block {
    display: none !important;
  }

  .cost-block {
    border-left: none !important;
    padding-left: 0 !important;
    min-height: auto !important;
  }
}

</style>
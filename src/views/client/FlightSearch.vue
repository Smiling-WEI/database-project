<template>
  <div class="page-container">
    <div class="white-card">
      <div class="card-title">
        <div class="blue-line"></div>
        <span>航班查询</span>
      </div>

      <div class="search-form-row">
        <div class="form-item">
          <span class="label">出发城市</span>
          <el-select
            v-model="searchForm.departure"
            placeholder="请选择城市"
            size="large"
            class="city-select"
          >
            <el-option
              v-for="city in cityOptions"
              :key="city"
              :label="city"
              :value="city"
            />
          </el-select>
        </div>

        <el-tooltip content="交换出发和到达城市" placement="top">
          <el-button class="exchange-btn" circle @click="swapCity">
            <el-icon><Switch /></el-icon>
          </el-button>
        </el-tooltip>

        <div class="form-item">
          <span class="label">到达城市</span>
          <el-select
            v-model="searchForm.arrival"
            placeholder="请选择城市"
            size="large"
            class="city-select"
          >
            <el-option
              v-for="city in cityOptions"
              :key="city"
              :label="city"
              :value="city"
            />
          </el-select>
        </div>

        <div class="form-item">
          <span class="label">出发日期</span>
          <el-date-picker
            v-model="searchForm.date"
            type="date"
            placeholder="选择日期"
            size="large"
            class="date-picker"
            value-format="YYYY-MM-DD"
            :disabled-date="disablePastDate"
          />
        </div>

        <div class="form-item btn-item">
          <el-button
            type="primary"
            size="large"
            class="search-btn"
            :loading="searching"
            @click="handleSearch"
          >
            <el-icon><Search /></el-icon>
            查询航班
          </el-button>
        </div>
      </div>

      <div v-if="historyList.length > 0" class="search-history">
        <span class="history-label">最近查询：</span>
        <button
          v-for="item in historyList"
          :key="item"
          type="button"
          class="history-item"
          @click="useHistory(item)"
        >
          {{ item.departure }} - {{ item.arrival }}
        </button>
        <button type="button" class="clear-history" @click="clearHistory">
          <el-icon><Delete /></el-icon>
          清除历史
        </button>
      </div>
    </div>

    <div v-if="hasSearched" class="white-card result-card">
      <div class="result-header">
        <div class="result-info">
          <strong>查询结果：</strong>
          {{ searchForm.departure }}
          <el-icon><Right /></el-icon>
          {{ searchForm.arrival }}
          <span class="date-text">{{ searchForm.date }}</span>
          <span class="count-text">共 {{ tableData.length }} 个航班</span>
        </div>
      </div>

      <el-empty
        v-if="tableData.length === 0"
        description="暂无符合条件的航班"
      />

      <el-table
        v-else
        :data="tableData"
        style="width: 100%"
        row-class-name="custom-row"
      >
        <el-table-column prop="flightNo" label="航班号" width="100" />

        <el-table-column prop="airline" label="航空公司" min-width="160">
          <template #default="{ row }">
            <div class="airline-cell">
              <span class="airline-dot" :class="row.airlineCode"></span>
              {{ row.airline }}
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="depAirport" label="出发机场" min-width="160" />
        <el-table-column prop="arrAirport" label="到达机场" min-width="160" />

        <el-table-column prop="depTime" label="起飞时间" align="center" width="100">
          <template #default="{ row }">
            <span class="time-text">{{ row.depTime }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="arrTime" label="到达时间" align="center" width="100">
          <template #default="{ row }">
            <span class="time-text">{{ row.arrTime }}</span>
          </template>
        </el-table-column>

        <el-table-column label="舱位" align="center" width="120">
          <template #default="{ row }">
            <div class="sub-cell-wrapper">
              <div v-if="row.cabins.length === 0" class="sub-cell-row muted-text">
                暂无可售舱位
              </div>
              <template v-else>
                <div
                  v-for="cabin in row.cabins"
                  :key="cabin.cabinName"
                  class="sub-cell-row"
                >
                  {{ cabin.cabinName }}
                </div>
              </template>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="价格" align="center" width="120">
          <template #default="{ row }">
            <div class="sub-cell-wrapper">
              <div v-if="row.cabins.length === 0" class="sub-cell-row muted-text">
                -
              </div>
              <template v-else>
                <div
                  v-for="cabin in row.cabins"
                  :key="cabin.cabinName"
                  class="sub-cell-row"
                >
                  <span v-if="cabin.price !== null" class="price-text">¥{{ cabin.price }}</span>
                  <span v-else class="muted-text">待定</span>
                </div>
              </template>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="剩余票数" align="center" width="120">
          <template #default="{ row }">
            <div class="sub-cell-wrapper">
              <div v-if="row.cabins.length === 0" class="sub-cell-row muted-text">
                -
              </div>
              <template v-else>
                <div
                  v-for="cabin in row.cabins"
                  :key="cabin.cabinName"
                  class="sub-cell-row"
                >
                  <span :class="['seat-text', cabin.seats === 0 ? 'sold-out-text' : '']">
                    {{ cabin.seats > 0 ? `剩余 ${cabin.seats} 张` : '无余票' }}
                  </span>
                </div>
              </template>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="操作" align="center" width="120">
          <template #default="{ row }">
            <div class="sub-cell-wrapper">
              <div v-if="row.cabins.length === 0" class="sub-cell-row">
                <el-button type="primary" size="small" class="buy-btn" disabled>
                  购买
                </el-button>
              </div>
              <template v-else>
                <div
                  v-for="cabin in row.cabins"
                  :key="cabin.cabinName"
                  class="sub-cell-row"
                >
                  <el-button
                    type="primary"
                    size="small"
                    class="buy-btn"
                    :disabled="cabin.seats === 0 || !cabin.pricingId"
                    @click="goToBooking(row, cabin)"
                  >
                    购买
                  </el-button>
                </div>
              </template>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="tableData.length > 0" class="pagination-wrapper">
        <el-pagination
          background
          layout="total, prev, pager, next"
          :page-size="10"
          :total="tableData.length"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Switch, Search, Delete, Right } from '@element-plus/icons-vue'
import { getFlightCabins, searchFlights } from '../../api/client/flight'

const router = useRouter()

const cityOptions = ['北京', '上海', '成都', '广州', '深圳']

const getTodayText = () => {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')

  return `${year}-${month}-${day}`
}

const searchForm = ref({
  departure: '北京',
  arrival: '上海',
  date: getTodayText()
})

const searching = ref(false)
const hasSearched = ref(false)
const tableData = ref([])
const historyList = ref([])

const disablePastDate = (date) => {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  return date < today
}

const formatTime = (value) => {
  if (!value) return '--:--'

  const text = String(value)
  const match = text.match(/(\d{2}):(\d{2})/)

  return match ? `${match[1]}:${match[2]}` : text
}

const normalizeCabin = (cabin) => {
  const seats = Number(cabin.remainingSeats ?? cabin.seats ?? 0)
  const price = cabin.price ?? cabin.salePrice

  return {
    pricingId: cabin.pricingId ?? null,
    cabinName: cabin.cabinName || cabin.cabinType || '',
    price: price === null || price === undefined ? null : Number(price),
    seats: Number.isNaN(seats) ? 0 : seats
  }
}

const normalizeFlight = (flight, cabins = []) => {
  const flightNo = flight.flightNo || ''

  return {
    instanceId: flight.instanceId,
    flightNo,
    airlineCode: flight.airlineCode || '',
    airline: flight.airline || flight.airlineName || '-',
    depAirport: flight.depAirport || '-',
    arrAirport: flight.arrAirport || '-',
    depTime: formatTime(flight.depTime),
    arrTime: formatTime(flight.arrTime),
    cabins: cabins.map(normalizeCabin).filter(cabin => cabin.cabinName)
  }
}

const swapCity = () => {
  const temp = searchForm.value.departure
  searchForm.value.departure = searchForm.value.arrival
  searchForm.value.arrival = temp
}

const clearHistory = () => {
  historyList.value = []
}

const useHistory = (item) => {
  searchForm.value.departure = item.departure
  searchForm.value.arrival = item.arrival
}

const addHistory = () => {
  const newHistory = {
    departure: searchForm.value.departure,
    arrival: searchForm.value.arrival
  }

  historyList.value = [
    newHistory,
    ...historyList.value.filter(
      item =>
        item.departure !== newHistory.departure ||
        item.arrival !== newHistory.arrival
    )
  ].slice(0, 5)
}

const handleSearch = async () => {
  if (!searchForm.value.departure || !searchForm.value.arrival || !searchForm.value.date) {
    ElMessage.warning('请先完整选择出发城市、到达城市和出发日期')
    return
  }

  if (searchForm.value.departure === searchForm.value.arrival) {
    ElMessage.warning('出发城市和到达城市不能相同')
    return
  }

  searching.value = true
  hasSearched.value = true

  try {
    const response = await searchFlights({
      departure: searchForm.value.departure,
      arrival: searchForm.value.arrival,
      date: searchForm.value.date
    })

    const flights = response.data.data || []

    tableData.value = await Promise.all(
      flights.map(async flight => {
        if (!flight.instanceId) {
          return normalizeFlight(flight)
        }

        try {
          const cabinResponse = await getFlightCabins(flight.instanceId)
          return normalizeFlight(flight, cabinResponse.data.data || [])
        } catch (error) {
          console.error(error)
          return normalizeFlight(flight)
        }
      })
    )

    addHistory()
  } catch (error) {
    tableData.value = []
    ElMessage.error(error.response?.data?.message || '航班查询失败，请稍后重试')
    console.error(error)
  } finally {
    searching.value = false
  }
}

const goToBooking = (flight, cabin) => {
  router.push({
    path: '/book',
    query: {
      instanceId: flight.instanceId,
      flightNo: flight.flightNo,
      airline: flight.airline,
      airlineCode: flight.airlineCode,
      pricingId: cabin.pricingId,
      cabinName: cabin.cabinName,
      price: cabin.price,
      depAirport: flight.depAirport,
      arrAirport: flight.arrAirport,
      depTime: flight.depTime,
      arrTime: flight.arrTime,
      date: searchForm.value.date
    }
  })
}
</script>

<style scoped>
.page-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.white-card {
  background: #ffffff;
  border-radius: 8px;
  padding: 24px 32px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
}

.card-title {
  display: flex;
  align-items: center;
  font-size: 18px;
  font-weight: bold;
  color: #1e293b;
  margin-bottom: 24px;
}

.blue-line {
  width: 4px;
  height: 18px;
  background-color: #1890ff;
  border-radius: 2px;
  margin-right: 10px;
}

.search-form-row {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 24px;
  width: 100%;
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.label {
  font-size: 13px;
  color: #64748b;
  font-weight: 500;
}

.city-select,
.date-picker {
  width: 180px;
}

.exchange-btn {
  margin-bottom: 1px;
  color: #64748b;
}

.exchange-btn:hover {
  color: #1890ff;
  border-color: #1890ff;
}

.btn-item {
  margin-left: auto;
}

.search-btn {
  width: 140px;
  font-weight: bold;
  background-color: #1890ff;
}

.search-history {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px dashed #e2e8f0;
  font-size: 13px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
}

.history-label {
  color: #94a3b8;
}

.history-item,
.clear-history {
  border: 0;
  background: transparent;
  cursor: pointer;
  font: inherit;
}

.history-item {
  color: #475569;
}

.history-item:hover {
  color: #1890ff;
}

.clear-history {
  color: #94a3b8;
  display: flex;
  align-items: center;
  gap: 4px;
}

.clear-history:hover {
  color: #ef4444;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  font-size: 14px;
}

.result-info {
  display: flex;
  align-items: center;
  gap: 6px;
}

.date-text,
.count-text {
  color: #64748b;
  margin-left: 8px;
}

:deep(.el-table .el-table__cell) {
  padding: 0 !important;
}

.sub-cell-wrapper {
  display: flex;
  flex-direction: column;
  width: 100%;
}

.sub-cell-row {
  min-height: 55px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-bottom: 1px solid #f1f5f9;
  padding: 8px 0;
  box-sizing: border-box;
}

.sub-cell-row:last-child {
  border-bottom: none;
}

.airline-cell {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
  padding-left: 12px;
}

.airline-dot {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  display: inline-block;
}

.CA {
  background-color: #e11d48;
}

.MU {
  background-color: #0284c7;
}

.time-text {
  font-size: 15px;
  font-weight: bold;
  color: #1e293b;
}

.price-text {
  font-size: 16px;
  font-weight: bold;
  color: #ef4444;
}

.seat-text {
  font-size: 13px;
  color: #475569;
}

.sold-out-text {
  color: #94a3b8;
  font-weight: normal;
}

.buy-btn {
  border-radius: 4px;
  font-weight: bold;
  width: 72px;
}

.pagination-wrapper {
  margin-top: 24px;
  display: flex;
  justify-content: flex-end;
}
</style>

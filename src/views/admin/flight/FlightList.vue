<template>
  <PageContainer
    title="航班管理"
    description="维护航班实例、执飞机型、座位数与运行状态"
  >
    <template #extra>
      <el-button type="primary" @click="goAddFlight">
        <el-icon><Plus /></el-icon>
        新增航班
      </el-button>
    </template>

    <!-- 筛选区域 -->
    <div class="filter-card">
      <el-form
        :model="queryForm"
        inline
        label-width="80px"
      >
        <el-form-item label="航班日期">
          <el-date-picker
            v-model="queryForm.date"
            type="date"
            placeholder="请选择日期"
            value-format="YYYY-MM-DD"
            clearable
            style="width: 170px"
          />
        </el-form-item>

        <el-form-item label="航班状态">
          <el-select
            v-model="queryForm.status"
            placeholder="请选择状态"
            clearable
            style="width: 150px"
          >
            <el-option label="正常" value="正常" />
            <el-option label="延误" value="延误" />
            <el-option label="取消" value="取消" />
            <el-option label="已完成" value="已完成" />
          </el-select>
        </el-form-item>

        <el-form-item label="航班号">
          <el-input
            v-model="queryForm.flightNo"
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
        :data="filteredFlights"
        stripe
        border
        table-layout="fixed"
        style="width: 100%"
        empty-text="暂无航班数据，待后端接口接入"
      >
        <el-table-column prop="instanceId" label="实例ID" width="90" />
        <el-table-column prop="flightNo" label="航班号" width="110" />
        <el-table-column prop="flightDate" label="航班日期" width="120" />
        <el-table-column prop="airlineName" label="航空公司" width="140" show-overflow-tooltip />
        <el-table-column prop="depAirport" label="出发机场" min-width="160" show-overflow-tooltip />
        <el-table-column prop="arrAirport" label="到达机场" min-width="160" show-overflow-tooltip />
        <el-table-column prop="aircraftModel" label="执飞机型" width="120" show-overflow-tooltip />
        <el-table-column prop="firstSeats" label="头等舱座位" width="120" />
        <el-table-column prop="economySeats" label="经济舱座位" width="120" />

        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="操作" fixed="right" width="170">
          <template #default="{ row }">
            <el-button
              type="primary"
              link
              @click="goEditFlight(row)"
            >
              编辑
            </el-button>

            <el-button
              type="warning"
              link
              @click="handleIrregularity(row)"
            >
              发布异常
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrap">
        <el-pagination
          background
          layout="total, prev, pager, next"
          :total="filteredFlights.length"
          :page-size="10"
        />
      </div>
    </div>
  </PageContainer>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import PageContainer from '../../../components/admin/PageContainer.vue'

const router = useRouter()

const queryForm = reactive({
  date: '',
  status: '',
  flightNo: ''
})

// 后续由后端接口赋值，例如：flightList.value = 接口返回的航班数组
const flightList = ref([])

const filteredFlights = computed(() => {
  return flightList.value.filter((item) => {
    const matchDate = !queryForm.date || item.flightDate === queryForm.date
    const matchStatus = !queryForm.status || item.status === queryForm.status
    const matchFlightNo = !queryForm.flightNo || item.flightNo?.includes(queryForm.flightNo)

    return matchDate && matchStatus && matchFlightNo
  })
})

const handleSearch = () => {
  ElMessage.info('查询条件已更新，待后端接口接入后获取真实数据')
}

const handleReset = () => {
  queryForm.date = ''
  queryForm.status = ''
  queryForm.flightNo = ''
}

const goAddFlight = () => {
  router.push('/admin/flights/edit')
}

const goEditFlight = (row) => {
  router.push({
    path: '/admin/flights/edit',
    query: {
      instanceId: row.instanceId
    }
  })
}

const handleIrregularity = () => {
  ElMessage.info('发布航班异常功能待后端接口接入')
}

const getStatusType = (status) => {
  if (status === '正常') return 'success'
  if (status === '延误') return 'warning'
  if (status === '取消') return 'danger'
  if (status === '已完成') return 'info'
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
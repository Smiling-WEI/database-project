<template>
  <PageContainer
    :title="isEdit ? '编辑航班' : '新增航班'"
    :description="isEdit ? '修改航班实例的时间、机型、座位数与运行状态' : '新增当前航司某一日期的航班实例并配置初始舱位票价'"
  >
    <template #extra>
      <el-button @click="goBack">
        返回列表
      </el-button>
    </template>

    <el-alert
      v-if="!canManageFlights"
      title="当前岗位仅可查看航班详情，无权新增或修改航班"
      type="info"
      :closable="false"
      show-icon
      class="permission-alert"
    />

    <div class="form-card">
      <el-form
        ref="formRef"
        :model="flightForm"
        :rules="rules"
        :disabled="!canManageFlights"
        label-width="110px"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="航班号" prop="flightNo">
              <el-input
                v-model="flightForm.flightNo"
                placeholder="例如 CA1833"
                :disabled="isEdit || !canManageFlights"
              />
            </el-form-item>
          </el-col>

          <el-col :span="12">
            <el-form-item label="航班日期" prop="flightDate">
              <el-date-picker
                v-model="flightForm.flightDate"
                type="date"
                placeholder="请选择航班日期"
                value-format="YYYY-MM-DD"
                style="width: 100%"
                :disabled="isEdit || !canManageFlights"
              />
            </el-form-item>
          </el-col>

          <el-col :span="24">
            <el-form-item label="航线" prop="routeId">
              <el-select
                v-model="flightForm.routeId"
                placeholder="请选择航线"
                style="width: 100%"
                :disabled="isEdit || !canManageFlights"
                filterable
              >
                <el-option
                  v-for="route in routes"
                  :key="route.routeId"
                  :label="route.routeLabel"
                  :value="route.routeId"
                />
              </el-select>
              <div class="form-tip">
                新增不存在的航班号时，系统会按当前航司代码校验航班号前缀，并将该航班号绑定到所选航线。
              </div>
            </el-form-item>
          </el-col>

          <el-col :span="12">
            <el-form-item label="起飞时间" prop="depTime">
              <el-time-picker
                v-model="flightForm.depTime"
                format="HH:mm"
                value-format="HH:mm"
                placeholder="请选择起飞时间"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>

          <el-col :span="12">
            <el-form-item label="到达时间" prop="arrTime">
              <el-time-picker
                v-model="flightForm.arrTime"
                format="HH:mm"
                value-format="HH:mm"
                placeholder="请选择到达时间"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>

          <el-col :span="12">
            <el-form-item label="执飞机型" prop="aircraftModel">
              <el-input
                v-model="flightForm.aircraftModel"
                placeholder="请输入执飞机型"
              />
            </el-form-item>
          </el-col>

          <el-col :span="12">
            <el-form-item label="航班状态" prop="status">
              <el-select
                v-model="flightForm.status"
                placeholder="请选择航班状态"
                style="width: 100%"
              >
                <el-option label="正常" value="正常" />
                <el-option label="延误" value="延误" />
                <el-option label="取消" value="取消" />
                <el-option label="已完成" value="已完成" />
              </el-select>
            </el-form-item>
          </el-col>

          <el-col :span="12">
            <el-form-item label="头等舱座位" prop="firstSeats">
              <el-input-number
                v-model="flightForm.firstSeats"
                :min="0"
                :step="1"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>

          <el-col :span="12">
            <el-form-item label="头等舱票价" prop="firstPrice">
              <el-input-number
                v-model="flightForm.firstPrice"
                :min="0"
                :precision="2"
                :step="100"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>

          <el-col :span="12">
            <el-form-item label="经济舱座位" prop="economySeats">
              <el-input-number
                v-model="flightForm.economySeats"
                :min="0"
                :step="1"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>

          <el-col :span="12">
            <el-form-item label="经济舱票价" prop="economyPrice">
              <el-input-number
                v-model="flightForm.economyPrice"
                :min="0"
                :precision="2"
                :step="100"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <div class="form-actions">
          <el-button @click="goBack">
            取消
          </el-button>
          <el-button
            type="primary"
            :disabled="!canManageFlights"
            @click="handleSubmit"
          >
            保存
          </el-button>
        </div>
      </el-form>
    </div>
  </PageContainer>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import PageContainer from '../../../components/admin/PageContainer.vue'
import api from '../../../api/index'
import {
  canManageFlights as canEditFlights,
  getStoredUser
} from '../../../utils/adminAuth'

const route = useRoute()
const router = useRouter()
const formRef = ref()

const isEdit = computed(() => Boolean(route.query.instanceId))
const currentUser = computed(() => getStoredUser())
const routes = ref([])

const canManageFlights = computed(() => {
  return canEditFlights(currentUser.value)
})

const flightForm = reactive({
  flightNo: '',
  flightDate: '',
  routeId: '',
  depTime: '',
  arrTime: '',
  aircraftModel: '',
  firstSeats: 0,
  firstPrice: 0,
  economySeats: 0,
  economyPrice: 0,
  status: '正常'
})

const rules = {
  flightNo: [
    { required: true, message: '请输入航班号', trigger: 'blur' }
  ],
  flightDate: [
    { required: true, message: '请选择航班日期', trigger: 'change' }
  ],
  routeId: [
    { required: true, message: '请选择航线', trigger: 'change' }
  ],
  depTime: [
    { required: true, message: '请选择起飞时间', trigger: 'change' }
  ],
  arrTime: [
    { required: true, message: '请选择到达时间', trigger: 'change' }
  ],
  aircraftModel: [
    { required: true, message: '请输入执飞机型', trigger: 'blur' }
  ],
  firstSeats: [
    { required: true, message: '请输入头等舱座位数', trigger: 'blur' }
  ],
  firstPrice: [
    { required: true, message: '请输入头等舱票价', trigger: 'blur' }
  ],
  economySeats: [
    { required: true, message: '请输入经济舱座位数', trigger: 'blur' }
  ],
  economyPrice: [
    { required: true, message: '请输入经济舱票价', trigger: 'blur' }
  ],
  status: [
    { required: true, message: '请选择状态', trigger: 'change' }
  ]
}

const loadRoutes = async () => {
  try {
    const response = await api.get('/admin/routes')
    routes.value = response.data.data || []
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '航线列表加载失败')
    console.error(error)
  }
}

const loadFlightDetail = async () => {
  if (!isEdit.value) return

  try {
    const instanceId = route.query.instanceId
    const response = await api.get(`/admin/flights/${instanceId}`)
    const flight = response.data.data

    flightForm.flightNo = flight.flightNo
    flightForm.flightDate = flight.flightDate
    flightForm.routeId = flight.routeId
    flightForm.depTime = flight.depTime || ''
    flightForm.arrTime = flight.arrTime || ''
    flightForm.aircraftModel = flight.aircraftModel
    flightForm.firstSeats = flight.firstSeats
    flightForm.economySeats = flight.economySeats
    flightForm.status = flight.status
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '航班详情加载失败')
    console.error(error)
  }
}

const goBack = () => {
  router.push('/admin/flights')
}

const handleSubmit = async () => {
  if (!canManageFlights.value) {
    ElMessage.warning('当前岗位无权新增或修改航班')
    return
  }

  if (!formRef.value) return

  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  if (!isEdit.value) {
    if (flightForm.firstSeats > 0 && Number(flightForm.firstPrice) <= 0) {
      ElMessage.warning('头等舱有座位时，头等舱票价必须大于 0')
      return
    }

    if (flightForm.economySeats > 0 && Number(flightForm.economyPrice) <= 0) {
      ElMessage.warning('经济舱有座位时，经济舱票价必须大于 0')
      return
    }
  }

  const payload = {
    route_id: flightForm.routeId,
    dep_time: flightForm.depTime,
    arr_time: flightForm.arrTime,
    aircraft_model: flightForm.aircraftModel,
    first_seats: flightForm.firstSeats,
    economy_seats: flightForm.economySeats,
    status: flightForm.status
  }

  try {
    if (isEdit.value) {
      await api.put(`/admin/flights/${route.query.instanceId}`, payload)
      ElMessage.success('航班信息已保存')
    } else {
      await api.post('/admin/flights', {
        flight_no: flightForm.flightNo,
        flight_date: flightForm.flightDate,
        first_price: flightForm.firstPrice,
        economy_price: flightForm.economyPrice,
        ...payload
      })
      ElMessage.success('航班已新增')
    }

    goBack()
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '航班保存失败')
    console.error(error)
  }
}

onMounted(async () => {
  await loadRoutes()
  await loadFlightDetail()
})
</script>

<style scoped>
.form-card {
  max-width: 980px;
  padding: 24px 24px 8px;
  border-radius: 18px;
  background: #ffffff;
  border: 1px solid #e2e8f0;
}

.form-tip {
  margin-top: 6px;
  color: #64748b;
  font-size: 12px;
  line-height: 1.5;
}

.form-actions {
  margin-top: 10px;
  padding: 18px 0 8px;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

:deep(.el-form-item) {
  margin-bottom: 20px;
}

.permission-alert {
  margin-bottom: 18px;
}
</style>

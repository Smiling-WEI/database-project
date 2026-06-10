<template>
  <PageContainer
    :title="isEdit ? '编辑航班' : '新增航班'"
    :description="isEdit ? '修改航班实例的机型、座位数与运行状态' : '新增当前航司某一日期的航班实例'"
  >
    <template #extra>
      <el-button @click="goBack">
        返回列表
      </el-button>
    </template>

    <el-alert
      v-if="isEdit"
      class="edit-alert"
      title="当前为编辑模式：后续应由后端根据 instanceId 返回航班详情并回显到表单。"
      type="info"
      show-icon
      :closable="false"
    />

    <div class="form-card">
      <el-form
        ref="formRef"
        :model="flightForm"
        :rules="rules"
        label-width="110px"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="航班号" prop="flightNo">
              <el-input
                v-model="flightForm.flightNo"
                placeholder="请输入航班号"
                :disabled="isEdit"
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
                :disabled="isEdit"
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
            <el-form-item label="经济舱座位" prop="economySeats">
              <el-input-number
                v-model="flightForm.economySeats"
                :min="0"
                :step="1"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>

          <el-col :span="24">
            <el-form-item label="接入说明">
              <el-input
                type="textarea"
                :rows="4"
                disabled
                model-value="当前页面已保留后端接入所需字段：flight_no、flight_date、aircraft_model、first_seats、economy_seats、status。后续联调时由后端接口完成新增、详情回显与修改保存。"
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
import { computed, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import PageContainer from '../../../components/admin/PageContainer.vue'

const route = useRoute()
const router = useRouter()
const formRef = ref()

const isEdit = computed(() => Boolean(route.query.instanceId))

// 删除写死默认航班信息，只保留空表单结构
const flightForm = reactive({
  flightNo: '',
  flightDate: '',
  aircraftModel: '',
  firstSeats: 0,
  economySeats: 0,
  status: '正常'
})

const rules = {
  flightNo: [
    { required: true, message: '请输入航班号', trigger: 'blur' }
  ],
  flightDate: [
    { required: true, message: '请选择航班日期', trigger: 'change' }
  ],
  aircraftModel: [
    { required: true, message: '请输入执飞机型', trigger: 'blur' }
  ],
  firstSeats: [
    { required: true, message: '请输入头等舱座位数', trigger: 'blur' }
  ],
  economySeats: [
    { required: true, message: '请输入经济舱座位数', trigger: 'blur' }
  ],
  status: [
    { required: true, message: '请选择状态', trigger: 'change' }
  ]
}

const goBack = () => {
  router.push('/admin/flights')
}

const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate((valid) => {
    if (!valid) return

    const payload = {
      flight_no: flightForm.flightNo,
      flight_date: flightForm.flightDate,
      aircraft_model: flightForm.aircraftModel,
      first_seats: flightForm.firstSeats,
      economy_seats: flightForm.economySeats,
      status: flightForm.status
    }

    console.log('待提交给后端的航班数据：', payload)

    if (isEdit.value) {
      ElMessage.info('表单校验通过，修改接口待后端接入')
    } else {
      ElMessage.info('表单校验通过，新增接口待后端接入')
    }
  })
}
</script>

<style scoped>
.edit-alert {
  margin-bottom: 18px;
}

.form-card {
  max-width: 980px;
  padding: 24px 24px 8px;
  border-radius: 18px;
  background: #ffffff;
  border: 1px solid #e2e8f0;
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
</style>
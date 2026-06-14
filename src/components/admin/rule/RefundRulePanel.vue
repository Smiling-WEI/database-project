<template>
  <div>
    <div class="toolbar">
      <el-alert
        title="规则字段严格对应 refund_rule：起飞前时间区间、手续费率、有效期和状态。"
        type="info"
        :closable="false"
        show-icon
      />
      <el-button
        type="primary"
        :disabled="!canEdit || requiresAirline"
        @click="handleAdd"
      >
        <el-icon><Plus /></el-icon>
        新增退票规则
      </el-button>
    </div>

    <el-alert
      v-if="requiresAirline"
      title="系统总管理员新增规则前需要先选择目标航空公司"
      type="warning"
      :closable="false"
      show-icon
      class="notice"
    />

    <div class="filter-card">
      <el-form :model="queryForm" inline label-width="80px">
        <el-form-item label="规则状态">
          <el-select
            v-model="queryForm.status"
            clearable
            placeholder="全部状态"
            style="width: 140px"
          >
            <el-option label="启用" value="启用" />
            <el-option label="停用" value="停用" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadRules">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <div class="table-card">
      <el-table
        v-loading="loading"
        :data="pagedRules"
        border
        stripe
        empty-text="暂无退票规则"
      >
        <el-table-column prop="ruleId" label="规则ID" width="90" />
        <el-table-column
          v-if="systemAdmin"
          prop="airlineName"
          label="航空公司"
          min-width="150"
        />
        <el-table-column label="起飞前时间区间" min-width="170">
          <template #default="{ row }">{{ formatHourRange(row) }}</template>
        </el-table-column>
        <el-table-column label="手续费比例" width="120">
          <template #default="{ row }">{{ formatPercent(row.feeRate) }}</template>
        </el-table-column>
        <el-table-column prop="validFrom" label="生效时间" min-width="175" />
        <el-table-column label="失效时间" min-width="175">
          <template #default="{ row }">{{ row.validTo || '长期有效' }}</template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === '启用' ? 'success' : 'info'">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" fixed="right" width="160">
          <template #default="{ row }">
            <el-button
              type="primary"
              link
              :disabled="!canEdit"
              @click="handleEdit(row)"
            >
              编辑
            </el-button>
            <el-button
              :type="row.status === '启用' ? 'danger' : 'success'"
              link
              :disabled="!canEdit"
              @click="handleStatus(row)"
            >
              {{ row.status === '启用' ? '停用' : '启用' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="pagination.currentPage"
          v-model:page-size="pagination.pageSize"
          background
          layout="total, prev, pager, next"
          :total="filteredRules.length"
        />
      </div>
    </div>

    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '修改退票规则' : '新增退票规则'"
      width="620px"
      @closed="resetForm"
    >
      <el-form
        ref="formRef"
        :model="ruleForm"
        :rules="formRules"
        label-width="130px"
      >
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="时间下限" prop="minHours">
              <el-input-number
                v-model="ruleForm.minHours"
                :min="0"
                controls-position="right"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="时间上限">
              <el-input-number
                v-model="ruleForm.maxHours"
                :min="ruleForm.minHours + 1"
                :disabled="ruleForm.noUpperLimit"
                controls-position="right"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="不设时间上限">
          <el-switch v-model="ruleForm.noUpperLimit" />
        </el-form-item>

        <el-form-item label="手续费比例" prop="feeRatePercent">
          <el-input-number
            v-model="ruleForm.feeRatePercent"
            :min="0"
            :max="100"
            :precision="2"
            controls-position="right"
            style="width: 100%"
          />
          <span class="form-help">按原票价百分比计算</span>
        </el-form-item>

        <el-form-item label="规则有效时间" prop="validRange">
          <el-date-picker
            v-model="ruleForm.validRange"
            type="datetimerange"
            range-separator="至"
            start-placeholder="生效时间"
            end-placeholder="失效时间"
            value-format="YYYY-MM-DD HH:mm:ss"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="规则状态" prop="status">
          <el-radio-group v-model="ruleForm.status">
            <el-radio label="启用" />
            <el-radio label="停用" />
          </el-radio-group>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">
          保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import {
  createRefundRule,
  getRefundRules,
  updateRefundRule,
  updateRefundRuleStatus
} from '../../../api/admin/rule'
import {
  canManageChangeRules,
  getAirlineScopeParams,
  getStoredUser,
  isSystemAdmin
} from '../../../utils/adminAuth'

const props = defineProps({
  airlineId: {
    type: [Number, String],
    default: ''
  }
})

const currentUser = computed(() => getStoredUser())
const systemAdmin = computed(() => isSystemAdmin(currentUser.value))
const canEdit = computed(() => canManageChangeRules(currentUser.value))
const requiresAirline = computed(() => systemAdmin.value && !props.airlineId)
const loading = ref(false)
const submitting = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const editingRuleId = ref(null)
const ruleList = ref([])
const formRef = ref()

const queryForm = reactive({ status: '' })
const pagination = reactive({ currentPage: 1, pageSize: 10 })
const ruleForm = reactive({
  minHours: 0,
  maxHours: 24,
  noUpperLimit: false,
  feeRatePercent: 0,
  validRange: [],
  status: '启用'
})

const formRules = {
  minHours: [{ required: true, message: '请输入时间下限', trigger: 'blur' }],
  feeRatePercent: [{ required: true, message: '请输入手续费比例', trigger: 'blur' }],
  validRange: [{ required: true, message: '请选择规则有效时间', trigger: 'change' }],
  status: [{ required: true, message: '请选择状态', trigger: 'change' }]
}

const filteredRules = computed(() => {
  return ruleList.value.filter(
    (item) => !queryForm.status || item.status === queryForm.status
  )
})

const pagedRules = computed(() => {
  const start = (pagination.currentPage - 1) * pagination.pageSize
  return filteredRules.value.slice(start, start + pagination.pageSize)
})

const loadRules = async () => {
  loading.value = true
  try {
    const response = await getRefundRules({
      ...getAirlineScopeParams(props.airlineId),
      status: queryForm.status || undefined
    })
    ruleList.value = response.data.data || []
  } catch (error) {
    ruleList.value = []
    ElMessage.error(error.response?.data?.message || '退票规则接口待后端接入')
  } finally {
    loading.value = false
  }
}

const resetForm = () => {
  ruleForm.minHours = 0
  ruleForm.maxHours = 24
  ruleForm.noUpperLimit = false
  ruleForm.feeRatePercent = 0
  ruleForm.validRange = []
  ruleForm.status = '启用'
  editingRuleId.value = null
  formRef.value?.clearValidate()
}

const handleReset = () => {
  queryForm.status = ''
  pagination.currentPage = 1
  loadRules()
}

const handleAdd = () => {
  isEdit.value = false
  resetForm()
  dialogVisible.value = true
}

const handleEdit = (row) => {
  isEdit.value = true
  editingRuleId.value = row.ruleId
  ruleForm.minHours = row.minHoursBeforeDeparture
  ruleForm.noUpperLimit = row.maxHoursBeforeDeparture === null
  ruleForm.maxHours = row.maxHoursBeforeDeparture ?? row.minHoursBeforeDeparture + 24
  ruleForm.feeRatePercent = Number(row.feeRate) * 100
  ruleForm.validRange = [row.validFrom, row.validTo].filter(Boolean)
  ruleForm.status = row.status
  dialogVisible.value = true
}

const handleStatus = async (row) => {
  const status = row.status === '启用' ? '停用' : '启用'
  try {
    await ElMessageBox.confirm(`确认${status}该退票规则吗？`, '规则状态确认')
    await updateRefundRuleStatus(row.ruleId, status)
    ElMessage.success(`规则已${status}`)
    loadRules()
  } catch (error) {
    if (error === 'cancel' || error === 'close') return
    ElMessage.error(error.response?.data?.message || '规则状态修改失败')
  }
}

const handleSubmit = async () => {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  if (!ruleForm.noUpperLimit && ruleForm.maxHours <= ruleForm.minHours) {
    ElMessage.warning('时间上限必须大于时间下限')
    return
  }

  const payload = {
    ...getAirlineScopeParams(props.airlineId),
    min_hours_before_departure: ruleForm.minHours,
    max_hours_before_departure: ruleForm.noUpperLimit ? null : ruleForm.maxHours,
    fee_rate: Number((ruleForm.feeRatePercent / 100).toFixed(4)),
    valid_from: ruleForm.validRange[0],
    valid_to: ruleForm.validRange[1] || null,
    status: ruleForm.status
  }

  submitting.value = true
  try {
    if (isEdit.value) {
      await updateRefundRule(editingRuleId.value, payload)
      ElMessage.success('退票规则已修改')
    } else {
      await createRefundRule(payload)
      ElMessage.success('退票规则已新增')
    }
    dialogVisible.value = false
    loadRules()
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '退票规则保存失败')
  } finally {
    submitting.value = false
  }
}

const formatHourRange = (row) => {
  if (row.maxHoursBeforeDeparture === null) {
    return `${row.minHoursBeforeDeparture} 小时以上`
  }
  return `${row.minHoursBeforeDeparture} - ${row.maxHoursBeforeDeparture} 小时`
}

const formatPercent = (value) => `${(Number(value || 0) * 100).toFixed(2)}%`

watch(() => props.airlineId, loadRules)
onMounted(loadRules)
</script>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 18px;
}

.toolbar .el-alert {
  flex: 1;
}

.notice {
  margin-bottom: 18px;
}

.filter-card {
  margin-bottom: 18px;
  padding: 18px 18px 0;
  border-radius: 16px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
}

.table-card {
  padding: 18px;
  border-radius: 16px;
  background: #fff;
  border: 1px solid #e2e8f0;
  overflow-x: auto;
}

.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 18px;
}

.form-help {
  margin-left: 10px;
  color: #94a3b8;
  font-size: 12px;
}
</style>

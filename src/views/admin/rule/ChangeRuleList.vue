<template>
  <PageContainer
    title="票务配置 / 退改签规则"
    description="统一维护退票与改签的时间区间、手续费比例和费用处理策略"
  >
    <template #extra>
      <el-button
        type="primary"
        :disabled="!canEditRules || (systemAdmin && !selectedAirlineId)"
        @click="handleAdd"
      >
        <el-icon><Plus /></el-icon>
        {{ activeRuleTab === 'refund' ? '新增退票规则' : '新增改签规则' }}
      </el-button>
    </template>

    <div v-if="systemAdmin" class="scope-card">
      <el-form inline label-width="80px">
        <AirlineScopeSelect
          v-model="selectedAirlineId"
          @change="handleAirlineChange"
        />
      </el-form>
    </div>

    <el-tabs
      v-model="activeRuleTab"
      class="rule-tabs"
      @tab-change="handleTabChange"
    >
      <el-tab-pane label="退票规则" name="refund" />
      <el-tab-pane label="改签规则" name="change" />
    </el-tabs>

    <div class="filter-card">
      <el-form :model="queryForm" inline label-width="90px">
        <el-form-item :label="activeRuleTab === 'refund' ? '退票类型' : '改签类型'">
          <el-select
            v-model="queryForm.changeType"
            :placeholder="activeRuleTab === 'refund' ? '请选择退票类型' : '请选择改签类型'"
            clearable
            style="width: 220px"
          >
            <el-option
              v-for="type in currentRuleTypes"
              :key="type"
              :label="type"
              :value="type"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="规则状态">
          <el-select
            v-model="queryForm.status"
            placeholder="请选择状态"
            clearable
            style="width: 140px"
          >
            <el-option label="启用" value="启用" />
            <el-option label="停用" value="停用" />
          </el-select>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <el-alert
      v-if="!canEditRules"
      :title="activeRuleTab === 'refund'
        ? '当前岗位仅可查看退票规则，无权新增或修改规则'
        : '当前岗位仅可查看改签规则，无权新增或修改规则'"
      type="info"
      :closable="false"
      show-icon
      class="permission-alert"
    />

    <div class="table-card">
      <el-table
        v-loading="loading"
        :data="pagedRules"
        stripe
        border
        table-layout="fixed"
        style="width: 100%"
        :empty-text="activeRuleTab === 'refund' ? '暂无退票规则' : '暂无改签规则'"
      >
        <el-table-column prop="ruleId" label="规则ID" width="90" />
        <el-table-column
          prop="changeType"
          :label="activeRuleTab === 'refund' ? '退票类型' : '改签类型'"
          min-width="190"
        />

        <el-table-column label="起飞前时间区间" width="170">
          <template #default="{ row }">
            {{ formatHourRange(row) }}
          </template>
        </el-table-column>

        <el-table-column label="手续费比例" width="120">
          <template #default="{ row }">
            {{ formatPercent(row.feeRate) }}
          </template>
        </el-table-column>

        <el-table-column
          v-if="activeRuleTab === 'refund'"
          label="退款处理"
          min-width="190"
        >
          <template #default="{ row }">
            {{ Number(row.feeRate || 0) === 0 ? '全额退款' : '扣除手续费后退款' }}
          </template>
        </el-table-column>

        <el-table-column
          v-if="activeRuleTab === 'change'"
          label="补收正差价"
          width="120"
        >
          <template #default="{ row }">
            <el-tag :type="row.chargePositiveDifference ? 'success' : 'info'">
              {{ row.chargePositiveDifference ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column
          v-if="activeRuleTab === 'change'"
          label="退还负差价"
          width="120"
        >
          <template #default="{ row }">
            <el-tag :type="row.refundNegativeDifference ? 'success' : 'info'">
              {{ row.refundNegativeDifference ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="validFrom" label="生效时间" min-width="175" />

        <el-table-column label="失效时间" min-width="175">
          <template #default="{ row }">
            {{ row.validTo || '长期有效' }}
          </template>
        </el-table-column>

        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === '启用' ? 'success' : 'info'">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="操作" fixed="right" width="100">
          <template #default="{ row }">
            <el-button
              type="primary"
              link
              :disabled="!canEditRules"
              @click="handleEdit(row)"
            >
              编辑
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
      :title="dialogTitle"
      width="660px"
      @closed="resetForm"
    >
      <el-form
        ref="formRef"
        :model="ruleForm"
        :rules="rules"
        label-width="130px"
      >
        <el-form-item :label="activeRuleTab === 'refund' ? '退票类型' : '改签类型'" prop="changeType">
          <el-select
            v-model="ruleForm.changeType"
            :placeholder="activeRuleTab === 'refund' ? '请选择退票类型' : '请选择改签类型'"
            style="width: 100%"
          >
            <el-option
              v-for="type in currentRuleTypes"
              :key="type"
              :label="type"
              :value="type"
            />
          </el-select>
        </el-form-item>

        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="时间下限" prop="minHours">
              <el-input-number
                v-model="ruleForm.minHours"
                :min="0"
                :step="1"
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
                :step="1"
                :disabled="ruleForm.noUpperLimit"
                controls-position="right"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="不设时间上限">
          <el-switch v-model="ruleForm.noUpperLimit" />
          <span class="form-help">例如“48 小时以上”</span>
        </el-form-item>

        <el-form-item label="手续费比例" prop="feeRatePercent">
          <el-input-number
            v-model="ruleForm.feeRatePercent"
            :min="0"
            :max="100"
            :precision="2"
            :step="1"
            controls-position="right"
            style="width: 100%"
          />
          <span class="form-help">按原票价百分比计算，例如 10 表示 10%</span>
        </el-form-item>

        <el-row v-if="activeRuleTab === 'change'" :gutter="16">
          <el-col :span="12">
            <el-form-item label="补收正差价">
              <el-switch v-model="ruleForm.chargePositiveDifference" />
            </el-form-item>
          </el-col>

          <el-col :span="12">
            <el-form-item label="退还负差价">
              <el-switch v-model="ruleForm.refundNegativeDifference" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-alert
          v-if="activeRuleTab === 'refund'"
          title="退票规则只计算退票手续费与退款金额，不需要设置补收或退还差价。"
          type="info"
          :closable="false"
          show-icon
          class="dialog-alert"
        />

        <el-form-item label="规则状态" prop="status">
          <el-radio-group v-model="ruleForm.status">
            <el-radio label="启用" />
            <el-radio label="停用" />
          </el-radio-group>
        </el-form-item>

        <el-form-item
          v-if="!isEdit"
          label="规则有效时间"
          prop="validRange"
        >
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

        <el-alert
          v-else
          title="编辑时保留原规则有效期，只修改规则内容和状态。"
          type="info"
          :closable="false"
          show-icon
        />
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          :loading="submitting"
          @click="handleSubmit"
        >
          保存
        </el-button>
      </template>
    </el-dialog>
  </PageContainer>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import PageContainer from '../../../components/admin/PageContainer.vue'
import AirlineScopeSelect from '../../../components/admin/AirlineScopeSelect.vue'
import {
  createChangeRule,
  getChangeRules,
  updateChangeRule
} from '../../../api/admin/rule'
import {
  canManageChangeRules,
  getAirlineScopeParams,
  getStoredUser,
  isSystemAdmin
} from '../../../utils/adminAuth'

const formRef = ref()
const activeRuleTab = ref('refund')
const selectedAirlineId = ref('')
const loading = ref(false)
const submitting = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const editingRuleId = ref(null)
const ruleList = ref([])

const refundTypes = [
  '乘客主动退票',
  '航司原因退票'
]

const changeTypes = [
  '乘客主动改签',
  '航司原因同航司改签',
  '航司原因跨航司改签'
]

const queryForm = reactive({
  changeType: '',
  status: ''
})

const pagination = reactive({
  currentPage: 1,
  pageSize: 10
})

const ruleForm = reactive({
  changeType: '',
  minHours: 0,
  maxHours: 24,
  noUpperLimit: false,
  feeRatePercent: 0,
  chargePositiveDifference: true,
  refundNegativeDifference: false,
  status: '启用',
  validRange: []
})

const currentUser = computed(() => getStoredUser())
const systemAdmin = computed(() => isSystemAdmin(currentUser.value))
const canEditRules = computed(() => canManageChangeRules(currentUser.value))

const currentRuleTypes = computed(() => {
  return activeRuleTab.value === 'refund' ? refundTypes : changeTypes
})

const dialogTitle = computed(() => {
  if (activeRuleTab.value === 'refund') {
    return isEdit.value ? '修改退票规则' : '新增退票规则'
  }

  return isEdit.value ? '修改改签规则' : '新增改签规则'
})

const rules = {
  changeType: [
    { required: true, message: '请选择规则类型', trigger: 'change' }
  ],
  minHours: [
    { required: true, message: '请输入时间下限', trigger: 'blur' }
  ],
  feeRatePercent: [
    { required: true, message: '请输入手续费比例', trigger: 'blur' }
  ],
  status: [
    { required: true, message: '请选择规则状态', trigger: 'change' }
  ],
  validRange: [
    { required: true, message: '请选择规则有效时间', trigger: 'change' }
  ]
}

const filteredRules = computed(() => {
  return ruleList.value.filter((item) => {
    const belongsToCurrentTab =
      activeRuleTab.value === 'refund'
        ? String(item.changeType || '').includes('退票')
        : String(item.changeType || '').includes('改签')

    const matchType =
      !queryForm.changeType ||
      item.changeType === queryForm.changeType

    const matchStatus =
      !queryForm.status ||
      item.status === queryForm.status

    return belongsToCurrentTab && matchType && matchStatus
  })
})

const pagedRules = computed(() => {
  const start = (pagination.currentPage - 1) * pagination.pageSize
  return filteredRules.value.slice(start, start + pagination.pageSize)
})

const loadRules = async () => {
  loading.value = true

  try {
    const response = await getChangeRules(
      getAirlineScopeParams(selectedAirlineId.value)
    )
    ruleList.value = response.data.data || []
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '退改签规则加载失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

const handleAirlineChange = () => {
  pagination.currentPage = 1
  loadRules()
}

const handleTabChange = () => {
  handleReset()
}

const handleSearch = () => {
  pagination.currentPage = 1
}

const handleReset = () => {
  queryForm.changeType = ''
  queryForm.status = ''
  pagination.currentPage = 1
}

const resetForm = () => {
  ruleForm.changeType = activeRuleTab.value === 'refund'
    ? '乘客主动退票'
    : '乘客主动改签'
  ruleForm.minHours = 0
  ruleForm.maxHours = 24
  ruleForm.noUpperLimit = false
  ruleForm.feeRatePercent = 0
  ruleForm.chargePositiveDifference = activeRuleTab.value !== 'refund'
  ruleForm.refundNegativeDifference = activeRuleTab.value === 'refund'
  ruleForm.status = '启用'
  ruleForm.validRange = []
  editingRuleId.value = null
  formRef.value?.clearValidate()
}

const handleAdd = () => {
  isEdit.value = false
  resetForm()
  dialogVisible.value = true
}

const handleEdit = (row) => {
  isEdit.value = true
  editingRuleId.value = row.ruleId
  ruleForm.changeType = row.changeType
  ruleForm.minHours = row.minHoursBeforeDeparture
  ruleForm.noUpperLimit = row.maxHoursBeforeDeparture === null
  ruleForm.maxHours = row.maxHoursBeforeDeparture ?? row.minHoursBeforeDeparture + 24
  ruleForm.feeRatePercent = Number(row.feeRate) * 100
  ruleForm.chargePositiveDifference = row.chargePositiveDifference
  ruleForm.refundNegativeDifference = row.refundNegativeDifference
  ruleForm.status = row.status
  ruleForm.validRange = [row.validFrom, row.validTo].filter(Boolean)
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!canEditRules.value || !formRef.value) return

  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  if (
    !ruleForm.noUpperLimit &&
    ruleForm.maxHours <= ruleForm.minHours
  ) {
    ElMessage.warning('时间上限必须大于时间下限')
    return
  }

  const payload = {
    ...getAirlineScopeParams(selectedAirlineId.value),
    change_type: ruleForm.changeType,
    min_hours_before_departure: ruleForm.minHours,
    max_hours_before_departure: ruleForm.noUpperLimit
      ? null
      : ruleForm.maxHours,
    fee_rate: Number((ruleForm.feeRatePercent / 100).toFixed(4)),
    charge_positive_difference: activeRuleTab.value === 'refund'
      ? false
      : ruleForm.chargePositiveDifference,
    refund_negative_difference: activeRuleTab.value === 'refund'
      ? true
      : ruleForm.refundNegativeDifference,
    status: ruleForm.status
  }

  if (!isEdit.value) {
    payload.valid_from = ruleForm.validRange[0]
    payload.valid_to = ruleForm.validRange[1]
  }

  submitting.value = true

  try {
    if (isEdit.value) {
      await updateChangeRule(editingRuleId.value, payload)
      ElMessage.success(activeRuleTab.value === 'refund' ? '退票规则已修改' : '改签规则已修改')
    } else {
      await createChangeRule(payload)
      ElMessage.success(activeRuleTab.value === 'refund' ? '退票规则已新增' : '改签规则已新增')
    }

    dialogVisible.value = false
    await loadRules()
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '退改签规则保存失败')
    console.error(error)
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

const formatPercent = (value) => {
  return `${(Number(value || 0) * 100).toFixed(2)}%`
}

onMounted(() => {
  loadRules()
})
</script>

<style scoped>
.filter-card {
  margin-bottom: 18px;
  padding: 18px 18px 0;
  border-radius: 16px;
  background: linear-gradient(135deg, #f8fafc 0%, #ffffff 100%);
  border: 1px solid #e2e8f0;
}

.scope-card {
  margin-bottom: 18px;
  padding: 18px 18px 0;
  border-radius: 16px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
}

.rule-tabs {
  margin-bottom: 12px;
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

.permission-alert {
  margin-bottom: 18px;
}

.dialog-alert {
  margin-bottom: 18px;
}

.form-help {
  margin-left: 10px;
  color: #64748b;
  font-size: 12px;
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

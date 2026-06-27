<template>
  <div class="passenger-page">
    <section class="page-panel">
      <div class="panel-header">
        <div class="section-title">
          <span class="blue-line"></span>
          <span>常用乘机人</span>
        </div>
        <el-button type="primary" size="large" @click="openAddDialog">
          <el-icon><Plus /></el-icon>
          新增乘机人
        </el-button>
      </div>

      <el-alert
        class="notice-alert"
        type="primary"
        show-icon
        :closable="false"
        title="温馨提示：乘机人信息将用于机票预订，请确保信息准确无误，并与身份证件一致。"
      />

      <div v-loading="loading" class="passenger-list">
        <el-empty v-if="passengerList.length === 0" description="暂无常用乘机人" />

        <article
          v-for="passenger in passengerList"
          :key="passenger.passengerId"
          class="passenger-card"
        >
          <div class="avatar-block">
            <el-avatar :size="58" class="passenger-avatar">
              <el-icon><UserFilled /></el-icon>
            </el-avatar>
          </div>

          <div class="basic-block">
            <div class="name-line">
              <strong>{{ passenger.realName }}</strong>
              <el-tag v-if="passenger.isDefault" type="primary" size="small">默认</el-tag>
            </div>
            <div class="passenger-type">{{ passenger.type }}</div>
            <div class="muted">证件号：{{ maskIdCard(passenger.idCard) }}</div>
            <div class="muted">手机：{{ maskPhone(passenger.phone) }}</div>
          </div>

          <div class="detail-grid">
            <div>
              <span>证件类型</span>
              <strong>身份证</strong>
            </div>
            <div>
              <span>性别</span>
              <strong>{{ passenger.gender }}</strong>
            </div>
            <div>
              <span>出生日期</span>
              <strong>{{ passenger.birthday }}</strong>
            </div>
            <div>
              <span>国家/地区</span>
              <strong>中国</strong>
            </div>
          </div>

          <div class="action-stack">
            <el-button plain :disabled="passenger.isDefault" @click="setDefault(passenger)">
              设为默认
            </el-button>
            <el-button plain type="primary" @click="openEditDialog(passenger)">
              <el-icon><Edit /></el-icon>
              编辑
            </el-button>
            <el-button plain type="danger" @click="handleDelete(passenger)">
              <el-icon><Delete /></el-icon>
              删除
            </el-button>
          </div>
        </article>
      </div>
    </section>

    <section class="usage-panel">
      <h3>使用说明</h3>
      <p>最多可添加 10 位常用乘机人。</p>
      <p>预订机票时可快速选择，无需重复填写身份信息。</p>
      <p>如果乘机人信息有误，请及时修改以免影响出行。</p>
    </section>

    <el-dialog
      v-model="dialogVisible"
      :title="editingPassenger ? '编辑乘机人' : '新增乘机人'"
      width="520px"
      @closed="resetForm"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="96px">
        <el-form-item label="姓名" prop="realName">
          <el-input v-model="form.realName" placeholder="请输入真实姓名" />
        </el-form-item>
        <el-form-item label="关系备注" prop="relationNote">
          <el-select v-model="form.relationNote" placeholder="请选择关系备注" style="width: 100%">
            <el-option label="本人" value="本人" />
            <el-option label="家属" value="家属" />
            <el-option label="朋友" value="朋友" />
            <el-option label="同事" value="同事" />
          </el-select>
        </el-form-item>
        <el-form-item label="身份证号" prop="idCard">
          <el-input v-model="form.idCard" placeholder="请输入 18 位身份证号码" maxlength="18" />
        </el-form-item>
        <el-form-item label="手机号码" prop="phone">
          <el-input v-model="form.phone" placeholder="请输入 11 位手机号码" maxlength="11" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitForm">
          保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete, Edit, Plus, UserFilled } from '@element-plus/icons-vue'
import {
  addPassenger,
  deletePassenger,
  getPassengers,
  updatePassenger
} from '../../api/client/passenger'

const loading = ref(false)
const saving = ref(false)
const dialogVisible = ref(false)
const formRef = ref()
const editingPassenger = ref(null)
const defaultPassengerId = ref(null)

const rawPassengerList = ref([])

const form = reactive({
  realName: '',
  relationNote: '',
  idCard: '',
  phone: ''
})

const rules = {
  realName: [{ required: true, message: '请输入真实姓名', trigger: 'blur' }],
  relationNote: [{ required: true, message: '请选择关系备注', trigger: 'change' }],
  idCard: [
    { required: true, message: '请输入身份证号码', trigger: 'blur' },
    { min: 18, max: 18, message: '身份证号码应为 18 位', trigger: 'blur' }
  ],
  phone: [
    { required: true, message: '请输入手机号码', trigger: 'blur' },
    { pattern: /^1\d{10}$/, message: '请输入 11 位手机号码', trigger: 'blur' }
  ]
}

const passengerList = computed(() => {
  return rawPassengerList.value.map(item => {
    const birthday = getBirthdayFromIdCard(item.idCard)
    const age = getAge(birthday)

    return {
      ...item,
      relationNote: item.relationNote || '本人',
      birthday,
      gender: getGenderFromIdCard(item.idCard),
      type: age < 12 ? '儿童' : '成人',
      isDefault: item.passengerId === defaultPassengerId.value
    }
  })
})

const loadPassengers = async () => {
  loading.value = true

  try {
    const response = await getPassengers()
    rawPassengerList.value = response.data.data || []

    if (rawPassengerList.value.length > 0) {
      defaultPassengerId.value = rawPassengerList.value[0].passengerId
    }
  } catch (error) {
    rawPassengerList.value = []
    defaultPassengerId.value = null
    ElMessage.error(error.response?.data?.message || '乘机人查询失败，请稍后重试')
    console.error(error)
  } finally {
    loading.value = false
  }
}

const openAddDialog = () => {
  editingPassenger.value = null
  dialogVisible.value = true
}

const openEditDialog = (passenger) => {
  editingPassenger.value = passenger
  form.realName = passenger.realName
  form.relationNote = passenger.relationNote
  form.idCard = passenger.idCard
  form.phone = passenger.phone
  dialogVisible.value = true
}

const resetForm = () => {
  form.realName = ''
  form.relationNote = ''
  form.idCard = ''
  form.phone = ''
  editingPassenger.value = null
  formRef.value?.clearValidate()
}

const submitForm = async () => {
  if (!formRef.value) return

  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  saving.value = true

  try {
    if (editingPassenger.value) {
      await updatePassenger(editingPassenger.value.passengerId, form)
      ElMessage.success('乘机人修改成功')
    } else {
      await addPassenger(form)
      ElMessage.success('乘机人添加成功')
    }

    dialogVisible.value = false
    await loadPassengers()
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '保存乘机人失败')
  } finally {
    saving.value = false
  }
}

const handleDelete = async (passenger) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除乘机人 ${passenger.realName} 吗？`,
      '删除确认',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
  } catch {
    return
  }

  try {
    await deletePassenger(passenger.passengerId)
    ElMessage.success('乘机人删除成功')
    await loadPassengers()
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '删除乘机人失败')
  }
}

const setDefault = (passenger) => {
  ElMessage.info(`后端暂未提供默认乘机人接口，无法设置 ${passenger.realName} 为默认`)
}

const getBirthdayFromIdCard = (idCard = '') => {
  if (idCard.length < 14) return '-'

  const value = idCard.slice(6, 14)
  return `${value.slice(0, 4)}-${value.slice(4, 6)}-${value.slice(6, 8)}`
}

const getGenderFromIdCard = (idCard = '') => {
  if (idCard.length < 17) return '-'
  return Number(idCard[16]) % 2 === 0 ? '女' : '男'
}

const getAge = (birthday) => {
  if (!birthday || birthday === '-') return 18
  const birthYear = Number(birthday.slice(0, 4))
  return new Date().getFullYear() - birthYear
}

const maskPhone = (phone = '') => {
  if (phone.length !== 11) return phone || '-'
  return `${phone.slice(0, 3)}****${phone.slice(-4)}`
}

const maskIdCard = (idCard = '') => {
  if (!idCard) return '-'
  if (idCard.length < 10) return idCard
  return `${idCard.slice(0, 6)}********${idCard.slice(-4)}`
}

onMounted(() => {
  loadPassengers()
})
</script>

<style scoped>
.passenger-page {
  max-width: 1180px;
  margin: 0 auto;
}

.page-panel,
.usage-panel {
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.84);
  box-shadow: 0 10px 30px rgba(30, 93, 140, 0.08);
  backdrop-filter: blur(10px);
}

.page-panel {
  padding: 24px 28px 12px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 20px;
  font-weight: 800;
  color: #0f172a;
}

.blue-line {
  width: 4px;
  height: 22px;
  border-radius: 2px;
  background: #0b7cff;
}

.notice-alert {
  margin-top: 28px;
  border: 1px solid #bfdbfe;
  background: rgba(239, 246, 255, 0.85);
}

.passenger-list {
  min-height: 260px;
  margin-top: 18px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.passenger-card {
  display: grid;
  grid-template-columns: 72px 260px 1fr 150px;
  gap: 22px;
  align-items: center;
  min-height: 150px;
  padding: 22px 24px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 6px 20px rgba(30, 93, 140, 0.06);
}

.avatar-block {
  display: flex;
  justify-content: center;
}

.passenger-avatar {
  color: #0b7cff;
  background: #e0f2fe;
}

.basic-block {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.name-line {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #0f172a;
  font-size: 20px;
}

.passenger-type {
  color: #334155;
  font-weight: 700;
}

.muted {
  color: #475569;
  font-size: 14px;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(150px, 1fr));
  gap: 16px 34px;
}

.detail-grid div {
  display: grid;
  grid-template-columns: 90px 1fr;
  align-items: center;
}

.detail-grid span {
  color: #64748b;
  font-size: 14px;
}

.detail-grid strong {
  color: #0f172a;
}

.action-stack {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.usage-panel {
  margin-top: 24px;
  padding: 20px 28px;
  border: 1px solid rgba(147, 197, 253, 0.6);
}

.usage-panel h3 {
  margin: 0 0 12px;
  color: #0b7cff;
}

.usage-panel p {
  margin: 8px 0;
  color: #475569;
}

@media (max-width: 1100px) {
  .passenger-card {
    grid-template-columns: 72px 1fr;
  }

  .detail-grid,
  .action-stack {
    grid-column: 2;
  }

  .action-stack {
    flex-direction: row;
    flex-wrap: wrap;
  }
}

@media (max-width: 720px) {
  .panel-header,
  .passenger-card,
  .detail-grid div {
    grid-template-columns: 1fr;
  }

  .passenger-card {
    display: flex;
    flex-direction: column;
    align-items: stretch;
  }

  .detail-grid {
    grid-template-columns: 1fr;
  }
}

/* ===== 常用乘机人卡片边界与隐私展示优化 ===== */

.passenger-list {
  border-radius: 8px;
}

.passenger-card {
  border: 1px solid rgba(203, 213, 225, 0.95);
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 8px 24px rgba(30, 93, 140, 0.08);
}

.detail-grid {
  padding: 18px 22px;
  border: 1px solid rgba(226, 232, 240, 0.95);
  border-radius: 8px;
  background: rgba(248, 250, 252, 0.86);
}


/* ===== 常用乘机人卡片最终排版修正 ===== */

.passenger-card {
  width: 100%;
  box-sizing: border-box;
  display: grid;
  grid-template-columns: 72px minmax(220px, 1fr) minmax(360px, 1.25fr) 140px;
  gap: 18px;
  align-items: center;
  padding: 24px 28px;
  overflow: hidden;
}

.passenger-card > * {
  min-width: 0;
}

.avatar-block {
  width: 72px;
  display: flex;
  justify-content: center;
}

.info-block {
  min-width: 0;
}

.info-block .muted {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.detail-grid {
  width: 100%;
  min-width: 0;
  box-sizing: border-box;
  display: grid;
  grid-template-columns: repeat(2, minmax(130px, 1fr));
  gap: 16px 28px;
  padding: 18px 20px;
  border: 1px solid rgba(226, 232, 240, 0.95);
  border-radius: 8px;
  background: rgba(248, 250, 252, 0.86);
}

.detail-grid div {
  min-width: 0;
}

.detail-grid span,
.detail-grid strong {
  display: block;
  white-space: nowrap;
}

.detail-grid strong {
  margin-top: 6px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.action-buttons,
.action-block,
.passenger-actions,
.passenger-card > div:last-child {
  width: 140px;
  min-width: 140px;
  justify-self: end;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.action-buttons .el-button,
.action-block .el-button,
.passenger-actions .el-button,
.passenger-card > div:last-child .el-button {
  width: 100%;
  margin-left: 0;
}

@media (max-width: 1100px) {
  .passenger-card {
    grid-template-columns: 72px 1fr;
  }

  .detail-grid,
  .action-buttons,
  .action-block,
  .passenger-actions,
  .passenger-card > div:last-child {
    grid-column: 1 / -1;
    width: 100%;
    min-width: 0;
  }
}


/* ===== 常用乘机人出生年月完整展示 ===== */

.passenger-card {
  grid-template-columns: 72px 260px minmax(520px, 1fr) 150px;
  gap: 18px;
}

.info-block {
  padding-left: 0;
}

.detail-grid {
  min-width: 520px;
  grid-template-columns: repeat(2, minmax(220px, 1fr));
  gap: 18px 36px;
}

.detail-grid strong {
  overflow: visible;
  text-overflow: clip;
  white-space: nowrap;
}

@media (max-width: 1100px) {
  .detail-grid {
    min-width: 0;
    grid-template-columns: repeat(2, minmax(180px, 1fr));
  }
}


/* ===== 常用乘机人卡片布局最终恢复：按钮回卡片内 + 出生日期完整显示 ===== */

.passenger-card {
  width: 100%;
  box-sizing: border-box;
  display: grid !important;
  grid-template-columns: 72px minmax(240px, 0.9fr) minmax(430px, 1.35fr) 150px !important;
  gap: 18px !important;
  align-items: center !important;
  padding: 24px 28px !important;
  overflow: visible !important;
}

.passenger-card > * {
  min-width: 0;
}

.avatar-block {
  width: 72px;
  display: flex;
  justify-content: center;
}

.info-block {
  min-width: 0;
  padding-left: 0 !important;
}

.info-block .muted {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.detail-grid {
  width: 100% !important;
  min-width: 0 !important;
  box-sizing: border-box;
  display: grid !important;
  grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
  gap: 18px 34px !important;
  padding: 18px 20px !important;
  border: 1px solid rgba(226, 232, 240, 0.95);
  border-radius: 8px;
  background: rgba(248, 250, 252, 0.86);
}

.detail-grid div {
  min-width: 0;
}

.detail-grid span,
.detail-grid strong {
  display: block;
  white-space: nowrap !important;
  overflow: visible !important;
  text-overflow: clip !important;
}

.detail-grid strong {
  margin-top: 6px;
}

/* 第四列就是右侧按钮区，不依赖原来的类名 */
.passenger-card > :nth-child(4) {
  width: 150px !important;
  min-width: 150px !important;
  justify-self: end !important;
  display: flex !important;
  flex-direction: column !important;
  gap: 12px !important;
}

.passenger-card > :nth-child(4) .el-button {
  width: 100% !important;
  margin-left: 0 !important;
}

@media (max-width: 1100px) {
  .passenger-card {
    grid-template-columns: 72px 1fr !important;
  }

  .detail-grid,
  .passenger-card > :nth-child(4) {
    grid-column: 1 / -1;
    width: 100% !important;
    min-width: 0 !important;
  }
}


/* ===== 常用乘机人卡片强制最终布局：彻底覆盖旧样式 ===== */

.passenger-list {
  width: 100%;
  box-sizing: border-box;
  overflow-x: hidden !important;
}

.passenger-card {
  width: 100% !important;
  max-width: 100% !important;
  box-sizing: border-box !important;
  display: grid !important;
  grid-template-columns: 56px 220px 1fr 116px !important;
  gap: 14px !important;
  align-items: center !important;
  padding: 22px 20px !important;
  overflow: hidden !important;
}

.passenger-card > * {
  min-width: 0 !important;
  box-sizing: border-box !important;
}

.avatar-block {
  width: 56px !important;
  min-width: 56px !important;
  display: flex !important;
  justify-content: center !important;
}

.passenger-avatar {
  width: 50px !important;
  height: 50px !important;
}

.info-block {
  width: 220px !important;
  min-width: 0 !important;
  padding-left: 0 !important;
}

.info-block .name-line {
  display: flex !important;
  align-items: center !important;
  gap: 8px !important;
  flex-wrap: nowrap !important;
}

.info-block .name-line h3,
.info-block strong {
  white-space: nowrap !important;
}

.info-block .muted {
  max-width: 210px !important;
  white-space: nowrap !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
}

.detail-grid {
  width: 100% !important;
  min-width: 0 !important;
  max-width: 100% !important;
  box-sizing: border-box !important;
  display: grid !important;
  grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
  gap: 16px 24px !important;
  padding: 16px 18px !important;
  border: 1px solid rgba(226, 232, 240, 0.95) !important;
  border-radius: 8px !important;
  background: rgba(248, 250, 252, 0.9) !important;
}

.detail-grid div {
  min-width: 0 !important;
}

.detail-grid span {
  display: block !important;
  color: #64748b !important;
  white-space: nowrap !important;
}

.detail-grid strong {
  display: block !important;
  margin-top: 6px !important;
  color: #0f172a !important;
  white-space: nowrap !important;
  overflow: visible !important;
  text-overflow: clip !important;
}

/* 第四个子元素就是右侧操作按钮区 */
.passenger-card > :nth-child(4) {
  width: 116px !important;
  min-width: 116px !important;
  max-width: 116px !important;
  justify-self: end !important;
  display: flex !important;
  flex-direction: column !important;
  gap: 10px !important;
}

.passenger-card > :nth-child(4) .el-button {
  width: 116px !important;
  min-width: 116px !important;
  margin-left: 0 !important;
  padding-left: 0 !important;
  padding-right: 0 !important;
}

@media (max-width: 1100px) {
  .passenger-card {
    grid-template-columns: 56px 1fr !important;
  }

  .detail-grid,
  .passenger-card > :nth-child(4) {
    grid-column: 1 / -1 !important;
    width: 100% !important;
    max-width: 100% !important;
  }

  .passenger-card > :nth-child(4) .el-button {
    width: 100% !important;
  }
}

</style>

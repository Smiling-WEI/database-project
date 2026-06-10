<template>
  <PageContainer
    title="管理员管理"
    description="维护后台管理员账号、角色权限与账号状态"
  >
    <template #extra>
      <el-button type="primary" @click="handleAdd">
        <el-icon><Plus /></el-icon>
        新增管理员
      </el-button>
    </template>

    <!-- 筛选区域 -->
    <div class="filter-card">
      <el-form
        :model="queryForm"
        inline
        label-width="80px"
      >
        <el-form-item label="管理员名">
          <el-input
            v-model="queryForm.name"
            placeholder="请输入管理员名"
            clearable
          />
        </el-form-item>

        <el-form-item label="角色">
          <el-select
            v-model="queryForm.role"
            placeholder="请选择角色"
            clearable
            style="width: 150px"
          >
            <el-option label="超级管理员" value="超级管理员" />
            <el-option label="航班管理员" value="航班管理员" />
            <el-option label="订单管理员" value="订单管理员" />
            <el-option label="客服管理员" value="客服管理员" />
          </el-select>
        </el-form-item>

        <el-form-item label="账号状态">
          <el-select
            v-model="queryForm.status"
            placeholder="请选择状态"
            clearable
            style="width: 150px"
          >
            <el-option label="正常" value="正常" />
            <el-option label="禁用" value="禁用" />
          </el-select>
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
        :data="filteredAdmins"
        stripe
        border
        table-layout="fixed"
        style="width: 100%"
        empty-text="暂无管理员数据，待后端接口接入"
      >
        <el-table-column prop="adminId" label="账号ID" width="90" />
        <el-table-column prop="name" label="管理员名" width="130" show-overflow-tooltip />
        <el-table-column prop="account" label="登录账号" width="150" show-overflow-tooltip />
        <el-table-column prop="phone" label="手机号" width="140" />
        <el-table-column prop="email" label="邮箱" min-width="200" show-overflow-tooltip />

        <el-table-column label="角色" width="130">
          <template #default="{ row }">
            <el-tag :type="getRoleType(row.role)">
              {{ row.role }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="lastLoginTime" label="最近登录" width="170" show-overflow-tooltip />

        <el-table-column label="账号状态" width="110">
          <template #default="{ row }">
            <el-tag :type="row.status === '正常' ? 'success' : 'danger'">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="操作" fixed="right" width="240">
          <template #default="{ row }">
            <el-button
              type="primary"
              link
              @click="handleEdit(row)"
            >
              编辑
            </el-button>

            <el-button
              v-if="row.status === '正常'"
              type="danger"
              link
              @click="handleDisable(row)"
            >
              禁用
            </el-button>

            <el-button
              v-else
              type="success"
              link
              @click="handleEnable(row)"
            >
              启用
            </el-button>

            <el-button
              type="info"
              link
              @click="handleResetPassword(row)"
            >
              重置密码
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrap">
        <el-pagination
          background
          layout="total, prev, pager, next"
          :total="filteredAdmins.length"
          :page-size="10"
        />
      </div>
    </div>

    <!-- 新增 / 编辑弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑管理员' : '新增管理员'"
      width="560px"
    >
      <el-alert
        class="dialog-alert"
        title="当前表单仅保留前端结构，后续由后端接口完成管理员新增、编辑与权限保存。"
        type="info"
        show-icon
        :closable="false"
      />

      <el-form
        ref="formRef"
        :model="adminForm"
        :rules="rules"
        label-width="90px"
      >
        <el-form-item label="管理员名" prop="name">
          <el-input
            v-model="adminForm.name"
            placeholder="请输入管理员姓名"
          />
        </el-form-item>

        <el-form-item label="登录账号" prop="account">
          <el-input
            v-model="adminForm.account"
            placeholder="请输入登录账号"
            :disabled="isEdit"
          />
        </el-form-item>

        <el-form-item label="手机号" prop="phone">
          <el-input
            v-model="adminForm.phone"
            placeholder="请输入手机号"
          />
        </el-form-item>

        <el-form-item label="邮箱" prop="email">
          <el-input
            v-model="adminForm.email"
            placeholder="请输入邮箱"
          />
        </el-form-item>

        <el-form-item label="角色" prop="role">
          <el-select
            v-model="adminForm.role"
            placeholder="请选择角色"
            style="width: 100%"
          >
            <el-option label="超级管理员" value="超级管理员" />
            <el-option label="航班管理员" value="航班管理员" />
            <el-option label="订单管理员" value="订单管理员" />
            <el-option label="客服管理员" value="客服管理员" />
          </el-select>
        </el-form-item>

        <el-form-item label="账号状态" prop="status">
          <el-radio-group v-model="adminForm.status">
            <el-radio label="正常" />
            <el-radio label="禁用" />
          </el-radio-group>
        </el-form-item>

        <el-form-item v-if="!isEdit" label="初始密码" prop="password">
          <el-input
            v-model="adminForm.password"
            type="password"
            placeholder="请输入初始密码"
            show-password
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">
          取消
        </el-button>
        <el-button type="primary" @click="handleSubmit">
          保存
        </el-button>
      </template>
    </el-dialog>
  </PageContainer>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import PageContainer from '../../../components/admin/PageContainer.vue'

const queryForm = reactive({
  name: '',
  role: '',
  status: ''
})

const dialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref()

const adminForm = reactive({
  name: '',
  account: '',
  phone: '',
  email: '',
  role: '',
  status: '正常',
  password: ''
})

// 后续由后端接口赋值，例如：adminList.value = 接口返回的管理员数组
const adminList = ref([])

const rules = {
  name: [
    { required: true, message: '请输入管理员名', trigger: 'blur' }
  ],
  account: [
    { required: true, message: '请输入登录账号', trigger: 'blur' }
  ],
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' }
  ],
  role: [
    { required: true, message: '请选择角色', trigger: 'change' }
  ],
  status: [
    { required: true, message: '请选择账号状态', trigger: 'change' }
  ],
  password: [
    { required: true, message: '请输入初始密码', trigger: 'blur' }
  ]
}

const filteredAdmins = computed(() => {
  return adminList.value.filter((item) => {
    const matchName =
      !queryForm.name ||
      item.name?.includes(queryForm.name) ||
      item.account?.includes(queryForm.name)

    const matchRole = !queryForm.role || item.role === queryForm.role
    const matchStatus = !queryForm.status || item.status === queryForm.status

    return matchName && matchRole && matchStatus
  })
})

const resetForm = () => {
  adminForm.name = ''
  adminForm.account = ''
  adminForm.phone = ''
  adminForm.email = ''
  adminForm.role = ''
  adminForm.status = '正常'
  adminForm.password = ''
}

const handleSearch = () => {
  ElMessage.info('查询条件已更新，待后端接口接入后获取真实数据')
}

const handleReset = () => {
  queryForm.name = ''
  queryForm.role = ''
  queryForm.status = ''
}

const handleAdd = () => {
  isEdit.value = false
  resetForm()
  dialogVisible.value = true
}

const handleEdit = (row) => {
  isEdit.value = true
  adminForm.name = row.name || ''
  adminForm.account = row.account || ''
  adminForm.phone = row.phone || ''
  adminForm.email = row.email || ''
  adminForm.role = row.role || ''
  adminForm.status = row.status || '正常'
  adminForm.password = ''
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate((valid) => {
    if (!valid) return

    const payload = {
      name: adminForm.name,
      account: adminForm.account,
      phone: adminForm.phone,
      email: adminForm.email,
      role: adminForm.role,
      status: adminForm.status,
      password: adminForm.password
    }

    console.log('待提交给后端的管理员数据：', payload)

    if (isEdit.value) {
      ElMessage.info('表单校验通过，管理员编辑接口待后端接入')
    } else {
      ElMessage.info('表单校验通过，管理员新增接口待后端接入')
    }
  })
}

const handleDisable = () => {
  ElMessage.info('禁用管理员功能待后端接口接入')
}

const handleEnable = () => {
  ElMessage.info('启用管理员功能待后端接口接入')
}

const handleResetPassword = () => {
  ElMessage.info('重置密码功能待后端接口接入')
}

const getRoleType = (role) => {
  if (role === '超级管理员') return 'danger'
  if (role === '航班管理员') return 'primary'
  if (role === '订单管理员') return 'success'
  if (role === '客服管理员') return 'warning'
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

.dialog-alert {
  margin-bottom: 18px;
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
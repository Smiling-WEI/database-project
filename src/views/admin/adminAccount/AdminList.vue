<template>
  <PageContainer
    title="管理员管理"
    description="维护本航空公司内部管理员账号、岗位权限与账号状态"
  >
    <template #extra>
      <el-button
  type="primary"
  :disabled="!canManageAdmins"
  @click="handleAdd"
>
        <el-icon><Plus /></el-icon>
        新增管理员
      </el-button>
    </template>

    <div class="filter-card">
      <el-form :model="queryForm" inline label-width="80px">
        <el-form-item label="管理员名">
          <el-input
            v-model="queryForm.name"
            placeholder="请输入姓名或登录账号"
            clearable
          />
        </el-form-item>

        <el-form-item label="内部角色">
          <el-select
            v-model="queryForm.role"
            placeholder="请选择角色"
            clearable
            style="width: 160px"
          >
            <el-option label="航司主管理员" value="航司主管理员" />
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

<el-alert
  v-if="!canManageAdmins"
  title="当前岗位仅可查看管理员信息，无权新增、编辑、启用、禁用或重置管理员密码"
  type="info"
  :closable="false"
  show-icon
  class="permission-alert"
/>
    <div class="table-card">
      <el-table
        :data="pagedAdmins"
        stripe
        border
        table-layout="fixed"
        style="width: 100%"
        empty-text="暂无管理员数据"
      >
        <el-table-column prop="adminId" label="账号ID" width="90" />
        <el-table-column prop="name" label="管理员名" width="150" show-overflow-tooltip />
        <el-table-column prop="account" label="登录账号" width="170" show-overflow-tooltip />
        <el-table-column prop="phone" label="手机号" width="135" />

        <el-table-column label="邮箱" min-width="210" show-overflow-tooltip>
          <template #default="{ row }">
            {{ formatValue(row.email) }}
          </template>
        </el-table-column>

        <el-table-column label="内部角色" width="140">
          <template #default="{ row }">
            <el-tag :type="getRoleType(row.role)">
              {{ row.role || '未知' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="最近登录" width="175" show-overflow-tooltip>
          <template #default="{ row }">
            {{ formatValue(row.lastLoginTime) }}
          </template>
        </el-table-column>

        <el-table-column label="账号状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ row.status || '未知' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="操作" fixed="right" width="245">
  <template #default="{ row }">
    <el-button
      type="primary"
      link
      :disabled="!canManageAdmins"
      @click="handleEdit(row)"
    >
      编辑
    </el-button>

    <el-button
      v-if="row.status === '正常'"
      type="danger"
      link
      :disabled="!canManageAdmins"
      @click="handleDisable(row)"
    >
      禁用
    </el-button>

    <el-button
      v-else
      type="success"
      link
      :disabled="!canManageAdmins"
      @click="handleEnable(row)"
    >
      启用
    </el-button>

    <el-button
      type="info"
      link
      :disabled="!canManageAdmins"
      @click="handleResetPassword(row)"
    >
      重置密码
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
          :total="filteredAdmins.length"
        />
      </div>
    </div>

    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑管理员' : '新增管理员'"
      width="580px"
    >
      <el-form
        ref="formRef"
        :model="adminForm"
        :rules="rules"
        label-width="100px"
      >
        <el-form-item label="管理员姓名" prop="name">
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

        <el-form-item label="身份证号" prop="idCard">
          <el-input
            v-model="adminForm.idCard"
            placeholder="请输入 18 位身份证号"
          />
        </el-form-item>

        <el-form-item label="手机号" prop="phone">
          <el-input
            v-model="adminForm.phone"
            placeholder="请输入 11 位手机号"
          />
        </el-form-item>

        <el-form-item label="邮箱" prop="email">
          <el-input
            v-model="adminForm.email"
            placeholder="请输入邮箱，可留空"
          />
        </el-form-item>

        <el-form-item label="内部角色" prop="role">
          <el-select
            v-model="adminForm.role"
            placeholder="请选择角色"
            style="width: 100%"
          >
            <el-option label="航司主管理员" value="航司主管理员" />
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

        <el-form-item
          v-if="!isEdit"
          label="初始密码"
          prop="password"
        >
          <el-input
            v-model="adminForm.password"
            type="password"
            placeholder="请输入不少于 6 位的初始密码"
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
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import PageContainer from '../../../components/admin/PageContainer.vue'
import api from '../../../api/index'

const queryForm = reactive({
  name: '',
  role: '',
  status: ''
})

const pagination = reactive({
  currentPage: 1,
  pageSize: 10
})

const dialogVisible = ref(false)
const isEdit = ref(false)
const editingAdminId = ref(null)
const formRef = ref()
const adminList = ref([])
const currentUser = computed(() => {
  try {
    return JSON.parse(localStorage.getItem('currentUser') || '{}')
  } catch (error) {
    console.error('登录用户信息解析失败', error)
    return {}
  }
})

const canManageAdmins = computed(() => {
  return currentUser.value.admin_role === '航司主管理员'
})

const adminForm = reactive({
  name: '',
  account: '',
  idCard: '',
  phone: '',
  email: '',
  role: '',
  status: '正常',
  password: ''
})

const rules = {
  name: [
    { required: true, message: '请输入管理员姓名', trigger: 'blur' }
  ],
  account: [
    { required: true, message: '请输入登录账号', trigger: 'blur' }
  ],
  idCard: [
    { required: true, message: '请输入身份证号', trigger: 'blur' },
    { len: 18, message: '身份证号必须为 18 位', trigger: 'blur' }
  ],
  phone: [
    {
      pattern: /^\d{11}$/,
      message: '手机号必须为 11 位数字',
      trigger: 'blur'
    }
  ],
  role: [
    { required: true, message: '请选择内部角色', trigger: 'change' }
  ],
  status: [
    { required: true, message: '请选择账号状态', trigger: 'change' }
  ],
  password: [
    { required: true, message: '请输入初始密码', trigger: 'blur' },
    { min: 6, message: '初始密码不能少于 6 位', trigger: 'blur' }
  ]
}

const loadAdmins = async () => {
  try {
    const response = await api.get('/admin/admins')

    if (response.data.success) {
      adminList.value = response.data.data || []
    } else {
      ElMessage.error(response.data.message || '管理员数据加载失败')
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '管理员数据加载失败')
    console.error(error)
  }
}

const filteredAdmins = computed(() => {
  return adminList.value.filter((item) => {
    const matchName =
      !queryForm.name ||
      String(item.name || '').includes(queryForm.name) ||
      String(item.account || '').includes(queryForm.name)

    const matchRole =
      !queryForm.role ||
      item.role === queryForm.role

    const matchStatus =
      !queryForm.status ||
      item.status === queryForm.status

    return matchName && matchRole && matchStatus
  })
})

const pagedAdmins = computed(() => {
  const start = (pagination.currentPage - 1) * pagination.pageSize
  const end = start + pagination.pageSize

  return filteredAdmins.value.slice(start, end)
})

const resetForm = () => {
  adminForm.name = ''
  adminForm.account = ''
  adminForm.idCard = ''
  adminForm.phone = ''
  adminForm.email = ''
  adminForm.role = ''
  adminForm.status = '正常'
  adminForm.password = ''
  editingAdminId.value = null
}

const handleSearch = () => {
  pagination.currentPage = 1
}

const handleReset = () => {
  queryForm.name = ''
  queryForm.role = ''
  queryForm.status = ''
  pagination.currentPage = 1
}

const handleAdd = () => {
  isEdit.value = false
  resetForm()
  dialogVisible.value = true
}

const handleEdit = (row) => {
  isEdit.value = true
  editingAdminId.value = row.adminId
  adminForm.name = row.name || ''
  adminForm.account = row.account || ''
  adminForm.idCard = row.idCard || ''
  adminForm.phone = row.phone || ''
  adminForm.email = row.email || ''
  adminForm.role = row.role || ''
  adminForm.status = row.status || '正常'
  adminForm.password = ''
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()

    const payload = {
      name: adminForm.name,
      account: adminForm.account,
      id_card: adminForm.idCard,
      phone: adminForm.phone,
      email: adminForm.email,
      role: adminForm.role,
      status: adminForm.status
    }

    if (isEdit.value) {
      await api.put(`/admin/admins/${editingAdminId.value}`, payload)
      ElMessage.success('管理员信息已保存')
    } else {
      await api.post('/admin/admins', {
        ...payload,
        password: adminForm.password
      })
      ElMessage.success('管理员已新增')
    }

    dialogVisible.value = false
    await loadAdmins()
  } catch (error) {
    if (!error?.response) {
      return
    }

    ElMessage.error(error.response?.data?.message || '管理员信息保存失败')
    console.error(error)
  }
}

const updateAdminStatus = async (row, status) => {
  try {
    await ElMessageBox.confirm(
      `确认将管理员“${row.account}”设置为“${status}”吗？`,
      '账号状态确认',
      {
        confirmButtonText: '确认',
        cancelButtonText: '取消',
        type: status === '禁用' ? 'warning' : 'info'
      }
    )

    await api.put(`/admin/admins/${row.adminId}/status`, {
      status
    })

    ElMessage.success(`管理员账号已${status === '禁用' ? '禁用' : '启用'}`)
    await loadAdmins()
  } catch (error) {
    if (error === 'cancel' || error === 'close') {
      return
    }

    ElMessage.error(error.response?.data?.message || '账号状态修改失败')
    console.error(error)
  }
}

const handleDisable = (row) => {
  updateAdminStatus(row, '禁用')
}

const handleEnable = (row) => {
  updateAdminStatus(row, '正常')
}

const handleResetPassword = async (row) => {
  try {
    const { value } = await ElMessageBox.prompt(
      `请输入管理员“${row.account}”的新密码`,
      '重置密码',
      {
        confirmButtonText: '确认',
        cancelButtonText: '取消',
        inputType: 'password',
        inputPattern: /^.{6,}$/,
        inputErrorMessage: '新密码不能少于 6 位'
      }
    )

    await api.put(`/admin/admins/${row.adminId}/reset-password`, {
      new_password: value
    })

    ElMessage.success('管理员密码已重置')
  } catch (error) {
    if (error === 'cancel' || error === 'close') {
      return
    }

    ElMessage.error(error.response?.data?.message || '密码重置失败')
    console.error(error)
  }
}

const formatValue = (value) => {
  if (value === undefined || value === null || value === '') {
    return '-'
  }

  return value
}

const getRoleType = (role) => {
  if (role === '航司主管理员') return 'danger'
  if (role === '航班管理员') return 'primary'
  if (role === '订单管理员') return 'success'
  if (role === '客服管理员') return 'warning'
  return 'info'
}

const getStatusType = (status) => {
  if (status === '正常') return 'success'
  if (status === '禁用') return 'danger'
  return 'info'
}

onMounted(() => {
  loadAdmins()
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
.permission-alert {
  margin-bottom: 18px;
}
</style>
<template>
  <PageContainer
    title="用户管理"
    description="查看用户信息、账号状态与乘机人管理情况"
  >
    <!-- 筛选区域 -->
    <div class="filter-card">
      <el-form
        :model="queryForm"
        inline
        label-width="80px"
      >
        <el-form-item label="用户姓名">
          <el-input
            v-model="queryForm.name"
            placeholder="请输入用户姓名"
            clearable
          />
        </el-form-item>

        <el-form-item label="手机号">
          <el-input
            v-model="queryForm.phone"
            placeholder="请输入手机号"
            clearable
          />
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
        :data="filteredUsers"
        stripe
        border
        table-layout="fixed"
        style="width: 100%"
        empty-text="暂无用户数据，待后端接口接入"
      >
        <el-table-column prop="userId" label="用户ID" width="90" />
        <el-table-column prop="username" label="用户账号" width="120" show-overflow-tooltip />
        <el-table-column prop="realName" label="真实姓名" width="120" show-overflow-tooltip />
        <el-table-column prop="phone" label="手机号" width="140" />
        <el-table-column prop="email" label="邮箱" min-width="200" show-overflow-tooltip />
        <el-table-column prop="passengerCount" label="常用乘机人" width="120" />
        <el-table-column prop="orderCount" label="订单数" width="100" />
        <el-table-column prop="createdAt" label="注册时间" width="170" show-overflow-tooltip />

        <el-table-column label="账号状态" width="110">
          <template #default="{ row }">
            <el-tag :type="row.status === '正常' ? 'success' : 'danger'">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="操作" fixed="right" width="200">
          <template #default="{ row }">
            <el-button
              type="primary"
              link
              @click="handleView(row)"
            >
              查看
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
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrap">
        <el-pagination
          background
          layout="total, prev, pager, next"
          :total="filteredUsers.length"
          :page-size="10"
        />
      </div>
    </div>

    <!-- 用户详情弹窗 -->
    <el-dialog
      v-model="detailVisible"
      title="用户详情"
      width="560px"
    >
      <div v-if="currentUser" class="detail-box">
        <div class="detail-row">
          <span>用户ID</span>
          <strong>{{ currentUser.userId }}</strong>
        </div>
        <div class="detail-row">
          <span>用户账号</span>
          <strong>{{ currentUser.username }}</strong>
        </div>
        <div class="detail-row">
          <span>真实姓名</span>
          <strong>{{ currentUser.realName }}</strong>
        </div>
        <div class="detail-row">
          <span>手机号</span>
          <strong>{{ currentUser.phone }}</strong>
        </div>
        <div class="detail-row">
          <span>邮箱</span>
          <strong>{{ currentUser.email }}</strong>
        </div>
        <div class="detail-row">
          <span>常用乘机人</span>
          <strong>{{ currentUser.passengerCount }} 人</strong>
        </div>
        <div class="detail-row">
          <span>历史订单数</span>
          <strong>{{ currentUser.orderCount }} 单</strong>
        </div>
        <div class="detail-row">
          <span>注册时间</span>
          <strong>{{ currentUser.createdAt }}</strong>
        </div>
        <div class="detail-row">
          <span>账号状态</span>
          <el-tag :type="currentUser.status === '正常' ? 'success' : 'danger'">
            {{ currentUser.status }}
          </el-tag>
        </div>
      </div>

      <el-empty
        v-else
        description="暂无用户详情，待后端数据接入"
      />

      <template #footer>
        <el-button @click="detailVisible = false">
          关闭
        </el-button>
      </template>
    </el-dialog>
  </PageContainer>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import PageContainer from '../../../components/admin/PageContainer.vue'

const queryForm = reactive({
  name: '',
  phone: '',
  status: ''
})

const detailVisible = ref(false)
const currentUser = ref(null)

// 后续由后端接口赋值，例如：userList.value = 接口返回的用户数组
const userList = ref([])

const filteredUsers = computed(() => {
  return userList.value.filter((item) => {
    const matchName =
      !queryForm.name ||
      item.username?.includes(queryForm.name) ||
      item.realName?.includes(queryForm.name)

    const matchPhone =
      !queryForm.phone ||
      item.phone?.includes(queryForm.phone)

    const matchStatus =
      !queryForm.status ||
      item.status === queryForm.status

    return matchName && matchPhone && matchStatus
  })
})

const handleSearch = () => {
  ElMessage.info('查询条件已更新，待后端接口接入后获取真实数据')
}

const handleReset = () => {
  queryForm.name = ''
  queryForm.phone = ''
  queryForm.status = ''
}

const handleView = (row) => {
  currentUser.value = row
  detailVisible.value = true
}

const handleDisable = () => {
  ElMessage.info('禁用用户功能待后端接口接入')
}

const handleEnable = () => {
  ElMessage.info('启用用户功能待后端接口接入')
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

.detail-box {
  padding: 4px 2px;
}

.detail-row {
  min-height: 42px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  border-bottom: 1px solid #eef2f7;
  color: #64748b;
  font-size: 14px;
}

.detail-row:last-child {
  border-bottom: none;
}

.detail-row strong {
  color: #1e293b;
  font-weight: 600;
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
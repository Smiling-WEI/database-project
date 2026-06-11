<template>
  <PageContainer
    title="控制台"
    description="查看航空订票系统的核心运营数据与常用管理入口"
  >
    <!-- 统计卡片 -->
    <div class="stat-grid">
      <div
        v-for="item in statCards"
        :key="item.label"
        class="stat-card"
      >
        <div class="stat-icon">
          <el-icon>
            <component :is="item.icon" />
          </el-icon>
        </div>

        <div class="stat-info">
          <div class="stat-value">
            {{ formatStatValue(item.value) }}
          </div>
          <div class="stat-label">{{ item.label }}</div>
        </div>
      </div>
    </div>

    <!-- 中间区域：快捷入口 + 系统提醒 -->
    <div class="dashboard-row">
      <section class="panel quick-panel">
        <div class="panel-header">
          <div>
            <h3>快捷入口</h3>
            <p>常用管理操作快速跳转</p>
          </div>
        </div>

        <div class="quick-list">
          <div
            v-for="item in quickActions"
            :key="item.title"
            class="quick-item"
            @click="goTo(item.path)"
          >
            <div class="quick-icon">
              <el-icon>
                <component :is="item.icon" />
              </el-icon>
            </div>

            <div>
              <div class="quick-title">{{ item.title }}</div>
              <div class="quick-desc">{{ item.desc }}</div>
            </div>
          </div>
        </div>
      </section>

      <section class="panel notice-panel">
        <div class="panel-header">
          <div>
            <h3>系统提醒</h3>
            <p>查看当前需要关注的管理事项</p>
          </div>
        </div>

        <div v-if="notices.length" class="notice-list">
          <div
            v-for="notice in notices"
            :key="notice.text"
            class="notice-item"
          >
            <el-tag
              :type="notice.type"
              size="small"
              effect="light"
            >
              {{ notice.label }}
            </el-tag>
            <span>{{ notice.text }}</span>
          </div>
        </div>

        <el-empty
          v-else
          description="暂无系统提醒"
          :image-size="90"
        />
      </section>
    </div>

    <!-- 底部区域：今日航班 + 近期订单 -->
    <div class="dashboard-row bottom-row">
      <section class="panel">
        <div class="panel-header">
          <div>
            <h3>今日航班概览</h3>
            <p>查看今日航班的基础运行情况</p>
          </div>

          <el-button type="primary" link @click="goTo('/admin/flights')">
            查看全部
          </el-button>
        </div>

        <el-table
          :data="todayFlights"
          stripe
          table-layout="fixed"
          style="width: 100%"
          empty-text="暂无今日航班数据"
        >
          <el-table-column prop="flightNo" label="航班号" width="110" />
          <el-table-column prop="flightDate" label="航班日期" width="120" />
          <el-table-column prop="route" label="航线" show-overflow-tooltip />

          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag
                :type="getFlightStatusType(row.status)"
                size="small"
              >
                {{ row.status || '未知' }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </section>

      <section class="panel">
        <div class="panel-header">
          <div>
            <h3>近期订单</h3>
            <p>查看近期订单的处理状态</p>
          </div>

          <el-button type="primary" link @click="goTo('/admin/orders')">
            查看全部
          </el-button>
        </div>

        <el-table
          :data="recentOrders"
          stripe
          table-layout="fixed"
          style="width: 100%"
          empty-text="暂无近期订单数据"
        >
          <el-table-column prop="orderId" label="订单ID" width="110" />
          <el-table-column prop="username" label="用户" width="100" />
          <el-table-column prop="flightNo" label="航班号" width="110" />

          <el-table-column label="状态" width="120">
            <template #default="{ row }">
              <el-tag
                :type="getOrderStatusType(row.orderStatus)"
                size="small"
              >
                {{ row.orderStatus || '未知' }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </section>
    </div>
  </PageContainer>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Promotion,
  Tickets,
  User,
  Setting,
  Plus,
  List
} from '@element-plus/icons-vue'
import PageContainer from '../../components/admin/PageContainer.vue'
import api from '../../api/index'

const router = useRouter()

const statCards = ref([
  {
    label: '今日航班',
    value: null,
    icon: Promotion
  },
  {
    label: '今日订单',
    value: null,
    icon: Tickets
  },
  {
    label: '注册用户',
    value: null,
    icon: User
  },
  {
    label: '系统管理员',
    value: null,
    icon: Setting
  }
])

const quickActions = [
  {
    title: '新增航班',
    desc: '录入新的航班计划',
    path: '/admin/flights/edit',
    icon: Plus
  },
  {
    title: '航班管理',
    desc: '维护航班信息与运行状态',
    path: '/admin/flights',
    icon: Promotion
  },
  {
    title: '订单管理',
    desc: '查看订单与处理状态',
    path: '/admin/orders',
    icon: List
  },
  {
    title: '用户管理',
    desc: '查看用户账号状态',
    path: '/admin/users',
    icon: User
  }
]

const notices = ref([])
const todayFlights = ref([])
const recentOrders = ref([])

const loadDashboard = async () => {
  try {
    const response = await api.get('/admin/dashboard/summary')
    const data = response.data.data

    statCards.value[0].value = data.todayFlightCount
    statCards.value[1].value = data.todayOrderCount
    statCards.value[2].value = data.totalUserCount
    statCards.value[3].value = data.adminCount

    notices.value = data.notices || []
    todayFlights.value = data.todayFlights || []
    recentOrders.value = data.recentOrders || []
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '控制台数据加载失败')
    console.error(error)
  }
}

const formatStatValue = (value) => {
  if (value === null || value === undefined || value === '') {
    return '--'
  }

  return value
}

const goTo = (path) => {
  router.push(path)
}

const getFlightStatusType = (status) => {
  if (status === '正常') return 'success'
  if (status === '延误') return 'warning'
  if (status === '取消') return 'danger'
  if (status === '已完成') return 'info'

  return 'info'
}

const getOrderStatusType = (status) => {
  if (status === '已支付') return 'success'
  if (status === '待支付') return 'warning'
  if (status === '已退票') return 'info'
  if (status === '已改签') return 'warning'
  if (status === '已取消') return 'info'

  return 'info'
}

onMounted(() => {
  loadDashboard()
})
</script>
<style scoped>
.stat-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 18px;
  margin-bottom: 20px;
}

.stat-card {
  min-height: 118px;
  padding: 20px;
  border-radius: 18px;
  display: flex;
  align-items: center;
  gap: 16px;
  background: linear-gradient(135deg, #ffffff 0%, #f8fbff 100%);
  border: 1px solid rgba(226, 232, 240, 0.9);
  box-shadow: 0 10px 28px rgba(148, 163, 184, 0.12);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #2563eb;
  font-size: 24px;
  background: rgba(37, 99, 235, 0.1);
}

.stat-value {
  color: #1e293b;
  font-size: 26px;
  font-weight: 700;
  line-height: 1;
}

.stat-label {
  margin-top: 8px;
  color: #64748b;
  font-size: 14px;
}

.dashboard-row {
  display: grid;
  grid-template-columns: 1.2fr 0.8fr;
  gap: 20px;
  margin-bottom: 20px;
}

.bottom-row {
  grid-template-columns: 1fr 1fr;
}

.panel {
  padding: 20px;
  border-radius: 18px;
  background: #ffffff;
  border: 1px solid rgba(226, 232, 240, 0.9);
  box-shadow: 0 10px 28px rgba(148, 163, 184, 0.1);
  max-width: 100%;
  overflow-x: auto;
}

.panel-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
}

.panel-header h3 {
  margin: 0;
  color: #1e293b;
  font-size: 17px;
  font-weight: 700;
}

.panel-header p {
  margin: 6px 0 0;
  color: #94a3b8;
  font-size: 13px;
}

.quick-list {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.quick-item {
  padding: 16px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  transition: all 0.2s ease;
}

.quick-item:hover {
  transform: translateY(-2px);
  background: #eff6ff;
  border-color: rgba(37, 99, 235, 0.28);
  box-shadow: 0 10px 24px rgba(37, 99, 235, 0.12);
}

.quick-icon {
  width: 38px;
  height: 38px;
  border-radius: 13px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #2563eb;
  font-size: 20px;
  background: rgba(37, 99, 235, 0.1);
}

.quick-title {
  color: #334155;
  font-size: 14px;
  font-weight: 600;
}

.quick-desc {
  margin-top: 4px;
  color: #94a3b8;
  font-size: 12px;
}

.notice-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.notice-item {
  min-height: 42px;
  padding: 10px 12px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  gap: 10px;
  color: #475569;
  font-size: 14px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
}

:deep(.el-empty) {
  padding: 12px 0;
}

:deep(.el-empty__description p) {
  color: #94a3b8;
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

@media (max-width: 1200px) {
  .stat-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .dashboard-row,
  .bottom-row {
    grid-template-columns: 1fr;
  }
}
</style>
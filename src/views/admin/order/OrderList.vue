<template>
  <PageContainer
    title="订单管理"
    description="查询订单，并集中查看退票、改签及其处理记录"
  >
    <div v-if="systemAdmin" class="scope-card">
      <el-form inline label-width="80px">
        <AirlineScopeSelect
          v-model="selectedAirlineId"
          @change="loadOrders"
        />
      </el-form>
    </div>

    <el-tabs v-model="activeTab" class="order-tabs" @tab-change="handleTabChange">
      <el-tab-pane label="订单列表" name="orders">
        <div class="filter-card">
          <el-form :model="queryForm" inline label-width="80px">
            <el-form-item label="订单号">
              <el-input
                v-model="queryForm.orderId"
                placeholder="请输入订单号"
                clearable
              />
            </el-form-item>

            <el-form-item label="手机号">
              <el-input
                v-model="queryForm.phone"
                placeholder="完整号码或后四位"
                clearable
              />
            </el-form-item>

            <el-form-item label="航班号">
              <el-input
                v-model="queryForm.flightNo"
                placeholder="请输入航班号"
                clearable
              />
            </el-form-item>

            <el-form-item label="订单状态">
              <el-select
                v-model="queryForm.orderStatus"
                placeholder="请选择订单状态"
                clearable
                style="width: 150px"
              >
                <el-option label="已支付" value="已支付" />
                <el-option label="已退票" value="已退票" />
                <el-option label="已改签" value="已改签" />
                <el-option label="已取消" value="已取消" />
              </el-select>
            </el-form-item>

            <el-form-item label="记录类型">
              <el-select
                v-model="queryForm.recordType"
                placeholder="请选择类型"
                clearable
                style="width: 150px"
              >
                <el-option label="有效订单" value="有效订单" />
                <el-option label="历史订单" value="历史订单" />
              </el-select>
            </el-form-item>

            <el-form-item label="乘机人">
              <el-input
                v-model="queryForm.passengerName"
                placeholder="请输入乘机人"
                clearable
              />
            </el-form-item>

            <el-form-item label="购票日期">
              <el-date-picker
                v-model="queryForm.dateRange"
                type="daterange"
                range-separator="至"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                value-format="YYYY-MM-DD"
                clearable
                style="width: 250px"
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

        <el-alert
          v-if="!canAssist"
          title="当前岗位仅可查看订单和退改签记录，无权发起后台退改签"
          type="info"
          :closable="false"
          show-icon
          class="permission-alert"
        />

        <div class="table-card">
          <el-table
            v-loading="loading"
            :data="pagedOrders"
            stripe
            border
            table-layout="fixed"
            style="width: 100%"
            empty-text="暂无订单数据"
          >
            <el-table-column prop="orderId" label="订单ID" width="100" />
            <el-table-column
              v-if="systemAdmin"
              prop="airlineName"
              label="航空公司"
              width="145"
              show-overflow-tooltip
            />
            <el-table-column prop="username" label="用户账号" width="120" show-overflow-tooltip />
            <el-table-column label="手机号" width="135">
              <template #default="{ row }">
                {{ maskPhone(row.phone) }}
              </template>
            </el-table-column>
            <el-table-column prop="passengerName" label="乘机人" width="110" show-overflow-tooltip />
            <el-table-column prop="flightNo" label="航班号" width="110" />
            <el-table-column prop="flightDate" label="航班日期" width="120" />
            <el-table-column prop="cabinType" label="舱位" width="100" />
            <el-table-column prop="seatNo" label="座位号" width="100" />

            <el-table-column prop="price" label="票价" width="100">
              <template #default="{ row }">
                {{ formatPrice(row.price) }}
              </template>
            </el-table-column>

            <el-table-column prop="purchaseTime" label="购票时间" width="170" show-overflow-tooltip />

            <el-table-column label="订单状态" width="120">
              <template #default="{ row }">
                <el-tag :type="getOrderStatusType(row.orderStatus)">
                  {{ row.orderStatus || '未知' }}
                </el-tag>
              </template>
            </el-table-column>

            <el-table-column label="记录类型" width="110">
              <template #default="{ row }">
                <el-tag :type="getRecordType(row.recordType)">
                  {{ row.recordType || '未知' }}
                </el-tag>
              </template>
            </el-table-column>

            <el-table-column label="操作" fixed="right" width="210">
              <template #default="{ row }">
                <el-button type="primary" link @click="handleView(row)">
                  查看
                </el-button>
                <el-button
                  type="danger"
                  link
                  :disabled="!canAssist || !canProcess(row)"
                  @click="handleAssist(row, 'refund')"
                >
                  退票
                </el-button>
                <el-button
                  type="warning"
                  link
                  :disabled="!canAssist || !canProcess(row)"
                  @click="handleAssist(row, 'change')"
                >
                  改签
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
              :total="filteredOrders.length"
            />
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane label="退票记录" name="refund" lazy>
        <RefundRecordPanel :airline-id="selectedAirlineId" />
      </el-tab-pane>

      <el-tab-pane label="改签记录" name="change" lazy>
        <ChangeRecordPanel
          :orders="ordersWithPhone"
          :airline-id="selectedAirlineId"
        />
      </el-tab-pane>
    </el-tabs>

    <el-dialog
      v-model="detailVisible"
      title="订单详情"
      width="620px"
    >
      <div v-if="currentOrder" class="detail-box">
        <div class="detail-row">
          <span>订单ID</span>
          <strong>{{ formatValue(currentOrder.orderId) }}</strong>
        </div>
        <div class="detail-row">
          <span>用户ID</span>
          <strong>{{ formatValue(currentOrder.userId) }}</strong>
        </div>
        <div class="detail-row">
          <span>用户账号</span>
          <strong>{{ formatValue(currentOrder.username) }}</strong>
        </div>
        <div class="detail-row">
          <span>用户手机号</span>
          <strong>{{ maskPhone(currentOrder.phone) }}</strong>
        </div>
        <div class="detail-row">
          <span>乘机人</span>
          <strong>{{ formatValue(currentOrder.passengerName) }}</strong>
        </div>
        <div class="detail-row">
          <span>乘机人证件</span>
          <strong>{{ formatValue(currentOrder.passengerIdCard) }}</strong>
        </div>
        <div class="detail-row">
          <span>航班号</span>
          <strong>{{ formatValue(currentOrder.flightNo) }}</strong>
        </div>
        <div class="detail-row">
          <span>航班日期</span>
          <strong>{{ formatValue(currentOrder.flightDate) }}</strong>
        </div>
        <div class="detail-row">
          <span>舱位</span>
          <strong>{{ formatValue(currentOrder.cabinType) }}</strong>
        </div>
        <div class="detail-row">
          <span>座位号</span>
          <strong>{{ formatValue(currentOrder.seatNo) }}</strong>
        </div>
        <div class="detail-row">
          <span>票价</span>
          <strong>{{ formatPrice(currentOrder.price) }}</strong>
        </div>
        <div class="detail-row">
          <span>购票时间</span>
          <strong>{{ formatValue(currentOrder.purchaseTime) }}</strong>
        </div>
        <div class="detail-row">
          <span>订单状态</span>
          <el-tag :type="getOrderStatusType(currentOrder.orderStatus)">
            {{ currentOrder.orderStatus || '未知' }}
          </el-tag>
        </div>
        <div class="detail-row">
          <span>记录类型</span>
          <el-tag :type="getRecordType(currentOrder.recordType)">
            {{ currentOrder.recordType || '未知' }}
          </el-tag>
        </div>
      </div>

      <template #footer>
        <el-button
          v-if="currentOrder?.orderStatus === '已退票'"
          type="primary"
          plain
          @click="goRecord('refund')"
        >
          查看退票记录
        </el-button>
        <el-button
          v-if="currentOrder?.orderStatus === '已改签'"
          type="primary"
          plain
          @click="goRecord('change')"
        >
          查看改签记录
        </el-button>
        <el-button @click="detailVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="assistVisible"
      :title="assistType === 'refund' ? '后台代办退票' : '后台代办改签'"
      width="680px"
      @closed="resetAssistForm"
    >
      <el-alert
        :title="assistType === 'refund'
          ? '系统将按当前有效退票规则计算手续费与实际退款金额'
          : '系统将按当前有效改签规则计算票价差额与改签手续费'"
        type="info"
        :closable="false"
        show-icon
      />

      <div v-if="assistOrder" class="assist-summary">
        <div>
          <span>订单</span>
          <strong>{{ assistOrder.orderId }}</strong>
        </div>
        <div>
          <span>乘机人</span>
          <strong>{{ assistOrder.passengerName || '-' }}</strong>
        </div>
        <div>
          <span>航班</span>
          <strong>{{ assistOrder.flightNo }} · {{ assistOrder.flightDate }}</strong>
        </div>
        <div>
          <span>票价</span>
          <strong>{{ formatPrice(assistOrder.price) }}</strong>
        </div>
      </div>

      <el-form
        ref="assistFormRef"
        :model="assistForm"
        label-width="110px"
      >
        <el-form-item
          v-if="assistType === 'change'"
          label="目标航班"
          required
        >
          <el-select
            v-model="assistForm.targetInstanceId"
            filterable
            placeholder="请选择目标航班"
            @change="handleTargetFlightChange"
            style="width: 100%"
          >
            <el-option
              v-for="flight in availableFlights"
              :key="flight.instanceId"
              :label="`${flight.airlineName || ''} · ${flight.flightNo} · ${flight.flightDate} · ${flight.depAirport} → ${flight.arrAirport}`"
              :value="flight.instanceId"
            />
          </el-select>
        </el-form-item>

        <el-form-item
          v-if="assistType === 'change'"
          label="目标舱位"
          required
        >
          <el-select
            v-model="assistForm.targetPricingId"
            filterable
            :disabled="!assistForm.targetInstanceId"
            :loading="loadingTargetCabins"
            placeholder="请先选择目标航班，再选择目标舱位"
            style="width: 100%"
          >
            <el-option
              v-for="cabin in targetCabins"
              :key="cabin.pricingId"
              :label="`${cabin.cabinType} · ¥${cabin.salePrice} · 剩余${cabin.remainingTickets ?? cabin.availableTickets ?? '-'}张`"
              :value="cabin.pricingId"
            />
          </el-select>
        </el-form-item>

        <el-form-item
          :label="assistType === 'refund' ? '退票原因' : '改签原因'"
          required
        >
          <el-input
            v-model="assistForm.reason"
            type="textarea"
            :rows="3"
            maxlength="500"
            show-word-limit
            :placeholder="assistType === 'refund' ? '请填写客服代退票原因' : '请填写客服代改签原因'"
          />
        </el-form-item>
      </el-form>

      <div v-if="assistPreview" class="preview-card">
        <div>
          <span>适用规则</span>
          <strong>{{ assistPreview.ruleDescription || `规则 ${assistPreview.ruleId || '-'}` }}</strong>
        </div>
        <template v-if="assistType === 'refund'">
          <div>
            <span>退票手续费</span>
            <strong>{{ formatPrice(assistPreview.refundFee) }}</strong>
          </div>
          <div>
            <span>实际退款金额</span>
            <strong class="success-text">{{ formatPrice(assistPreview.refundAmount) }}</strong>
          </div>
        </template>
        <template v-else>
          <div>
            <span>票价差额</span>
            <strong>{{ formatPrice(assistPreview.fareDifference) }}</strong>
          </div>
          <div>
            <span>改签手续费</span>
            <strong>{{ formatPrice(assistPreview.changeFee) }}</strong>
          </div>
          <div>
            <span>应补金额</span>
            <strong>{{ formatPrice(assistPreview.payableAmount) }}</strong>
          </div>
          <div>
            <span>应退金额</span>
            <strong class="success-text">{{ formatPrice(assistPreview.refundableAmount) }}</strong>
          </div>
        </template>
      </div>

      <template #footer>
        <el-button @click="assistVisible = false">取消</el-button>
        <el-button
          :loading="previewing"
          @click="handlePreview"
        >
          费用预览
        </el-button>
        <el-button
          type="primary"
          :loading="submittingAssist"
          :disabled="!assistPreview"
          @click="handleAssistSubmit"
        >
          确认{{ assistType === 'refund' ? '退票' : '改签' }}
        </el-button>
      </template>
    </el-dialog>
  </PageContainer>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import api from '../../../api'
import { ElMessage } from 'element-plus'
import { useRoute, useRouter } from 'vue-router'
import PageContainer from '../../../components/admin/PageContainer.vue'
import AirlineScopeSelect from '../../../components/admin/AirlineScopeSelect.vue'
import ChangeRecordPanel from '../../../components/admin/order/ChangeRecordPanel.vue'
import RefundRecordPanel from '../../../components/admin/order/RefundRecordPanel.vue'
import {
  getAdminOrders,
  previewAdminChange,
  previewAdminRefund,
  submitAdminChange,
  submitAdminRefund
} from '../../../api/admin/order'
import { getAdminUsers } from '../../../api/admin/user'
import { getAdminFlights } from '../../../api/admin/flight'
import {
  canAssistTicketChanges,
  getAirlineScopeParams,
  getStoredUser,
  isSystemAdmin
} from '../../../utils/adminAuth'

const route = useRoute()
const router = useRouter()
const validTabs = ['orders', 'refund', 'change']
const activeTab = ref(
  validTabs.includes(route.query.tab) ? route.query.tab : 'orders'
)

const queryForm = reactive({
  orderId: '',
  phone: '',
  flightNo: '',
  orderStatus: '',
  recordType: '',
  passengerName: '',
  dateRange: []
})

const pagination = reactive({
  currentPage: 1,
  pageSize: 10
})

const detailVisible = ref(false)
const currentOrder = ref(null)
const assistVisible = ref(false)
const assistType = ref('refund')
const assistOrder = ref(null)
const assistFormRef = ref()
const assistPreview = ref(null)
const previewing = ref(false)
const submittingAssist = ref(false)
const availableFlights = ref([])
const targetCabins = ref([])
const loadingTargetCabins = ref(false)
const selectedAirlineId = ref(route.query.airlineId || '')
const loading = ref(false)
const orderList = ref([])
const phoneByUserId = ref({})

const currentUser = computed(() => getStoredUser())
const systemAdmin = computed(() => isSystemAdmin(currentUser.value))
const canAssist = computed(() => canAssistTicketChanges(currentUser.value))

const ordersWithPhone = computed(() => {
  return orderList.value.map((item) => ({
    ...item,
    phone: phoneByUserId.value[item.userId] || ''
  }))
})

const assistForm = reactive({
  targetInstanceId: null,
  targetPricingId: null,
  reason: ''
})

const filteredOrders = computed(() => {
  return ordersWithPhone.value.filter((item) => {
    const matchOrderId =
      !queryForm.orderId ||
      String(item.orderId || '').includes(queryForm.orderId.trim())

    const matchPhone =
      !queryForm.phone ||
      String(item.phone || '').includes(queryForm.phone.trim())

    const matchFlightNo =
      !queryForm.flightNo ||
      String(item.flightNo || '')
        .toLowerCase()
        .includes(queryForm.flightNo.toLowerCase())

    const matchOrderStatus =
      !queryForm.orderStatus ||
      item.orderStatus === queryForm.orderStatus

    const matchRecordType =
      !queryForm.recordType ||
      item.recordType === queryForm.recordType

    const matchPassengerName =
      !queryForm.passengerName ||
      String(item.passengerName || '')
        .toLowerCase()
        .includes(queryForm.passengerName.toLowerCase())

    const purchaseDate = String(item.purchaseTime || '').slice(0, 10)
    const matchDateRange =
      !queryForm.dateRange?.length ||
      (
        purchaseDate >= queryForm.dateRange[0] &&
        purchaseDate <= queryForm.dateRange[1]
      )

    return (
      matchOrderId &&
      matchPhone &&
      matchFlightNo &&
      matchOrderStatus &&
      matchRecordType &&
      matchPassengerName &&
      matchDateRange
    )
  })
})

const pagedOrders = computed(() => {
  const start = (pagination.currentPage - 1) * pagination.pageSize
  return filteredOrders.value.slice(start, start + pagination.pageSize)
})

const loadOrders = async () => {
  loading.value = true

  try {
    const [orderResponse, userResponse] = await Promise.all([
      getAdminOrders(getAirlineScopeParams(selectedAirlineId.value)),
      getAdminUsers(getAirlineScopeParams(selectedAirlineId.value))
    ])

    if (orderResponse.data.success) {
      orderList.value = orderResponse.data.data || []
      phoneByUserId.value = (userResponse.data.data || []).reduce(
        (result, user) => {
          result[user.userId] = user.phone || ''
          return result
        },
        {}
      )
      openRequestedAction()
    } else {
      ElMessage.error(orderResponse.data.message || '订单数据加载失败')
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '订单数据加载失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

const openRequestedAction = () => {
  const orderId = route.query.orderId
  const action = route.query.action
  if (!orderId || !['refund', 'change'].includes(action)) return

  const order = ordersWithPhone.value.find(
    (item) => String(item.orderId) === String(orderId)
  )
  if (!order) return

  queryForm.orderId = String(orderId)
  activeTab.value = 'orders'
  handleAssist(order, action)
}

const handleTabChange = (name) => {
  const query = name === 'orders' ? {} : { tab: name }
  router.replace({ path: '/admin/orders', query })
}

const handleSearch = () => {
  pagination.currentPage = 1
}

const handleReset = () => {
  queryForm.orderId = ''
  queryForm.phone = ''
  queryForm.flightNo = ''
  queryForm.orderStatus = ''
  queryForm.recordType = ''
  queryForm.passengerName = ''
  queryForm.dateRange = []
  pagination.currentPage = 1
}

const handleView = (row) => {
  currentOrder.value = row
  detailVisible.value = true
}

const canProcess = (row) => {
  const orderStatus = String(row.orderStatus || '').trim()
  const recordType = String(row.recordType || '').trim()

  const activeStatuses = [
    '已支付',
    '已出票',
    '宸叉敮浠?',
    '宸插嚭绁?'
  ]

  const activeRecordTypes = [
    '有效订单',
    '鏈夋晥璁㈠崟'
  ]

  return activeStatuses.includes(orderStatus) &&
    activeRecordTypes.includes(recordType)
}


const handleAssist = (row, type) => {
  if (!canAssist.value || !canProcess(row)) return
  resetAssistForm()
  assistOrder.value = row
  assistType.value = type
  assistVisible.value = true
  if (type === 'change') loadAvailableFlights()
}

const resetAssistForm = () => {
  assistForm.targetInstanceId = null
  assistForm.targetPricingId = null
  assistForm.reason = ''
  targetCabins.value = []
  assistPreview.value = null
}

const loadAvailableFlights = async () => {
  try {
    const response = await getAdminFlights({
      ...getAirlineScopeParams(selectedAirlineId.value),
      change_candidate_for_order_id: assistOrder.value?.orderId
    })
    availableFlights.value = (response.data.data || []).filter(
      (item) => item.instanceId !== assistOrder.value?.instanceId
    )
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '目标航班接口待后端接入')
  }
}

const handleTargetFlightChange = async () => {
  assistForm.targetPricingId = null
  assistPreview.value = null
  targetCabins.value = []

  if (!assistForm.targetInstanceId) return

  await loadTargetCabins(assistForm.targetInstanceId)
}

const normalizeCabinPricing = (item) => {
  return {
    ...item,
    pricingId:
      item.pricingId ??
      item.pricing_id ??
      item.priceId ??
      item.price_id ??
      item.cabinPricingId ??
      item.cabin_pricing_id ??
      item.id,
    cabinType:
      item.cabinType ??
      item.cabin_type ??
      item.cabin ??
      item.type,
    salePrice:
      item.salePrice ??
      item.sale_price ??
      item.price ??
      item.ticketPrice ??
      item.ticket_price,
    remainingTickets:
      item.remainingTickets ??
      item.remaining_tickets ??
      item.availableTickets ??
      item.available_tickets ??
      item.remainingSeats ??
      item.remaining_seats ??
      item.leftTickets ??
      item.left_tickets ??
      '-'
  }
}

const loadTargetCabins = async (instanceId) => {
  loadingTargetCabins.value = true

  try {
    const response = await api.get(`/admin/flights/${instanceId}/cabins`)

    const data = response.data?.data ?? []

    let raw = []

    if (Array.isArray(data)) {
      raw = data
    } else if (Array.isArray(data.records)) {
      raw = data.records
    } else if (Array.isArray(data.list)) {
      raw = data.list
    } else if (Array.isArray(data.items)) {
      raw = data.items
    } else if (Array.isArray(data.cabins)) {
      raw = data.cabins
    } else if (Array.isArray(data.prices)) {
      raw = data.prices
    } else if (Array.isArray(data.priceList)) {
      raw = data.priceList
    } else if (Array.isArray(data.pricingList)) {
      raw = data.pricingList
    } else if (Array.isArray(data.cabinPrices)) {
      raw = data.cabinPrices
    } else if (data && typeof data === 'object') {
      raw = Object.values(data).find((value) => Array.isArray(value)) || []
    }

    targetCabins.value = raw
      .map(normalizeCabinPricing)
      .filter((item) => item.pricingId && item.cabinType)

    if (targetCabins.value.length === 0) {
      ElMessage.warning('该目标航班暂无舱位票价，请先到舱位票价页面配置')
    }
  } catch (error) {
    targetCabins.value = []
    console.error('目标舱位票价加载失败：', error)
    ElMessage.error(error.response?.data?.message || error.message || '目标舱位票价加载失败')
  } finally {
    loadingTargetCabins.value = false
  }
}

const validateAssist = () => {
  if (!assistForm.reason.trim()) {
    ElMessage.warning(`请填写${assistType.value === 'refund' ? '退票' : '改签'}原因`)
    return false
  }
  if (assistType.value === 'change' && !assistForm.targetInstanceId) {
    ElMessage.warning('请选择目标航班')
    return false
  }

  if (assistType.value === 'change' && !assistForm.targetPricingId) {
    ElMessage.warning('请选择目标舱位')
    return false
  }

  return true
}

const handlePreview = async () => {
  if (!validateAssist() || !assistOrder.value) return
  previewing.value = true
  try {
    const payload = {
      reason: assistForm.reason.trim(),
      target_instance_id: assistForm.targetInstanceId || undefined,
      new_pricing_id: assistForm.targetPricingId || undefined,
      target_pricing_id: assistForm.targetPricingId || undefined,
      new_cabin_pricing_id: assistForm.targetPricingId || undefined,
      operator_type: '客服代操作',
      irregularity_id: route.query.irregularityId || undefined
    }
    const response = assistType.value === 'refund'
      ? await previewAdminRefund(assistOrder.value.orderId, payload)
      : await previewAdminChange(assistOrder.value.orderId, payload)
    assistPreview.value = response.data.data || null
  } catch (error) {
    assistPreview.value = null
    ElMessage.error(error.response?.data?.message || '费用预览接口待后端接入')
  } finally {
    previewing.value = false
  }
}

const handleAssistSubmit = async () => {
  if (!assistPreview.value || !validateAssist() || !assistOrder.value) return
  submittingAssist.value = true
  try {
    const payload = {
      reason: assistForm.reason.trim(),
      target_instance_id: assistForm.targetInstanceId || undefined,
      new_pricing_id: assistForm.targetPricingId || undefined,
      target_pricing_id: assistForm.targetPricingId || undefined,
      new_cabin_pricing_id: assistForm.targetPricingId || undefined,
      preview_token: assistPreview.value.previewToken,
      operator_type: '客服代操作',
      irregularity_id: route.query.irregularityId || undefined
    }
    if (assistType.value === 'refund') {
      await submitAdminRefund(assistOrder.value.orderId, payload)
    } else {
      await submitAdminChange(assistOrder.value.orderId, payload)
    }
    ElMessage.success(`后台${assistType.value === 'refund' ? '退票' : '改签'}处理成功`)
    assistVisible.value = false
    await loadOrders()
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '代办接口待后端接入')
  } finally {
    submittingAssist.value = false
  }
}

const goRecord = (tab) => {
  detailVisible.value = false
  activeTab.value = tab
  handleTabChange(tab)
}

const formatValue = (value) => {
  if (value === undefined || value === null || value === '') return '-'
  return value
}

const formatPrice = (price) => {
  if (price === undefined || price === null || price === '') return '-'
  return `¥${price}`
}

const maskPhone = (phone) => {
  const text = String(phone || '')
  if (text.length !== 11) return text || '-'
  return `${text.slice(0, 3)}****${text.slice(-4)}`
}

const getOrderStatusType = (status) => {
  if (status === '已支付') return 'success'
  if (status === '已退票') return 'info'
  if (status === '已改签') return 'warning'
  if (status === '已取消') return 'danger'
  return 'info'
}

const getRecordType = (recordType) => {
  if (recordType === '有效订单') return 'success'
  if (recordType === '历史订单') return 'info'
  return 'info'
}

onMounted(() => {
  loadOrders()
})
</script>

<style scoped>
.order-tabs {
  padding: 0 4px;
}

.scope-card {
  margin-bottom: 18px;
  padding: 18px 18px 0;
  border-radius: 16px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
}

.filter-card {
  margin-bottom: 18px;
  padding: 18px 18px 0;
  border-radius: 16px;
  background: linear-gradient(135deg, #f8fafc 0%, #ffffff 100%);
  border: 1px solid #e2e8f0;
}

.permission-alert {
  margin-bottom: 18px;
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

.assist-summary {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin: 18px 0 24px;
}

.assist-summary div {
  padding: 14px;
  border-radius: 12px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
}

.assist-summary span {
  display: block;
  margin-bottom: 6px;
  color: #94a3b8;
  font-size: 12px;
}

.assist-summary strong {
  color: #334155;
  font-size: 14px;
}

.preview-card {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  padding: 16px;
  border-radius: 14px;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
}

.preview-card span {
  display: block;
  margin-bottom: 5px;
  color: #64748b;
  font-size: 12px;
}

.preview-card strong {
  color: #334155;
}

.success-text {
  color: #16a34a !important;
}

:deep(.el-tabs__header) {
  margin-bottom: 20px;
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

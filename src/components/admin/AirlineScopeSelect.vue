<template>
  <el-form-item v-if="systemAdmin" label="航空公司">
    <el-select
      :model-value="modelValue"
      filterable
      clearable
      :placeholder="allowAll ? '全部航空公司' : '请选择航空公司'"
      :loading="loading"
      style="width: 220px"
      @update:model-value="emit('update:modelValue', $event)"
      @change="emit('change', $event)"
    >
      <el-option
        v-for="airline in airlines"
        :key="airline.airlineId"
        :label="`${airline.airlineName}（${airline.airlineCode}）`"
        :value="airline.airlineId"
      />
    </el-select>
  </el-form-item>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getAdminAirlines } from '../../api/admin/airline'
import { getStoredUser, isSystemAdmin } from '../../utils/adminAuth'

defineProps({
  modelValue: {
    type: [Number, String],
    default: ''
  },
  allowAll: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['update:modelValue', 'change', 'loaded'])
const loading = ref(false)
const airlines = ref([])
const systemAdmin = computed(() => isSystemAdmin(getStoredUser()))

const loadAirlines = async () => {
  if (!systemAdmin.value) return
  loading.value = true

  try {
    const response = await getAdminAirlines()
    airlines.value = response.data.data || []
    emit('loaded', airlines.value)
  } catch (error) {
    ElMessage.error(
      error.response?.data?.message ||
      '航空公司列表接口待后端接入'
    )
  } finally {
    loading.value = false
  }
}

onMounted(loadAirlines)
</script>

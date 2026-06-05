<template>
  <div class="search-container">
    
    <div class="hero-section">
      <h1 style="margin: 0; font-size: 32px; letter-spacing: 2px;">
        <el-icon><Promotion /></el-icon> 探索您的云端之旅
      </h1>
      <p style="opacity: 0.8; margin-top: 10px;">高效并发 · 安全票务</p>
    </div>
    <el-form :inline="true" :model="searchForm" class="search-form">
      <el-form-item label="出发地">
        <el-input v-model="searchForm.departure" placeholder="例如：北京" />
      </el-form-item>
      <el-form-item label="目的地">
        <el-input v-model="searchForm.arrival" placeholder="例如：上海" />
      </el-form-item>
      <el-form-item label="出发日期">
        <el-date-picker v-model="searchForm.date" type="date" placeholder="选择日期" value-format="YYYY-MM-DD" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="onSubmit">查询航班</el-button>
      </el-form-item>
    </el-form>

    <div class="table-container" v-if="flightList.length > 0">
      <el-table :data="flightList" style="width: 100%" stripe border>
        
        <el-table-column prop="flightNo" label="航班号" width="120" />
        
        <el-table-column label="起降机场" width="200">
          <template #default="scope">
            {{ scope.row.depAirport }} ✈️ {{ scope.row.arrAirport }}
          </template>
        </el-table-column>

        <el-table-column label="起降时间" width="150">
          <template #default="scope">
            {{ scope.row.depTime }} - {{ scope.row.arrTime }}
          </template>
        </el-table-column>

        <el-table-column prop="price" label="经济舱价格(元)" width="150" />
        
        <el-table-column label="余票状态" width="120">
          <template #default="scope">
            <el-tag :type="scope.row.seats > 10 ? 'success' : (scope.row.seats > 0 ? 'warning' : 'danger')">
              {{ scope.row.seats > 0 ? `余票: ${scope.row.seats}` : '已售罄' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="120">
          <template #default="scope">
            <el-button 
              type="primary" 
              size="small" 
              :disabled="scope.row.seats === 0" 
              @click="handleBook(scope.row)"
            >
              预订
            </el-button>
          </template>
        </el-table-column>

      </el-table>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
// 1. 引入我们刚刚配好的 api
import api from '../../api/index'
// 2. 引入 Element Plus 的消息提示工具
import { ElMessage } from 'element-plus'

const router = useRouter()
const searchForm = reactive({ departure: '北京', arrival: '上海', date: '' })
const flightList = ref([])

// 3. 将 onSubmit 改造为异步函数 (async/await)
const onSubmit = async () => {
  console.log('准备向后端发送请求，条件是：', searchForm)
  
  try {
    // 解析每一行：
    // await 会让代码在这里耐心等待，直到后端把数据传回来
    // api.get 表示发送一个 GET 请求给后端，路径是 /flights/search
    // { params: searchForm } 会自动把你的搜索条件拼接到网址后面送给后端
    const response = await api.get('/flights/search', { params: searchForm })

    // 假设 2 号同学按约定返回的格式是 { code: 200, message: "成功", data: [...] }
    if (response.data.code === 200) {
      // 把后端传回来的真实数组，赋值给页面的表格
      flightList.value = response.data.data
      ElMessage.success('查询成功！')
    } else {
      // 如果后端查不到数据或报错，把后端的错误信息弹窗提示给用户
      ElMessage.warning(response.data.message || '未查询到相关航班')
    }
  } catch (error) {
    // 捕获网络异常（比如后端代码崩了，或者服务器没开）
    ElMessage.error('网络请求失败，请检查后端服务是否启动')
    console.error(error)
  }
}

// handleBook 保持不变...
const handleBook = (flight) => {
  router.push('/book')
}
</script>

<style scoped>
/* 整个页面的外层容器 */
.search-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-bottom: 50px;
}

/* 顶部巨大的欢迎横幅区域 */
.hero-section {
  width: 100%;
  height: 200px;
  background: linear-gradient(120deg, #005a9e, #0081c6); /* 航空蓝渐变 */
  color: white;
  text-align: center;
  padding-top: 40px;
  margin-bottom: -60px; /* 故意设置负边距，让搜索卡片能“压”在这个蓝色背景上 */
}

/* 重构搜索表单，把它变成一个悬浮的卡片 */
.search-form {
  background: white;
  padding: 30px 40px;
  border-radius: 12px; /* 圆角变得更大更柔和 */
  /* 给搜索卡片加上非常立体的弥散阴影 */
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 15px; /* 让输入框之间的间距更自然 */
  z-index: 10; /* 保证卡片浮在蓝色横幅之上 */
  width: 80%;
  max-width: 900px;
}

/* 去除表单项自带的底部间距，让表单在卡片里更紧凑 */
.search-form .el-form-item {
  margin-bottom: 0;
}

/* 美化航班列表展示区 */
.table-container {
  width: 85%;
  max-width: 1000px;
  margin-top: 40px;
  background: white;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.05); /* 淡淡的底座阴影 */
}
</style>
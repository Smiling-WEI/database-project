<template>
  <div class="passenger-container">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <h2>👨‍👩‍👧 我的常用乘机人</h2>
          <el-button type="primary" @click="openAddDialog">+ 新增乘机人</el-button>
        </div>
      </template>

      <el-table :data="passengerList" border stripe style="width: 100%">
        <el-table-column prop="realName" label="真实姓名" width="120" />
        <el-table-column prop="relation" label="关系" width="100">
          <template #default="scope">
            <el-tag size="small">{{ scope.row.relation }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="idCard" label="身份证号" width="200" />
        <el-table-column prop="phone" label="联系电话" />
        
        <el-table-column label="操作" width="100">
          <template #default="scope">
            <el-popconfirm 
              title="确定要删除这个乘机人吗？" 
              confirm-button-text="删除" 
              cancel-button-text="取消"
              @confirm="handleDelete(scope.$index, scope.row)"
            >
              <template #reference>
                <el-button type="danger" size="small" plain>删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" title="新增常用乘机人" width="400px">
      <el-form :model="addForm" :rules="rules" ref="addFormRef" label-width="90px">
        <el-form-item label="真实姓名" prop="realName">
          <el-input v-model="addForm.realName" placeholder="如：李四" />
        </el-form-item>
        <el-form-item label="关系备注" prop="relation">
          <el-select v-model="addForm.relation" placeholder="请选择关系">
            <el-option label="本人" value="本人" />
            <el-option label="家属" value="家属" />
            <el-option label="朋友" value="朋友" />
            <el-option label="同事" value="同事" />
          </el-select>
        </el-form-item>
        <el-form-item label="身份证号" prop="idCard">
          <el-input v-model="addForm.idCard" placeholder="18位身份证号" maxlength="18" />
        </el-form-item>
        <el-form-item label="联系电话" prop="phone">
          <el-input v-model="addForm.phone" placeholder="11位手机号" maxlength="11" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取 消</el-button>
          <el-button type="primary" @click="submitAdd">确 定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'

// 1. 模拟的乘机人列表数据 (对应数据库里的 passenger 和 user_passenger 联表查询结果)
const passengerList = ref([
  { id: 1, realName: '张三', relation: '本人', idCard: '110105199001011234', phone: '13800138000' },
  { id: 2, realName: '李四', relation: '家属', idCard: '110105199205055678', phone: '13900139000' }
])

// 2. 弹窗控制与表单数据
const dialogVisible = ref(false)
const addFormRef = ref(null)
const addForm = reactive({
  realName: '',
  relation: '',
  idCard: '',
  phone: ''
})

// 3. 表单校验规则
const rules = reactive({
  realName: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  relation: [{ required: true, message: '请选择关系', trigger: 'change' }],
  idCard: [
    { required: true, message: '请输入身份证号', trigger: 'blur' },
    { len: 18, message: '身份证号必须是18位', trigger: 'blur' }
  ],
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { len: 11, message: '手机号必须是11位', trigger: 'blur' }
  ]
})

// 4. 打开新增弹窗，并清空上次填写的旧数据
const openAddDialog = () => {
  addForm.realName = ''
  addForm.relation = ''
  addForm.idCard = ''
  addForm.phone = ''
  dialogVisible.value = true
}

// 5. 提交新增乘机人
const submitAdd = () => {
  addFormRef.value.validate((valid) => {
    if (valid) {
      // 校验通过，模拟发送给后端保存。这里我们直接把它塞进前端数组里演示效果
      passengerList.value.push({ 
        id: Date.now(), // 随便生成一个临时ID
        ...addForm 
      })
      ElMessage.success('添加乘机人成功！')
      dialogVisible.value = false // 关闭弹窗
    }
  })
}

// 6. 删除乘机人
const handleDelete = (index, row) => {
  // 模拟发送删除请求给后端
  console.log('准备删除的乘机人ID是：', row.id)
  passengerList.value.splice(index, 1) // 从前端数组中移除该行
  ElMessage.success(`已删除乘机人: ${row.realName}`)
}
</script>

<style scoped>
.passenger-container {
  padding: 40px;
  max-width: 900px;
  margin: 0 auto;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
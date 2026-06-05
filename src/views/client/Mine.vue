<template>
  <div class="mine-container">
    <el-row :gutter="20">
      <el-col :span="8">
        <el-card shadow="hover" class="profile-card">
          <div class="avatar-area">
            <el-avatar :size="80" src="https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png" />
            <h3>张三</h3>
            <p>普通会员</p>
          </div>
          <el-divider />
          <div class="info-list">
            <p><strong>账号：</strong> admin123</p>
            <p><strong>手机号：</strong> 138****8888</p>
            <p><strong>注册时间：</strong> 2026-05-01</p>
          </div>
        </el-card>
      </el-col>

      <el-col :span="16">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>⚙️ 账户设置与管理</span>
            </div>
          </template>
          
          <el-menu class="setting-menu" router>
            <el-menu-item index="/passengers">
              <el-icon><UserFilled /></el-icon>
              <span>常用乘机人管理 (新增/修改)</span>
            </el-menu-item>
            <el-menu-item index="/orders">
              <el-icon><List /></el-icon>
              <span>我的历史订单</span>
            </el-menu-item>
            <el-menu-item index="">
              <el-icon><Lock /></el-icon>
              <span>修改密码</span>
            </el-menu-item>
          </el-menu>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.mine-container { padding: 40px; max-width: 1000px; margin: 0 auto; }
.profile-card { text-align: center; }
.avatar-area h3 { margin: 10px 0 5px 0; }
.avatar-area p { color: #909399; margin: 0; font-size: 14px; }
.info-list { text-align: left; line-height: 2; color: #606266; }
.setting-menu { border-right: none; }
</style>
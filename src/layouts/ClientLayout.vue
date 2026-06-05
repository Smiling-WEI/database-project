<template>
  <div class="layout-container">
    
    <el-menu 
      mode="vertical" 
      router 
      :default-active="$route.path" 
      class="side-nav"
    >
      <div class="logo-area">
        <h3>✈️ 航空票务</h3>
      </div>

      <el-menu-item index="/home">
        <el-icon><Monitor /></el-icon>
        <span>首页 (查询)</span>
      </el-menu-item>
      
      <el-menu-item index="/orders">
        <el-icon><Tickets /></el-icon>
        <span>我的订单</span>
      </el-menu-item>
      
      <el-menu-item index="/mine">
        <el-icon><User /></el-icon>
        <span>个人中心</span>
      </el-menu-item>
      
      <div class="spacer"></div>

      <el-menu-item @click="handleLogout" class="logout-item">
        <el-icon><SwitchButton /></el-icon>
        <span>退出登录</span>
      </el-menu-item>
    </el-menu>

    <div class="main-content">
      <router-view />
    </div>
    
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
const router = useRouter()

const handleLogout = () => {
  router.push('/login')
}
</script>

<style scoped>
/* 1. 外层大容器：改为左右排布 (flex-direction 默认为 row) */
.layout-container {
  display: flex;
  height: 100vh; /* 高度占满全屏 */
  width: 100vw;
  background: url('../assets/bg2.png') no-repeat center center fixed;
  background-size: cover;
  overflow: hidden; /* 防止整个大页面出现滚动条 */
}

/* 2. 左侧导航侧边栏 */
.side-nav {
  width: 220px; /* 固定侧边栏宽度 */
  display: flex;
  flex-direction: column; /* 让侧边栏里的选项从上往下排 */
  
  /* 毛玻璃特效 */
  background: rgba(255, 255, 255, 0.6) !important;
  backdrop-filter: blur(15px);
  border-right: none !important; /* 隐藏 Element Plus 默认的丑陋右边框 */
}

/* 3. 顶部 Logo 样式 */
.logo-area {
  height: 80px;
  display: flex;
  justify-content: center;
  align-items: center;
  color: #1a4f82;
  letter-spacing: 2px;
}

/* 4. 核心：强制菜单内容居中！ */
.side-nav .el-menu-item {
  display: flex;
  justify-content: center; /* 水平居中 */
  align-items: center;     /* 垂直居中 */
  font-size: 15px;
  font-weight: bold;
}

/* 微调：让图标和文字之间有一点呼吸感，不至于挤在一起 */
.side-nav .el-menu-item .el-icon {
  margin-right: 10px; 
}

/* 5. 弹簧占位符：利用 flex-grow 吸收所有剩余空间 */
.spacer {
  flex-grow: 1;
}

.logout-item {
  margin-bottom: 20px; /* 距离底部留点缝隙 */
}

/* 6. 右侧内容区 */
.main-content {
  flex: 1; /* 占据屏幕右侧剩下的所有宽度 */
  padding: 30px;
  /* 右侧内容如果太长，只允许右侧区域自己上下滚动，左边导航栏不动 */
  overflow-y: auto; 
}
</style>
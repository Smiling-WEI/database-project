<template>
  <div class="admin-layout">
    <AppSidebar :collapsed="sidebarCollapsed" />

    <div class="admin-main">
      <AppHeader
        :sidebar-collapsed="sidebarCollapsed"
        @toggle-sidebar="toggleSidebar"
      />

      <main class="admin-content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import AppSidebar from '../components/admin/AppSidebar.vue'
import AppHeader from '../components/admin/AppHeader.vue'

const sidebarCollapsed = ref(
  sessionStorage.getItem('adminSidebarCollapsed') === 'true'
)

const toggleSidebar = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value
  sessionStorage.setItem(
    'adminSidebarCollapsed',
    String(sidebarCollapsed.value)
  )
}
</script>

<style scoped>
.admin-layout {
  min-height: 100vh;
  display: flex;
  background: linear-gradient(135deg, #eaf4ff 0%, #f7fbff 45%, #eef7ff 100%);
}

.admin-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.admin-content {
  flex: 1;
  padding: 24px;
  overflow: auto;
}
</style>

<template>
  <div class="admin-layout">
    <AppSidebar />

    <div class="admin-main">
      <AppHeader />

      <main class="admin-content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import AppSidebar from '../components/admin/AppSidebar.vue'
import AppHeader from '../components/admin/AppHeader.vue'
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
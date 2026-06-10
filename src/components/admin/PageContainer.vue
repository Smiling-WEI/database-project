<template>
  <section class="page-container">
    <div v-if="title || description || $slots.extra" class="page-header">
      <div>
        <h2 v-if="title">{{ title }}</h2>
        <p v-if="description">{{ description }}</p>
      </div>

      <div v-if="$slots.extra" class="page-extra">
        <slot name="extra" />
      </div>
    </div>

    <slot />
  </section>
</template>

<script setup>
defineProps({
  title: {
    type: String,
    default: ''
  },
  description: {
    type: String,
    default: ''
  }
})
</script>

<style scoped>
.page-container {
  width: 100%;
  max-width: 100%;
  min-height: calc(100vh - 124px);
  padding: 22px;
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.82);
  backdrop-filter: blur(18px);
  box-shadow: 0 18px 42px rgba(148, 163, 184, 0.16);
  border: 1px solid rgba(226, 232, 240, 0.9);
  box-sizing: border-box;
  overflow: hidden;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 20px;
}

h2 {
  margin: 0;
  color: #1e293b;
  font-size: 20px;
  font-weight: 700;
}

p {
  margin: 6px 0 0;
  color: #64748b;
  font-size: 14px;
}

.page-extra {
  flex-shrink: 0;
}
</style>
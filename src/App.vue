<template>
  <router-view />
</template>

<script setup>
</script>

<style>
/* 保证全屏无白边，去掉所有多余的边距 */
body, html { 
  margin: 0; 
  padding: 0; 
  height: 100%; 
  font-family: 'Microsoft YaHei', sans-serif; 
}
</style>
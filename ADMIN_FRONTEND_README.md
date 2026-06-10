# 管理端前端完成说明

## 一、当前完成范围

本部分为航空订票系统的管理端前端页面，已完成基础布局、核心页面结构和前端交互框架。

已完成页面包括：

| 页面 | 路由 | 状态 |
|---|---|---|
| 管理端控制台 | `/admin/dashboard` | 已完成页面结构 |
| 航班管理 | `/admin/flights` | 已完成页面结构 |
| 航班新增 / 编辑 | `/admin/flights/edit` | 已完成页面结构 |
| 订单管理 | `/admin/orders` | 已完成页面结构 |
| 用户管理 | `/admin/users` | 已完成页面结构 |
| 管理员管理 | `/admin/admins` | 已完成页面结构 |

管理端整体布局包括：

- 左侧菜单栏：`src/components/admin/AppSidebar.vue`
- 顶部栏：`src/components/admin/AppHeader.vue`
- 页面容器：`src/components/admin/PageContainer.vue`
- 管理端总布局：`src/layouts/AdminLayout.vue`

公共登录页已增加身份选择：

- 普通用户登录后跳转：`/home`
- 管理员登录后跳转：`/admin/dashboard`

当前登录页仅做前端分流，真实登录校验、token、权限控制等待后端接口接入。

---

## 二、当前数据处理方式

管理端页面已删除直接写入代码中的业务实例数据。

目前各页面使用空数组作为后端数据接入位置，例如：

```js
const flightList = ref([])
const orderList = ref([])
const userList = ref([])
const adminList = ref([])
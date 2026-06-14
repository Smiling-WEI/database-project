import { createRouter, createWebHistory } from 'vue-router'

// 1. 公共页面：退一层去 views 根目录找
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import ForgotPassword from '../views/ForgotPassword.vue'

// 2. 布局骨架：退一层去 layouts 找
import ClientLayout from '../layouts/ClientLayout.vue'
import AdminLayout from '../layouts/AdminLayout.vue'

// 3. 客户端页面：去 views/client 找
import FlightSearch from '../views/client/FlightSearch.vue'
import BookingConfirm from '../views/client/BookingConfirm.vue'
import MyOrders from '../views/client/MyOrders.vue'
import PassengerManage from '../views/client/PassengerManage.vue'
import Mine from '../views/client/Mine.vue'

// 4. 管理端页面：去 views/admin 找
import Dashboard from '../views/admin/Dashboard.vue'
import FlightList from '../views/admin/flight/FlightList.vue'
import FlightEdit from '../views/admin/flight/FlightEdit.vue'
import FlightIrregularity from '../views/admin/flight/FlightIrregularity.vue'
import UserList from '../views/admin/user/UserList.vue'
import OrderList from '../views/admin/order/OrderList.vue'
import AdminList from '../views/admin/adminAccount/AdminList.vue'
import CabinPricing from '../views/admin/pricing/CabinPricing.vue'
import ChangeRuleList from '../views/admin/rule/ChangeRuleList.vue'
import AdminProfile from '../views/admin/Profile.vue'
import CrossAirlineCoordination from '../views/admin/coordination/CrossAirlineCoordination.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    // 默认打开网页直接跳转到登录页
    { path: '/', redirect: '/login' },
    
    // 公共路由区
    { path: '/login', name: 'Login', component: Login },
    { path: '/register', name: 'Register', component: Register },
    { path: '/forgot-password', name: 'ForgotPassword', component: ForgotPassword },
    
    // 乘客端（客户端）主框架路由
    {
      path: '/sys',
      component: ClientLayout,
      redirect: '/home', // 默认进入航班查询首页
      children: [
        { path: '/home', component: FlightSearch },
        { path: '/orders', component: MyOrders },
        { path: '/mine', component: Mine },
        { path: '/book', component: BookingConfirm },
        { path: '/passengers', component: PassengerManage }
      ]
    },

    // 管理端主框架路由
    {
      path: '/admin',
      component: AdminLayout,
      redirect: '/admin/dashboard', // 默认进入控制台首页
      children: [
        { path: 'dashboard', component: Dashboard },
        { path: 'flights', component: FlightList },
        { path: 'flights/edit', component: FlightEdit },
        {
          path: 'flights/:instanceId/irregularities',
          component: FlightIrregularity
        },
        { path: 'pricing', component: CabinPricing },
        { path: 'change-rules', component: ChangeRuleList },
        {
          path: 'change-records',
          redirect: '/admin/orders?tab=change'
        },
        { path: 'users', component: UserList },
        { path: 'orders', component: OrderList },
        { path: 'admins', component: AdminList },
        { path: 'coordination', component: CrossAirlineCoordination },
        { path: 'profile', component: AdminProfile }
      ]
    }
  ]
})

export default router

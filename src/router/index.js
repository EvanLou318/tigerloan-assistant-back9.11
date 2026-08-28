import { createRouter, createWebHashHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    redirect: '/login',
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/auth/Login.vue'),
    meta: { title: '登录' },
  },
  {
    path: '/change-password',
    name: 'ChangePassword',
    component: () => import('../views/auth/ChangePassword.vue'),
    meta: { title: '修改密码', requiresAuth: true },
  },
  {
    path: '/home',
    name: 'Home',
    component: () => import('../views/home/Index.vue'),
    meta: { title: '首页', requiresAuth: true, tabbar: true },
  },
  {
    path: '/products',
    name: 'ProductList',
    component: () => import('../views/product/List.vue'),
    meta: { title: '产品库', requiresAuth: true, tabbar: true },
  },
  {
    path: '/products/create',
    name: 'ProductCreate',
    component: () => import('../views/product/Create.vue'),
    meta: { title: '录入产品', requiresAuth: true },
  },
  {
    path: '/products/:id',
    name: 'ProductDetail',
    component: () => import('../views/product/Detail.vue'),
    meta: { title: '产品详情', requiresAuth: true },
  },
  {
    path: '/customers',
    name: 'CustomerList',
    component: () => import('../views/customer/List.vue'),
    meta: { title: '客户', requiresAuth: true, tabbar: true },
  },
  {
    path: '/customers/create',
    name: 'CustomerCreate',
    component: () => import('../views/customer/Create.vue'),
    meta: { title: '新建客户', requiresAuth: true },
  },
  {
    path: '/customers/:id/materials',
    name: 'CustomerMaterial',
    component: () => import('../views/customer/Material.vue'),
    meta: { title: '补充资料', requiresAuth: true },
  },
  {
    path: '/customers/:id',
    name: 'CustomerDetail',
    component: () => import('../views/customer/Detail.vue'),
    meta: { title: '客户档案', requiresAuth: true },
  },
  {
    path: '/customers/:id/match',
    name: 'CustomerMatch',
    component: () => import('../views/customer/Match.vue'),
    meta: { title: 'AI匹配', requiresAuth: true },
  },
  {
    path: '/customers/:id/simulation',
    name: 'CustomerSimulation',
    component: () => import('../views/customer/Simulation.vue'),
    meta: { title: '场景推演', requiresAuth: true },
  },
  {
    path: '/schedules',
    name: 'ScheduleList',
    component: () => import('../views/schedule/List.vue'),
    meta: { title: '日程计划', requiresAuth: true },
  },
  {
    path: '/schedules/create',
    name: 'ScheduleCreate',
    component: () => import('../views/schedule/Create.vue'),
    meta: { title: '新建日程', requiresAuth: true },
  },
  {
    path: '/assistant',
    name: 'Assistant',
    component: () => import('../views/assistant/Index.vue'),
    meta: { title: 'AI 助理', requiresAuth: true },
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('../views/profile/Index.vue'),
    meta: { title: '我的', requiresAuth: true, tabbar: true },
  },
  // ---------- 管理后台（桌面端） ----------
  {
    path: '/admin',
    component: () => import('../views/admin/Layout.vue'),
    meta: { title: '管理后台', requiresAuth: true, admin: true },
    children: [
      { path: '', redirect: '/admin/dashboard' },
      { path: 'dashboard', name: 'AdminDashboard', component: () => import('../views/admin/Dashboard.vue'), meta: { title: '数据看板', requiresAuth: true, admin: true } },
      { path: 'customers', name: 'AdminCustomers', component: () => import('../views/admin/Customers.vue'), meta: { title: '客户管理', requiresAuth: true, admin: true } },
      { path: 'products', name: 'AdminProducts', component: () => import('../views/admin/Products.vue'), meta: { title: '产品管理', requiresAuth: true, admin: true } },
      { path: 'schedules', name: 'AdminSchedules', component: () => import('../views/admin/Schedules.vue'), meta: { title: '日程管理', requiresAuth: true, admin: true } },
      { path: 'users', name: 'AdminUsers', component: () => import('../views/admin/Users.vue'), meta: { title: '用户管理', requiresAuth: true, admin: true } },
      { path: 'security', name: 'AdminSecurity', component: () => import('../views/admin/Security.vue'), meta: { title: '权限与安全', requiresAuth: true, admin: true } },
      { path: 'services', name: 'AdminServices', component: () => import('../views/admin/Services.vue'), meta: { title: '三方服务', requiresAuth: true, admin: true } },
    ],
  },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  if (to.meta.requiresAuth && !token) {
    next('/login')
  } else if (to.path === '/login' && token) {
    next('/home')
  } else {
    next()
  }
})

export default router

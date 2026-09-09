// ==================== 智贷助手 · 后端服务入口 ====================
// 技术栈：Node.js + Express + SQLite(node:sqlite) + JWT
// 启动：npm run server   （默认端口 3001，前端 vite 已配置代理）
//
// AI 能力默认 auto：管理后台「三方服务」按分类切换 mock / 真实供应商；
// 也可用环境变量强制：AI_PROVIDER=mock|real，见 server/services/ai/real.js

import express from 'express'
import cors from 'cors'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { config } from './config.js'
import './db.js'
import { seedIfEmpty } from './seed.js'
import { ensureRBACSeed } from './rbac.js'
import { authRequired } from './middleware/auth.js'
import { fail } from './utils.js'
import authRoutes from './routes/auth.js'
import productRoutes from './routes/products.js'
import customerRoutes from './routes/customers.js'
import scheduleRoutes from './routes/schedules.js'
import dashboardRoutes from './routes/dashboard.js'
import aiRoutes from './routes/ai.js'
import adminRoutes from './routes/admin.js'
import serviceRoutes from './routes/services.js'
import { SERVICE_CATEGORIES, getCategoryRuntime } from './services/ai/registry.js'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

// 首次启动播种演示数据
seedIfEmpty()
// RBAC 角色权限 + 系统设置增量播种（旧库安全升级）
ensureRBACSeed()

const app = express()
app.use(cors())
app.use(express.json({ limit: '20mb' }))

// 上传文件静态服务
app.use('/uploads', express.static(path.join(__dirname, 'uploads'), { maxAge: '7d' }))

// ---------- API 路由 ----------
app.use('/api/auth', authRoutes)
app.use('/api/products', authRequired, productRoutes)
app.use('/api/customers', authRequired, customerRoutes)
app.use('/api/schedules', authRequired, scheduleRoutes)
app.use('/api/dashboard', authRequired, dashboardRoutes)
app.use('/api/ai', authRequired, aiRoutes)
app.use('/api/admin', authRequired, adminRoutes)
app.use('/api/services', authRequired, serviceRoutes)

// 健康检查（含 AI 各分类实际运行模式，供管理后台顶栏徽标展示）
app.get('/api/health', (req, res) => {
  const modes = SERVICE_CATEGORIES.map((c) => getCategoryRuntime(c.code).mode)
  const realCount = modes.filter((m) => m === 'real').length
  const summary = realCount === modes.length ? 'Real' : realCount > 0 ? 'Mixed' : 'Mock'
  res.json({ success: true, data: { status: 'ok', aiProvider: summary, categories: modes, time: new Date().toISOString() } })
})

// ---------- 生产模式：托管前端构建产物（dist/） ----------
const distDir = path.join(__dirname, '..', 'dist')
if (fs.existsSync(distDir)) {
  app.use(express.static(distDir))
  // SPA 回退：非 API 的 GET 请求返回 index.html（hash 路由其实无需回退，但保持通用）
  app.get(/^\/(?!api|uploads).*/, (req, res) => {
    res.sendFile(path.join(distDir, 'index.html'))
  })
}

// ---------- 404 与全局错误处理 ----------
app.use('/api', (req, res) => fail(res, 404, '接口不存在'))

app.use((err, req, res, next) => {
  if (res.headersSent) return next(err)
  console.error('[server]', err)
  fail(res, err.status || 500, err.message || '服务器内部错误')
})

app.listen(config.port, '0.0.0.0', () => {
  console.log('========================================')
  console.log('  智贷助手后端已启动')
  console.log(`  地址: http://localhost:${config.port}`)
  console.log(`  AI Provider: ${config.aiProvider}（mock=模拟 / real=真实服务）`)
  console.log('  测试账号: 13800138000 / abc123')
  console.log('========================================')
})

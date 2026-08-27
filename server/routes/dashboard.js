// ==================== 仪表盘路由 ====================

import { Router } from 'express'
import { db, rowToSchedule } from '../db.js'
import { ok } from '../utils.js'

const router = Router()

// GET /api/dashboard  统计概览 + 今日日程预览
router.get('/', (req, res) => {
  const userId = req.user.id

  const customerCount = db.prepare('SELECT COUNT(*) AS n FROM customers WHERE user_id = ?').get(userId).n
  const productCount = db.prepare('SELECT COUNT(*) AS n FROM products WHERE user_id = ?').get(userId).n
  const activeProductCount = db.prepare("SELECT COUNT(*) AS n FROM products WHERE user_id = ? AND status = 'active'").get(userId).n
  const simulationCount = db.prepare('SELECT COUNT(*) AS n FROM simulations WHERE user_id = ?').get(userId).n
  const pendingScheduleCount = db.prepare('SELECT COUNT(*) AS n FROM schedules WHERE user_id = ? AND done = 0').get(userId).n

  // 今日日程（本地时区当天 00:00 ~ 24:00，未完成）
  const start = new Date()
  start.setHours(0, 0, 0, 0)
  const end = new Date(start)
  end.setDate(end.getDate() + 1)
  const todayRows = db.prepare(`
    SELECT * FROM schedules
    WHERE user_id = ? AND done = 0 AND start_time >= ? AND start_time < ?
    ORDER BY start_time ASC LIMIT 3`)
    .all(userId, start.toISOString(), end.toISOString())

  const todayCount = db.prepare(`
    SELECT COUNT(*) AS n FROM schedules
    WHERE user_id = ? AND done = 0 AND start_time >= ? AND start_time < ?`)
    .get(userId, start.toISOString(), end.toISOString()).n

  ok(res, {
    customerCount,
    productCount,
    activeProductCount,
    simulationCount,
    todayScheduleCount: todayCount,
    pendingScheduleCount,
    todaySchedules: todayRows.map(rowToSchedule),
  })
})

export default router

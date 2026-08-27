// ==================== 日程计划路由 ====================

import { Router } from 'express'
import { db, rowToSchedule } from '../db.js'
import { ok, fail, genId, fmtDateTime, BizError } from '../utils.js'

const router = Router()

function findSchedule(id, userId) {
  const row = db.prepare('SELECT * FROM schedules WHERE id = ? AND user_id = ?').get(id, userId)
  if (!row) throw new BizError('日程不存在', 404)
  return row
}

// GET /api/schedules  日程列表
router.get('/', (req, res) => {
  const rows = db.prepare('SELECT * FROM schedules WHERE user_id = ? ORDER BY start_time ASC').all(req.user.id)
  ok(res, rows.map(rowToSchedule))
})

// GET /api/schedules/:id  日程详情
router.get('/:id', (req, res) => {
  ok(res, rowToSchedule(findSchedule(req.params.id, req.user.id)))
})

// POST /api/schedules  创建日程
router.post('/', (req, res) => {
  const b = req.body || {}
  if (!b.title?.trim()) throw new BizError('请填写日程标题')
  if (!b.startTime) throw new BizError('请选择开始时间')

  const id = genId('sch')
  db.prepare(`
    INSERT INTO schedules (id, user_id, title, start_time, end_time, reminder_time, priority, type,
      location, remark, customer_id, customer_name, done, source, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`)
    .run(id, req.user.id, b.title.trim(), b.startTime, b.endTime || b.startTime,
      b.reminderTime || null, b.priority || 'P1', b.type || 'task',
      b.location || '', b.remark || '', b.customerId || null, b.customerName || '',
      0, b.source || 'text', fmtDateTime())

  ok(res, rowToSchedule(findSchedule(id, req.user.id)))
})

// PATCH /api/schedules/:id  更新日程（字段级，含完成状态）
router.patch('/:id', (req, res) => {
  const row = findSchedule(req.params.id, req.user.id)
  const b = req.body || {}

  db.prepare(`
    UPDATE schedules SET
      title = ?, start_time = ?, end_time = ?, reminder_time = ?, priority = ?, type = ?,
      location = ?, remark = ?, customer_id = ?, customer_name = ?, done = ?, updated_at = ?
    WHERE id = ? AND user_id = ?`)
    .run(
      b.title !== undefined ? String(b.title).trim() : row.title,
      b.startTime !== undefined ? b.startTime : row.start_time,
      b.endTime !== undefined ? b.endTime : row.end_time,
      b.reminderTime !== undefined ? (b.reminderTime || null) : row.reminder_time,
      b.priority !== undefined ? b.priority : row.priority,
      b.type !== undefined ? b.type : row.type,
      b.location !== undefined ? String(b.location) : row.location,
      b.remark !== undefined ? String(b.remark) : row.remark,
      b.customerId !== undefined ? (b.customerId || null) : row.customer_id,
      b.customerName !== undefined ? String(b.customerName) : row.customer_name,
      b.done !== undefined ? (b.done ? 1 : 0) : row.done,
      fmtDateTime(), req.params.id, req.user.id)

  ok(res, rowToSchedule(findSchedule(req.params.id, req.user.id)))
})

// DELETE /api/schedules/:id  删除日程
router.delete('/:id', (req, res) => {
  findSchedule(req.params.id, req.user.id)
  db.prepare('DELETE FROM schedules WHERE id = ? AND user_id = ?').run(req.params.id, req.user.id)
  ok(res, { deleted: true })
})

// 统一错误处理
router.use((err, req, res, next) => {
  if (err instanceof BizError) return fail(res, err.status, err.message)
  next(err)
})

export default router

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

// 时间统一归一化为 ISO 字符串再入库。
// 原因：前端 todaySchedules / 逾期判断靠 new Date(str) 解析，若把「2026-09-10 14:00:00」
// 这类裸本地时间原样存库，各家浏览器解析行为不一致，会导致日程在首页「今日」列表里凭空消失。
// 校验用解析后的时间戳，存储用归一化结果，保证「能通过的必定能正确渲染」。
function normalizeTime(value, label) {
  const ms = new Date(value).getTime()
  if (Number.isNaN(ms)) throw new BizError(`${label}格式不正确`)
  return { ms, iso: new Date(ms).toISOString() }
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

  // 枚举字段白名单：非法值会让列表的优先级色条/类型图标渲染落空
  const PRIORITIES = ['P0', 'P1', 'P2']
  const TYPES = ['task', 'call', 'meeting']
  if (b.priority !== undefined && !PRIORITIES.includes(b.priority)) {
    throw new BizError('优先级只能是 P0 / P1 / P2')
  }
  if (b.type !== undefined && !TYPES.includes(b.type)) {
    throw new BizError('日程类型不合法')
  }

  // 时间合法性：倒挂的时间会让列表排序、逾期判断、提醒调度全部失真
  const start = normalizeTime(b.startTime, '开始时间')
  let endIso = start.iso
  if (b.endTime) {
    const end = normalizeTime(b.endTime, '结束时间')
    if (end.ms < start.ms) throw new BizError('结束时间不能早于开始时间')
    endIso = end.iso
  }
  let reminderIso = null
  if (b.reminderTime) {
    const rem = normalizeTime(b.reminderTime, '提醒时间')
    if (rem.ms > start.ms) throw new BizError('提醒时间不能晚于开始时间')
    reminderIso = rem.iso
  }

  const id = genId('sch')
  db.prepare(`
    INSERT INTO schedules (id, user_id, title, start_time, end_time, reminder_time, priority, type,
      location, remark, customer_id, customer_name, done, source, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`)
    .run(id, req.user.id, b.title.trim(), start.iso, endIso,
      reminderIso, b.priority || 'P1', b.type || 'task',
      b.location || '', b.remark || '', b.customerId || null, b.customerName || '',
      0, b.source || 'text', fmtDateTime())

  ok(res, rowToSchedule(findSchedule(id, req.user.id)))
})

// PATCH /api/schedules/:id  更新日程（字段级，含完成状态）
router.patch('/:id', (req, res) => {
  const row = findSchedule(req.params.id, req.user.id)
  const b = req.body || {}

  // 时间校验基于「合并后的最终值」，避免只传 endTime 就绕过创建时的约束
  const nextStart = b.startTime !== undefined ? b.startTime : row.start_time
  const nextEnd = b.endTime !== undefined ? b.endTime : row.end_time
  const nextReminder = b.reminderTime !== undefined ? b.reminderTime : row.reminder_time

  // 枚举字段白名单（与创建保持一致）
  if (b.priority !== undefined && !['P0', 'P1', 'P2'].includes(b.priority)) {
    throw new BizError('优先级只能是 P0 / P1 / P2')
  }
  if (b.type !== undefined && !['task', 'call', 'meeting'].includes(b.type)) {
    throw new BizError('日程类型不合法')
  }
  if (b.title !== undefined && !String(b.title).trim()) {
    throw new BizError('请填写日程标题')
  }

  // 与创建一致：解析校验并归一化为 ISO 后再落库（历史裸本地时间行也会被顺带纠正）
  const start = normalizeTime(nextStart, '开始时间')
  let endIso = start.iso
  if (nextEnd) {
    const end = normalizeTime(nextEnd, '结束时间')
    if (end.ms < start.ms) throw new BizError('结束时间不能早于开始时间')
    endIso = end.iso
  }
  let reminderIso = null
  if (nextReminder) {
    const rem = normalizeTime(nextReminder, '提醒时间')
    if (rem.ms > start.ms) throw new BizError('提醒时间不能晚于开始时间')
    reminderIso = rem.iso
  }

  db.prepare(`
    UPDATE schedules SET
      title = ?, start_time = ?, end_time = ?, reminder_time = ?, priority = ?, type = ?,
      location = ?, remark = ?, customer_id = ?, customer_name = ?, done = ?, updated_at = ?
    WHERE id = ? AND user_id = ?`)
    .run(
      b.title !== undefined ? String(b.title).trim() : row.title,
      start.iso,
      endIso,
      reminderIso,
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

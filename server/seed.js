// ==================== 种子数据 ====================
// 首次启动时写入演示数据（与原前端原型 mock 数据一致）
// 测试账号：13800138000 / abc123

import bcrypt from 'bcryptjs'
import { db, getMaterialsByCustomer } from './db.js'
import { fmtDateTime } from './utils.js'

const seedUser = {
  phone: '13800138000',
  password: 'abc123',
  name: '李经理',
  role: 'loan_manager',
}

const seedProducts = [
  {
    id: 'p001', productName: '招商银行闪电贷', institution: '招商银行',
    minRate: 4.2, maxRate: 7.8, minAmount: 1, maxAmount: 30,
    loanTerm: '12-36个月', repaymentMethod: '等额本息',
    conditions: '年龄22-55周岁；月收入≥5000元；征信良好，近3个月查询≤6次',
    status: 'active', createdAt: '2026-08-10 09:30:00', source: 'text',
  },
  {
    id: 'p002', productName: '建设银行公积金贷', institution: '建设银行',
    minRate: 3.45, maxRate: 5.6, minAmount: 5, maxAmount: 50,
    loanTerm: '6-60个月', repaymentMethod: '等额本息/先息后本',
    conditions: '公积金连续缴存≥12个月；基数≥3000元；征信无当前逾期',
    status: 'active', createdAt: '2026-08-08 14:20:00', source: 'image',
  },
  {
    id: 'p003', productName: '工商银行融e借', institution: '工商银行',
    minRate: 3.6, maxRate: 6.0, minAmount: 2, maxAmount: 80,
    loanTerm: '6-36个月', repaymentMethod: '等额本息',
    conditions: '年龄18-60周岁；代发工资客户优先；负债率≤50%',
    status: 'active', createdAt: '2026-08-05 10:15:00', source: 'pdf',
  },
  {
    id: 'p004', productName: '农业银行网捷贷', institution: '农业银行',
    minRate: 3.8, maxRate: 6.5, minAmount: 1, maxAmount: 20,
    loanTerm: '12-36个月', repaymentMethod: '等额本息',
    conditions: '年龄20-55周岁；月收入≥3000元；征信良好',
    status: 'disabled', createdAt: '2026-07-28 16:40:00', source: 'text',
  },
  {
    id: 'p005', productName: '浦发银行点贷', institution: '浦发银行',
    minRate: 5.2, maxRate: 9.0, minAmount: 1, maxAmount: 30,
    loanTerm: '6-36个月', repaymentMethod: '等额本息',
    conditions: '年龄22-50周岁；有稳定工作；负债率≤60%',
    status: 'active', createdAt: '2026-08-12 11:00:00', source: 'voice',
  },
]

const seedCustomers = [
  {
    id: 'c001', name: '张明', phone: '138****6688', idCard: '310***********1234',
    age: 32, gender: '男', source: 'friend', city: '上海', maritalStatus: '已婚', education: '本科',
    monthlyIncome: 15000, housingFundBase: 3500, totalDebt: 80000, creditCardUsage: 45,
    queryCount1m: 2, queryCount3m: 5, queryCount6m: 8, maxOverdueMonths: 0,
    propertyValue: 280, hasMortgage: false, carValue: 15, expectedAmount: 20, expectedRate: 5.0,
    employer: '上海某科技有限公司', position: '产品经理',
    materials: [
      { id: 'm001', type: '身份证', source: 'upload', time: '2026-08-15 10:30', confidence: 0.99 },
      { id: 'm002', type: '银行流水', source: 'upload', time: '2026-08-15 10:32', confidence: 0.95 },
      { id: 'm003', type: '征信报告', source: 'photo', time: '2026-08-15 10:35', confidence: 0.92 },
    ],
    createdAt: '2026-08-15 10:25:00',
  },
  {
    id: 'c002', name: '李芳', phone: '139****2233', idCard: '420***********5678',
    age: 28, gender: '女', source: 'online', city: '北京', maritalStatus: '未婚', education: '硕士',
    monthlyIncome: 22000, housingFundBase: 5000, totalDebt: 30000, creditCardUsage: 20,
    queryCount1m: 1, queryCount3m: 2, queryCount6m: 3, maxOverdueMonths: 0,
    propertyValue: 0, hasMortgage: false, carValue: 0, expectedAmount: 15, expectedRate: 4.0,
    employer: '北京某互联网公司', position: '高级运营',
    materials: [
      { id: 'm004', type: '身份证', source: 'upload', time: '2026-08-14 14:00', confidence: 0.99 },
      { id: 'm005', type: '工资流水', source: 'upload', time: '2026-08-14 14:05', confidence: 0.97 },
    ],
    createdAt: '2026-08-14 13:50:00',
  },
  {
    id: 'c003', name: '王强', phone: '136****4455', idCard: '510***********9012',
    age: 45, gender: '男', source: 'walkin', city: '成都', maritalStatus: '离异', education: '大专',
    monthlyIncome: 8000, housingFundBase: 1200, totalDebt: 150000, creditCardUsage: 75,
    queryCount1m: 4, queryCount3m: 9, queryCount6m: 12, maxOverdueMonths: 2,
    propertyValue: 150, hasMortgage: true, carValue: 8, expectedAmount: 10, expectedRate: 8.0,
    employer: '成都某制造企业', position: '车间主任',
    materials: [
      { id: 'm006', type: '身份证', source: 'photo', time: '2026-08-13 09:00', confidence: 0.98 },
      { id: 'm007', type: '征信报告', source: 'upload', time: '2026-08-13 09:10', confidence: 0.90 },
    ],
    createdAt: '2026-08-13 08:50:00',
  },
]

// 日程时间：相对今天的偏移（保证演示数据始终"新鲜"）
const _t = (offset, hh, mm) => {
  const d = new Date()
  d.setDate(d.getDate() + offset)
  d.setHours(hh, mm, 0, 0)
  return d.toISOString()
}

const seedSchedules = [
  {
    id: 'sch001', title: '与张总确认招商闪电贷额度',
    startTime: _t(0, 10, 0), endTime: _t(0, 11, 0), reminderTime: _t(0, 9, 30),
    priority: 'P0', type: 'meeting', location: '客户公司·星汇中心 A 座 18F',
    remark: '携带征信报告，重点沟通放款时效', customerId: 'c001', customerName: '张志远',
    done: false, source: 'text', createdAt: '2026-08-19 09:00:00',
  },
  {
    id: 'sch002', title: '回访建设银行李经理',
    startTime: _t(0, 14, 30), endTime: _t(0, 15, 30), reminderTime: _t(0, 14, 0),
    priority: 'P1', type: 'call', location: '电话',
    remark: '确认新一批公积金贷准入门槛调整', customerId: null, customerName: '',
    done: false, source: 'voice', createdAt: '2026-08-19 09:15:00',
  },
  {
    id: 'sch003', title: '整理本周客户匹配报告',
    startTime: _t(0, 17, 0), endTime: _t(0, 18, 0), reminderTime: null,
    priority: 'P2', type: 'task', location: '',
    remark: '汇总 12 个客户的最新匹配结果', customerId: null, customerName: '',
    done: false, source: 'text', createdAt: '2026-08-19 09:30:00',
  },
  {
    id: 'sch004', title: '提交陈女士贷款材料补充',
    startTime: _t(1, 10, 0), endTime: _t(1, 11, 0), reminderTime: _t(1, 9, 0),
    priority: 'P0', type: 'task', location: '线上提交',
    remark: '营业执照、流水、收入证明', customerId: 'c002', customerName: '陈雪',
    done: false, source: 'text', createdAt: '2026-08-19 10:00:00',
  },
  {
    id: 'sch005', title: '与王先生沟通负债优化方案',
    startTime: _t(2, 15, 0), endTime: _t(2, 16, 30), reminderTime: _t(2, 14, 30),
    priority: 'P1', type: 'meeting', location: '咖啡厅·星巴克中山店',
    remark: '推演报告备齐，重点对比前后产品', customerId: 'c003', customerName: '王浩',
    done: false, source: 'text', createdAt: '2026-08-19 10:30:00',
  },
  {
    id: 'sch006', title: '参加银行产品培训',
    startTime: _t(-2, 14, 0), endTime: _t(-2, 16, 0), reminderTime: _t(-2, 13, 30),
    priority: 'P2', type: 'meeting', location: '招行分行 3F 会议室',
    remark: '', customerId: null, customerName: '',
    done: true, source: 'text', createdAt: '2026-08-17 10:00:00',
  },
]

const seedSimulation = {
  id: 's001', customerId: 'c001', name: '收入提升+降负债推演', createdAt: '2026-08-16 15:30:00',
  adjustments: {
    monthlyIncome: { old: 15000, new: 25000 },
    totalDebt: { old: 80000, new: 50000 },
  },
  matchResult: {
    approved: [
      { productId: 'p002', productName: '建设银行公积金贷', reason: '月收入25000，公积金基数3500≥3000，符合准入' },
      { productId: 'p003', productName: '工商银行融e借', reason: '负债率降低至25%，符合≤50%要求' },
    ],
    rejected: [],
  },
}

export function seedIfEmpty() {
  const userCount = db.prepare('SELECT COUNT(*) AS n FROM users').get().n
  if (userCount > 0) return

  console.log('[seed] 首次启动，写入演示数据...')

  // 整体包在事务里：任一步失败全部回滚，保证种子数据完整
  const run = db.transaction(() => {
    // 用户
    const hash = bcrypt.hashSync(seedUser.password, 10)
    const info = db.prepare(
      'INSERT INTO users (phone, password_hash, name, role, created_at) VALUES (?, ?, ?, ?, ?)'
    ).run(seedUser.phone, hash, seedUser.name, seedUser.role, fmtDateTime())
    const userId = Number(info.lastInsertRowid)

    // 产品
    const insProduct = db.prepare(`
      INSERT INTO products (id, user_id, product_name, institution, min_rate, max_rate, min_amount, max_amount,
        loan_term, repayment_method, conditions, status, source, created_at)
      VALUES (@id, @userId, @productName, @institution, @minRate, @maxRate, @minAmount, @maxAmount,
        @loanTerm, @repaymentMethod, @conditions, @status, @source, @createdAt)`)

    for (const p of seedProducts) {
      insProduct.run({ ...p, userId })
    }

    // 客户 + 材料
    const insCustomer = db.prepare(`
      INSERT INTO customers (id, user_id, name, phone, id_card, age, gender, source, city, marital_status, education,
        occupation, remark, monthly_income, housing_fund_base, total_debt, credit_card_usage,
        query_count_1m, query_count_3m, query_count_6m, max_overdue_months, property_value, has_mortgage,
        car_value, expected_amount, expected_rate, employer, position, created_at, updated_at)
      VALUES (@id, @userId, @name, @phone, @idCard, @age, @gender, @source, @city, @maritalStatus, @education,
        @occupation, @remark, @monthlyIncome, @housingFundBase, @totalDebt, @creditCardUsage,
        @queryCount1m, @queryCount3m, @queryCount6m, @maxOverdueMonths, @propertyValue, @hasMortgage,
        @carValue, @expectedAmount, @expectedRate, @employer, @position, @createdAt, @createdAt)`)

    const insMaterial = db.prepare(`
      INSERT INTO materials (id, customer_id, type, source, confidence, created_at)
      VALUES (?, ?, ?, ?, ?, ?)`)

    for (const c of seedCustomers) {
      const { materials, ...custFields } = c
      insCustomer.run({ ...custFields, hasMortgage: c.hasMortgage ? 1 : 0, occupation: '', remark: '', userId })
      for (const m of materials) {
        insMaterial.run(m.id, c.id, m.type, m.source, m.confidence, m.time)
      }
    }

    // 推演记录
    db.prepare(`
      INSERT INTO simulations (id, user_id, customer_id, name, adjustments, match_result, created_at)
      VALUES (?, ?, ?, ?, ?, ?, ?)`)
      .run(seedSimulation.id, userId, seedSimulation.customerId, seedSimulation.name,
        JSON.stringify(seedSimulation.adjustments), JSON.stringify(seedSimulation.matchResult),
        seedSimulation.createdAt)

    // 日程
    const insSchedule = db.prepare(`
      INSERT INTO schedules (id, user_id, title, start_time, end_time, reminder_time, priority, type,
        location, remark, customer_id, customer_name, done, source, created_at)
      VALUES (@id, @userId, @title, @startTime, @endTime, @reminderTime, @priority, @type,
        @location, @remark, @customerId, @customerName, @done, @source, @createdAt)`)

    for (const s of seedSchedules) {
      insSchedule.run({ ...s, done: s.done ? 1 : 0, userId })
    }
  })

  run()
  console.log(`[seed] 完成：${seedProducts.length} 产品 / ${seedCustomers.length} 客户 / ${seedSchedules.length} 日程，账号 ${seedUser.phone}`)
}

// 直接运行本文件时可手动触发播种检查（node server/seed.js）
import { pathToFileURL } from 'node:url'
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  seedIfEmpty()
  console.log('[seed] 当前材料数：', getMaterialsByCustomer('c001').length)
}

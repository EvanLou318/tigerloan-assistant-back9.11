// ==================== SQLite 数据库层 ====================
// node:sqlite（Node 22 内置官方 SQLite）：同步 API，零原生编译依赖，
// 便于一键发布到无编译环境的沙箱。数据文件位于 server/data/loan.db。

import { DatabaseSync } from 'node:sqlite'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const dataDir = path.join(__dirname, 'data')
fs.mkdirSync(dataDir, { recursive: true })

export const db = new DatabaseSync(path.join(dataDir, 'loan.db'))

// ---------- better-sqlite3 兼容层 ----------
// 事务：db.transaction(fn) 返回可调用包装函数（BEGIN / COMMIT / ROLLBACK）
db.transaction = (fn) => (...args) => {
  db.exec('BEGIN')
  try {
    const result = fn(...args)
    db.exec('COMMIT')
    return result
  } catch (err) {
    db.exec('ROLLBACK')
    throw err
  }
}
// PRAGMA 设置类调用（本库仅用于 journal_mode / foreign_keys）
db.pragma = (sql) => {
  db.exec(`PRAGMA ${sql}`)
}

db.pragma('journal_mode = WAL')
db.pragma('foreign_keys = ON')

// ---------- 建表 ----------
db.exec(`
CREATE TABLE IF NOT EXISTS users (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  phone         TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  name          TEXT NOT NULL DEFAULT '',
  role          TEXT NOT NULL DEFAULT 'loan_manager',
  created_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS products (
  id               TEXT PRIMARY KEY,
  user_id          INTEGER NOT NULL,
  product_name     TEXT NOT NULL,
  institution      TEXT NOT NULL DEFAULT '',
  min_rate         REAL NOT NULL DEFAULT 0,
  max_rate         REAL NOT NULL DEFAULT 0,
  rate_type        TEXT NOT NULL DEFAULT 'annual',
  min_amount       REAL NOT NULL DEFAULT 0,
  max_amount       REAL NOT NULL DEFAULT 0,
  loan_term        TEXT NOT NULL DEFAULT '',
  repayment_method TEXT NOT NULL DEFAULT '',
  conditions       TEXT NOT NULL DEFAULT '',
  status           TEXT NOT NULL DEFAULT 'active',
  source           TEXT NOT NULL DEFAULT 'text',
  created_at       TEXT NOT NULL,
  updated_at       TEXT
);

CREATE TABLE IF NOT EXISTS customers (
  id                 TEXT PRIMARY KEY,
  user_id            INTEGER NOT NULL,
  name               TEXT NOT NULL,
  phone              TEXT NOT NULL DEFAULT '',
  id_card            TEXT NOT NULL DEFAULT '',
  age                INTEGER NOT NULL DEFAULT 0,
  gender             TEXT NOT NULL DEFAULT '',
  source             TEXT NOT NULL DEFAULT '',
  city               TEXT NOT NULL DEFAULT '',
  marital_status     TEXT NOT NULL DEFAULT '',
  education          TEXT NOT NULL DEFAULT '',
  occupation         TEXT NOT NULL DEFAULT '',
  remark             TEXT NOT NULL DEFAULT '',
  monthly_income     REAL NOT NULL DEFAULT 0,
  housing_fund_base  REAL NOT NULL DEFAULT 0,
  total_debt         REAL NOT NULL DEFAULT 0,
  credit_card_usage  REAL NOT NULL DEFAULT 0,
  query_count_1m     INTEGER NOT NULL DEFAULT 0,
  query_count_3m     INTEGER NOT NULL DEFAULT 0,
  query_count_6m     INTEGER NOT NULL DEFAULT 0,
  max_overdue_months INTEGER NOT NULL DEFAULT 0,
  property_value     REAL NOT NULL DEFAULT 0,
  has_mortgage       INTEGER NOT NULL DEFAULT 0,
  car_value          REAL NOT NULL DEFAULT 0,
  expected_amount    REAL NOT NULL DEFAULT 0,
  expected_rate      REAL NOT NULL DEFAULT 0,
  employer           TEXT NOT NULL DEFAULT '',
  position           TEXT NOT NULL DEFAULT '',
  created_at         TEXT NOT NULL,
  updated_at         TEXT
);

CREATE TABLE IF NOT EXISTS materials (
  id          TEXT PRIMARY KEY,
  customer_id TEXT NOT NULL,
  type        TEXT NOT NULL,
  source      TEXT NOT NULL DEFAULT 'upload',
  confidence  REAL NOT NULL DEFAULT 0.9,
  field_count INTEGER NOT NULL DEFAULT 0,
  source_name TEXT NOT NULL DEFAULT '',
  file_path   TEXT,
  created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS simulations (
  id           TEXT PRIMARY KEY,
  user_id      INTEGER NOT NULL,
  customer_id  TEXT NOT NULL,
  name         TEXT NOT NULL DEFAULT '',
  adjustments  TEXT NOT NULL,  -- JSON: { field: { old, new } }
  match_result TEXT NOT NULL,  -- JSON: { approved: [...], rejected: [...] }
  created_at   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS schedules (
  id            TEXT PRIMARY KEY,
  user_id       INTEGER NOT NULL,
  title         TEXT NOT NULL,
  start_time    TEXT NOT NULL,
  end_time      TEXT,
  reminder_time TEXT,
  priority      TEXT NOT NULL DEFAULT 'P1',
  type          TEXT NOT NULL DEFAULT 'task',
  location      TEXT NOT NULL DEFAULT '',
  remark        TEXT NOT NULL DEFAULT '',
  customer_id   TEXT,
  customer_name TEXT NOT NULL DEFAULT '',
  done          INTEGER NOT NULL DEFAULT 0,
  source        TEXT NOT NULL DEFAULT 'text',
  created_at    TEXT NOT NULL,
  updated_at    TEXT
);

CREATE INDEX IF NOT EXISTS idx_products_user    ON products(user_id);
CREATE INDEX IF NOT EXISTS idx_customers_user   ON customers(user_id);
CREATE INDEX IF NOT EXISTS idx_materials_cust   ON materials(customer_id);
CREATE INDEX IF NOT EXISTS idx_sim_user_cust    ON simulations(user_id, customer_id);
CREATE INDEX IF NOT EXISTS idx_schedules_user   ON schedules(user_id);

-- RBAC 角色权限模型 + 系统设置
CREATE TABLE IF NOT EXISTS roles (
  code        TEXT PRIMARY KEY,
  name        TEXT NOT NULL,
  description TEXT NOT NULL DEFAULT '',
  sort        INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS permissions (
  code   TEXT PRIMARY KEY,
  name   TEXT NOT NULL,
  module TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS role_permissions (
  role_code       TEXT NOT NULL,
  permission_code TEXT NOT NULL,
  PRIMARY KEY (role_code, permission_code)
);

CREATE TABLE IF NOT EXISTS settings (
  key   TEXT PRIMARY KEY,
  value TEXT NOT NULL
);

-- 三方服务供应商配置（大模型 / OCR / ASR，可后台切换服务商）
CREATE TABLE IF NOT EXISTS service_providers (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  category    TEXT NOT NULL,              -- llm | ocr | asr
  name        TEXT NOT NULL,              -- 展示名，如"通义千问"
  provider_type TEXT NOT NULL,            -- 协议/厂商类型，如 openai-compatible | tencent | aliyun | xfyun | custom
  base_url    TEXT NOT NULL DEFAULT '',
  api_key     TEXT NOT NULL DEFAULT '',   -- 存储明文，接口输出时脱敏
  secret_key  TEXT NOT NULL DEFAULT '',   -- 部分厂商需要（腾讯云等）
  model       TEXT NOT NULL DEFAULT '',   -- LLM 模型名
  extra       TEXT NOT NULL DEFAULT '{}', -- 预留扩展参数 JSON
  enabled     INTEGER NOT NULL DEFAULT 1,
  is_default  INTEGER NOT NULL DEFAULT 0, -- 分类内互斥：仅一个默认
  remark      TEXT NOT NULL DEFAULT '',
  created_at  TEXT NOT NULL,
  updated_at  TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sp_category ON service_providers(category);

-- 操作审计日志：权限/用户/设置/三方服务/客户删除等敏感操作留痕
CREATE TABLE IF NOT EXISTS audit_logs (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id    INTEGER NOT NULL,
  user_name  TEXT NOT NULL DEFAULT '',
  action     TEXT NOT NULL,               -- 动作码，如 user.create / role.perms_update
  target     TEXT NOT NULL DEFAULT '',    -- 操作对象简述，如 用户ID 3 / 角色 supervisor
  detail     TEXT NOT NULL DEFAULT '',    -- 补充说明（不含敏感明文）
  ip         TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_logs(action);
`)

// ---------- 轻量迁移：为已存在的旧库补齐后加的列 ----------
// CREATE TABLE IF NOT EXISTS 不会修改已有表，老库需要显式 ALTER
function ensureColumn(table, column, ddl) {
  const cols = db.prepare(`PRAGMA table_info(${table})`).all()
  if (!cols.some((c) => c.name === column)) {
    db.exec(`ALTER TABLE ${table} ADD COLUMN ${ddl}`)
  }
}
ensureColumn('products', 'rate_type', "rate_type TEXT NOT NULL DEFAULT 'annual'")

// ---------- 行 → 前端对象 映射（snake_case → camelCase） ----------

export function rowToProduct(r) {
  if (!r) return null
  return {
    id: r.id,
    productName: r.product_name,
    institution: r.institution,
    minRate: r.min_rate,
    maxRate: r.max_rate,
    rateType: r.rate_type || 'annual',
    minAmount: r.min_amount,
    maxAmount: r.max_amount,
    loanTerm: r.loan_term,
    repaymentMethod: r.repayment_method,
    conditions: r.conditions,
    status: r.status,
    source: r.source,
    createdAt: r.created_at,
    updatedAt: r.updated_at || r.created_at,
  }
}

export function rowToMaterial(r) {
  if (!r) return null
  return {
    id: r.id,
    type: r.type,
    source: r.source,
    confidence: r.confidence,
    fieldCount: r.field_count,
    sourceName: r.source_name,
    filePath: r.file_path,
    time: r.created_at,
  }
}

export function rowToCustomer(r, materials = []) {
  if (!r) return null
  return {
    id: r.id,
    name: r.name,
    phone: r.phone,
    idCard: r.id_card,
    age: r.age,
    gender: r.gender,
    source: r.source,
    city: r.city,
    maritalStatus: r.marital_status,
    education: r.education,
    occupation: r.occupation,
    remark: r.remark,
    monthlyIncome: r.monthly_income,
    housingFundBase: r.housing_fund_base,
    totalDebt: r.total_debt,
    creditCardUsage: r.credit_card_usage,
    queryCount1m: r.query_count_1m,
    queryCount3m: r.query_count_3m,
    queryCount6m: r.query_count_6m,
    maxOverdueMonths: r.max_overdue_months,
    propertyValue: r.property_value,
    hasMortgage: !!r.has_mortgage,
    carValue: r.car_value,
    expectedAmount: r.expected_amount,
    expectedRate: r.expected_rate,
    employer: r.employer,
    position: r.position,
    materials,
    createdAt: r.created_at,
    updatedAt: r.updated_at || r.created_at,
  }
}

export function rowToSchedule(r) {
  if (!r) return null
  return {
    id: r.id,
    title: r.title,
    startTime: r.start_time,
    endTime: r.end_time,
    reminderTime: r.reminder_time,
    priority: r.priority,
    type: r.type,
    location: r.location,
    remark: r.remark,
    customerId: r.customer_id,
    customerName: r.customer_name,
    done: !!r.done,
    source: r.source,
    createdAt: r.created_at,
    updatedAt: r.updated_at || r.created_at,
  }
}

export function rowToSimulation(r) {
  if (!r) return null
  return {
    id: r.id,
    customerId: r.customer_id,
    name: r.name,
    adjustments: JSON.parse(r.adjustments),
    matchResult: JSON.parse(r.match_result),
    createdAt: r.created_at,
  }
}

// ---------- 通用查询 ----------

export function getMaterialsByCustomer(customerId) {
  return db.prepare('SELECT * FROM materials WHERE customer_id = ? ORDER BY created_at DESC').all(customerId).map(rowToMaterial)
}

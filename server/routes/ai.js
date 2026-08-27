// ==================== AI 能力路由 ====================
// OCR / ASR / LLM 提取 / 匹配引擎 / AI 助理
// 全部经 Provider 层分发（mock / real），前端只依赖这里的接口契约

import { Router } from 'express'
import multer from 'multer'
import path from 'node:path'
import fs from 'node:fs'
import { fileURLToPath } from 'node:url'
import { db, rowToProduct } from '../db.js'
import { ok, fail, genId } from '../utils.js'
import { getAI } from '../services/ai/index.js'

const router = Router()

// ---------- 文件上传配置 ----------
const __dirname = path.dirname(fileURLToPath(import.meta.url))
const uploadsDir = path.join(__dirname, '..', 'uploads')
fs.mkdirSync(uploadsDir, { recursive: true })

const storage = multer.diskStorage({
  destination: (req, file, cb) => cb(null, uploadsDir),
  filename: (req, file, cb) => {
    const ext = (path.extname(file.originalname || '') || '').replace(/[^.\w]/g, '').slice(0, 10)
    cb(null, genId('f') + ext)
  },
})
const upload = multer({
  storage,
  limits: { fileSize: 20 * 1024 * 1024 }, // 20MB
})

// async 包装：Express 4 不会自动捕获 async 错误
const wrap = (fn) => (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next)

// ---------- OCR：按材料类型 ----------
const OCR_TYPES = {
  idcard: 'ocrIdCard',
  bankflow: 'ocrBankStatement',
  credit: 'ocrCreditReport',
  income: 'ocrIncomeProof',
  social: 'ocrSocialSecurity',
  property: 'ocrProperty',
  license: 'ocrBusinessLicense',
}

// POST /api/ai/ocr/:type   （multipart 可携带 file；或 JSON 传 { text } 模拟输入）
router.post('/ocr/:type', upload.single('file'), wrap(async (req, res) => {
  const fn = OCR_TYPES[req.params.type]
  if (!fn) return fail(res, 400, `不支持的材料类型：${req.params.type}`)

  const provider = getAI()
  const result = await provider[fn](req.file || null, req.body?.text)

  // 若有真实上传文件，附加可访问路径供前端存档
  if (req.file) result.filePath = `/uploads/${req.file.filename}`
  ok(res, result)
}))

// ---------- ASR：语音转文字 ----------
// POST /api/ai/asr   （multipart 可携带 audio；或 JSON 传 { text } 模拟转写结果）
router.post('/asr', upload.single('file'), wrap(async (req, res) => {
  const provider = getAI()
  const result = await provider.asr(req.file || null, req.body?.text)
  ok(res, result)
}))

// ---------- LLM 结构化提取 ----------

// POST /api/ai/extract/customer-voice  语音口述 → 建档字段（含逐字段置信度）
router.post('/extract/customer-voice', wrap(async (req, res) => {
  const { text } = req.body || {}
  ok(res, await getAI().extractCustomerFromVoice(text))
}))

// POST /api/ai/extract/voice  语音口述 → 客户画像摘要
router.post('/extract/voice', wrap(async (req, res) => {
  const { text } = req.body || {}
  ok(res, await getAI().extractFromVoice(text))
}))

// POST /api/ai/extract/product  产品资料（文本/PDF/图片）→ 结构化产品字段
router.post('/extract/product', upload.single('file'), wrap(async (req, res) => {
  const { text } = req.body || {}
  ok(res, await getAI().extractProduct(text || '', req.file || null))
}))

// POST /api/ai/extract/schedule  自然语言 → 日程结构化字段
router.post('/extract/schedule', wrap(async (req, res) => {
  const { text } = req.body || {}
  ok(res, await getAI().extractSchedule(text))
}))

// ---------- 匹配引擎 ----------

// POST /api/ai/match  一键匹配 / 场景推演共用
// body: { customer: {...客户画像（推演时可带调整值）}, products?: [...]（缺省取库内全部启用产品） }
router.post('/match', wrap(async (req, res) => {
  const { customer, products } = req.body || {}
  if (!customer) return fail(res, 400, '缺少客户画像数据')

  const productList = Array.isArray(products) && products.length > 0
    ? products
    : db.prepare("SELECT * FROM products WHERE user_id = ? AND status = 'active'").all(req.user.id).map(rowToProduct)

  ok(res, await getAI().match(customer, productList))
}))

// ---------- AI 助理 ----------

// POST /api/ai/assistant  意图识别 + 实体提取（NLU 层，读写由前端 store 执行）
router.post('/assistant', wrap(async (req, res) => {
  const { text } = req.body || {}
  if (!text?.trim()) return fail(res, 400, '请输入指令')
  ok(res, await getAI().assistantReply(text))
}))

// 统一错误处理（含 real provider 未配置的场景）
router.use((err, req, res, next) => {
  if (err instanceof multer.MulterError) {
    return fail(res, 400, `文件上传失败：${err.message}`)
  }
  console.error('[ai]', err)
  fail(res, 500, err.message || 'AI 服务处理失败')
})

export default router

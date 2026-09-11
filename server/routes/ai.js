// ==================== AI 能力路由 ====================
// OCR / ASR / LLM 提取 / 匹配引擎 / AI 助理
// 全部经 Provider 层分发（mock / real），前端只依赖这里的接口契约

import { Router } from 'express'
import multer from 'multer'
import path from 'node:path'
import fs from 'node:fs'
import { fileURLToPath } from 'node:url'
import { db, rowToProduct } from '../db.js'
import { ok, fail, genId, BizError } from '../utils.js'
import { getAI } from '../services/ai/index.js'

const router = Router()

// ---------- 文件上传配置 ----------
const __dirname = path.dirname(fileURLToPath(import.meta.url))
const uploadsDir = path.join(__dirname, '..', 'uploads')
fs.mkdirSync(uploadsDir, { recursive: true })

// 允许的扩展名 → 规范化的落盘后缀
// 本业务只需「证件/流水图片 + PDF + 语音」，别的一律拒绝，避免上传 .html/.js/.svg
// 之类可执行/可脚本化文件后被 /uploads 静态直链执行（存储型 XSS）。
const ALLOWED_EXT = {
  '.jpg': '.jpg',
  '.jpeg': '.jpg',
  '.png': '.png',
  '.webp': '.webp',
  '.heic': '.heic',
  '.bmp': '.bmp',
  '.pdf': '.pdf',
  '.mp3': '.mp3',
  '.wav': '.wav',
  '.m4a': '.m4a',
  '.aac': '.aac',
  '.ogg': '.ogg',
  '.amr': '.amr',
}
// 与扩展名对应的 MIME 前缀校验，双保险（扩展名可伪造，MIME 由客户端声明，两者都过才算数）
const ALLOWED_MIME_PREFIX = ['image/', 'application/pdf', 'audio/']

function safeExt(file) {
  const raw = path.extname(file.originalname || '').toLowerCase()
  return ALLOWED_EXT[raw] || null
}

const storage = multer.diskStorage({
  destination: (req, file, cb) => cb(null, uploadsDir),
  filename: (req, file, cb) => {
    // 后缀只从白名单映射里取，不信客户端原始字符串
    const ext = safeExt(file) || '.bin'
    cb(null, genId('f') + ext)
  },
})

const upload = multer({
  storage,
  limits: { fileSize: 20 * 1024 * 1024, files: 1 }, // 20MB
  fileFilter: (req, file, cb) => {
    const ext = safeExt(file)
    if (!ext) return cb(new multer.MulterError('LIMIT_UNEXPECTED_FILE', 'file'))
    const mimeOk = ALLOWED_MIME_PREFIX.some((p) => String(file.mimetype || '').startsWith(p))
    if (!mimeOk) return cb(new multer.MulterError('LIMIT_UNEXPECTED_FILE', 'file'))
    cb(null, true)
  },
})

// async 包装：Express 4 不会自动捕获 async 错误
const wrap = (fn) => (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next)

// ---------- 临时文件回收（仅 ASR 用） ----------
// 录音音频是一次性的：识别完即无价值，响应结束时无条件回收。
// 不能依赖 Provider 自己去删——异常路径、提前 return、甚至「成功但忘了删」
// 都会让 /uploads 无限增长。挂在 res finish 上，任何分支都会执行到。
// 注意 OCR 不能用这个：它要返回 filePath 供前端存档长期引用。
function reclaimTempFile(req, res, next) {
  const target = req.file?.path
  if (!target) return next()
  // finish 与 close 都会触发，加个幂等标记避免重复 unlink
  let done = false
  const cleanup = () => {
    if (done) return
    done = true
    fs.rm(target, { force: true }, () => {})
  }
  res.on('finish', cleanup)
  res.on('close', cleanup)
  next()
}

// multer 默认错误（如 The "cb" argument must be of type function）对用户毫无意义，
// 且 fileFilter 拒绝时只报 LIMIT_UNEXPECTED_FILE，看不出到底是格式还是大小的问题。
const MULTER_MSG = {
  LIMIT_FILE_SIZE: '上传文件超过 20MB 限制，请压缩后重试',
  LIMIT_FILE_COUNT: '一次只能上传一个文件',
  LIMIT_UNEXPECTED_FILE: '不支持的文件类型。语音请上传 wav/mp3/aac/amr/ogg 音频，材料请上传 jpg/png/webp/heic/bmp 图片或 PDF',
}
function multerErrors(err, req, res, next) {
  if (!err) return next()
  if (err instanceof multer.MulterError) {
    return next(new BizError(MULTER_MSG[err.code] || `上传失败：${err.message}`))
  }
  return next(err)
}

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
router.post('/ocr/:type', upload.single('file'), multerErrors, wrap(async (req, res) => {
  const fn = OCR_TYPES[req.params.type]
  if (!fn) return fail(res, 400, `不支持的材料类型：${req.params.type}`)

  const provider = getAI()
  const result = await provider[fn](req.file || null, req.body?.text)

  // 若有真实上传文件，附加可访问路径供前端存档
  if (req.file) result.filePath = `/uploads/${req.file.filename}`
  ok(res, result)
}))

// ---------- ASR：语音转文字 ----------
// POST /api/ai/asr
//   multipart: 字段 file（录音音频，wav/mp3/aac/amr/opus）+ 可选 sampleRate
//   JSON:      { text } 走演示链路（无录音时返回示例口述文本）
// 音频读进内存即失去价值：响应发出前同步回收。
// 放在 ok() 之前是为了严格保证「客户端拿到响应时文件已经不在了」；
// 极少数 Windows 句柄占用导致删失败时，由 res 上的 reclaimTempFile 兜底。
function reclaimNow(req) {
  const p = req.file?.path
  if (!p) return
  try {
    fs.rmSync(p, { force: true })
  } catch {
    /* 交给 reclaimTempFile 兜底 */
  }
}

router.post('/asr', upload.single('file'), multerErrors, reclaimTempFile, wrap(async (req, res) => {
  const provider = getAI()
  const opts = { sampleRate: Number(req.body?.sampleRate) || undefined }
  try {
    const result = await provider.asr(req.file || null, req.body?.text, opts)
    reclaimNow(req)
    ok(res, result)
  } catch (e) {
    reclaimNow(req)
    throw e
  }
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
// 附件只用于提取，提取完即无价值，与 ASR 一样走响应期回收
router.post('/extract/product', upload.single('file'), multerErrors, reclaimTempFile, wrap(async (req, res) => {
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
    if (err.code === 'LIMIT_FILE_SIZE') {
      return fail(res, 400, '文件过大：单个文件不能超过 20MB')
    }
    if (err.code === 'LIMIT_UNEXPECTED_FILE') {
      return fail(res, 400, '文件类型不支持：仅允许上传图片（jpg/png/webp/heic/bmp）、PDF 或语音（mp3/wav/m4a/aac/ogg/amr）')
    }
    return fail(res, 400, `文件上传失败：${err.message}`)
  }
  console.error('[ai]', err)
  fail(res, 500, err.message || 'AI 服务处理失败')
})

export default router

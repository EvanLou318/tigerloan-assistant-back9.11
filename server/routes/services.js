// ==================== 三方服务供应商管理 ====================
// 管理后台「三方服务」配置：大模型 / OCR / ASR 供应商的增删改、启停、
// 设默认（分类内互斥）、连通性测试。API Key 输出时脱敏，留空提交不覆盖。

import { Router } from 'express'
import { db } from '../db.js'
import { ok, fail, genId, fmtDateTime, BizError } from '../utils.js'
import { encryptSecret, decryptSecret } from '../secureStore.js'
import { requirePerm } from '../middleware/auth.js'
import { writeAudit } from '../audit.js'
import {
  SERVICE_CATEGORIES,
  isValidCategory,
  listProviders,
  getCategoryRuntime,
  getActiveProvider,
  callLLM,
} from '../services/ai/registry.js'
import * as aliyun from '../services/ai/aliyun.js'

const router = Router()

const wrap = (fn) => (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next)

// 供应商类型选项（前端下拉 + 校验共用）
const PROVIDER_TYPES = {
  llm: ['openai-compatible', 'anthropic', 'custom'],
  ocr: ['tencent', 'aliyun', 'xfyun', 'baidu', 'custom'],
  asr: ['tencent', 'xfyun', 'aliyun', 'custom'],
}

// ---------- 输出脱敏 ----------
function maskKey(key) {
  if (!key) return ''
  if (key.length <= 8) return '****'
  return `${key.slice(0, 4)}****${key.slice(-4)}`
}

// ---------- extra 扩展字段 ----------
// extra 存厂商特有参数，当前用于阿里云 ASR 的 appkey。
// 输出时同样脱敏：appkey 与 AccessToken 都属于可直接调接口的凭证。
function safeExtra(text) {
  try {
    return JSON.parse(text || '{}')
  } catch {
    return {}
  }
}

function rowOut(r) {
  // 凭证落库为密文（enc:v1:），出参时解密后再脱敏；extra.appkey 同理
  const apiKey = decryptSecret(r.api_key)
  const extra = safeExtra(r.extra)
  const appKey = decryptSecret(extra.appkey)
  return {
    id: r.id,
    category: r.category,
    name: r.name,
    providerType: r.provider_type,
    baseUrl: r.base_url,
    apiKeyMasked: maskKey(apiKey),
    hasKey: !!apiKey,
    hasSecret: !!r.secret_key,
    model: r.model,
    appKeyMasked: appKey ? maskKey(appKey) : '',
    hasAppKey: !!appKey,
    // 视觉模型名（非凭证，明文展示，用于图片/材料识别）
    visionModel: extra.visionModel || '',
    enabled: !!r.enabled,
    isDefault: !!r.is_default,
    remark: r.remark,
    createdAt: r.created_at,
    updatedAt: r.updated_at,
  }
}

// GET /api/services  供应商列表（按分类分组）
router.get('/', requirePerm('admin.services.view'), (req, res) => {
  const groups = SERVICE_CATEGORIES.map((c) => {
    const rows = db
      .prepare('SELECT * FROM service_providers WHERE category = ? ORDER BY is_default DESC, created_at ASC')
      .all(c.code)
    const runtime = getCategoryRuntime(c.code)
    return {
      category: c.code,
      name: c.name,
      desc: c.desc,
      needsModel: c.needsModel,
      providerTypes: PROVIDER_TYPES[c.code] || ['custom'],
      mode: runtime.mode, // real | mock
      activeProvider: runtime.provider
        ? { id: runtime.provider.id, name: runtime.provider.name, baseUrl: runtime.provider.baseUrl, model: runtime.provider.model }
        : null,
      providers: rows.map(rowOut),
    }
  })
  ok(res, groups)
})

// POST /api/services  新增供应商
router.post('/', requirePerm('admin.services.manage'), wrap(async (req, res) => {
  const b = req.body || {}
  const { category, name, providerType, baseUrl, apiKey, secretKey, model, enabled, isDefault, remark } = b

  if (!isValidCategory(category)) throw new BizError('服务分类不正确（llm / ocr / asr）')
  if (!name?.trim()) throw new BizError('请填写供应商名称')
  const types = PROVIDER_TYPES[category] || []
  if (providerType && !types.includes(providerType)) {
    throw new BizError(`该分类支持的类型：${types.join(' / ')}`)
  }
  if (category === 'llm' && isDefault && !apiKey) {
    throw new BizError('设为默认的 LLM 供应商必须填写 API Key')
  }
  if (category === 'asr' && providerType === 'aliyun' && !b.appkey) {
    throw new BizError('阿里云 ASR 必须填写 AppKey')
  }

  const now = fmtDateTime()
  const setDefault = isDefault && apiKey ? 1 : 0
  if (setDefault) {
    db.prepare('UPDATE service_providers SET is_default = 0 WHERE category = ?').run(category)
  }
  const info = db
    .prepare(`INSERT INTO service_providers (category, name, provider_type, base_url, api_key, secret_key, model, extra, enabled, is_default, remark, created_at, updated_at)
              VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`)
    .run(category, name.trim(), providerType || 'custom', baseUrl || '', encryptSecret(apiKey || ''), encryptSecret(secretKey || ''), model || '', JSON.stringify({ appkey: encryptSecret(b.appkey || ''), ...(b.visionModel ? { visionModel: b.visionModel.trim() } : {}) }), enabled === false ? 0 : 1, setDefault, remark || '', now, now)
  writeAudit(req, 'service.create', `${name.trim()}（${category}）`, `类型 ${providerType || 'custom'}${setDefault ? '，已设为默认' : ''}`)
  ok(res, { id: info.lastInsertRowid })
}))

// PUT /api/services/:id  更新（apiKey/secretKey 留空 = 保持不变）
router.put('/:id', requirePerm('admin.services.manage'), wrap(async (req, res) => {
  const row = db.prepare('SELECT * FROM service_providers WHERE id = ?').get(req.params.id)
  if (!row) throw new BizError('供应商不存在', 404)
  const b = req.body || {}

  if (b.name !== undefined && !b.name?.trim()) throw new BizError('名称不能为空')
  if (b.category !== undefined && b.category !== row.category) throw new BizError('不允许修改分类，请新建')

  const nextKey = b.apiKey === '' || b.apiKey === undefined ? row.api_key : encryptSecret(b.apiKey)
  const nextSecret = b.secretKey === '' || b.secretKey === undefined ? row.secret_key : encryptSecret(b.secretKey)
  const nextEnabled = b.enabled === undefined ? row.enabled : b.enabled ? 1 : 0
  let nextDefault = b.isDefault === undefined ? row.is_default : b.isDefault ? 1 : 0

  if (nextDefault && (!nextKey || !nextEnabled)) {
    throw new BizError('默认供应商必须启用且已配置 API Key')
  }
  if (nextDefault && !row.is_default) {
    db.prepare('UPDATE service_providers SET is_default = 0 WHERE category = ?').run(row.category)
  }
  // 取消默认时至少保证不出现"全无默认"导致配置失效——允许，运行时会回退 mock

  // extra 合并写入：只更新传了 appkey / visionModel 的情况，留空保持原值
  const curExtra = safeExtra(row.extra)
  const nextExtra = JSON.stringify({
    ...curExtra,
    ...(b.appkey !== undefined ? { appkey: encryptSecret(b.appkey) } : {}),
    ...(b.visionModel !== undefined ? { visionModel: b.visionModel.trim() } : {}),
  })

  db.prepare(`UPDATE service_providers SET name = ?, provider_type = ?, base_url = ?, api_key = ?, secret_key = ?, model = ?, extra = ?, enabled = ?, is_default = ?, remark = ?, updated_at = ? WHERE id = ?`)
    .run(
      b.name !== undefined ? b.name.trim() : row.name,
      b.providerType || row.provider_type,
      b.baseUrl !== undefined ? b.baseUrl : row.base_url,
      nextKey,
      nextSecret,
      b.model !== undefined ? b.model : row.model,
      nextExtra,
      nextEnabled,
      nextDefault,
      b.remark !== undefined ? b.remark : row.remark,
      fmtDateTime(),
      row.id
    )
  writeAudit(req, 'service.update', `${row.name}（${row.category}）`, Object.keys(b).filter((k) => k !== 'apiKey' && k !== 'secretKey').join('、') || '无字段变更')
  ok(res, { id: row.id })
}))

// POST /api/services/:id/default  设为分类默认（互斥）
router.post('/:id/default', requirePerm('admin.services.manage'), (req, res) => {
  const row = db.prepare('SELECT * FROM service_providers WHERE id = ?').get(req.params.id)
  if (!row) throw new BizError('供应商不存在', 404)
  if (!row.enabled) throw new BizError('请先启用该供应商')
  if (!row.api_key) throw new BizError('请先填写 API Key')

  const tx = db.transaction(() => {
    db.prepare('UPDATE service_providers SET is_default = 0 WHERE category = ?').run(row.category)
    db.prepare('UPDATE service_providers SET is_default = 1, updated_at = ? WHERE id = ?').run(fmtDateTime(), row.id)
  })
  tx()
  writeAudit(req, 'service.default', `${row.name}（${row.category}）`, '设为分类默认供应商')
  ok(res, { id: row.id, category: row.category })
})

// DELETE /api/services/:id
router.delete('/:id', requirePerm('admin.services.manage'), (req, res) => {
  const row = db.prepare('SELECT * FROM service_providers WHERE id = ?').get(req.params.id)
  if (!row) throw new BizError('供应商不存在', 404)
  db.prepare('DELETE FROM service_providers WHERE id = ?').run(row.id)
  writeAudit(req, 'service.delete', `${row.name}（${row.category}）`)
  ok(res, { id: row.id })
})

// POST /api/services/:id/test  连通性测试
router.post('/:id/test', requirePerm('admin.services.view'), wrap(async (req, res) => {
  const row = db.prepare('SELECT * FROM service_providers WHERE id = ?').get(req.params.id)
  if (!row) throw new BizError('供应商不存在', 404)

  const apiKey = decryptSecret(row.api_key)
  if (!apiKey) return ok(res, { pass: false, message: '未配置 API Key' })

  try {
    if (row.category === 'llm') {
      // 真实调用一次 chat/completions（1 token 级请求）
      const started = Date.now()
      const baseUrl = (row.base_url || 'https://api.openai.com/v1').replace(/\/+$/, '')
      const resp = await fetch(`${baseUrl}/chat/completions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${apiKey}` },
        body: JSON.stringify({ model: row.model || 'gpt-4o-mini', messages: [{ role: 'user', content: 'ping' }], max_tokens: 1 }),
        signal: AbortSignal.timeout(15000),
      })
      if (resp.ok) {
        return ok(res, { pass: true, message: `连接成功（${Date.now() - started}ms，模型 ${row.model || '默认'}）` })
      }
      const detail = await resp.text().catch(() => '')
      return ok(res, { pass: false, message: `HTTP ${resp.status}：${detail.slice(0, 120)}` })
    }

    // ASR：阿里云智能语音交互已接入，做真实鉴权校验
    if (row.category === 'asr' && row.provider_type === 'aliyun') {
      const appkey = decryptSecret(safeExtra(row.extra).appkey)
      if (!appkey) return ok(res, { pass: false, message: '未配置 AppKey' })
      const started = Date.now()
      await aliyun.ping({ token: apiKey, appkey, endpoint: row.base_url || undefined })
      return ok(res, {
        pass: true,
        message: `阿里云鉴权通过（${Date.now() - started}ms）。AccessToken 为控制台临时凭证，约 24 小时后失效，届时请在此重新更新。`,
      })
    }

    // OCR / 其它厂商 ASR：探测 base_url 可达性（厂商 SDK 未接入前的基本校验）
    if (row.category === 'ocr') {
      return ok(res, {
        pass: !!row.base_url || !!row.api_key,
        message: row.base_url
          ? `凭证与地址已配置。注意：${row.provider_type} 类型的 OCR 调用尚未在代码中接入，配置后材料识别会以演示数据代替并明确标注`
          : '凭证已配置。注意：OCR 厂商调用尚未在代码中接入，配置后材料识别会以演示数据代替并明确标注',
      })
    }
    if (row.base_url) {
      const started = Date.now()
      const resp = await fetch(row.base_url, { method: 'HEAD', signal: AbortSignal.timeout(10000) }).catch(() => null)
      if (resp && resp.ok) {
        return ok(res, { pass: true, message: `服务地址可达（${Date.now() - started}ms）。注意：该分类真实调用尚未在代码中接入` })
      }
      return ok(res, { pass: false, message: `服务地址探测失败（HTTP ${resp ? resp.status : '不可达'}）` })
    }
    return ok(res, { pass: true, message: '凭证已配置。该分类真实调用尚未在代码中接入' })
  } catch (e) {
    return ok(res, { pass: false, message: e.message || '测试失败' })
  }
}))

// GET /api/services/active  当前各分类运行时（供调试/展示）
router.get('/active', requirePerm('admin.services.view'), (req, res) => {
  ok(res, SERVICE_CATEGORIES.map((c) => {
    const rt = getCategoryRuntime(c.code)
    return {
      category: c.code,
      mode: rt.mode,
      provider: rt.provider ? { id: rt.provider.id, name: rt.provider.name } : null,
    }
  }))
})

export default router

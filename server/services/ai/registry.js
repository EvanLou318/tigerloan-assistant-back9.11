// ==================== 三方服务供应商注册表 ====================
// 统一读取 service_providers 表（管理后台可配置），为 AI 运行时提供：
//   1. 每个分类（llm/ocr/asr）当前生效的供应商配置
//   2. 每个分类的运行模式：real（已配置可用供应商）| mock（未配置，走模拟）
//   3. callLLM：OpenAI 兼容协议调用封装（真实 LLM 接入点）
// 换服务商 = 后台改配置 + 设默认，代码零改动

import { db } from '../../db.js'
import { config } from '../../config.js'
import { decryptSecret } from '../../secureStore.js'

// ---------- 分类目录（管理后台与前端共用语义） ----------
export const SERVICE_CATEGORIES = [
  {
    code: 'llm',
    name: '大模型（LLM）',
    desc: '结构化提取 / AI 匹配 / 智能助理，走 OpenAI 兼容协议',
    needsModel: true,
  },
  {
    code: 'ocr',
    name: '文字识别（OCR）',
    desc: '身份证 / 流水 / 征信报告等材料识别',
    needsModel: false,
  },
  {
    code: 'asr',
    name: '语音识别（ASR）',
    desc: '语音录入 / 口述建档的转写',
    needsModel: false,
  },
]

const CATEGORIES = new Set(SERVICE_CATEGORIES.map((c) => c.code))

export function isValidCategory(c) {
  return CATEGORIES.has(c)
}

function rowToProvider(r) {
  const extra = safeParse(r.extra)
  return {
    id: r.id,
    category: r.category,
    name: r.name,
    providerType: r.provider_type,
    baseUrl: r.base_url,
    // 凭证落库为密文（enc:v1:），调用时解密
    apiKey: decryptSecret(r.api_key),
    secretKey: decryptSecret(r.secret_key),
    model: r.model,
    extra: { ...extra, ...(extra.appkey ? { appkey: decryptSecret(extra.appkey) } : {}) },
    enabled: !!r.enabled,
    isDefault: !!r.is_default,
    remark: r.remark,
    createdAt: r.created_at,
    updatedAt: r.updated_at,
  }
}

function safeParse(text) {
  try {
    return JSON.parse(text || '{}')
  } catch {
    return {}
  }
}

// ---------- 查询 ----------

// 某分类全部供应商（按默认优先、创建时间排序）
export function listProviders(category) {
  const rows = db
    .prepare('SELECT * FROM service_providers WHERE category = ? ORDER BY is_default DESC, created_at ASC')
    .all(category)
  return rows.map(rowToProvider)
}

// 某分类当前生效的供应商（默认且启用且已配置 key）
export function getActiveProvider(category) {
  const rows = db
    .prepare('SELECT * FROM service_providers WHERE category = ? AND is_default = 1 AND enabled = 1')
    .all(category)
  for (const r of rows) {
    const p = rowToProvider(r)
    if (p.apiKey) return p
  }
  // 没有满足条件的默认项时，取第一个启用且有 key 的（容错）
  const fallback = db
    .prepare('SELECT * FROM service_providers WHERE category = ? AND enabled = 1')
    .all(category)
  for (const r of fallback) {
    const p = rowToProvider(r)
    if (p.apiKey) return p
  }
  return null
}

// 环境变量兜底：后台未配置时，仍可用 env 里的 key（保留原有部署习惯）
function envFallback(category) {
  if (category === 'llm' && config.llmApiKey) {
    return {
      id: 0,
      category: 'llm',
      name: '环境变量配置',
      providerType: 'openai-compatible',
      baseUrl: config.llmBaseUrl,
      apiKey: config.llmApiKey,
      secretKey: '',
      model: config.llmModel,
      extra: {},
      enabled: true,
      isDefault: false,
      remark: '来自环境变量 LLM_*',
    }
  }
  if (category === 'ocr' && config.ocrApiKey) {
    return {
      id: 0, category: 'ocr', name: '环境变量配置', providerType: 'custom',
      baseUrl: '', apiKey: config.ocrApiKey, secretKey: config.ocrSecretKey, model: '',
      extra: {}, enabled: true, isDefault: false, remark: '来自环境变量 OCR_*',
    }
  }
  if (category === 'asr' && config.asrApiKey) {
    return {
      id: 0, category: 'asr', name: '环境变量配置', providerType: 'custom',
      baseUrl: '', apiKey: config.asrApiKey, secretKey: config.asrSecretKey, model: '',
      extra: {}, enabled: true, isDefault: false, remark: '来自环境变量 ASR_*',
    }
  }
  return null
}

// 某分类运行模式（real / mock）与生效供应商（供状态接口与 AI 工厂使用）
export function getCategoryRuntime(category) {
  const provider = getActiveProvider(category) || envFallback(category)
  return {
    category,
    mode: provider ? 'real' : 'mock',
    provider,
  }
}

// ---------- 真实调用：OpenAI 兼容协议 LLM ----------
// real.js 各 LLM 能力统一走这里；未配置时抛出明确错误。
async function chatCompletion(messages, options = {}) {
  const { provider } = getCategoryRuntime('llm')
  if (!provider) {
    throw new Error('大模型服务未配置：请在管理后台「三方服务」中添加并启用 LLM 供应商')
  }
  const baseUrl = (provider.baseUrl || 'https://api.openai.com/v1').replace(/\/+$/, '')
  const res = await fetch(`${baseUrl}/chat/completions`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${provider.apiKey}`,
    },
    body: JSON.stringify({
      model: options.model || provider.model || 'gpt-4o-mini',
      messages,
      temperature: options.temperature ?? 0.2,
      ...(options.responseFormat ? { response_format: options.responseFormat } : {}),
    }),
    signal: AbortSignal.timeout(options.timeout || 60000),
  })
  if (!res.ok) {
    const detail = await res.text().catch(() => '')
    throw new Error(`LLM 服务返回 ${res.status}：${detail.slice(0, 200)}`)
  }
  const json = await res.json()
  return json.choices?.[0]?.message?.content ?? ''
}

export async function callLLM(messages, options = {}) {
  return chatCompletion(messages, options)
}

// 视觉调用：OpenAI 兼容 image_url 块（DeepSeek 用 deepseek-v4-flash-vision-exp，
// 可在供应商 extra.visionModel 里覆盖模型名）。图片只能出现在 user 消息中。
export async function callLLMVision({ system, text, imageDataUrl, temperature = 0.1 }) {
  const { provider } = getCategoryRuntime('llm')
  const messages = [
    { role: 'system', content: system },
    {
      role: 'user',
      content: [
        { type: 'text', text },
        { type: 'image_url', image_url: { url: imageDataUrl, detail: 'high' } },
      ],
    },
  ]
  return chatCompletion(messages, {
    model: provider?.extra?.visionModel || 'deepseek-v4-flash-vision-exp',
    temperature,
  })
}

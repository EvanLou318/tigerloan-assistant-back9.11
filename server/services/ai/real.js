// ==================== AI Real Provider ====================
// 真实 AI 服务接入层：接口签名与 mock.js 完全一致
//
// 【运行前提】
//   LLM 能力：在管理后台「三方服务」配置一个 OpenAI 兼容协议供应商（base_url /
//     api_key / model）并设为默认即可，本文件通过 registry.callLLM 自动使用该配置。
//     也可继续用环境变量（AI_PROVIDER=real + LLM_*）。
//   OCR / ASR：厂商协议差异大（腾讯云需签名、讯飞 WebSocket 等），保留 TODO，
//     供应商账号在后台「三方服务」配置后，在下方对应位置实现真实调用即可。
//
// 换服务商 = 后台改配置，本文件与前端均零改动。

import { callLLM } from './registry.js'

// ---------- 工具：LLM 结构化 JSON 输出 ----------
async function askJSON(system, user) {
  const content = await callLLM(
    [
      { role: 'system', content: `${system}\n只输出一个合法的 JSON 对象，不要输出任何其他文字或代码块标记。` },
      { role: 'user', content: user },
    ],
    { temperature: 0.1, responseFormat: { type: 'json_object' } }
  )
  const cleaned = content.replace(/^```(?:json)?\s*/i, '').replace(/\s*```$/, '').trim()
  try {
    return JSON.parse(cleaned)
  } catch {
    const m = cleaned.match(/\{[\s\S]*\}/)
    if (m) return JSON.parse(m[0])
    throw new Error('大模型返回的不是合法 JSON，请检查模型是否支持 JSON 输出')
  }
}

function todayISO(d = new Date()) {
  return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString()
}

// ---------- OCR ----------
// TODO: 接入真实 OCR（如腾讯云通用文字识别 / 阿里云读光 / 内部 OCR 网关）
//   供应商账号已在管理后台「三方服务」配置，可用 getActiveProvider('ocr') 取得
//   { baseUrl, apiKey, secretKey, providerType }，按厂商协议调用后
//   将返回结果映射为与 mock 相同的结构：{ success, data, confidence, source }
const ocrNotReady = (service) => {
  throw new Error(`OCR 真实调用尚未接入：${service} 的供应商账号已在后台配置，请在 server/services/ai/real.js 对应 TODO 处实现厂商调用`)
}
export const ocrIdCard = async (file) => ocrNotReady('身份证 OCR')
export const ocrBankStatement = async (file) => ocrNotReady('银行流水 OCR')
export const ocrCreditReport = async (file) => ocrNotReady('征信报告 OCR')
export const ocrIncomeProof = async (file) => ocrNotReady('收入证明 OCR')
export const ocrSocialSecurity = async (file) => ocrNotReady('社保公积金 OCR')
export const ocrProperty = async (file) => ocrNotReady('房产证 OCR')
export const ocrBusinessLicense = async (file) => ocrNotReady('营业执照 OCR')

// ---------- ASR ----------
// TODO: 接入真实 ASR（腾讯云一句话识别 / 讯飞语音听写），传入音频 Buffer
export const asr = async (file, fallbackText) => {
  if (fallbackText) return { success: true, text: fallbackText, confidence: 0.99, source: 'ASR' }
  throw new Error('ASR 真实调用尚未接入：请在 real.js 实现厂商调用（音频文件由 multer 落盘）')
}

// ---------- LLM 结构化提取（已可用：配置供应商即生效） ----------

export const extractFromVoice = async (text) => {
  const j = await askJSON(
    '你是贷款客户资料提取助手。从语音转写文本中提取客户画像字段，提取不到的字段填 null。',
    `文本：${text}\n输出 JSON：{"name":"","gender":"男/女/null","age":0,"city":"","employer":"","position":"","monthlyIncome":0,"housingFundBase":0,"propertyValue":0,"hasMortgage":false,"carValue":0,"creditOverdue":false,"queryCount3m":0,"expectedAmount":0,"confidence":0.9}`
  )
  return { success: true, data: j, confidence: j.confidence || 0.9, source: '语音口述（LLM）' }
}

export const extractCustomerFromVoice = async (text) => {
  const j = await askJSON(
    '你是贷款客户建档助手。从语音转写文本提取建档字段，每个字段带置信度(0-1)，提取不到的字段省略。',
    `文本：${text}\n输出 JSON：{"data":{"name":{"value":"","confidence":0.9},"phone":{"value":"","confidence":0.9},"gender":{"value":"男","confidence":0.9},"age":{"value":0,"confidence":0.9},"city":{"value":"","confidence":0.9},"occupation":{"value":"","confidence":0.9},"source":{"value":"friend/telemarketing/walkin/online/referral/other","confidence":0.8},"remark":{"value":"","confidence":0.8},"employer":{"value":"","confidence":0.9},"monthlyIncome":{"value":0,"confidence":0.9}},"recognizedTypes":["客户基本信息"],"summary":"一句话总结","confidence":0.9}`
  )
  return {
    success: true,
    transcript: text,
    recognizedTypes: j.recognizedTypes || ['客户基本信息'],
    summary: j.summary || '已自动识别并提取字段',
    confidence: j.confidence || 0.9,
    source: '语音口述（LLM）',
    data: j.data || {},
  }
}

export const extractProduct = async (rawText) => {
  const j = await askJSON(
    '你是贷款产品信息提取助手。从产品文本/解析结果中提取产品要素。',
    `文本：${rawText || '（见附件，当前先按文本处理）'}\n输出 JSON：{"productName":"","institution":"","minRate":0,"maxRate":0,"minAmount":0,"maxAmount":0,"loanTerm":"如 6-60个月","repaymentMethod":"","conditions":"准入条件原文","confidence":0.9}`
  )
  return { success: true, data: j, confidence: j.confidence || 0.9, source: 'LLM 提取' }
}

export const extractSchedule = async (text) => {
  const j = await askJSON(
    '你是日程解析助手。把自然语言解析为日程字段。时间统一输出 ISO 格式（含时区偏移），未提及结束时间默认开始后 1 小时。',
    `当前时间：${todayISO()}\n文本：${text}\n输出 JSON：{"title":"","startTime":"","endTime":"","priority":"P0/P1/P2","type":"task/call/meeting","location":"","customerName":"","remark":"","confidence":0.9}`
  )
  return {
    data: {
      title: j.title || '新日程',
      startTime: j.startTime || todayISO(),
      endTime: j.endTime || todayISO(new Date(Date.now() + 3600000)),
      priority: j.priority || 'P1',
      type: j.type || 'task',
      location: j.location || '',
      customerName: j.customerName || '',
      remark: j.remark || '',
    },
    confidence: j.confidence || 0.9,
  }
}

// ---------- 匹配引擎（LLM 版） ----------
export const match = async (customer, products) => {
  const active = products.filter((p) => p.status === 'active')
  const j = await askJSON(
    '你是贷款产品准入匹配引擎。根据客户画像逐个判断产品准入条件是否满足。',
    `客户画像：${JSON.stringify(customer)}\n产品列表：${JSON.stringify(active.map((p) => ({ productId: p.id, productName: p.productName, institution: p.institution, minRate: p.minRate, maxRate: p.maxRate, maxAmount: p.maxAmount, loanTerm: p.loanTerm, conditions: p.conditions })))}\n输出 JSON：{"approved":[{"productId":"","productName":"","institution":"","minRate":0,"maxRate":0,"maxAmount":0,"loanTerm":"","reasons":["满足的具体条件"]}],"rejected":[{"productId":"","productName":"","institution":"","failedConditions":[{"condition":"不满足的条件","value":"客户实际值","suggestion":"优化建议"}]}]}\n要求：approved 按 minRate 从低到高；每个产品必须出现在且仅出现在一个分组中。`
  )
  return {
    approved: (j.approved || []).map((p) => ({
      ...p,
      reasons: Array.isArray(p.reasons) ? p.reasons : [p.reasons || '符合准入条件'],
    })),
    rejected: (j.rejected || []).map((p) => ({
      ...p,
      failedConditions: p.failedConditions || [],
    })),
  }
}

// ---------- AI 助理（LLM 意图识别 + 回复） ----------
export const assistantReply = async (text) => {
  const j = await askJSON(
    '你是贷款经理的智能助理。识别用户意图并给出确认式回复。可选意图：schedule_create（创建日程）、customer_create（新建客户）、customer_update（更新客户资料）、customer_query（查询客户）、match（产品匹配）、qa（咨询问答）。entities 中给出提取到的实体（姓名/手机号/时间/金额/字段等）。',
    `用户输入：${text}\n输出 JSON：{"intent":"schedule_create","entities":{},"reply":"一句话确认回复"}`
  )
  return {
    intent: j.intent || 'qa',
    entities: { ...(j.entities || {}), rawText: text },
    reply: j.reply || '好的，请补充更多信息。',
  }
}

export const realProvider = {
  name: 'real',
  ocrIdCard,
  ocrBankStatement,
  ocrCreditReport,
  ocrIncomeProof,
  ocrSocialSecurity,
  ocrProperty,
  ocrBusinessLicense,
  asr,
  extractFromVoice,
  extractCustomerFromVoice,
  extractProduct,
  extractSchedule,
  match,
  assistantReply,
}

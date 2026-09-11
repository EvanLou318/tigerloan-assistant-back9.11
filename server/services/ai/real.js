// ==================== AI Real Provider ====================
// 真实 AI 服务接入层：接口签名与 mock.js 完全一致
//
// 【运行前提】
//   LLM 能力：在管理后台「三方服务」配置一个 OpenAI 兼容协议供应商（base_url /
//     api_key / model）并设为默认即可，本文件通过 registry.callLLM 自动使用该配置。
//     也可继续用环境变量（AI_PROVIDER=real + LLM_*）。
//   OCR：厂商协议差异大（腾讯云需签名、阿里云读光等），保留 TODO，
//     供应商账号在后台「三方服务」配置后，在下方对应位置实现真实调用即可。
//   ASR：已接入阿里云智能语音交互（一句话识别 REST API），见 ./aliyun.js。
//     后台「三方服务 - ASR」新增 provider_type=aliyun 的供应商：
//     api_key 填 AccessToken、extra.appkey 填项目 AppKey、base_url 留空用默认公网网关。
//
// 换服务商 = 后台改配置，本文件与前端均零改动。

import path from 'node:path'
import fs from 'node:fs'
import { callLLM, callLLMVision, getCategoryRuntime } from './registry.js'
import * as aliyun from './aliyun.js'
import { extractPdfText } from './pdf.js'
import { mockProvider } from './mock.js'

// ---------- 工具：LLM 结构化 JSON 输出 ----------
function parseJSONContent(content) {
  const cleaned = content.replace(/^```(?:json)?\s*/i, '').replace(/\s*```$/, '').trim()
  try {
    return JSON.parse(cleaned)
  } catch {
    const m = cleaned.match(/\{[\s\S]*\}/)
    if (m) return JSON.parse(m[0])
    throw new Error('大模型返回的不是合法 JSON，请检查模型是否支持 JSON 输出')
  }
}

async function askJSON(system, user) {
  const content = await callLLM(
    [
      { role: 'system', content: `${system}\n只输出一个合法的 JSON 对象，不要输出任何其他文字或代码块标记。` },
      { role: 'user', content: user },
    ],
    { temperature: 0.1, responseFormat: { type: 'json_object' } }
  )
  return parseJSONContent(content)
}

// ---------- 工具：图片附件 → base64 data URL（视觉模型输入） ----------
const VISION_MIME = { '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.gif': 'image/gif', '.webp': 'image/webp' }
function visionMimeOf(filename = '') {
  return VISION_MIME[path.extname(filename).toLowerCase()] || null
}
async function fileToDataUrl(file) {
  const mime = visionMimeOf(file.originalname)
  if (!mime) throw new Error(`视觉模型不支持的图片格式：${file.originalname}（支持 jpg/png/gif/webp）`)
  const buf = await fs.promises.readFile(file.path)
  if (!buf.length) throw new Error('图片文件为空')
  // 48MiB 请求体上限，20MB 上传限制下 base64 后 ~27MB，安全
  return `data:${mime};base64,${buf.toString('base64')}`
}

async function visionAskJSON(system, text, imageDataUrl) {
  const content = await callLLMVision({
    system: `${system}\n只输出一个合法的 JSON 对象，不要输出任何其他文字或代码块标记。`,
    text,
    imageDataUrl,
  })
  return parseJSONContent(content)
}

function todayISO(d = new Date()) {
  return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString()
}

// ---------- OCR ----------
// 走 DeepSeek 视觉模型（deepseek-v4-flash-vision-exp）直接读图，
// 字段结构对齐 mock.js 同名方法（Material.vue 的字段映射依赖这些键）。
// 视觉调用失败（网络/格式/配额）时降级为演示数据并标注原因，不打断业务。
const OCR_SPECS = {
  ocrIdCard: {
    label: '身份证',
    prompt: '识别身份证正反面照片。输出 JSON：{"name":"","idNumber":"18位","gender":"男/女","age":0,"city":"","ethnicity":"","birthDate":"YYYY-MM-DD","address":"","issueAuthority":"","validFrom":"YYYY-MM-DD","validTo":"YYYY-MM-DD","confidence":0.9}。某字段图中不存在就填空串或 null。',
  },
  ocrBankStatement: {
    label: '银行流水',
    prompt: '识别银行流水截图/照片。输出 JSON：{"bank":"","monthlyAvgIncome":0,"monthlyAvgExpense":0,"dailyAvgBalance":0,"period":"如 近6个月","largeTransactions":[{"date":"YYYY-MM-DD","amount":0,"type":"转入/转出","note":""}],"lateNightTransactions":[],"stability":"良好/一般/较差","confidence":0.9}。金额单位为元（元→数字，万→乘10000）。',
  },
  ocrCreditReport: {
    label: '征信报告',
    prompt: '识别个人征信报告照片。输出 JSON：{"queryCount1m":0,"queryCount3m":0,"queryCount6m":0,"queryCount12m":0,"maxOverdueMonths":0,"maxOverdueAmount":0,"currentOverdue":"无/有","totalDebt":0,"loanBalance":0,"creditCardUsed":0,"creditCardTotal":0,"creditCardUsage":0,"guaranteeBalance":0,"confidence":0.9}。金额单位为元，使用率单位为百分比数字。',
  },
  ocrIncomeProof: {
    label: '收入证明',
    prompt: '识别收入证明照片。输出 JSON：{"name":"被证明人姓名","employer":"","position":"","monthlyIncome":0,"incomeSource":"如 工资代发","companyPhone":"","confidence":0.9}。月收入单位为元（"1.5万"→15000）。',
  },
  ocrSocialSecurity: {
    label: '社保公积金',
    prompt: '识别社保/公积金缴存记录截图。输出 JSON：{"employer":"","housingFundBase":0,"socialSecurityBase":0,"housingFundMonths":0,"socialSecurityMonths":0,"confidence":0.9}。基数与月数均为数字。',
  },
  ocrProperty: {
    label: '房产证',
    prompt: '识别不动产权证/房产证照片。输出 JSON：{"propertyValue":0,"propertyArea":0,"propertyAddress":"","hasMortgage":false,"mortgageBalance":0,"confidence":0.9}。propertyValue 单位为万元（面积×单价或图示估价），面积单位平方米， mortgageBalance 单位为万元。',
  },
  ocrBusinessLicense: {
    label: '营业执照',
    prompt: '识别营业执照照片。输出 JSON：{"employer":"企业名称","position":"法定代表人","businessType":"","registeredCapital":0,"establishDate":"YYYY-MM-DD","businessStatus":"存续/注销等","confidence":0.9}。registeredCapital 单位为万元。',
  },
}

// 兜底：视觉调用失败时的演示数据（带原因说明）
async function ocrDemoFallback(method, reason) {
  const demo = await mockProvider[method]()
  return {
    ...demo,
    demo: true,
    source: `${demo.source}（演示）`,
    note: `${OCR_SPECS[method].label}视觉识别失败（${String(reason).slice(0, 120)}），已回退演示数据`,
  }
}

function makeVisionOcr(method) {
  return async (file) => {
    const spec = OCR_SPECS[method]
    let dataUrl
    try {
      if (!file) throw new Error('未提供图片文件')
      dataUrl = await fileToDataUrl(file)
    } catch (e) {
      return ocrDemoFallback(method, e.message)
    }
    try {
      const j = await visionAskJSON(
        `你是贷款材料识别助手，负责识别${spec.label}照片中的文字与数值。`,
        `请识别这张${spec.label}图片，严格按下述 schema 输出：${spec.prompt}`,
        dataUrl
      )
      const { confidence, ...data } = j
      if (!data || Object.keys(data).length === 0) throw new Error('未识别到任何字段')
      return { success: true, data, confidence: confidence || 0.9, source: `${spec.label}（DeepSeek Vision）` }
    } catch (e) {
      console.error('[ocr-vision] fail:', String(e.message).slice(0, 500))
      return ocrDemoFallback(method, e.message)
    }
  }
}
export const ocrIdCard = makeVisionOcr('ocrIdCard')
export const ocrBankStatement = makeVisionOcr('ocrBankStatement')
export const ocrCreditReport = makeVisionOcr('ocrCreditReport')
export const ocrIncomeProof = makeVisionOcr('ocrIncomeProof')
export const ocrSocialSecurity = makeVisionOcr('ocrSocialSecurity')
export const ocrProperty = makeVisionOcr('ocrProperty')
export const ocrBusinessLicense = makeVisionOcr('ocrBusinessLicense')

// ---------- ASR ----------
// 已接入阿里云智能语音交互「一句话识别」REST API。
// 约定：优先级 demo 文本 > 真实音频。无音频时回退到调用方传入的示例文本，
// 保证演示/测试链路不依赖真实录音设备。
export const asr = async (file, fallbackText, opts = {}) => {
  if (!file) {
    if (fallbackText) {
      return { success: true, text: fallbackText, confidence: 0.99, source: 'ASR' }
    }
    throw new Error('未提供音频文件，也没有示例文本')
  }

  const { provider } = getCategoryRuntime('asr')
  if (!provider) {
    throw new Error('ASR 服务未配置：请在管理后台「三方服务 - ASR」添加并启用供应商')
  }
  if (provider.providerType !== 'aliyun') {
    throw new Error(`暂未实现 ${provider.providerType} 类型的 ASR 调用，请改用 aliyun 或在 aliyun.js 同级新增适配器`)
  }

  const appkey = provider.extra?.appkey || provider.model
  const format = aliyun.formatFromExt(file.filename || file.originalname || '')
  if (!format) {
    throw new Error(`无法识别音频格式：${file.originalname}（阿里云支持 pcm/wav/mp3/aac/amr/opus）`)
  }

  const audio = await aliyun.readAudio(file.path)
  const r = await aliyun.recognize({
    token: provider.apiKey,
    appkey,
    audio,
    format,
    sampleRate: opts.sampleRate || provider.extra?.sampleRate || 16000,
    endpoint: provider.baseUrl || undefined,
  })

  return {
    success: true,
    text: r.text,
    // 阿里云不返回置信度，用任务 ID 表明是真实调用；前端按真实结果展示
    confidence: r.text ? 0.95 : 0,
    source: '阿里云智能语音交互',
    taskId: r.taskId,
    language: '普通话',
  }
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

export const extractProduct = async (rawText, file) => {
  let text = (rawText || '').trim()
  let source = 'LLM 提取'

  // 附件处理：PDF 抽出可读文本层后交给 LLM；图片走视觉模型直接识别；
  // 扫描件 PDF / 不支持的格式降级演示
  let fileIssue = ''
  if (file) {
    const ext = path.extname(file.originalname || '').toLowerCase()
    if (ext === '.pdf') {
      const buf = await fs.promises.readFile(file.path)
      const pdfText = extractPdfText(buf)
      if (pdfText) {
        text = [text, pdfText].filter(Boolean).join('\n')
        source = 'PDF 文本 + LLM 提取'
      } else {
        fileIssue = 'PDF 没有可读的文本层（扫描件），请将扫描页截图为图片后上传识别'
      }
    } else if (visionMimeOf(file.originalname)) {
      // 图片：交给视觉模型做 OCR + 字段提取，一次调用完成
      try {
        const dataUrl = await fileToDataUrl(file)
        const j = await visionAskJSON(
          '你是贷款产品信息提取助手，负责识别产品宣传图/产品要素表图片中的文字。',
          `请识别图片中的贷款产品信息并提取要素。输出 JSON：{"productName":"","institution":"","minRate":0,"maxRate":0,"minAmount":0,"maxAmount":0,"loanTerm":"如 6-60个月","repaymentMethod":"","conditions":"准入条件原文","confidence":0.9}。利率为百分比数字（3.5% → 3.5），额度单位为元（"30万"→300000）。图中没有的字段填 null。`,
          dataUrl
        )
        return { success: true, data: j, confidence: j.confidence || 0.85, source: '图片识别（DeepSeek Vision）' }
      } catch (e) {
        fileIssue = `图片视觉识别失败：${String(e.message).slice(0, 100)}`
      }
    } else {
      fileIssue = `不支持的附件格式：${file.originalname || '未知'}（支持 pdf / jpg / png / webp）`
    }
  }

  // 拿不到可交给大模型的文字：回退演示数据并打 demo 标记，
  // 保证「产品录入」演示流程不断，同时让前端能提示这不是真实提取
  if (!text) {
    if (!file) fileIssue = '未提供产品文本或附件'
    const demo = await mockProvider.extractProduct(rawText)
    return {
      ...demo,
      demo: true,
      source: `演示数据（${fileIssue}）`,
      note: fileIssue,
    }
  }

  const j = await askJSON(
    '你是贷款产品信息提取助手。从产品文本/解析结果中提取产品要素。',
    `文本：${text}\n输出 JSON：{"productName":"","institution":"","minRate":0,"maxRate":0,"minAmount":0,"maxAmount":0,"loanTerm":"如 6-60个月","repaymentMethod":"","conditions":"准入条件原文","confidence":0.9}`
  )
  return { success: true, data: j, confidence: j.confidence || 0.9, source }
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

// ---------- AI 助理（LLM 意图识别 + 结构化实体） ----------
// 注意：意图枚举与实体字段必须与前端 assistant/Index.vue 的消费逻辑严格对齐
// （mock.js assistantReply 是那套 schema 的参照实现），否则意图识别对了也执行不了。
const ASSISTANT_HINT =
  '我可以帮你完成这些事：\n· 客户：新增客户 张三 13800138000\n· 资料：更新张三的月收入为2万\n' +
  '· 产品：录入产品 招行闪电贷 利率3.5%起\n· 日程：明天下午3点与张总面谈\n' +
  '· 查询：张三的档案 / 明天有什么日程 / 有哪些产品'

export const assistantReply = async (text) => {
  const j = await askJSON(
    `你是贷款经理的智能助理，负责意图识别与实体提取。识别结果会直接交给下游系统执行，因此实体字段名必须严格遵守各意图的 schema，不得自造字段名。
可选意图与实体 schema（无法提取的字段填空串或省略）：
1. schedule_create（创建/安排日程）：{"title":"","startTime":"ISO8601含时区偏移","endTime":"ISO8601含时区偏移（默认开始后1小时）","priority":"P0/P1/P2","type":"task/call/meeting","location":"","customerName":"","remark":""}
2. customer_create（新建客户）：{"name":"","phone":"11位手机号"}
3. customer_update（更新客户档案字段）：{"name":"客户姓名","phone":"","field":"monthlyIncome|totalDebt|housingFundBase|propertyValue|employer|occupation","fieldLabel":"月均收入/总负债/公积金基数/房产价值(万)/工作单位/职业","value":数字（月收入/负债/公积金基数单位为元，房产价值单位为万，"2万"要换算成20000）}
4. product_create（录入产品）：{"productName":"","institution":"含银行/金融等后缀","minRate":数字,"maxAmount":数字（单位万）}
5. query_schedule（查询日程安排）：{"scope":"today|tomorrow|upcoming"}
6. query_customer（查询客户档案）：{"name":"","phone":""}
7. query_product（查询产品库）：{}
8. query_match（为某个客户匹配产品）：{"name":"客户姓名"}
9. unknown（以上意图都不是）：entities 为 {}，reply 用简短话术说明你能做什么。
时间类表述（明天下午3点等）必须结合当前时间换算成 ISO8601。`,
    `当前时间：${todayISO()}\n用户输入：${text}\n输出 JSON：{"intent":"schedule_create","entities":{},"reply":"给用户的确认话术，查询类意图填空串"}`
  )
  const intent = j.intent || 'unknown'
  return {
    intent,
    entities: { ...(j.entities || {}), rawText: text },
    reply: intent === 'unknown' ? (j.reply || ASSISTANT_HINT) : j.reply || '',
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

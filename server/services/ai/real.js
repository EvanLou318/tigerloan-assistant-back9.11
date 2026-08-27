// ==================== AI Real Provider（骨架） ====================
// 真实 AI 服务接入层：接口签名与 mock.js 完全一致
//
// 【如何启用】
//   1. 在环境变量（或启动命令）中配置：
//        AI_PROVIDER=real
//        LLM_API_KEY=...            大模型 key（OpenAI 兼容协议）
//        LLM_BASE_URL=...           可选，默认 https://api.openai.com/v1
//        LLM_MODEL=...              可选，默认 gpt-4o-mini
//        OCR_API_KEY / OCR_SECRET_KEY=...    OCR 服务凭证（腾讯云/阿里云/讯飞等）
//        ASR_API_KEY / ASR_SECRET_KEY=...    ASR 服务凭证
//   2. 在下方对应 TODO 位置实现真实调用（每处均已标注）
//   3. 重启后端即可，前端无需任何改动
//
// 未配置 key 时调用将返回明确错误提示，不影响其他功能

import { config } from '../../config.js'

function notConfigured(service) {
  throw new Error(`真实 AI 服务未配置：${service} 需要 API Key。请在环境变量中配置后重启（当前 AI_PROVIDER=${config.aiProvider}）`)
}

// ---------- OCR ----------
// TODO: 接入真实 OCR（如腾讯云通用文字识别 / 阿里云读光 / 内部 OCR 网关）
//   传入 req.file（multer 已落盘）或文本描述，调用厂商 SDK/HTTP API，
//   将返回结果映射为与 mock 相同的结构：{ success, data, confidence, source }
export const ocrIdCard = async (file) => notConfigured('身份证 OCR')
export const ocrBankStatement = async (file) => notConfigured('银行流水 OCR')
export const ocrCreditReport = async (file) => notConfigured('征信报告 OCR')
export const ocrIncomeProof = async (file) => notConfigured('收入证明 OCR')
export const ocrSocialSecurity = async (file) => notConfigured('社保公积金 OCR')
export const ocrProperty = async (file) => notConfigured('房产证 OCR')
export const ocrBusinessLicense = async (file) => notConfigured('营业执照 OCR')

// ---------- ASR ----------
// TODO: 接入真实 ASR（如腾讯云一句话识别 / 讯飞语音听写）
//   传入音频文件 Buffer，返回 { success, text, duration, language }
export const asr = async (file, fallbackText) => notConfigured('语音识别 ASR')

// ---------- LLM 结构化提取 ----------
// TODO: 统一走 LLM 完成。建议实现一个 callLLM(prompt, system) 帮助函数：
//   POST {LLM_BASE_URL}/chat/completions
//   headers: Authorization: Bearer {LLM_API_KEY}
//   body: { model: config.llmModel, messages: [...] }
//   再用 JSON mode / function calling 约束输出为与 mock 相同的结构
export const extractFromVoice = async (text) => notConfigured('大模型语音信息提取')
export const extractCustomerFromVoice = async (text) => notConfigured('大模型客户建档提取')
export const extractProduct = async (text, file) => notConfigured('大模型产品信息提取')
export const extractSchedule = async (text) => notConfigured('大模型日程解析')

// ---------- 匹配引擎 ----------
// 建议实现：将客户画像 + 产品准入条件组装为 prompt，让 LLM 输出
// { approved: [...], rejected: [...] }，或实现确定性规则引擎（可参考 mock.js 的 RULE_PARSERS）
export const match = async (customer, products) => notConfigured('AI 匹配引擎')

// ---------- AI 助理 ----------
// 建议实现：意图识别（可用 LLM function calling，工具集与 mock 的 intent 枚举一致）
export const assistantReply = async (text) => notConfigured('AI 助理')

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

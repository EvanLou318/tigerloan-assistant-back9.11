// ==================== AI Provider 工厂 ====================
// 模式选择（config.aiProvider / 环境变量 AI_PROVIDER）：
//   auto（默认）→ 按分类自动：管理后台「三方服务」里配置了可用供应商的走真实调用，
//                 其余走 mock —— 换服务商只需后台改配置
//   mock        → 全部强制模拟
//   real        → 全部强制真实（未配置的分类调用时报明确错误）
// 前端只与 /api/ai/* 接口交互，切换 Provider 对前端完全透明

import { config } from '../../config.js'
import { mockProvider } from './mock.js'
import { realProvider } from './real.js'
import { getCategoryRuntime } from './registry.js'

// 每个能力归属的三方服务分类
// 注意：7 个材料 OCR 走 LLM 视觉模型（deepseek-v4-flash-vision-exp），
// 依赖 llm 分类的供应商配置而非 ocr 分类 —— ocr 分类留给未来专用 OCR 厂商。
const METHOD_CATEGORY = {
  ocrIdCard: 'llm',
  ocrBankStatement: 'llm',
  ocrCreditReport: 'llm',
  ocrIncomeProof: 'llm',
  ocrSocialSecurity: 'llm',
  ocrProperty: 'llm',
  ocrBusinessLicense: 'llm',
  asr: 'asr',
  extractFromVoice: 'llm',
  extractCustomerFromVoice: 'llm',
  extractProduct: 'llm',
  extractSchedule: 'llm',
  match: 'llm',
  assistantReply: 'llm',
}

// auto 模式：逐方法判断分类是否有可用真实供应商
const smartProvider = { name: 'auto' }
for (const [method, category] of Object.entries(METHOD_CATEGORY)) {
  smartProvider[method] = (...args) => {
    const { mode } = getCategoryRuntime(category)
    const impl = mode === 'real' ? realProvider[method] : mockProvider[method]
    return impl(...args)
  }
}

export function getAI() {
  if (config.aiProvider === 'real') return realProvider
  if (config.aiProvider === 'mock') return mockProvider
  return smartProvider
}

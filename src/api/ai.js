// ==================== AI 能力 API ====================
// 与后端 AI Provider（mock/real 可切换）契约对齐：
// OCR / ASR / LLM 结构化提取 / 匹配引擎 / AI 助理
// 返回结构与原前端 mock 完全一致，未来后端切换真实 AI 服务前端零改动

import request from './index'

// ---------- OCR：各材料类型 ----------
export function ocrIdCard(text) {
  return request.post('/ai/ocr/idcard', { text })
}

export function ocrBankStatement(text) {
  return request.post('/ai/ocr/bankflow', { text })
}

export function ocrCreditReport(text) {
  return request.post('/ai/ocr/credit', { text })
}

export function ocrIncomeProof(text) {
  return request.post('/ai/ocr/income', { text })
}

export function ocrSocialSecurity(text) {
  return request.post('/ai/ocr/social', { text })
}

export function ocrProperty(text) {
  return request.post('/ai/ocr/property', { text })
}

export function ocrBusinessLicense(text) {
  return request.post('/ai/ocr/license', { text })
}

// ---------- ASR：语音转文字 ----------
export function asr(text) {
  return request.post('/ai/asr', { text })
}

// ---------- LLM 结构化提取 ----------

// 语音口述 → 客户画像摘要
export function extractFromVoice(text) {
  return request.post('/ai/extract/voice', { text })
}

// 语音口述 → 建档字段（含逐字段置信度）
export function extractCustomerFromVoice(text) {
  return request.post('/ai/extract/customer-voice', { text })
}

// 产品资料 → 结构化产品字段
export function extractProduct(text) {
  return request.post('/ai/extract/product', { text })
}

// 自然语言 → 日程结构化字段
export function extractSchedule(text) {
  return request.post('/ai/extract/schedule', { text })
}

// ---------- 匹配引擎 ----------
// customer: 客户画像（推演时可带调整值）；products: 产品数组（空则后端取库内启用产品）
export function matchProducts(customer, products) {
  return request.post('/ai/match', { customer, products })
}

// ---------- AI 助理：意图识别 + 实体提取 ----------
export function assistantReply(text) {
  return request.post('/ai/assistant', { text })
}

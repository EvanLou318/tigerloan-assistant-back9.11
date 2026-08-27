// ==================== AI Provider 工厂 ====================
// 根据环境变量 AI_PROVIDER 选择实现：
//   mock（默认）→ 模拟数据，无需任何 key
//   real        → 真实服务（见 real.js 的接入说明）
// 前端只与 /api/ai/* 接口交互，切换 Provider 对前端完全透明

import { config } from '../../config.js'
import { mockProvider } from './mock.js'
import { realProvider } from './real.js'

export function getAI() {
  if (config.aiProvider === 'real') return realProvider
  return mockProvider
}

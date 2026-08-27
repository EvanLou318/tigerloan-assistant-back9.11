// ==================== 通用工具 ====================

const pad = (n) => String(n).padStart(2, '0')

// 统一时间格式：YYYY-MM-DD HH:mm:ss（与前端原型展示格式一致）
export function fmtDateTime(d = new Date()) {
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

// 短 ID 生成：前缀 + 时间戳36进制 + 随机串
export function genId(prefix) {
  return prefix + Date.now().toString(36) + Math.random().toString(36).slice(2, 6)
}

// 统一成功响应：{ success: true, data }
export function ok(res, data = null) {
  res.json({ success: true, data })
}

// 统一失败响应：{ success: false, message }
export function fail(res, status, message) {
  res.status(status).json({ success: false, message })
}

// 业务错误（可被全局错误处理器转为 4xx）
export class BizError extends Error {
  constructor(message, status = 400) {
    super(message)
    this.status = status
  }
}

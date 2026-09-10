// ==================== 服务端配置 ====================
// 所有配置均可通过环境变量覆盖；未来接入真实 AI 服务时，
// 在此填写对应 key 或通过 .env / 环境变量注入即可。

export const config = {
  // 服务端口（前端 vite proxy 指向这里）
  port: Number(process.env.PORT || 3001),

  // JWT 密钥：生产环境务必通过环境变量 JWT_SECRET 覆盖
  // 注意：这里刻意不使用环境变量覆盖。部署环境（多实例沙箱）中不同实例可能注入不同的
  // 环境变量，会导致「A 实例签发的 token 在 B 实例校验失败 → 登录即掉线」。固定密钥可保证
  // 任意实例签发的 token 都能被校验通过。如需更换密钥，直接修改本常量即可。
  jwtSecret: 'loan-assistant-dev-secret-do-not-use-in-prod',
  jwtExpires: process.env.JWT_EXPIRES || '7d',

  // AI Provider：auto（默认，按管理后台三方服务配置逐分类切换）| mock | real
  aiProvider: process.env.AI_PROVIDER || 'auto',

  // —— 未来接入真实 AI 服务时填写（当前留空走 mock）——
  // 通用大模型（OpenAI 兼容协议）
  llmApiKey: process.env.LLM_API_KEY || '',
  llmBaseUrl: process.env.LLM_BASE_URL || 'https://api.openai.com/v1',
  llmModel: process.env.LLM_MODEL || 'gpt-4o-mini',
  // OCR / ASR 服务（如腾讯云、阿里云、讯飞等）
  ocrApiKey: process.env.OCR_API_KEY || '',
  ocrSecretKey: process.env.OCR_SECRET_KEY || '',
  asrApiKey: process.env.ASR_API_KEY || '',
  asrSecretKey: process.env.ASR_SECRET_KEY || '',
}

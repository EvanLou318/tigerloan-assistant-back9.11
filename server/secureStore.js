// ==================== 敏感凭证加解密 ====================
// service_providers.api_key / secret_key / extra.appkey 落库前 AES-256-GCM 加密，
// 读取时解密。加密密钥从 JWT 密钥派生（同一环境变量注入，无需额外配置）。
//
// 兼容性：enc:v1: 前缀标记密文；无前缀的存量明文原样返回（读取兼容），
// 下一次保存时会自动升级为密文。

import crypto from 'node:crypto'
import { config } from './config.js'

const PREFIX = 'enc:v1:'

let derivedKey = null
function key() {
  if (!derivedKey) {
    derivedKey = crypto.createHash('sha256').update(String(config.jwtSecret)).digest()
  }
  return derivedKey
}

/** 明文 → 密文（已是密文或空值时原样返回） */
export function encryptSecret(plain) {
  const s = String(plain || '')
  if (!s || s.startsWith(PREFIX)) return s
  const iv = crypto.randomBytes(12)
  const cipher = crypto.createCipheriv('aes-256-gcm', key(), iv)
  const data = Buffer.concat([cipher.update(s, 'utf8'), cipher.final()])
  const tag = cipher.getAuthTag()
  return PREFIX + [iv.toString('base64'), tag.toString('base64'), data.toString('base64')].join('.')
}

/** 密文 → 明文（无前缀视为存量明文原样返回；解密失败视为未配置返回空串） */
export function decryptSecret(stored) {
  const s = String(stored || '')
  if (!s) return ''
  if (!s.startsWith(PREFIX)) return s
  try {
    const [ivB64, tagB64, dataB64] = s.slice(PREFIX.length).split('.')
    if (!ivB64 || !tagB64 || !dataB64) return ''
    const decipher = crypto.createDecipheriv('aes-256-gcm', key(), Buffer.from(ivB64, 'base64'))
    decipher.setAuthTag(Buffer.from(tagB64, 'base64'))
    return Buffer.concat([decipher.update(Buffer.from(dataB64, 'base64')), decipher.final()]).toString('utf8')
  } catch {
    // 密钥更换后旧密文不可解——宁可当作未配置回退 mock，也不能报 500
    return ''
  }
}

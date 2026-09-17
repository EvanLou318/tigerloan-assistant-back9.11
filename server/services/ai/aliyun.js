// ==================== 阿里云智能语音交互（ASR）适配器 ====================
// 一句话识别 RESTful API：https://help.aliyun.com/zh/isi/developer-reference/use-restful-apis
//
// 约束（厂商限制，非本项目设定）：
//   - 单声道、16 bit 采样位数
//   - 采样率 8000 / 16000 Hz
//   - 时长 ≤ 60 秒（超时需改用录音文件识别 API）
//   - Ethnicity 模型语种由控制台项目决定，不能通过请求参数指定
//
// 鉴权：控制台临时 AccessToken（有效期通常 24h）走 X-NLS-Token 头。
//      生产环境建议改用 AccessKey + CreateToken 自动刷新，见 requireAlibabaNlsToken。

import fs from 'node:fs/promises'

const DEFAULT_ENDPOINT = 'https://nls-gateway-cn-shanghai.aliyuncs.com/stream/v1/asr'

// 阿里云常见状态码（核心错误必须翻译成人话，否则用户只看到一串数字）
const STATUS_TEXT = {
  20000000: 'SUCCESS',
  // 注意：40000001 是个"口袋码"——除参数错误外，Token 失效/过期实际也返回它
  // （message 带 ACCESS_DENIED，上方 recognize 已按文本识别并翻译成明确的过期提示）
  40000001: '请求参数有误（若多次出现请检查 Token 是否已失效）',
  40000002: '默认无效：请求参数缺失',
  40010001: '授权失败：AppKey 无效或被删除',
  40010002: '授权失败：AccessToken 无效或已过期',
  40010003: 'AccessToken 过期',
  40020001: '服务未开通',
  40020002: '服务欠费',
  40020003: '请求参数或并发超出限制',
  40030001: '内部错误',
  40030002: '未知错误',
  40030003: '请求超时',
  40040001: '音频解码失败：格式或采样率与声明不符',
  40040002: '音频文件过大',
  40040003: '音频时长超限（一句话识别最长 60 秒）',
  40040004: '音频为空',
}

// 阿里云接受的音频格式；不在此列的一律拒绝，避免带着错格式白跑一趟
const SUPPORTED_FORMATS = new Set(['pcm', 'wav', 'opus', 'speex', 'amr', 'mp3', 'aac'])

/**
 * 从文件扩展名推断阿里云 format 参数。
 * 注意：阿里云的 pcm 指「裸 PCM」，带 RIFF 头的必须声明 wav，两者不可混用。
 */
export function formatFromExt(filename = '') {
  const ext = filename.toLowerCase().split('.').pop()
  if (ext === 'mp3') return 'mp3'
  if (ext === 'wav') return 'wav'
  if (ext === 'amr') return 'amr'
  if (ext === 'aac' || ext === 'm4a') return 'aac'
  if (ext === 'opus') return 'opus'
  if (ext === 'pcm' || ext === 'raw') return 'pcm'
  return null
}

/** 阿里云只支持 8k/16k，前端若给出其他采样率需重采样或拒绝 */
export function normalizeSampleRate(rate) {
  const n = Number(rate)
  if (!Number.isFinite(n)) return 16000
  if (n >= 16000) return 16000
  return 8000
}

function isExpiredToken(status) {
  return status === 40010002 || status === 40010003
}

/**
 * 调用阿里云一句话识别。
 * @param {object} opts
 * @param {string} opts.token    AccessToken（X-NLS-Token）
 * @param {string} opts.appkey   项目 AppKey
 * @param {Buffer} opts.audio    音频二进制
 * @param {string} opts.format   pcm|wav|mp3|aac|amr|opus|speex
 * @param {number} [opts.sampleRate]
 * @param {string} [opts.endpoint] 自定义网关（VPC/内网或换地域）
 * @returns {{ text, taskId, status, message }}
 */
export async function recognize({ token, appkey, audio, format, sampleRate = 16000, endpoint }) {
  if (!token) throw new Error('阿里云 ASR 未配置 AccessToken')
  if (!appkey) throw new Error('阿里云 ASR 未配置 AppKey')
  if (!SUPPORTED_FORMATS.has(format)) {
    throw new Error(`阿里云 ASR 不支持的音频格式：${format}（支持 ${[...SUPPORTED_FORMATS].join('/')}）`)
  }
  const rate = normalizeSampleRate(sampleRate)

  const url = new URL(endpoint || DEFAULT_ENDPOINT)
  url.searchParams.set('appkey', appkey)
  url.searchParams.set('format', format)
  url.searchParams.set('sample_rate', String(rate))

  const res = await fetch(url, {
    method: 'POST',
    headers: {
      'X-NLS-Token': token,
      // 官方文档示例用 audio/wav；octet-stream 对其它封装格式同样有效
      'Content-Type': format === 'wav' ? 'audio/wav' : 'application/octet-stream',
    },
    body: audio,
    signal: AbortSignal.timeout(25000),
  })

  const json = await res.json().catch(() => null)
  if (!json) {
    throw new Error(`阿里云 ASR 响应解析失败（HTTP ${res.status}）`)
  }

  const status = Number(json.status)
  if (status !== 20000000) {
    const rawMsg = String(json.message || '')
    const detail = STATUS_TEXT[status] || rawMsg || '未知错误'
    // 实测：Token 失效/过期时阿里云并不返回文档中的 40010002/40010003 专码，
    // 而是统一包成 40000001 + message "Meta:ACCESS_DENIED:The token '...' is invalid!/expired"。
    // 因此必须同时看 message 文本，否则过期会被误报成「请求参数有误」。
    if (isExpiredToken(status) || /ACCESS_DENIED/i.test(rawMsg) || /token.{0,40}(invalid|expired|denied)/i.test(rawMsg)) {
      throw new Error(`阿里云 AccessToken 已失效或被拒绝（${status}）。控制台临时 Token 有效期约 24 小时，请到智能语音交互控制台重新生成，并在「三方服务-语音识别」中更新；长期方案请改用 AccessKey 自动刷新`)
    }
    throw new Error(`阿里云 ASR 识别失败（${status}）：${detail}`)
  }

  return {
    text: json.result || '',
    taskId: json.task_id || '',
    status,
    message: json.message || 'SUCCESS',
  }
}

/**
 * 连通性自检：用一段静音向云端发一次请求。
 * 目的不是拿到文字，而是验证 Token / AppKey 是否仍然有效，
 * 因此把 SUCCESS 与「音频为空」都视为鉴权通过。
 */
export async function ping({ token, appkey, endpoint }) {
  // 200ms 静音 PCM（16kHz/16bit 单声道）
  const samples = 16000 * 0.2
  const silence = Buffer.alloc(Math.floor(samples) * 2)
  try {
    await recognize({ token, appkey, audio: silence, format: 'pcm', sampleRate: 16000, endpoint })
    return true
  } catch (e) {
    const msg = String(e?.message || '')
    // 白名单判定：只有"音频内容类拒绝"说明请求已通过鉴权层（Token/AppKey 有效），视为连通；
    // 其余一切错误（鉴权/账户/未配置/网络/本地参数）都视为不连通。
    // 静音探测音频会命中 40000001（参数有误，纯音频内容问题）或 40040004（音频为空）。
    const contentRejected = msg.includes('阿里云 ASR 识别失败')
      && /40000001|40040001|40040003|40040004/.test(msg)
    if (!contentRejected) throw e
    return true
  }
}

/** 读取 multer 落盘的音频文件 */
export async function readAudio(filePath) {
  return fs.readFile(filePath)
}

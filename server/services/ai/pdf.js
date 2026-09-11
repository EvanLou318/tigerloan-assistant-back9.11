// ==================== 极简 PDF 文本抽取 ====================
// 不引第三方依赖：只处理常见的 FlateDecode 内容流 + 文本操作符（Tj / TJ / ' / "）。
// 目的很单一：把产品 PDF 里的文字掏出来喂给大模型。
// 扫描件 / 图片型 PDF / CID 中文子集字体会抽不出可读文本 —— 由调用方降级处理。

import zlib from 'node:zlib'

// 内容流可能被 deflate 压缩，也可能原始存放；两种都试一遍
function tryInflate(buf) {
  for (const fn of [zlib.inflateSync, zlib.inflateRawSync]) {
    try {
      return fn(buf)
    } catch {
      /* 不是压缩数据，换下一种或放弃 */
    }
  }
  return null
}

// PDF 字面量字符串转义：\n \r \t \b \f \( \) \\ 以及 \ddd 八进制
function decodeLiteral(raw) {
  let out = ''
  for (let i = 0; i < raw.length; i += 1) {
    const c = raw[i]
    if (c !== '\\') {
      out += c
      continue
    }
    const n = raw[i + 1]
    i += 1
    const simple = { n: '\n', r: '\r', t: '\t', b: '\b', f: '\f' }
    if (n in simple) out += simple[n]
    else if (n >= '0' && n <= '7') {
      out += String.fromCharCode(parseInt(raw.slice(i, i + 3), 8))
      i += 2
    } else out += n || ''
  }
  return out
}

// 十六进制字符串 <48656C6C6F>：能解成可打印 ASCII 才要，
// 否则大概率是 CID 字形索引（中文子集字体），解出来是一堆乱码，直接丢弃
function decodeHex(body) {
  const hex = body.replace(/\s+/g, '')
  if (!hex || hex.length % 2) return null
  let out = ''
  for (let i = 0; i < hex.length; i += 2) {
    const code = parseInt(hex.slice(i, i + 2), 16)
    if (code < 0x20 || code > 0x7e) return null
    out += String.fromCharCode(code)
  }
  return out
}

// 按出现顺序抓出内容流里的字符串对象
function stringsFrom(content) {
  const res = []
  const re = /\((?:\\.|[^\\()])*\)|<[0-9a-fA-F\s]+>/g
  let m
  while ((m = re.exec(content))) {
    const token = m[0]
    if (token[0] === '(') {
      res.push(decodeLiteral(token.slice(1, -1)))
    } else {
      const d = decodeHex(token.slice(1, -1))
      if (d) res.push(d)
    }
  }
  return res
}

/**
 * 从 PDF 二进制中抽取文本
 * @param {Buffer} buf
 * @returns {string} 抽取失败或无文本层时返回空串
 */
export function extractPdfText(buf) {
  if (!Buffer.isBuffer(buf) || !buf.length) return ''
  const raw = buf.toString('latin1')

  const chunks = []
  const streamRe = /stream\r?\n?/g
  let m
  while ((m = streamRe.exec(raw))) {
    const start = m.index + m[0].length
    const end = raw.indexOf('endstream', start)
    if (end < 0) break
    streamRe.lastIndex = end + 'endstream'.length

    const slice = Buffer.from(raw.slice(start, end), 'latin1')
    const inflated = tryInflate(slice)
    const content = inflated ? inflated.toString('latin1') : raw.slice(start, end)
    chunks.push(...stringsFrom(content))
  }

  // 全程按 latin1 搬运字节，这里一次性还原成 UTF-8（纯 ASCII 不受影响）
  let text = chunks.join('')
  try {
    text = Buffer.from(text, 'latin1').toString('utf8')
  } catch {
    /* 保持原样 */
  }
  text = text.replace(/\s+/g, ' ').trim()
  // 抽出来的东西几乎全是乱码就没意义了，交给调用方降级
  const printable = text.replace(/[^\x20-\x7e一-龥]/g, '').length
  return printable >= 20 ? text : ''
}

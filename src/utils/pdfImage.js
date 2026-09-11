// PDF → 图片：把 PDF 首页渲染成 JPEG，交给视觉模型识别
// 背景：DeepSeek Vision 只收图片（JPEG/PNG/GIF/WebP），不收 PDF。
// 服务端 pdf.js 抽文本层只能覆盖文字版 PDF，扫描件（图片型）抽不出文本。
// 在浏览器端把 PDF 任意版本（文字版/扫描件）统一栅格化成图片，
// 即可让所有 PDF 都走同一条视觉识别链路，用户不再需要"截图后上传"。
import * as pdfjsLib from 'pdfjs-dist'
import workerUrl from 'pdfjs-dist/build/pdf.worker.min.mjs?url'

pdfjsLib.GlobalWorkerOptions.workerSrc = workerUrl

/**
 * 把 PDF 第一页渲染为 JPEG Blob
 * @param {File|Blob} file 用户选择的 PDF 文件
 * @param {{maxWidth?: number, quality?: number}} opts
 * @returns {Promise<{blob: Blob, name: string}>}
 */
export async function pdfFirstPageToImage(file, { maxWidth = 1600, quality = 0.85 } = {}) {
  const data = await file.arrayBuffer()
  const doc = await pdfjsLib.getDocument({ data }).promise
  try {
    const page = await doc.getPage(1)
    const base = page.getViewport({ scale: 1 })
    // 放大到目标宽度，上限 2 倍避免字太小的扫描件看不清；同时别超视口太大
    const scale = Math.min(2, Math.max(1, maxWidth / base.width))
    const viewport = page.getViewport({ scale })
    const canvas = document.createElement('canvas')
    canvas.width = Math.ceil(viewport.width)
    canvas.height = Math.ceil(viewport.height)
    const ctx = canvas.getContext('2d')
    // 白底：透明背景的 PDF 渲染后不至于变成黑图
    ctx.fillStyle = '#ffffff'
    ctx.fillRect(0, 0, canvas.width, canvas.height)
    await page.render({ canvasContext: ctx, viewport }).promise
    const blob = await new Promise((resolve, reject) => {
      canvas.toBlob((b) => (b ? resolve(b) : reject(new Error('PDF 转图片失败'))), 'image/jpeg', quality)
    })
    const baseName = (file.name || 'page.pdf').replace(/\.pdf$/i, '')
    return { blob, name: `${baseName}.jpg` }
  } finally {
    doc.destroy()
  }
}

/** 判断文件是否 PDF */
export function isPdf(file) {
  const n = (file?.name || '').toLowerCase()
  return file?.type === 'application/pdf' || n.endsWith('.pdf')
}

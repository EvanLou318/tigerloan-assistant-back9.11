// ==================== 浏览器录音工具 ====================
// 目标：产出阿里云「一句话识别」要求的音频 —— 16kHz / 16bit / 单声道 WAV。
//
// 为什么不用 MediaRecorder 直出：浏览器 MediaRecorder 默认产出 webm(opus) 容器，
// 而阿里云一句话识别只接受 pcm / wav / opus / speex / amr / mp3 / aac，
// webm 不在其列，直接上传会报 40040001 音频解码失败。
// 因此走 WebAudio 采集 Float32 → 降采样到 16k → 转 Int16 → 封装 RIFF WAV，
// 格式完全可控、且与浏览器编码实现无关。

const TARGET_RATE = 16000

/** Float32 立体声/单声道混合为单声道 */
function downmixToMono(input) {
  const ch0 = input[0]
  if (input.length === 1) return ch0
  const out = new Float32Array(ch0.length)
  for (let c = 0; c < input.length; c++) {
    const chan = input[c]
    for (let i = 0; i < ch0.length; i++) out[i] += chan[i]
  }
  for (let i = 0; i < out.length; i++) out[i] /= input.length
  return out
}

/** Float32(-1~1) → Int16 PCM */
function floatTo16BitPCM(input) {
  const out = new Int16Array(input.length)
  for (let i = 0; i < input.length; i++) {
    const s = Math.max(-1, Math.min(1, input[i]))
    out[i] = s < 0 ? s * 0x8000 : s * 0x7fff
  }
  return out
}

/** 给裸 PCM 加 44 字节 RIFF 头，得到标准 wav */
function encodeWav(pcm, sampleRate) {
  const bytesPerSample = 2
  const blockAlign = bytesPerSample // 单声道
  const buffer = new ArrayBuffer(44 + pcm.length * bytesPerSample)
  const view = new DataView(buffer)

  const writeStr = (offset, str) => {
    for (let i = 0; i < str.length; i++) view.setUint8(offset + i, str.charCodeAt(i))
  }

  writeStr(0, 'RIFF')
  view.setUint32(4, 36 + pcm.length * bytesPerSample, true)
  writeStr(8, 'WAVE')
  writeStr(12, 'fmt ')
  view.setUint32(16, 16, true) // fmt chunk 长度
  view.setUint16(20, 1, true) // PCM
  view.setUint16(22, 1, true) // 单声道
  view.setUint32(24, sampleRate, true)
  view.setUint32(28, sampleRate * blockAlign, true) // byte rate
  view.setUint16(32, blockAlign, true)
  view.setUint16(34, 8 * bytesPerSample, true) // 位深
  writeStr(36, 'data')
  view.setUint32(40, pcm.length * bytesPerSample, true)

  let offset = 44
  for (let i = 0; i < pcm.length; i++) {
    view.setInt16(offset, pcm[i], true)
    offset += 2
  }
  return new Blob([buffer], { type: 'audio/wav' })
}

/**
 * 开始录音。
 * @returns {Promise<{ stop: () => Promise<Blob>, cancel: () => void, supported: true }>}
 * @throws 麦克风不可用 / 用户拒绝授权 / 非安全上下文时抛出可读错误
 */
export async function startRecording() {
  if (!navigator.mediaDevices?.getUserMedia) {
    throw new Error('当前浏览器不支持录音，或页面非 HTTPS/安全上下文')
  }

  let stream
  try {
    stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        // 只是「建议」，浏览器可能忽略；实际采样率由 AudioContext 重采样保证
        sampleRate: TARGET_RATE,
        channelCount: 1,
        echoCancellation: true,
        noiseSuppression: true,
      },
    })
  } catch (e) {
    const name = e?.name || ''
    if (name === 'NotAllowedError' || name === 'PermissionDeniedError') {
      throw new Error('麦克风权限被拒绝，请在浏览器设置中允许后再试')
    }
    if (name === 'NotFoundError' || name === 'DevicesNotFoundError') {
      throw new Error('未检测到麦克风设备')
    }
    throw new Error(`无法访问麦克风：${e?.message || name || '未知原因'}`)
  }

  const AudioCtx = window.AudioContext || window.webkitAudioContext
  const ctx = new AudioCtx({ sampleRate: TARGET_RATE })
  const source = ctx.createMediaStreamSource(stream)
  // 缓冲区取 4096：兼顾实时性与回调开销，取太小在高采样率下会掉帧
  const processor = ctx.createScriptProcessor(4096, 1, 1)

  const chunks = []
  let frames = 0

  processor.onaudioprocess = (e) => {
    const mono = downmixToMono([e.inputBuffer.getChannelData(0)])
    chunks.push(new Float32Array(mono))
    frames += mono.length
  }

  source.connect(processor)
  processor.connect(ctx.destination)

  function teardown() {
    try {
      source.disconnect()
      processor.disconnect()
    } catch {}
    stream.getTracks().forEach((t) => t.stop())
    ctx.close().catch(() => {})
  }

  return {
    supported: true,
    cancel: teardown,
    stop: async () => {
      teardown()
      if (!frames) return null
      // 合并所有片段后再统一量化，避免逐块 Quantize 的累积误差
      const merged = new Float32Array(frames)
      let offset = 0
      for (const c of chunks) {
        merged.set(c, offset)
        offset += c.length
      }
      const pcm = floatTo16BitPCM(merged)
      const blob = encodeWav(pcm, TARGET_RATE)
      return {
        blob,
        durationMs: Math.round((frames / TARGET_RATE) * 1000),
        sampleRate: TARGET_RATE,
      }
    },
  }
}

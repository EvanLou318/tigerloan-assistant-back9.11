# -*- coding: utf-8 -*-
"""生成符合阿里云一句话识别要求的测试音频：16kHz / 16bit / 单声道 PCM WAV"""
import math
import struct
import wave


def gen_tone(path, freq=440.0, seconds=1.0, rate=16000):
    n = int(seconds * rate)
    frames = bytearray()
    for i in range(n):
        # 加淡入淡出，避免爆音
        env = min(1.0, i / (rate * 0.02), (n - i) / (rate * 0.05))
        v = 0.3 * env * math.sin(2 * math.pi * freq * i / rate)
        frames += struct.pack('<h', int(v * 32767))
    with wave.open(path, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(bytes(frames))
    print(f'written {path}: {rate}Hz mono 16bit {seconds}s')


if __name__ == '__main__':
    gen_tone('.qa_test_16k.wav', seconds=1.0, rate=16000)

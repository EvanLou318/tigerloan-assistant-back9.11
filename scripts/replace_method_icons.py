# -*- coding: utf-8 -*-
"""把 product/Create.vue 录入方式卡片的内联彩色 svg 换成统一线性 AppIcon。"""
import re
import pathlib

P = pathlib.Path(__file__).resolve().parent.parent / 'src/views/product/Create.vue'
text = P.read_text(encoding='utf-8')

NAMES = ['edit', 'mic', 'image', 'file-text']
pat = re.compile(
    r'<div class="method-icon"[^>]*>\s*<svg[\s\S]*?</svg>\s*</div>'
)

i = {'n': 0}


def repl(_m):
    name = NAMES[i['n']]
    i['n'] += 1
    return (
        '<div class="method-icon">\n'
        f'            <AppIcon name="{name}" :size="24" color="var(--color-primary)" />\n'
        '          </div>'
    )


new_text, count = pat.subn(repl, text)
P.write_text(new_text, encoding='utf-8')
print('replaced:', count)

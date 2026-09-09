# -*- coding: utf-8 -*-
"""把移动端/组件中的 Vant 字体图标批量替换为统一线性图标 AppIcon。"""
import re
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent / 'src'

NAME_MAP = {
    'arrow': 'chevron-right',
    'arrow-up': 'chevron-up',
    'arrow-down': 'chevron-down',
    'arrow-left': 'chevron-left',
    'add-o': 'plus',
    'plus': 'plus',
    'ellipsis': 'more',
    'shop-o': 'bank',
    'edit': 'edit',
    'volume-o': 'volume',
    'mic': 'mic',
    'stop': 'stop',
    'play': 'play',
    'chat-o': 'message',
    'comment-o': 'message',
    'passed': 'check-circle',
    'success': 'check-circle',
    'records': 'list',
    'notes-o': 'file-text',
    'description': 'file-text',
    'orders-o': 'file-text',
    'search': 'search',
    'photo-o': 'image',
    'cross': 'close',
    'share-o': 'share',
    'clock-o': 'clock',
    'bell': 'bell',
    'circle': 'circle',
    'delete-o': 'trash',
    'scan': 'scan',
    'info-o': 'info',
    'question-o': 'help',
    'replay': 'refresh',
    'lock': 'lock',
    'password': 'key',
    'phone': 'phone',
    'contact': 'user',
    'location-o': 'map-pin',
    'friends-o': 'users',
    'home-o': 'home',
    'apps-o': 'grid',
    'todo-list-o': 'calendar',
}

PAT = re.compile(r'<van-icon\b((?:(?!/>).)*?)/>', re.S)


def convert(attrs: str):
    m = re.search(r'\bname="([^"]+)"', attrs)
    if not m:
        return None
    name = NAME_MAP.get(m.group(1))
    if not name:
        return None
    out = [f'name="{name}"']
    sz = re.search(r'\bsize="([^"]+)"', attrs)
    if sz:
        out.append(f':size="{sz.group(1)}"')
    cl = re.search(r'\bcolor="([^"]+)"', attrs)
    if cl:
        out.append(f'color="{cl.group(1)}"')
    for other in re.findall(r'(?:v-if|v-else-if|v-else|class|style|@click|@[a-z.]+)="[^"]*"', attrs):
        out.append(other)
    return '<AppIcon ' + ' '.join(out) + ' />'


total = 0
changed_files = []
for f in ROOT.rglob('*.vue'):
    if 'admin' in f.parts:
        continue
    text = f.read_text(encoding='utf-8')
    if '<van-icon' not in text:
        continue
    counter = [0]

    def repl(m):
        new = convert(m.group(1))
        if new is None:
            return m.group(0)
        counter[0] += 1
        return new

    new_text = PAT.sub(repl, text)
    if counter[0]:
        f.write_text(new_text, encoding='utf-8')
        total += counter[0]
        changed_files.append((str(f.relative_to(ROOT)), counter[0]))

for name, c in changed_files:
    print(f'{c:3d}  {name}')
print('total replaced:', total)

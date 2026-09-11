# -*- coding: utf-8 -*-
"""生成带中文文字的测试图片（产品要素表 / 收入证明），供视觉 OCR 端到端验证。"""
from PIL import Image, ImageDraw, ImageFont

DIR = r"C:\Users\madta\WorkBuddy\2026-08-19-12-24-26\loan-assistant\scripts"
FONT = r"C:\Windows\Fonts\msyh.ttc"


def draw(path, lines):
    img = Image.new("RGB", (860, len(lines) * 70 + 80), "white")
    d = ImageDraw.Draw(img)
    font = ImageFont.truetype(FONT, 30)
    y = 40
    for line in lines:
        d.text((40, y), line, fill="black", font=font)
        y += 70
    img.save(path)
    print("saved", path)


draw(
    DIR + r"\_vision_product.png",
    [
        "贷款产品要素表",
        "产品名称：招行公积金信用贷",
        "机构：招商银行",
        "年利率：3.2%-4.8%",
        "额度：5万-80万",
        "期限：12-60个月",
        "还款方式：等额本息",
        "准入：公积金连续缴存满12个月，征信无当前逾期",
    ],
)
draw(
    DIR + r"\_vision_income.png",
    [
        "收入证明",
        "兹证明 王小明 系我司正式员工，",
        "工作单位：上海星辰科技有限公司",
        "职位：产品经理",
        "月收入：人民币壹万伍仟捌佰元整（15800元）",
        "收入来源：工资代发",
        "联系电话：021-66668888",
        "2026年9月1日",
    ],
)

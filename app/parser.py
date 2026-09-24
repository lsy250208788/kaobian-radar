# -*- coding: utf-8 -*-
"""从公告文本中提取关键日期（报名、笔试、打印准考证、成绩、面试等）"""
import re

# label -> 匹配模式
DATE = r"(\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日|\d{4}\s*年\d{1,2}月|\d{1,2}\s*月\s*\d{1,2}\s*日)"

LABEL_PATTERNS = [
    ("报名", r"报名(?:时间|截止(?:时间)?)?[^。；\n，]{0,20}?" + DATE),
    ("报名截止", r"报名.{0,6}(?:截止|结束)[^。；\n，]{0,15}?" + DATE),
    ("笔试", r"笔试(?:时间|日期)?[^。；\n，]{0,20}?" + DATE),
    ("准考证打印", r"打印准考证[^。；\n，]{0,20}?" + DATE),
    ("成绩", r"成绩(?:查询|公布)[^。；\n，]{0,20}?" + DATE),
    ("面试", r"面试(?:时间|日期)?[^。；\n，]{0,20}?" + DATE),
    ("资格审查", r"资格(?:复审|审查|审核)[^。；\n，]{0,20}?" + DATE),
]


def _norm_date(s):
    """统一为 YYYY-MM-DD；缺年份时默认按当前年份"""
    import time
    s = re.sub(r"\s+", "", s)
    m = re.match(r"(\d{4})年(\d{1,2})月(\d{1,2})日?", s)
    if m:
        y, mo, d = m.groups()
        return f"{int(y):04d}-{int(mo):02d}-{int(d):02d}"
    m = re.match(r"(\d{4})年(\d{1,2})月", s)
    if m:
        y, mo = m.groups()
        return f"{int(y):04d}-{int(mo):02d}-01"
    m = re.match(r"(\d{1,2})月(\d{1,2})日?", s)
    if m:
        mo, d = m.groups()
        y = time.localtime().tm_year
        return f"{y:04d}-{int(mo):02d}-{int(d):02d}"
    return None


def extract_dates(text):
    """返回 [(label, 'YYYY-MM-DD'), ...]"""
    found = []
    seen = set()
    for label, pat in LABEL_PATTERNS:
        m = re.search(pat, text or "")
        if m:
            date_str = _norm_date(m.group(1))
            if date_str and (label, date_str) not in seen:
                seen.add((label, date_str))
                found.append((label, date_str))
    return found

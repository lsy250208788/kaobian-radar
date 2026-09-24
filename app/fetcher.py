# -*- coding: utf-8 -*-
"""公告雷达：抓取官网公告列表，关键词过滤，入库去重"""
import logging
import re
from urllib.parse import urljoin

import requests

import db

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("fetcher")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
}

# 关键词 → 分类
KEYWORDS = {
    "教师": ["教师", "教资", "教育局", "学校招聘", "师德"],
    "医疗": ["医院", "卫生健康", "卫健委", "医疗", "护士", "疾控"],
    "公务员": ["公务员", "招录", "选调", "省考", "国考"],
    "事业单位": ["事业单位", "事编", "编制", "公开招聘", "综合岗"],
    "国企": ["国企", "国资委", "烟草", "电网", "银行", "中石化", "运营商"],
}

# 明显无关的链接
NOISE = ["index", "javascript", "#", ".css", ".js", ".jpg", ".png", "mailto"]


def classify(title):
    for cat, words in KEYWORDS.items():
        if any(w in title for w in words):
            return cat
    if any(w in title for w in ["招聘", "公开招聘"]):
        return "事业单位"
    return "其他"


def _decode(resp):
    """中文政府网站编码不一，依次尝试"""
    for enc in ("utf-8", "gb18030", "gbk"):
        try:
            return resp.content.decode(enc)
        except UnicodeDecodeError:
            continue
    return resp.text


# 提取 <a> 链接（政府站结构各异，用宽松正则）
A_RE = re.compile(
    r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', re.S | re.I
)
TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")


def fetch_source(source):
    """抓取单个源，返回 (新增数, 错误信息)"""
    name, url = source["name"], source["url"]
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15, verify=False)
        resp.raise_for_status()
        html = _decode(resp)
    except Exception as e:
        return 0, f"{name}: {type(e).__name__} {e}"

    added = 0
    base = url
    for href, inner in A_RE.findall(html):
        text = WS_RE.sub(" ", TAG_RE.sub("", inner)).strip()
        if not (8 <= len(text) <= 120):
            continue
        if any(n in href.lower() for n in NOISE):
            continue
        # 关键词过滤：至少命中一个招聘相关词
        if not any(w in text for w in
                   ["招聘", "招录", "招考", "公告", "选调", "招用", "考试"]):
            continue
        full = urljoin(base, href.strip())
        if not full.startswith("http"):
            continue
        cat = classify(text)
        if cat == "其他":
            continue
        new_id = db.upsert_announcement(text, full, source=name, category=cat)
        if new_id:
            added += 1
            # 尝试解析公告正文里的关键日期（首页仅标题时跳过）
            import parser as date_parser
            for label, d in date_parser.extract_dates(text):
                db.add_key_date(new_id, label, d)
    return added, None


def scan_all():
    """扫描全部启用的源，返回摘要"""
    results = []
    total = 0
    for s in db.list_sources():
        if not s["enabled"]:
            continue
        added, err = fetch_source(s)
        total += added
        results.append({"source": s["name"], "added": added, "error": err})
    return {"total_new": total, "sources": results}

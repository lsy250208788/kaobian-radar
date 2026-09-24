# -*- coding: utf-8 -*-
"""文案工坊：模板生成 + 可选 AI（OpenAI 兼容接口）"""
import json

import requests

import db

# 各平台文案模板。占位符：{title} {region} {category} {deadline} {content_brief}
TEMPLATES = {
    "小红书笔记": {
        "title": "🔥{region}{category}招人啦！{title_short}",
        "body": (
            "📣 重磅消息！{region}{category}招聘来咯～\n\n"
            "📌 本次招聘要点：\n{content_brief}\n\n"
            "⏰ 报名截止：{deadline}\n"
            "🔗 公告原文戳主页链接 / 评论区置顶\n\n"
            "💡 适合人群：\n"
            "✅ 想进{category}编制的宝子\n"
            "✅ 应届&往届都可以看\n\n"
            "现在准备完全来得及！需要备考资料的宝子评论区扣1️⃣\n\n"
            "#{region}{category} #招聘 #考编 #事业编 #上岸"
        ),
    },
    "公众号推文": {
        "title": "【招聘】{region}{category}公开招聘！{title_short}",
        "body": (
            "各位考生注意啦！{region}{category}发布最新招聘公告。\n\n"
            "一、招聘概况\n{content_brief}\n\n"
            "二、重要时间\n报名截止：{deadline}\n\n"
            "三、公告原文\n{url}\n\n"
            "如需报考条件解读、岗位表分析和备考资料，欢迎在后台留言或添加客服咨询。"
        ),
    },
    "朋友圈短文案": {
        "title": "",
        "body": (
            "【{region}{category}招聘】{title_short}，"
            "报名截止{deadline}，条件符合的抓紧报！"
            "需要岗位表和备考资料找我👇"
        ),
    },
    "社群答疑话术": {
        "title": "",
        "body": (
            "@所有人 \n📢 {region}{category}新公告来了！\n"
            "{title}\n"
            "报名截止：{deadline}\n"
            "公告全文：{url}\n"
            "有疑问群里问，我看到会回复～"
        ),
    },
}

SYSTEM_PROMPT = (
    "你是一位精通招聘考试推广的公众号/小红书运营专家，服务对象是备考"
    "公务员、事业单位、教师、医疗、国企招聘考试的考生。"
    "根据给定的公告信息，为指定平台生成推广文案。要求："
    "1. 小红书风格要口语化、有emoji、带话题标签；"
    "2. 公众号风格要正式、信息完整；"
    "3. 朋友圈要简短、有紧迫感；"
    "4. 不得编造公告中不存在的条件或日期。"
)


def _brief(content, limit=300):
    content = (content or "").strip()
    if len(content) > limit:
        content = content[:limit] + "……"
    return content or "详见公告原文"


def _title_short(title, limit=30):
    return (title or "")[:limit] + ("…" if len(title or "") > limit else "")


def _deadline(aid):
    dates = db.list_key_dates()
    for d in dates:
        if d.get("announcement_id") == aid and d["label"] in ("报名", "报名截止"):
            return d["date"]
    return "以公告原文为准"


def render_from_template(platform, ann):
    tpl = TEMPLATES.get(platform)
    if not tpl:
        return None
    variables = {
        "title": ann["title"],
        "title_short": _title_short(ann["title"]),
        "region": ann.get("region") or "广东",
        "category": ann.get("category") or "事业单位",
        "deadline": _deadline(ann["id"]),
        "content_brief": _brief(ann.get("content")),
        "url": ann.get("url") or "",
    }
    out = {"title": "", "body": ""}
    for key in ("title", "body"):
        text = tpl[key]
        for k, v in variables.items():
            text = text.replace("{" + k + "}", v)
        out[key] = text
    return out


def render_with_ai(platform, ann, base_url, api_key, model):
    """调用 OpenAI 兼容 /chat/completions 接口"""
    url = base_url.rstrip("/") + "/chat/completions"
    user_prompt = (
        f"公告标题：{ann['title']}\n"
        f"地区：{ann.get('region')}\n类别：{ann.get('category')}\n"
        f"公告内容摘要：{_brief(ann.get('content'), 1500)}\n"
        f"目标平台：{platform}\n请直接输出文案，不要多余解释。"
    )
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.7,
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=120)
    resp.raise_for_status()
    data = resp.json()
    text = data["choices"][0]["message"]["content"].strip()
    title, _, body = text.partition("\n")
    if len(title) > 40 or not title:
        return {"title": "", "body": text}
    return {"title": title.strip(), "body": body.strip()}

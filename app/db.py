# -*- coding: utf-8 -*-
"""SQLite 数据层：公告、关键日期、发布台账、设置"""
import json
import os
import sqlite3
import sys
import time

if getattr(sys, "frozen", False):
    # 打包为 exe 后，数据存放在 exe 所在目录
    BASE_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "kaobian.db")
SETTINGS_PATH = os.path.join(DATA_DIR, "settings.json")

os.makedirs(DATA_DIR, exist_ok=True)


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        """CREATE TABLE IF NOT EXISTS announcements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            url TEXT UNIQUE,
            source TEXT DEFAULT '',
            region TEXT DEFAULT '广东',
            category TEXT DEFAULT '其他',
            content TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime')),
            starred INTEGER DEFAULT 0
        )"""
    )
    c.execute(
        """CREATE TABLE IF NOT EXISTS key_dates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            announcement_id INTEGER,
            label TEXT NOT NULL,
            date TEXT NOT NULL,
            UNIQUE(announcement_id, label)
        )"""
    )
    c.execute(
        """CREATE TABLE IF NOT EXISTS publish_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            announcement_id INTEGER NOT NULL,
            platform TEXT NOT NULL,
            status TEXT DEFAULT '已发布',
            published_at TEXT DEFAULT (datetime('now','localtime')),
            link TEXT DEFAULT '',
            note TEXT DEFAULT '',
            views INTEGER DEFAULT 0,
            likes INTEGER DEFAULT 0
        )"""
    )
    c.execute(
        """CREATE TABLE IF NOT EXISTS sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            url TEXT NOT NULL UNIQUE,
            enabled INTEGER DEFAULT 1
        )"""
    )
    # 默认监控源：以广东为主，兼顾全国性渠道（均为实测可访问的站点）
    defaults = [
        ("广东人事考试网", "https://rsks.gd.gov.cn/"),
        ("广东省教育厅", "https://edu.gd.gov.cn/"),
        ("广东省人力资源和社会保障厅", "https://hrss.gd.gov.cn/"),
        ("广东省教育考试院", "https://eea.gd.gov.cn/"),
        ("广州市人力资源和社会保障局", "https://rsj.gz.gov.cn/"),
        # 清远地区
        ("清远市人力资源和社会保障局", "https://www.gdqy.gov.cn/channel/srlzyhshbz/?menuid=null"),
        ("清远市人社局-通知公告", "https://www.gdqy.gov.cn/xxgk/zzjg/zfjg/srlzyhshbz/zhzx/tzgg/"),
        ("清远市教育局", "https://www.gdqy.gov.cn/channel/qysjyj/"),
        ("清远市教育局-通知公告", "https://www.gdqy.gov.cn/xxgk/zzjg/zfjg/qysjyj/tzgga/"),
        # 清远下辖县市区（均实测可抓取）
        ("清城区-通知公告", "https://www.qingcheng.gov.cn/xxgk/tzgg2/"),
        ("清新区-人事信息", "https://www.qingxin.gov.cn/zwgk/rsxx/"),
        ("英德市-招聘信息", "https://www.yingde.gov.cn/zwgk/rsxx/zpxx/"),
        ("连州市-人事信息", "http://www.lianzhou.gov.cn/xxgk/rsxx2/index.html"),
        ("连州市-事业编招聘", "https://www.lianzhou.gov.cn/xxgk/rsxx/sydwzp/"),
        ("连南县-招聘信息", "https://www.liannan.gov.cn/zwgk/zpxx/"),
        ("连山县-招聘信息", "https://www.gdls.gov.cn/zwgk/rsxx/zpxx/"),
        ("佛冈县-通知公告", "https://www.fogang.gov.cn/ywdt/gggs/tzgg/"),
        ("阳山县-人事招聘", "https://www.yangshan.gov.cn/xxgk/zfxxgkml/zfbmxxgkml/qt/ryzl/"),
    ]
    for name, url in defaults:
        c.execute(
            "INSERT OR IGNORE INTO sources(name,url) VALUES(?,?)", (name, url)
        )
    # 迁移：清理已失效（404/403）的旧源
    for broken in ("https://hrss.gd.gov.cn/gdsydw/",
                   "https://hrss.gd.gov.cn/zwgk/tzgg/",
                   "https://www.gdzz.cn/"):
        c.execute("DELETE FROM sources WHERE url=?", (broken,))
    conn.commit()
    conn.close()


def now_str():
    return time.strftime("%Y-%m-%d %H:%M:%S")


# ---------- 示例数据（首次启动空库时预置，可删除） ----------
SAMPLES = [
    {"title": "【示例】2026年广东省梅州市梅县区公开招聘教师60名公告",
     "url": "sample://jiaoshi-meixian",
     "region": "广东", "category": "教师",
     "content": "报名时间：2026年10月10日至2026年10月16日。笔试时间：2026年11月2日。面试时间：2026年11月20日。招聘岗位为梅县区公办中小学教师，要求相应教师资格证。"},
    {"title": "【示例】2026年下半年广州市事业单位公开招聘工作人员公告",
     "url": "sample://shiyewei-guangzhou",
     "region": "广东", "category": "事业单位",
     "content": "报名时间：2026年10月8日至2026年10月12日。笔试时间：2026年10月26日。本次公开招聘事业单位工作人员215名。"},
    {"title": "【示例】2026年广东省公务员考试录用公告（节选示例）",
     "url": "sample://gongwuyuan-gd",
     "region": "广东", "category": "公务员",
     "content": "报名时间：2026年11月5日至2026年11月11日。笔试时间：2026年12月14日。全省各级机关计划招录公务员15801名。"},
    {"title": "【示例】佛山市三水区人民医院公开招聘护理人员公告",
     "url": "sample://yiliao-foshan",
     "region": "广东", "category": "医疗",
     "content": "报名时间：2026年9月28日至2026年10月9日。面试时间：2026年10月18日。招聘护士、药师等岗位共35名。"},
    {"title": "【示例】中国南方电网广东公司2026年校园招聘公告",
     "url": "sample://guoqi-nfdw",
     "region": "广东", "category": "国企",
     "content": "报名截止：2026年10月20日。笔试时间：2026年11月8日。面向2026届高校毕业生招聘电气类、计算机类等岗位。"},
]


def seed_samples_if_empty():
    conn = get_conn()
    count = conn.execute("SELECT COUNT(*) AS c FROM announcements").fetchone()["c"]
    conn.close()
    if count > 0:
        return 0
    import parser as date_parser
    for s in SAMPLES:
        aid = add_announcement_manual(s["title"], s["url"], s["content"],
                                      s["region"], s["category"])
        if aid:
            for label, d in date_parser.extract_dates(s["content"]):
                add_key_date(aid, label, d)
    return len(SAMPLES)


# ---------- 公告 ----------
def list_announcements(keyword="", category="", only_unpublished=0):
    conn = get_conn()
    q = (
        "SELECT a.*, "
        "(SELECT COUNT(*) FROM publish_records p WHERE p.announcement_id=a.id) AS pub_count "
        "FROM announcements a WHERE 1=1"
    )
    args = []
    if keyword:
        q += " AND (a.title LIKE ? OR a.content LIKE ?)"
        args += [f"%{keyword}%", f"%{keyword}%"]
    if category:
        q += " AND a.category=?"
        args.append(category)
    if only_unpublished:
        q += " AND (SELECT COUNT(*) FROM publish_records p WHERE p.announcement_id=a.id)=0"
    q += " ORDER BY a.created_at DESC LIMIT 500"
    rows = [dict(r) for r in conn.execute(q, args)]
    conn.close()
    return rows


def upsert_announcement(title, url, source="", content="", region="广东", category="其他"):
    conn = get_conn()
    c = conn.cursor()
    try:
        c.execute(
            "INSERT INTO announcements(title,url,source,region,category,content) VALUES(?,?,?,?,?,?)",
            (title, url, source, region, category, content or ""),
        )
        conn.commit()
        return c.lastrowid
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def add_announcement_manual(title, url, content="", region="广东", category="其他"):
    return upsert_announcement(title, url or ("manual://" + now_str()), "手动录入",
                               content, region, category)


def get_announcement(aid):
    conn = get_conn()
    row = conn.execute("SELECT * FROM announcements WHERE id=?", (aid,)).fetchone()
    conn.close()
    return dict(row) if row else None


def delete_announcement(aid):
    conn = get_conn()
    conn.execute("DELETE FROM announcements WHERE id=?", (aid,))
    conn.execute("DELETE FROM key_dates WHERE announcement_id=?", (aid,))
    conn.execute("DELETE FROM publish_records WHERE announcement_id=?", (aid,))
    conn.commit()
    conn.close()


def star_announcement(aid, starred):
    conn = get_conn()
    conn.execute("UPDATE announcements SET starred=? WHERE id=?", (1 if starred else 0, aid))
    conn.commit()
    conn.close()


# ---------- 关键日期 ----------
def add_key_date(announcement_id, label, date):
    conn = get_conn()
    try:
        conn.execute(
            "INSERT OR IGNORE INTO key_dates(announcement_id,label,date) VALUES(?,?,?)",
            (announcement_id, label, date),
        )
        conn.commit()
    finally:
        conn.close()


def list_key_dates(days=0):
    conn = get_conn()
    q = (
        "SELECT k.*, a.title AS announcement_title, a.region "
        "FROM key_dates k LEFT JOIN announcements a ON a.id=k.announcement_id "
        "WHERE date >= date('now','localtime')"
    )
    args = []
    if days:
        q += " AND date <= date('now','localtime',?)"
        args.append(f"+{days} day")
    q += " ORDER BY k.date ASC"
    rows = [dict(r) for r in conn.execute(q, args)]
    conn.close()
    return rows


# ---------- 发布台账 ----------
def add_publish_record(announcement_id, platform, status="已发布", link="", note="", views=0, likes=0):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "INSERT INTO publish_records(announcement_id,platform,status,link,note,views,likes) "
        "VALUES(?,?,?,?,?,?,?)",
        (announcement_id, platform, status, link, note, views, likes),
    )
    conn.commit()
    rid = c.lastrowid
    conn.close()
    return rid


def list_publish_records(announcement_id=None):
    conn = get_conn()
    q = (
        "SELECT p.*, a.title AS announcement_title FROM publish_records p "
        "LEFT JOIN announcements a ON a.id=p.announcement_id"
    )
    args = []
    if announcement_id:
        q += " WHERE p.announcement_id=?"
        args.append(announcement_id)
    q += " ORDER BY p.published_at DESC"
    rows = [dict(r) for r in conn.execute(q, args)]
    conn.close()
    return rows


def delete_publish_record(rid):
    conn = get_conn()
    conn.execute("DELETE FROM publish_records WHERE id=?", (rid,))
    conn.commit()
    conn.close()


def publish_stats():
    conn = get_conn()
    rows = [dict(r) for r in conn.execute(
        "SELECT platform, COUNT(*) AS cnt, SUM(views) AS views, SUM(likes) AS likes "
        "FROM publish_records GROUP BY platform")]
    total_ann = conn.execute("SELECT COUNT(*) AS c FROM announcements").fetchone()["c"]
    conn.close()
    return {"by_platform": rows, "total_announcements": total_ann}


# ---------- 监控源 ----------
def list_sources():
    conn = get_conn()
    rows = [dict(r) for r in conn.execute("SELECT * FROM sources ORDER BY id")]
    conn.close()
    return rows


def add_source(name, url):
    conn = get_conn()
    try:
        conn.execute("INSERT INTO sources(name,url) VALUES(?,?)", (name, url))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def toggle_source(sid, enabled):
    conn = get_conn()
    conn.execute("UPDATE sources SET enabled=? WHERE id=?", (1 if enabled else 0, sid))
    conn.commit()
    conn.close()


# ---------- 设置（AI 接口等） ----------
def load_settings():
    if os.path.exists(SETTINGS_PATH):
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                pass
    return {"ai_base_url": "", "ai_api_key": "", "ai_model": "", "reminder_days": 7}


def save_settings(data):
    cur = load_settings()
    cur.update({k: v for k, v in data.items() if v != "" or k in ("ai_base_url", "ai_model")})
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(cur, f, ensure_ascii=False, indent=2)
    return cur

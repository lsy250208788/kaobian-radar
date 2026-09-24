# -*- coding: utf-8 -*-
"""考编雷达 kaobian-radar —— 招聘考试推广工作台
本地运行：启动后自动打开浏览器 http://127.0.0.1:8765
"""
import os
import sys
import threading
import time
import webbrowser

from flask import Flask, jsonify, request, send_from_directory

import copywriter
import db
import fetcher
import parser as date_parser

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), "static"))


# ---------- 页面 ----------
@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


# ---------- 公告 ----------
@app.route("/api/announcements")
def api_list_announcements():
    return jsonify(db.list_announcements(
        keyword=request.args.get("keyword", ""),
        category=request.args.get("category", ""),
        only_unpublished=int(request.args.get("only_unpublished", 0)),
    ))


@app.route("/api/announcements", methods=["POST"])
def api_add_announcement():
    d = request.json or {}
    if not d.get("title"):
        return jsonify({"error": "标题不能为空"}), 400
    aid = db.add_announcement_manual(
        d["title"], d.get("url", ""), d.get("content", ""),
        d.get("region", "广东"), d.get("category", "其他"),
    )
    if aid:
        for label, dt in date_parser.extract_dates(d.get("content", "")):
            db.add_key_date(aid, label, dt)
    return jsonify({"id": aid})


@app.route("/api/announcements/<int:aid>", methods=["DELETE"])
def api_del_announcement(aid):
    db.delete_announcement(aid)
    return jsonify({"ok": True})


@app.route("/api/announcements/<int:aid>/star", methods=["POST"])
def api_star(aid):
    db.star_announcement(aid, bool((request.json or {}).get("starred")))
    return jsonify({"ok": True})


# ---------- 扫描 ----------
@app.route("/api/scan", methods=["POST"])
def api_scan():
    return jsonify(fetcher.scan_all())


@app.route("/api/sources")
def api_sources():
    return jsonify(db.list_sources())


@app.route("/api/sources", methods=["POST"])
def api_add_source():
    d = request.json or {}
    if not d.get("name") or not d.get("url"):
        return jsonify({"error": "名称和网址必填"}), 400
    ok = db.add_source(d["name"], d["url"])
    return jsonify({"ok": ok}) if ok else (jsonify({"error": "该网址已存在"}), 400)


@app.route("/api/sources/<int:sid>/toggle", methods=["POST"])
def api_toggle_source(sid):
    db.toggle_source(sid, bool((request.json or {}).get("enabled")))
    return jsonify({"ok": True})


# ---------- 文案 ----------
@app.route("/api/generate", methods=["POST"])
def api_generate():
    d = request.json or {}
    ann = db.get_announcement(int(d.get("announcement_id", 0)))
    if not ann:
        return jsonify({"error": "公告不存在"}), 404
    platform = d.get("platform", "小红书笔记")
    out = copywriter.render_from_template(platform, ann)
    if out is None:
        return jsonify({"error": "未知平台模板"}), 400
    return jsonify(out)


@app.route("/api/generate_ai", methods=["POST"])
def api_generate_ai():
    d = request.json or {}
    ann = db.get_announcement(int(d.get("announcement_id", 0)))
    if not ann:
        return jsonify({"error": "公告不存在"}), 404
    s = db.load_settings()
    if not (s.get("ai_base_url") and s.get("ai_api_key") and s.get("ai_model")):
        return jsonify({"error": "请先在【设置】里配置 AI 接口地址、密钥和模型"}), 400
    try:
        out = copywriter.render_with_ai(
            d.get("platform", "小红书笔记"), ann,
            s["ai_base_url"], s["ai_api_key"], s["ai_model"])
    except Exception as e:
        return jsonify({"error": f"AI 调用失败：{type(e).__name__}: {e}"}), 502
    return jsonify(out)


@app.route("/api/templates")
def api_templates():
    return jsonify(list(copywriter.TEMPLATES.keys()))


# ---------- 发布台账 ----------
@app.route("/api/publish_records")
def api_records():
    aid = request.args.get("announcement_id")
    return jsonify(db.list_publish_records(int(aid) if aid else None))


@app.route("/api/publish_records", methods=["POST"])
def api_add_record():
    d = request.json or {}
    if not d.get("announcement_id") or not d.get("platform"):
        return jsonify({"error": "公告和平台必填"}), 400
    rid = db.add_publish_record(
        int(d["announcement_id"]), d["platform"], d.get("status", "已发布"),
        d.get("link", ""), d.get("note", ""),
        int(d.get("views") or 0), int(d.get("likes") or 0))
    return jsonify({"id": rid})


@app.route("/api/publish_records/<int:rid>", methods=["DELETE"])
def api_del_record(rid):
    db.delete_publish_record(rid)
    return jsonify({"ok": True})


@app.route("/api/stats")
def api_stats():
    return jsonify(db.publish_stats())


# ---------- 关键日期 / 提醒 ----------
@app.route("/api/key_dates")
def api_key_dates():
    days = int(request.args.get("days", 0))
    return jsonify(db.list_key_dates(days))


@app.route("/api/today_brief")
def api_today_brief():
    s = db.load_settings()
    days = int(s.get("reminder_days", 7))
    dates = db.list_key_dates(days)
    unpublished = [a for a in db.list_announcements(only_unpublished=1)][:20]
    return jsonify({"reminder_days": days, "upcoming": dates, "unpublished": unpublished})


# ---------- 设置 ----------
@app.route("/api/settings")
def api_get_settings():
    s = db.load_settings()
    s["ai_api_key"] = "••••已保存•••" if s.get("ai_api_key") else ""
    return jsonify(s)


@app.route("/api/settings", methods=["POST"])
def api_set_settings():
    d = request.json or {}
    if d.get("ai_api_key", "").startswith("••••"):
        d.pop("ai_api_key", None)  # 未修改密钥
    cur = db.save_settings(d)
    cur["ai_api_key"] = "••••已保存•••" if cur.get("ai_api_key") else ""
    return jsonify(cur)


def find_free_port(start=8765):
    """从 start 开始找第一个可用端口，避免端口占用导致启动失败"""
    import socket
    for port in range(start, start + 20):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    return start


def open_browser(port):
    time.sleep(1.2)
    webbrowser.open(f"http://127.0.0.1:{port}")


def auto_scan():
    """启动时后台静默扫描一次官网"""
    time.sleep(2)
    try:
        result = fetcher.scan_all()
        print(f"[自动扫描] 新增 {result['total_new']} 条公告")
    except Exception as e:
        print(f"[自动扫描] 失败：{type(e).__name__}: {e}")


def main():
    db.init_db()
    seeded = db.seed_samples_if_empty()
    if seeded:
        print(f"[初始化] 已预置 {seeded} 条示例公告（可删除）")
    port = find_free_port()
    threading.Thread(target=auto_scan, daemon=True).start()
    threading.Thread(target=open_browser, args=(port,), daemon=True).start()
    print("=" * 50)
    print("  考编雷达 kaobian-radar 已启动")
    print(f"  请在浏览器访问 http://127.0.0.1:{port}")
    print("  关闭此窗口即可退出软件")
    print("=" * 50)
    app.run(host="127.0.0.1", port=port, debug=False)


if __name__ == "__main__":
    main()

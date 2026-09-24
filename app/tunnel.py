# -*- coding: utf-8 -*-
"""公网分享模块：通过 Cloudflare Quick Tunnel（免费、无需注册）
把本机端口映射为一个临时公网地址 https://xxx.trycloudflare.com
"""
import os
import re
import subprocess
import sys
import threading
import time

_URL_RE = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")

_proc = None
_url = None
_lock = threading.Lock()


def _find_binary():
    """定位 cloudflared.exe：打包后取 _MEIPASS，源码运行取项目 tools 目录"""
    if getattr(sys, "frozen", False):
        cand = os.path.join(sys._MEIPASS, "cloudflared.exe")
        if os.path.exists(cand):
            return cand
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cand = os.path.join(base, "tools", "cloudflared.exe")
    return cand if os.path.exists(cand) else None


def _log_path():
    binary = _find_binary()
    return os.path.join(os.path.dirname(binary) or ".", "tunnel.log")


def status():
    return {"running": _proc is not None and _proc.poll() is None, "url": _url}


def start(port):
    """启动隧道；返回 (ok, url_or_error)"""
    global _proc, _url
    with _lock:
        if _proc is not None and _proc.poll() is None:
            return True, _url or "隧道启动中，请稍候再查询"
        binary = _find_binary()
        if not binary:
            return False, "未找到 cloudflared.exe（应内置于软件中）"
        _url = None
        logpath = _log_path()
        try:
            if os.path.exists(logpath):
                os.remove(logpath)  # 清掉旧日志，避免解析到过期 URL
        except OSError:
            pass
        try:
            _proc = subprocess.Popen(
                [binary, "tunnel", "--url", f"http://127.0.0.1:{port}",
                 "--no-autoupdate", "--logfile", logpath],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except Exception as e:
            _proc = None
            return False, f"启动失败: {type(e).__name__}: {e}"
    return True, None


def wait_url(timeout=40):
    """轮询日志解析公网地址（cloudflared 把 URL 输出到日志文件）"""
    global _url
    logpath = _log_path()
    deadline = time.time() + timeout
    while time.time() < deadline:
        if _proc is not None and _proc.poll() is not None:
            return None  # 进程已退出
        try:
            with open(logpath, encoding="utf-8", errors="replace") as f:
                m = _URL_RE.search(f.read())
            if m:
                _url = m.group(0)
                return _url
        except OSError:
            pass
        time.sleep(1)
    return None


def stop():
    global _proc, _url
    with _lock:
        if _proc is not None:
            try:
                _proc.terminate()
                _proc.wait(timeout=10)
            except Exception:
                try:
                    _proc.kill()
                except Exception:
                    pass
        _proc = None
        _url = None

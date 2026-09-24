# -*- coding: utf-8 -*-
"""恢复被破坏的 .git：init + fetch 远程历史 + 恢复 v0.1.5 改动 + 推送"""
import os
import shutil
import subprocess

ROOT = r'C:\Users\shuig\WorkBuddy\kaobian-radar'
TMP = r'C:\Users\shuig\WorkBuddy\kaobian-radar\_recover_tmp'
GIT = r'C:/Users/shuig/.workbuddy/binaries/PortableGit/versions/1.2.0/cmd/git.exe'
REMOTE = 'https://github.com/lsy250208788/kaobian-radar.git'

env = dict(os.environ,
           GIT_EDITOR='true', GIT_SEQUENCE_EDITOR='true', GIT_PAGER='cat',
           GIT_TERMINAL_PROMPT='0')

def run(*args, **kw):
    r = subprocess.run([GIT, *args], capture_output=True, cwd=ROOT, env=env,
                       timeout=180, **kw)
    out = r.stdout.decode('utf-8', errors='replace').strip()
    err = r.stderr.decode('utf-8', errors='replace').strip()
    return r.returncode, out, err

# 1. 备份 v0.1.5 改动文件
os.makedirs(TMP, exist_ok=True)
for f in ['app/db.py', 'app/static/index.html']:
    src = os.path.join(ROOT, f.replace('/', os.sep))
    dst = os.path.join(TMP, os.path.basename(f))
    shutil.copy2(src, dst)
print('1. 备份完成')

# 2. 重建仓库
for d in ['.git']:
    p = os.path.join(ROOT, d)
    if os.path.isdir(p):
        shutil.rmtree(p, ignore_errors=True)
print('2. init:', run('init')[0] == 0)
run('config', 'user.name', '乜野丸')
run('config', 'user.email', 'nienowan@users.noreply.github.com')
run('remote', 'add', 'origin', REMOTE)

# 3. 拉取远程历史（直连优先）
code, out, err = run('-c', 'http.proxy=', '-c', 'https.proxy=', 'fetch', 'origin', 'main')
print('3. fetch:', code, (err or out)[:150])
if code != 0:
    code, out, err = run('fetch', 'origin', 'main')
    print('   fetch(代理):', code, (err or out)[:150])
assert code == 0, 'fetch 失败'

# 4. 重置到远程版本
code, out, err = run('reset', '--hard', 'FETCH_HEAD')
print('4. reset:', code)
code, out, err = run('log', '--oneline', '-3')
print('   远程历史:'); print('  ' + out.replace('\n', '\n  '))

# 5. 恢复 v0.1.5 改动
shutil.copy2(os.path.join(TMP, 'db.py'), os.path.join(ROOT, 'app', 'db.py'))
shutil.copy2(os.path.join(TMP, 'index.html'), os.path.join(ROOT, 'app', 'static', 'index.html'))
shutil.rmtree(TMP, ignore_errors=True)
print('5. v0.1.5 改动已恢复')

# 6. 提交
MSG = ("feat: v0.1.5 监控源扩展至清远全市 9 个县市区\n\n"
       "- 新增: 清城区/清新区/英德市/连州市(2源)/连南县/连山县/佛冈县/阳山县\n"
       "- 9 个县级源全部实测可抓取, 单次扫描共抓取 125 条公告\n"
       "- 分类准确(教师/医疗/事业单位/国企), URL 去重正常")
code, out, err = run('add', '-A')
code, out, err = run('commit', '-m', MSG)
print('6. commit:', code, out[:80] or err[:150])

# 7. 推送
code, out, err = run('-c', 'http.proxy=', '-c', 'https.proxy=', 'push', '-u', 'origin', 'main')
print('7. push:', code, (out or err)[:200])
if code != 0:
    code, out, err = run('push', '-u', 'origin', 'main')
    print('   push(代理):', code, (out or err)[:200])
print('DONE')

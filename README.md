# 📡 考编雷达 kaobian-radar

一款为**招聘考试推广运营**打造的本地工作台：把「盯公告 → 写文案 → 发平台 → 记台账」整条流水线装进一个 exe。

专为公考/事编/教师/医疗/国企招聘类自媒体运营者设计，以广东省为主（监控源可自由增删）。

## ✨ 功能

| 模块 | 说明 |
|------|------|
| 📡 公告雷达 | 定时/手动扫描人事考试网、人社厅等官网公告，按关键词自动分类（公务员/事业单位/教师/医疗/国企）并去重；也支持手动粘贴录入 |
| ✍️ 文案工坊 | 选中公告一键生成小红书笔记、公众号推文、朋友圈文案、社群话术初稿；模板离线可用，也可接自定义 AI 接口（OpenAI 兼容格式）精写 |
| 📋 发布台账 | 记录每条公告在哪些平台发过、何时发的、浏览/点赞数据，按平台汇总统计 |
| 📅 日程提醒 | 自动从公告正文提取报名截止、笔试、面试等关键日期；启动时弹窗汇总未来 7 天待办和未发布公告 |
| 🌓 双主题 | 浅色 / 深色一键切换 |

## 🚀 快速开始

### 方式一：直接运行 exe（推荐）

1. 下载或编译 `kaobian-radar.exe`，双击运行
2. 软件会启动本地服务并自动打开浏览器（`http://127.0.0.1:8765`）
3. 关闭命令行窗口即退出

数据全部保存在 exe 同级的 `data/` 文件夹（SQLite），**不上传任何服务器**。

### 方式二：源码运行

```bash
pip install flask requests
python app/main.py
```

### 打包 exe

```bash
pip install pyinstaller
pyinstaller --noconfirm --onefile --name kaobian-radar ^
  --add-data "app/static;static" --paths app app/main.py
```

> Linux/macOS 打包时把 `--add-data` 的 `;` 换成 `:`。

## 🤖 配置 AI 精写（可选）

在【设置】页填写 OpenAI 兼容接口：

- **Base URL**：如 `https://api.deepseek.com/v1`（DeepSeek / 通义 / Kimi 等均支持此格式）
- **API Key**
- **模型名**：如 `deepseek-chat`

不配置也完全可用——模板生成不需要联网。

## 🌐 添加监控源

内置 5 个广东主流招聘信息源，可在【设置】页增删，任何能列出公告链接的网页都可以作为源。

## 📁 目录结构

```
kaobian-radar/
├── app/
│   ├── main.py        # Flask 入口 + API
│   ├── db.py          # SQLite 数据层
│   ├── fetcher.py     # 公告抓取与分类
│   ├── parser.py      # 关键日期提取
│   ├── copywriter.py  # 文案模板 + AI 调用
│   └── static/index.html  # 前端单页
├── data/              # 运行时数据（gitignore）
├── dist/kaobian-radar.exe
└── requirements.txt
```

## ⚠️ 免责声明

- 公告信息以各官方网站原文为准，本工具仅作信息聚合辅助
- 抓取频率较低（手动触发为主），请勿高频请求他人网站
- 请遵守目标网站的 robots 协议与服务条款

## License

MIT

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目简介

微信公众号草稿箱管理 Skill，可作为 OpenClaw（Telegram Bot 平台）的插件运行，也可通过命令行独立使用。

## 环境准备

```bash
# Python 依赖
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Node.js 依赖（Markdown 转换脚本）
cd scripts && npm ci && cd ..

# 配置文件
cp config.yaml.template config.yaml
# 然后填入真实的 appid 和 appsecret
```

## 常用命令

```bash
# 测试连接（验证配置和白名单）
python3 wechat_mp.py test

# 查看草稿数量
python3 wechat_mp.py count

# 查看草稿列表
python3 wechat_mp.py list --count 5

# 创建草稿（--thumb 支持 media_id、本地路径、http URL 三种）
python3 wechat_mp.py draft --title "标题" --content "<p>正文</p>"
python3 wechat_mp.py draft --title "标题" --content "<p>正文</p>" --thumb ./cover.jpg

# 删除草稿
python3 wechat_mp.py delete --media-id MEDIA_ID

# 直接调用 Markdown 转换脚本
node scripts/convert_markdown_to_wx_html.mjs --input input.md --output output.html
```

## 架构说明

### 两层设计

| 文件 | 职责 |
|------|------|
| `wechat_mp.py` | 核心层：微信公众号 API 封装 + CLI 入口 |
| `handler.py` | 接入层：OpenClaw / Telegram Bot 消息路由与格式化 |
| `scripts/convert_markdown_to_wx_html.mjs` | 工具：Markdown → 微信公众号兼容 HTML（带内联样式） |

### 核心类

- **`WeChatMPSkill`**（`wechat_mp.py`）：封装所有微信 API 调用，access_token 自动缓存到 `.cache/token_cache.json`（300s 提前刷新），支持上传本地/远程封面图
- **`WeChatMPHandler`**（`handler.py`）：解析 Telegram 消息文本，路由到对应操作，Markdown 转换优先调用 Node 脚本，降级使用内置正则

### Markdown 转换策略

`handler.py` 的 `_format_for_wechat()` 采用两阶段降级：
1. 调用 `scripts/convert_markdown_to_wx_html.mjs`（依赖 `marked`，输出含内联样式的公众号兼容 HTML）
2. 若 node 不可用或脚本失败，降级到 `_markdown_to_html()` 内置正则转换

### OpenClaw Skill 接入

`skill.json` 定义 Skill 元信息，`handler.py` 的 `handle_message(message, context)` 是入口函数。`context` 中的 `attachments` 字段用于传递封面图片。

## 配置

`config.yaml`（基于 `config.yaml.template`）：

```yaml
appid: "wx..."          # 公众号 AppID
appsecret: "..."        # 公众号 AppSecret
default_author: "Gamehu"
default_source_url: ""  # 可选，原文链接
```

token 缓存路径可通过环境变量 `WECHAT_MP_CACHE_FILE` 覆盖。

## 常见问题

- **错误 40164**：服务器 IP 未加入公众号后台白名单
- **错误 40001**：AppSecret 错误，删除 `.cache/token_cache.json` 后重试
- **素材库无图片**：需在公众号后台预先上传至少一张图片素材（用于默认封面）

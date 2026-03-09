---
name: wechat-mp-skill
description: 微信公众号草稿箱管理 Skill，支持发布图文消息到公众号草稿箱
version: 1.0.0
author: Gamehu
---

# WeChat MP Draft Skill

微信公众号草稿箱管理 Skill，支持将 Markdown/HTML 内容发布到公众号草稿箱。

## 功能

- 创建图文草稿
- 自动上传封面图片
- 查看草稿列表
- 删除草稿
- Markdown 转微信公众号兼容 HTML

## 前置要求

1. 微信公众号（订阅号或服务号）
2. 已开启开发者模式
3. 已获取 AppID / AppSecret
4. 已在公众号后台配置服务器出口 IP 白名单

## 配置

首次使用前执行：

```bash
cp config.yaml.template config.yaml
```

然后填写：

```yaml
appid: "wx_your_appid_here"
appsecret: "your_appsecret_here"
default_author: "Your Name"
default_source_url: ""
```

## 使用方法

### 通过 OpenClaw / Telegram 指令

创建草稿：

```text
发布草稿
标题：文章标题
内容：文章内容（支持 Markdown）
```

查看草稿：

```text
草稿列表
```

删除草稿：

```text
删除草稿 MEDIA_ID
```

统计数量：

```text
草稿数量
```

### 通过命令行

```bash
python3 wechat_mp.py test
python3 wechat_mp.py count
python3 wechat_mp.py list --count 5
python3 wechat_mp.py draft --title "标题" --content "<p>正文</p>"
python3 wechat_mp.py delete --media-id MEDIA_ID
```

## 故障排查

### 错误 40164：IP 不在白名单

在微信公众号后台「开发 -> 基本配置 -> IP 白名单」中添加当前服务器公网 IP。

### 错误 40001：access_token 无效

检查 AppSecret 是否正确，必要时删除 `.cache/token_cache.json` 后重试。

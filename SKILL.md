---
name: wechat-mp-skill
description: Use when 需要通过对话或命令行创建、查询、删除微信公众号草稿，或排查草稿发布失败、封面上传失败、40164/40001 等常见问题
---

# WeChat MP Draft Skill

用于把 Markdown/HTML 内容安全发布到微信公众号草稿箱，并提供列表、删除、统计与故障排查能力。

## Skill 类型

`Business Process & Team Automation`（主） + `Runbook`（辅）。
目标是把“写内容 -> 转换 -> 发草稿 -> 失败排查”压缩成稳定流程。

## 何时使用

- 你要快速创建公众号草稿，避免手工进后台粘贴内容。
- 你要把 Markdown 转为微信公众号更兼容的 HTML。
- 你遇到这些症状：
- `40164`（IP 白名单未配置）
- `40001`（access_token 无效）
- 封面上传失败 / 没传封面时自动选图失败
- 你需要批量查看或删除草稿。

## 不适用场景

- 你要“直接发布上线”而不是“创建草稿”（本 Skill 不负责发布接口）。
- 你要复杂排版（多列、复杂卡片、深度样式调优）；此时建议先在专门排版工具处理。

## 快速流程

1. 准备配置（`config.yaml`）。
2. 用“发布草稿”或 CLI 创建草稿。
3. 失败时按 `Gotchas` 和“故障排查”定位。
4. 用“草稿列表 / 删除草稿 / 草稿数量”做后续管理。

## 配置前置

1. 微信公众号（订阅号或服务号）
2. 已开启开发者模式
3. 已获取 AppID / AppSecret
4. 已在公众号后台配置服务器出口 IP 白名单

首次使用：

```bash
cp config.yaml.template config.yaml
```

最小配置：

```yaml
appid: "wx_your_appid_here"
appsecret: "your_appsecret_here"
default_author: "Your Name"
default_source_url: ""
```

## 使用方式

### 对话指令（OpenClaw / Telegram）

创建草稿（支持 Markdown）：

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

### CLI

```bash
python3 wechat_mp.py test
python3 wechat_mp.py count
python3 wechat_mp.py list --count 5
python3 wechat_mp.py draft --title "标题" --content "<p>正文</p>"
python3 wechat_mp.py delete --media-id MEDIA_ID
```

## 渐进式披露（Progressive Disclosure）

- 常规使用：先读本文件即可。
- 需要看执行细节：再看 `handler.py`（消息解析与回退逻辑）。
- 需要看 API 与 token/cache 行为：再看 `wechat_mp.py`。
- 需要看 Markdown 转换质量：再看 `scripts/convert_markdown_to_wx_html.mjs`。

## Gotchas（高价值）

1. 不传封面时会尝试使用素材库第一张图片；素材库为空会失败。  
建议：生产环境明确传封面，避免依赖“默认首图”。
2. Markdown 转换依赖 Node + `marked`；缺依赖时现在会直接报错（不再静默降级），避免“成功但样式错”。  
建议：部署时先执行 `cd scripts && npm ci`。
3. “草稿箱”是高频词，容易与普通聊天语境重叠触发。  
建议：优先使用“草稿列表 / 草稿数量”等更明确命令。
4. 只给标题不写内容时，系统会把标题作为正文。  
建议：在流程里显式校验“内容是否为空”。
5. `40001` 可能来自错误密钥，也可能来自旧缓存。  
建议：先校验 `config.yaml`，再清理 `.cache/token_cache.json` 重试。

## 故障排查

### 错误 40164：IP 不在白名单

在微信公众号后台「开发 -> 基本配置 -> IP 白名单」中添加当前服务器公网 IP。

### 错误 40001：access_token 无效

检查 AppSecret 是否正确，必要时删除 `.cache/token_cache.json` 后重试。

# wechat-mp-skill

一个用于创建和管理微信公众号草稿箱的 Skill，既可通过聊天命令使用，也可直接通过 CLI 调用。
它覆盖草稿创建、查询、计数、删除、Markdown 转微信公众号兼容 HTML，以及 `40164`、`40001`、token 缓存和封面上传失败等常见问题。

## 适用场景

适用于：
- 把 Markdown 或 HTML 内容创建为微信公众号草稿
- 查询、统计、删除草稿箱内容
- 排查常见微信公众号草稿接口错误

不适用于：
- 最终发布或上线流程
- 非微信公众号内容系统
- 复杂视觉排版或深度样式设计

## 仓库结构

- `SKILL.md`：面向 agent 的触发条件和执行流程
- `references/command-contract.md`：聊天命令与 CLI 的精确契约
- `references/troubleshooting.md`：常见故障处理说明
- `handler.py`：聊天命令路由入口
- `wechat_mp.py`：微信公众号 API 封装和 CLI
- `scripts/convert_markdown_to_wx_html.mjs`：Markdown 转微信兼容 HTML
- `assets/*.txt`：用于 discovery / logic / edge-case 验证的提示词模板

## 最小安装

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd scripts && npm ci && cd ..
cp config.yaml.template config.yaml
```

填写 `config.yaml`：

```yaml
appid: "wx_your_appid_here"
appsecret: "your_appsecret_here"
default_author: "Your Name"
default_source_url: ""
```

## 最小使用方式

CLI：

```bash
python3 wechat_mp.py test
python3 wechat_mp.py count
python3 wechat_mp.py draft --title "测试文章" --content "<p>这是一篇测试草稿</p>"
python3 wechat_mp.py list --count 5
python3 wechat_mp.py delete --media-id MEDIA_ID
```

聊天命令：

```text
发布草稿
标题：文章标题
内容：文章内容（支持 Markdown 或 HTML）
```

其他支持的命令：
- `草稿列表`
- `查看草稿`
- `草稿数量`
- `删除草稿 MEDIA_ID`
- `微信草稿帮助`
- `草稿帮助`

创建草稿的触发词必须是完整命令，例如 `微信草稿`、`发送微信草稿` 或 `发布草稿`。不会对裸 `草稿` 这类更短字符串触发创建流程。

## Validation Prompts 怎么用

`assets/` 目录下的文本文件不是运行时代码，而是手动拿去喂给 LLM 的验证模板：

- `assets/discovery-validation-prompt.txt`：检查 frontmatter 是否容易被正确触发
- `assets/logic-validation-prompt.txt`：检查 workflow 是否足够确定、会不会逼 agent 猜步骤
- `assets/edge-case-validation-prompt.txt`：专门追问失败路径和边界条件

建议在每次修改 `SKILL.md`、`skill.json` 或命令契约后，至少手动跑一轮这三类验证。

## 下一步看哪里

- 看 `SKILL.md`：理解 agent 侧执行流程
- 看 `references/command-contract.md`：查看精确输入契约和命令优先级
- 看 `references/troubleshooting.md`：查看 `40164`、`40001`、Markdown 转换和封面失败的处理方式

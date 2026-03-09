# wechat-mp-skill

一个可独立发布的微信公众号草稿箱 Skill，适用于 OpenClaw，也可以直接通过命令行调用。

## 仓库内容

- `wechat_mp.py`: 微信公众号草稿箱 API 封装和 CLI
- `handler.py`: OpenClaw Skill 入口
- `skill.json`: Skill 元信息
- `config.yaml.template`: 配置模板
- `scripts/convert_markdown_to_wx_html.mjs`: Markdown 转微信兼容 HTML
- `deploy.sh`: 部署到 OpenClaw 服务器的示例脚本

## 已做的安全处理

- 未包含真实 `appid` / `appsecret`
- 所有敏感配置均通过 `config.yaml` 本地填写
- token 缓存默认写入仓库内 `.cache/`，已加入 `.gitignore`

## 快速开始

### 1. 安装依赖

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd scripts
npm ci
cd ..
```

### 2. 配置微信公众号参数

```bash
cp config.yaml.template config.yaml
```

编辑 `config.yaml`：

```yaml
appid: "__FILL_ME_WECHAT_APPID__"
appsecret: "__FILL_ME_WECHAT_APPSECRET__"
default_author: "Your Name"
default_source_url: ""
```

### 3. 验证连接

```bash
python3 wechat_mp.py test
python3 wechat_mp.py count
```

### 4. 创建草稿

```bash
python3 wechat_mp.py draft \
  --title "测试文章" \
  --content "<p>这是一篇测试草稿</p>"
```

指定封面图片时，`--thumb` 支持三种形式：

- 已有素材 `media_id`
- 本地图片路径
- `http(s)` 图片 URL

例如：

```bash
python3 wechat_mp.py draft \
  --title "带封面的文章" \
  --content "<p>正文</p>" \
  --thumb ./cover.jpg
```

## 集成 OpenClaw

1. 将整个目录复制到 OpenClaw skills 目录，例如 `/root/.openclaw/skills/wechat-mp-skill`
2. 复制 `config.yaml.template` 为 `config.yaml` 并填写真实参数
3. 执行：

```bash
python3 -m pip install -r requirements.txt
cd scripts && npm ci
```

4. 在 OpenClaw 中加载该 skill

## 常见问题

### 为什么 `python3 wechat_mp.py test` 报 40164？

公众号后台没有把当前服务器公网 IP 加入白名单。

### 为什么提示素材库中没有图片？

当你没有提供 `--thumb` 或消息附件时，skill 会尝试使用公众号素材库中的第一张图片作为默认封面。请先在公众号后台上传一张图片素材。

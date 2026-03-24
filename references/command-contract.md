# Command Contract

Use these exact request shapes when normalizing user intent.

## Chat Commands

### Create draft

```text
发布草稿
标题：文章标题
内容：文章内容（支持 Markdown 或 HTML）
```

Accepted aliases for the first line:
- `发布草稿`
- `微信草稿`
- `发送微信草稿`

Behavior rules:
- Attachments may provide the cover image.
- Never trigger draft creation on bare `草稿` or other shorter fuzzy phrases. The create command must match a full command phrase at least as specific as `微信草稿`.
- If `内容：` is omitted, ask for content unless the caller explicitly wants title-as-body behavior.
- `微信草稿帮助` and `草稿帮助` are help commands, not create commands.

### List drafts

```text
草稿列表
```

Alias:
- `查看草稿`

Optional count suffix:
- `草稿列表 5条`
- `查看草稿 10条`

### Delete draft

```text
删除草稿 MEDIA_ID
```

### Count drafts

```text
草稿数量
```

### Help

```text
微信草稿帮助
```

Alias:
- `草稿帮助`

Priority rule:
- Match help commands before draft-creation commands because `微信草稿帮助` contains the broader `微信草稿` prefix.

## CLI Commands

```bash
python3 wechat_mp.py test
python3 wechat_mp.py count
python3 wechat_mp.py list --count 5
python3 wechat_mp.py draft --title "标题" --content "<p>正文</p>"
python3 wechat_mp.py delete --media-id MEDIA_ID
```

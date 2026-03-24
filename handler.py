#!/usr/bin/env python3
"""
OpenClaw Skill 处理器
处理 Telegram Bot 发送的指令
"""
import os
import sys
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

# 添加 skill 目录到路径
SKILL_DIR = Path(__file__).parent
sys.path.insert(0, str(SKILL_DIR))

from wechat_mp import WeChatMPSkill, WeChatMPError


class WeChatMPHandler:
    """OpenClaw Telegram Bot 处理器"""
    CREATE_DRAFT_COMMANDS = ("微信草稿", "发送微信草稿", "发布草稿")
    LIST_DRAFT_COMMANDS = ("草稿列表", "查看草稿")
    HELP_COMMANDS = ("微信草稿帮助", "草稿帮助")
    DELETE_DRAFT_COMMANDS = ("删除草稿", "移除草稿")
    COUNT_DRAFT_COMMANDS = ("草稿数量",)
    
    def __init__(self):
        self.skill = None
        self._init_skill()
    
    def _init_skill(self):
        """初始化 Skill"""
        try:
            self.skill = WeChatMPSkill()
            return True
        except WeChatMPError as e:
            print(f"❌ Skill 初始化失败: {e}")
            return False
    
    def handle_message(self, message: str, attachments: list = None) -> str:
        """
        处理 Telegram 消息
        
        Args:
            message: 消息文本
            attachments: 附件列表（图片等）
            
        Returns:
            回复文本
        """
        if not self.skill:
            return "❌ 微信公众号 Skill 未配置，请检查 AppID 和 AppSecret"
        
        text = message.strip()

        # 帮助
        if self._matches_command(text, self.HELP_COMMANDS):
            return self._get_help()

        # 查看草稿列表
        elif self._matches_command(text, self.LIST_DRAFT_COMMANDS):
            return self._handle_list_drafts(text)

        # 发布草稿指令
        elif self._matches_command(text, self.CREATE_DRAFT_COMMANDS):
            return self._handle_create_draft(text, attachments)
        
        # 删除草稿
        elif self._matches_command(text, self.DELETE_DRAFT_COMMANDS):
            return self._handle_delete_draft(text)
        
        # 统计草稿
        elif self._matches_command(text, self.COUNT_DRAFT_COMMANDS):
            return self._handle_count_drafts()

        else:
            return None  # 不处理，让其他 skill 处理

    def _matches_command(self, text: str, commands: tuple[str, ...]) -> bool:
        """命令匹配：支持精确匹配和“命令 + 换行参数”的格式。"""
        normalized = text.strip()
        return any(
            normalized == command or normalized.startswith(f"{command}\n")
            for command in commands
        )
    
    def _handle_create_draft(self, text: str, attachments: list = None) -> str:
        """处理创建草稿请求"""
        try:
            # 解析标题和内容
            # 格式1: 发布草稿 标题：xxx 内容：xxx
            # 格式2: 发布草稿
            #       标题：xxx
            #       内容：xxx
            
            title = None
            content = None
            thumb_source = None
            
            # 提取标题
            title_match = re.search(r'标题[:：]\s*(.+?)(?:\n|$|内容[:：])', text, re.DOTALL)
            if title_match:
                title = title_match.group(1).strip()
            
            # 提取内容
            content_match = re.search(r'内容[:：]\s*(.+)$', text, re.DOTALL)
            if content_match:
                content = content_match.group(1).strip()
            
            # 检查附件（封面图片）
            if attachments:
                for att in attachments:
                    if att.get('type') in {'photo', 'image', 'file'}:
                        thumb_source = att.get('url') or att.get('file_path')
                        break
            
            # 如果没有提取到标题和内容，提示用户
            if not title:
                return """❌ 缺少标题

请使用以下格式：
发布草稿
标题：你的文章标题
内容：文章内容（支持 Markdown/HTML）

可选：附带封面图片"""
            
            if not content:
                return """❌ 缺少内容

请使用以下格式：
发布草稿
标题：你的文章标题
内容：文章内容（支持 Markdown/HTML）

可选：附带封面图片"""
            
            # 转换 Markdown 为微信公众号友好的 HTML（优先使用 markdown-to-wx-html）
            content_html = self._format_for_wechat(content)
            
            # 创建草稿
            result = self.skill.create_draft(
                title=title,
                content=content_html,
                thumb_url=thumb_source
            )
            
            media_id = result.get('media_id')
            
            return f"""✅ 草稿创建成功！

📄 标题：{title}
🆔 Media ID：`{media_id}`

你可以在微信公众号后台的「草稿箱」中查看和编辑。
"""
        except WeChatMPError as e:
            return f"❌ 创建草稿失败：{e}"
        except Exception as e:
            return f"❌ 错误：{e}"
    
    def _handle_list_drafts(self, text: str) -> str:
        """处理查看草稿列表请求"""
        try:
            # 解析数量参数
            count_match = re.search(r'(\d+)条', text)
            count = int(count_match.group(1)) if count_match else 10
            count = min(count, 20)  # 最大 20
            
            items = self.skill.list_drafts(offset=0, count=count, no_content=1)
            
            if not items:
                return "📭 草稿箱是空的"
            
            return self.skill.format_draft_list(items)
            
        except WeChatMPError as e:
            return f"❌ 获取草稿列表失败：{e}"
        except Exception as e:
            return f"❌ 错误：{e}"
    
    def _handle_delete_draft(self, text: str) -> str:
        """处理删除草稿请求"""
        try:
            # 提取 Media ID
            # 格式: 删除草稿 xxx 或 删除草稿 media_id=xxx
            media_id_match = re.search(r'(?:删除|移除)草稿\s+([a-zA-Z0-9_-]+)', text)
            
            if not media_id_match:
                return """❌ 缺少草稿 ID

请使用以下格式：
删除草稿 MEDIA_ID

例如：
删除草稿 1234567890abcdef"""
            
            media_id = media_id_match.group(1)
            
            success = self.skill.delete_draft(media_id)
            
            if success:
                return f"✅ 草稿已删除\n\n🆔 Media ID：`{media_id}`"
            else:
                return "❌ 删除失败"
                
        except WeChatMPError as e:
            return f"❌ 删除草稿失败：{e}"
        except Exception as e:
            return f"❌ 错误：{e}"
    
    def _handle_count_drafts(self) -> str:
        """处理统计草稿请求"""
        try:
            count = self.skill.get_draft_count()
            return f"📊 当前草稿箱共有 **{count}** 条草稿"
        except Exception as e:
            return f"❌ 获取统计失败：{e}"
    
    def _format_for_wechat(self, text: str) -> str:
        """内容转微信公众号 HTML。
        - 明确 HTML 输入：原样返回
        - Markdown 输入：必须使用 wx 转换脚本（缺依赖时给出明确报错）
        """
        if self._looks_like_html(text):
            return text

        node = shutil.which('node')
        script = SKILL_DIR / 'scripts' / 'convert_markdown_to_wx_html.mjs'

        if not node or not script.exists():
            raise WeChatMPError(
                "Markdown 样式转换器不可用：缺少 node 或 scripts/convert_markdown_to_wx_html.mjs。"
                "请执行：cd scripts && npm ci"
            )

        with tempfile.NamedTemporaryFile('w', suffix='.md', delete=False, encoding='utf-8') as md_file:
            md_file.write(text or '')
            md_path = md_file.name

        with tempfile.NamedTemporaryFile('w', suffix='.html', delete=False, encoding='utf-8') as html_file:
            html_path = html_file.name

        try:
            proc = subprocess.run(
                [node, str(script), '--input', md_path, '--output', html_path],
                cwd=str(script.parent),
                capture_output=True,
                text=True,
                timeout=30,
                check=False
            )

            if proc.returncode == 0:
                with open(html_path, 'r', encoding='utf-8') as f:
                    html = f.read().strip()
                if html:
                    return html

            reason = (proc.stderr or proc.stdout or '').strip()
            raise WeChatMPError(
                "Markdown 样式转换失败。请先执行：cd scripts && npm ci。"
                + (f" 详细错误：{reason[:200]}" if reason else "")
            )
        except WeChatMPError:
            raise
        except Exception as e:
            raise WeChatMPError(f"Markdown 样式转换失败：{e}")
        finally:
            try:
                os.unlink(md_path)
            except Exception:
                pass
            try:
                os.unlink(html_path)
            except Exception:
                pass

    def _looks_like_html(self, text: str) -> bool:
        """简单判断输入是否已是 HTML。"""
        if not text:
            return False
        return bool(re.search(r'<[a-zA-Z][^>]*>', text))

    def _markdown_to_html(self, text: str) -> str:
        """简单 Markdown 转 HTML"""
        import re
        
        html = text
        
        # 代码块
        html = re.sub(r'```(\w+)?\n(.*?)```', r'<pre><code>\2</code></pre>', html, flags=re.DOTALL)
        
        # 行内代码
        html = re.sub(r'`([^`]+)`', r'<code>\1</code>', html)
        
        # 粗体
        html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
        html = re.sub(r'__(.+?)__', r'<strong>\1</strong>', html)
        
        # 斜体
        html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
        html = re.sub(r'_(.+?)_', r'<em>\1</em>', html)
        
        # 链接
        html = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', html)
        
        # 段落（简单处理）
        paragraphs = html.split('\n\n')
        html = ''.join(f'<p>{p}</p>' for p in paragraphs if p.strip())
        
        return html
    
    def _get_help(self) -> str:
        """获取帮助信息"""
        return """📚 微信公众号草稿箱 Skill 使用帮助

可用指令：

1️⃣ **发布草稿**
```
发布草稿
标题：文章标题
内容：文章内容（支持 Markdown）
```
可选：附带封面图片

2️⃣ **查看草稿列表**
```
草稿列表
查看草稿
```

3️⃣ **删除草稿**
```
删除草稿 MEDIA_ID
```

4️⃣ **草稿统计**
```
草稿数量
```

💡 **提示**：
- 标题最多 64 字节
- 内容必填，支持 Markdown 语法
- 可以附带图片作为封面
- 创建的草稿可以在公众号后台编辑后发布
"""


# OpenClaw Skill 入口
def handle_message(message: str, context: dict = None) -> str:
    """
    OpenClaw Skill 入口函数
    
    Args:
        message: 消息文本
        context: 上下文信息（包含 attachments 等）
        
    Returns:
        回复文本，如果不需要处理则返回 None
    """
    handler = WeChatMPHandler()
    
    attachments = []
    if context and 'attachments' in context:
        attachments = context['attachments']
    
    return handler.handle_message(message, attachments)


# 测试
if __name__ == "__main__":
    # 测试帮助
    handler = WeChatMPHandler()
    print(handler._get_help())

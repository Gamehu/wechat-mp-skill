import json
import mimetypes
import os
import re
import tempfile
import time
from pathlib import Path
from urllib.parse import urlparse

import requests
import yaml

SKILL_DIR = Path(__file__).parent
DEFAULT_CACHE_FILE = SKILL_DIR / ".cache" / "token_cache.json"


class WeChatMPError(Exception):
    pass


class WeChatMPSkill:
    TOKEN_URL = "https://api.weixin.qq.com/cgi-bin/token"
    DRAFT_ADD_URL = "https://api.weixin.qq.com/cgi-bin/draft/add"
    DRAFT_BATCHGET_URL = "https://api.weixin.qq.com/cgi-bin/draft/batchget"
    DRAFT_COUNT_URL = "https://api.weixin.qq.com/cgi-bin/draft/count"
    DRAFT_DELETE_URL = "https://api.weixin.qq.com/cgi-bin/draft/delete"
    MATERIAL_BATCHGET_URL = "https://api.weixin.qq.com/cgi-bin/material/batchget_material"
    MATERIAL_ADD_URL = "https://api.weixin.qq.com/cgi-bin/material/add_material"

    def __init__(self):
        self.config = self._load_config()
        self.appid = self.config.get("appid")
        self.appsecret = self.config.get("appsecret")
        self.default_author = self.config.get("default_author", "Gamehu")
        self.default_source_url = self.config.get("default_source_url", "")
        cache_file = os.environ.get("WECHAT_MP_CACHE_FILE")
        self.cache_file = Path(cache_file) if cache_file else DEFAULT_CACHE_FILE
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)

        if not self.appid or not self.appsecret:
            raise WeChatMPError("未配置 AppID 或 AppSecret，请先复制 config.yaml.template 为 config.yaml 后填写")

    def _load_config(self):
        config = {
            "appid": "",
            "appsecret": "",
            "default_author": "Gamehu",
            "default_source_url": "",
        }
        config_path = SKILL_DIR / "config.yaml"
        if not config_path.exists():
            return config

        with open(config_path, "r", encoding="utf-8") as file:
            config.update(yaml.safe_load(file) or {})
        return config

    def _request_json(self, method, url, *, ok_errcodes=None, **kwargs):
        ok_errcodes = {0} if ok_errcodes is None else set(ok_errcodes)
        # 将 json= 参数手动序列化为 UTF-8，避免默认 ensure_ascii=True 导致中文乱码
        if "json" in kwargs:
            kwargs["data"] = json.dumps(kwargs.pop("json"), ensure_ascii=False).encode("utf-8")
            kwargs.setdefault("headers", {})["Content-Type"] = "application/json"
        response = requests.request(method, url, timeout=30, **kwargs)
        response.raise_for_status()

        try:
            result = response.json()
        except ValueError as exc:
            raise WeChatMPError(f"微信接口返回了非 JSON 响应: {response.text[:200]}") from exc

        errcode = result.get("errcode")
        if errcode not in (None, *ok_errcodes):
            errmsg = result.get("errmsg", "unknown error")
            raise WeChatMPError(f"[{errcode}] {errmsg}")
        return result

    def _get_access_token(self):
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r", encoding="utf-8") as file:
                    cache = json.load(file)
                if time.time() < cache.get("expire_time", 0) - 300:
                    return cache["access_token"]
            except (OSError, KeyError, ValueError, TypeError):
                pass

        result = self._request_json(
            "GET",
            self.TOKEN_URL,
            params={
                "grant_type": "client_credential",
                "appid": self.appid,
                "secret": self.appsecret,
            },
            ok_errcodes=set(),
        )

        token = result.get("access_token")
        if not token:
            raise WeChatMPError("获取 access_token 失败")

        with open(self.cache_file, "w", encoding="utf-8") as file:
            json.dump(
                {
                    "access_token": token,
                    "expire_time": time.time() + result.get("expires_in", 7200),
                },
                file,
                ensure_ascii=False,
                indent=2,
            )
        return token

    def _build_url(self, endpoint):
        return f"{endpoint}?access_token={self._get_access_token()}"

    def get_default_image_media_id(self):
        result = self._request_json(
            "POST",
            self._build_url(self.MATERIAL_BATCHGET_URL),
            json={"type": "image", "offset": 0, "count": 1},
        )

        items = result.get("item", [])
        if not items:
            raise WeChatMPError("素材库中没有图片，请先在公众号后台上传至少一张图片素材")

        name = items[0].get("name", "未命名")[:20]
        print(f"   使用默认封面: {name}")
        return items[0]["media_id"]

    def _download_remote_file(self, source):
        response = requests.get(source, timeout=30)
        response.raise_for_status()

        suffix = Path(urlparse(source).path).suffix or ".jpg"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as file:
            file.write(response.content)
            return Path(file.name)

    def upload_image_for_thumb(self, source):
        temp_file = None
        source_path = Path(source)

        if re.match(r"^https?://", source, flags=re.IGNORECASE):
            temp_file = self._download_remote_file(source)
            source_path = temp_file
        elif not source_path.exists():
            raise WeChatMPError(f"封面文件不存在: {source}")

        mime_type = mimetypes.guess_type(source_path.name)[0] or "image/jpeg"
        filename = source_path.name or "cover.jpg"

        try:
            with open(source_path, "rb") as file:
                result = self._request_json(
                    "POST",
                    self._build_url(self.MATERIAL_ADD_URL) + "&type=image",
                    files={"media": (filename, file, mime_type)},
                    data={"type": "image"},
                )
        finally:
            if temp_file:
                temp_file.unlink(missing_ok=True)

        media_id = result.get("media_id")
        if not media_id:
            raise WeChatMPError("上传封面图片失败，接口未返回 media_id")
        return media_id

    def _resolve_thumb_media_id(self, thumb_media_id=None, thumb_source=None):
        if thumb_media_id:
            return thumb_media_id
        if thumb_source:
            print("   正在上传封面图片...")
            return self.upload_image_for_thumb(thumb_source)
        print("   未提供封面，使用默认封面...")
        return self.get_default_image_media_id()

    def create_draft(
        self,
        title,
        content,
        author=None,
        thumb_media_id=None,
        thumb_url=None,
        source_url=None,
        digest=None,
    ):
        thumb_media_id = self._resolve_thumb_media_id(
            thumb_media_id=thumb_media_id,
            thumb_source=thumb_url,
        )

        plain = re.sub(r"<[^>]+>", "", content or "").strip()
        # WeChat digest 实测安全上限约 60 字节，以字符数截断更可靠
        draft_digest = digest or (plain[:20] + "..." if len(plain) > 20 else plain)

        article = {
            "title": title,
            "author": author or self.default_author,
            "digest": draft_digest,
            "content": content,
            "thumb_media_id": thumb_media_id,
            "content_source_url": source_url or self.default_source_url,
            "need_open_comment": 0,
            "only_fans_can_comment": 0,
        }

        print(f"📝 正在创建草稿: {title}")
        result = self._request_json(
            "POST",
            self._build_url(self.DRAFT_ADD_URL),
            json={"articles": [article]},
        )

        media_id = result.get("media_id")
        if not media_id:
            raise WeChatMPError("创建草稿失败，接口未返回 media_id")
        print(f"✅ 成功! Media ID: {media_id}")
        return result

    def list_drafts(self, offset=0, count=10, no_content=1):
        result = self._request_json(
            "POST",
            self._build_url(self.DRAFT_BATCHGET_URL),
            json={"offset": offset, "count": count, "no_content": no_content},
        )
        return result.get("item", [])

    def format_draft_list(self, items):
        lines = ["📚 草稿列表：", ""]
        for index, item in enumerate(items, start=1):
            news = item.get("content", {}).get("news_item", [{}])[0]
            title = news.get("title", "无标题")
            author = news.get("author") or self.default_author
            media_id = item.get("media_id", "未知")
            update_time = item.get("update_time", 0)
            lines.append(f"{index}. {title}")
            lines.append(f"   作者：{author}")
            lines.append(f"   Media ID：`{media_id}`")
            if update_time:
                lines.append(f"   更新时间戳：{update_time}")
            lines.append("")
        return "\n".join(lines).strip()

    def delete_draft(self, media_id):
        self._request_json(
            "POST",
            self._build_url(self.DRAFT_DELETE_URL),
            json={"media_id": media_id},
        )
        return True

    def get_draft_count(self):
        result = self._request_json("GET", self._build_url(self.DRAFT_COUNT_URL))
        return result.get("total_count", 0)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="微信公众号草稿箱工具")
    sub = parser.add_subparsers(dest="cmd")

    draft = sub.add_parser("draft", help="创建草稿")
    draft.add_argument("--title", "-t", required=True)
    draft.add_argument("--content", "-c", required=True)
    draft.add_argument("--author", "-a")
    draft.add_argument("--thumb", help="封面图片 media_id、本地路径或 http(s) URL")
    draft.add_argument("--source-url", help="原文链接，可选")

    list_parser = sub.add_parser("list", help="查看草稿列表")
    list_parser.add_argument("--count", type=int, default=5)

    delete_parser = sub.add_parser("delete", help="删除草稿")
    delete_parser.add_argument("--media-id", required=True)

    sub.add_parser("test", help="测试配置和 access_token")
    sub.add_parser("count", help="查看草稿数量")

    args = parser.parse_args()
    if not args.cmd:
        parser.print_help()
        return

    skill = WeChatMPSkill()

    if args.cmd == "test":
        skill._get_access_token()
        print(f"连接正常，草稿数: {skill.get_draft_count()}")
    elif args.cmd == "draft":
        skill.create_draft(
            title=args.title,
            content=args.content,
            author=args.author,
            thumb_url=args.thumb,
            source_url=args.source_url,
        )
    elif args.cmd == "list":
        print(skill.format_draft_list(skill.list_drafts(count=args.count)))
    elif args.cmd == "delete":
        skill.delete_draft(args.media_id)
        print(f"已删除草稿: {args.media_id}")
    elif args.cmd == "count":
        print(f"草稿数量: {skill.get_draft_count()}")


if __name__ == "__main__":
    main()

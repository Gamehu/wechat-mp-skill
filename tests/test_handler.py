import unittest
from unittest.mock import Mock, patch

from handler import WeChatMPHandler


class HandlerCommandRoutingTests(unittest.TestCase):
    def create_handler(self):
        with patch.object(WeChatMPHandler, "_init_skill", autospec=True) as init_skill:
            def fake_init(instance):
                instance.skill = Mock()
                return True

            init_skill.side_effect = fake_init
            return WeChatMPHandler()

    def test_view_drafts_alias_routes_to_list_handler(self):
        handler = self.create_handler()
        handler._handle_list_drafts = Mock(return_value="ok")

        result = handler.handle_message("查看草稿")

        self.assertEqual(result, "ok")
        handler._handle_list_drafts.assert_called_once_with("查看草稿")

    def test_help_command_routes_to_help_handler_before_generic_create_match(self):
        handler = self.create_handler()
        handler._get_help = Mock(return_value="help")
        handler._handle_create_draft = Mock(return_value="draft")

        result = handler.handle_message("微信草稿帮助")

        self.assertEqual(result, "help")
        handler._get_help.assert_called_once_with()
        handler._handle_create_draft.assert_not_called()

    def test_create_draft_requires_explicit_content(self):
        handler = self.create_handler()
        handler._format_for_wechat = Mock(return_value="<p>x</p>")

        result = handler._handle_create_draft("发布草稿\n标题：只有标题")

        self.assertIn("缺少内容", result)
        handler._format_for_wechat.assert_not_called()

    def test_delete_command_does_not_trigger_on_embedded_text(self):
        handler = self.create_handler()
        handler._handle_delete_draft = Mock(return_value="deleted")

        result = handler.handle_message("请告诉我删除草稿接口怎么设计")

        self.assertIsNone(result)
        handler._handle_delete_draft.assert_not_called()

    def test_count_command_does_not_trigger_on_embedded_text(self):
        handler = self.create_handler()
        handler._handle_count_drafts = Mock(return_value="count")

        result = handler.handle_message("我想知道草稿数量接口的返回字段")

        self.assertIsNone(result)
        handler._handle_count_drafts.assert_not_called()

    def test_short_grass_draft_phrase_does_not_trigger_create(self):
        handler = self.create_handler()
        handler._handle_create_draft = Mock(return_value="draft")

        result = handler.handle_message("草稿\n标题：测试\n内容：正文")

        self.assertIsNone(result)
        handler._handle_create_draft.assert_not_called()

    def test_wechat_draft_phrase_triggers_create(self):
        handler = self.create_handler()
        handler._handle_create_draft = Mock(return_value="draft")

        result = handler.handle_message("微信草稿\n标题：测试\n内容：正文")

        self.assertEqual(result, "draft")
        handler._handle_create_draft.assert_called_once_with("微信草稿\n标题：测试\n内容：正文", None)


if __name__ == "__main__":
    unittest.main()

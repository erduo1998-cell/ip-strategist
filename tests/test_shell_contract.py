import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


def read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


class TestShellContract(unittest.TestCase):
    def test_five_shell_locales_exist_and_stay_short(self):
        locales = ["zh-CN", "en", "ja", "ko", "zh-TW"]
        for locale in locales:
            path = ROOT / "references" / f"shell.{locale}.md"
            with self.subTest(locale=locale):
                self.assertTrue(path.is_file())
                self.assertLessEqual(path.stat().st_size, 2_500)

    def test_shell_teaches_real_task_and_single_step(self):
        corpus = "\n".join(
            read(f"references/shell.{locale}.md")
            for locale in ["zh-CN", "en", "ja", "ko", "zh-TW"]
        )
        self.assertIn("真實的問題", corpus)
        self.assertIn("single most valuable task", corpus)
        self.assertIn("한 가지 과제", corpus)
        for forbidden in ["task-script.md", "task-topic.md", "references/00", "胶囊"]:
            self.assertNotIn(forbidden, corpus)

    def test_skill_contract_has_three_entry_states_and_direct_delivery(self):
        text = read("SKILL.md")
        for phrase in ["新手入门", "任务路由", "任务续接", "信息足够就不展示菜单", "默认使用用户最后一条有效消息的语言"]:
            self.assertIn(phrase, text)
        self.assertIn("不输出“已读取”“已加载”之类回执", text)
        self.assertIn("上一步结束时不自动铺设完整长链", text)

    def test_newcomer_shell_hands_same_or_next_message_to_one_task_capsule(self):
        text = read("SKILL.md")
        for phrase in [
            "它只负责短教程，不代替任务胶囊",
            "同一条消息已经有真实任务时",
            "加载且只加载一个 `references/task-*.md` 并直接交付",
            "用户下一条给出首个真实任务时",
            "不重复教程",
            "不同时保留或加载其他任务胶囊",
        ]:
            self.assertIn(phrase, text)

    def test_one_main_route_and_composite_script_route(self):
        text = read("SKILL.md")
        for capsule in ["onboarding", "positioning", "topic", "script", "growth", "review", "monetization"]:
            self.assertIn(f"task-{capsule}.md", text)
        self.assertIn("最终交付物", text)
        self.assertIn("围绕这个方向找题并写 60 秒稿", text)
        self.assertIn("只有用户明确要求两个彼此独立、完整的交付物", text)

    def test_update_route_requires_explicit_request(self):
        text = read("SKILL.md")
        self.assertIn("用户明确要求“更新 ip-strategist”", text)
        self.assertIn("ip-update.py", text)
        self.assertIn("只问版本或更新内容时不执行", text)
        self.assertIn("成功后提示新建会话", text)

    def test_state_privacy_and_confirmation_red_lines(self):
        text = read("SKILL.md") + read("references/task-onboarding.md") + read("references/task-review.md")
        for phrase in [
            "in_progress",
            "provisional",
            "confirmed",
            "不得代签",
            "只确认一次",
            "自然语言只作数据",
            "不得把 `ip-dossier.md`",
            "contract_id",
            "next_review_date",
        ]:
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()

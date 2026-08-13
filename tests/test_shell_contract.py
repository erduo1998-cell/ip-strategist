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
        self.assertIn("根因、症狀或待驗證假設", corpus)
        self.assertIn("root cause, a symptom, or an untested hypothesis", corpus)
        self.assertIn("근본 원인인지 증상인지 검증되지 않은 가설인지", corpus)
        for forbidden in ["task-script.md", "task-topic.md", "references/00", "胶囊"]:
            self.assertNotIn(forbidden, corpus)

    def test_skill_contract_has_three_entry_states_and_direct_delivery(self):
        text = read("SKILL.md")
        for phrase in ["新手入门", "首次建档", "断点续访", "任务路由", "默认使用用户最后一条有效消息的语言"]:
            self.assertIn(phrase, text)
        self.assertIn("不输出“已读取”“已加载”之类回执", text)
        self.assertIn("上一步结束时不自动铺设完整长链", text)

    def test_newcomer_shell_never_bypasses_required_onboarding(self):
        text = read("SKILL.md")
        for phrase in [
            "同一条消息已有真实任务时，把它作为建档证据和后续待办",
            "把原任务按用户原意记入“上次会话约定”作为建档后待办",
            "任何定位、选题、写稿、增长、复盘或变现任务都先路由到",
            "不得用三问微诊断、显式假设或通用建议冒充完整判断",
            "无论用户提出什么新任务，都先从 `onboarding_step` 续完建档",
            "档案为 `provisional` 或 `confirmed` 且校验通过时",
        ]:
            self.assertIn(phrase, text)

        onboarding = read("references/task-onboarding.md")
        self.assertIn("建档完成后重判并处理：", onboarding)
        self.assertIn("不得让用户重新输入", onboarding)

    def test_formal_tasks_require_dossier_summary_and_problem_reframe(self):
        text = read("SKILL.md")
        for phrase in [
            "后续每个任务必须先读取任务相关档案摘要、历史数据、依据账本和认知沉淀",
            "根因、症状还是待验证假设",
            "所有正式任务都消费 `ip-context.py` 的任务相关摘要",
            "问题重判",
            "是症状或伪问题时，先明确纠偏并改解真正问题",
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

    def test_shells_request_consent_before_the_first_onboarding_question(self):
        shells = {
            "references/shell.zh-CN.md": ("是否同意", "为什么现在做 IP"),
            "references/shell.zh-TW.md": ("是否同意", "為什麼現在做 IP"),
            "references/shell.en.md": ("Do you consent", "why build an IP now"),
            "references/shell.ja.md": ("同意しますか", "なぜ今 IP を始めるのか"),
            "references/shell.ko.md": ("동의하시나요", "왜 지금 IP를 만들려는가"),
        }
        for relative, (consent, first_question) in shells.items():
            with self.subTest(relative=relative):
                text = read(relative)
                self.assertIn(consent, text)
                self.assertIn(first_question, text)
                self.assertLess(text.index(consent), text.index(first_question))

    def test_new_dossier_template_has_no_persistent_bypass_mode(self):
        text = read("templates/dossier-template.md")
        self.assertIn("档案使用状态", text)
        self.assertIn("完整能力", text)
        self.assertNotIn("- **默认模式**", text)
        self.assertNotIn("B（单次咨询）", text)


if __name__ == "__main__":
    unittest.main()

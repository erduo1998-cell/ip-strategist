import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


def read(relative_path):
    return (ROOT / relative_path).read_text(encoding="utf-8")


class TestOnboardingStructure(unittest.TestCase):
    def test_reference_has_navigation_six_modules_and_completion_gate(self):
        text = read("references/11-建档诊断.md")
        self.assertTrue(text.startswith("---\n"))
        self.assertIn("dimension: 建档诊断", text)
        self.assertIn("## 目录", text)
        for step in ["goal", "evidence", "audience", "value", "business", "execution"]:
            self.assertIn("`%s`" % step, text)
        self.assertIn("每轮只问一个核心问题", text)
        self.assertIn("首次建档完成门槛", text)
        self.assertIn("v0.1 建档草案输出格式", text)
        self.assertIn("已确认事实/暂定假设/未知", text)
        self.assertIn("下一步验证", text)

    def test_skill_routes_onboarding_and_preserves_main_workflow(self):
        text = read("SKILL.md")
        self.assertIn('version: "1.9.0"', text)
        self.assertIn("十二个维度文件（00-11）", text)
        self.assertIn("references/11-建档诊断.md", text)
        self.assertIn("onboarding_status: in_progress", text)
        self.assertIn("视为已同意，不重复询问", text)
        self.assertIn("不机械重问通用首问", text)
        self.assertIn("in_progress → provisional", text)
        self.assertIn("provisional → confirmed", text)
        self.assertIn("初始化依据账本只有三种状态", text)
        self.assertIn("不得复制空模板后直接放行", text)
        self.assertIn("三问微诊断", text)
        for phase in ["**1. 诊**", "**2. 契**", "**3. 行**", "**4. 盘**"]:
            self.assertIn(phase, text)
        self.assertIn("7 个 definitive 字段", text)

    def test_dossier_schema_exposes_onboarding_state_and_core_fields(self):
        text = read("templates/dossier-template.md")
        self.assertIn("schema_version: 1.9", text)
        self.assertIn("onboarding_status: in_progress", text)
        self.assertIn("onboarding_step: goal", text)
        for label in [
            "为什么现在做 IP",
            "90 天唯一主要目标",
            "成功标准",
            "目标用户的具体状态",
            "用户的核心问题",
            "信任依据",
            "当前价值",
            "未来价值",
            "当前主行为",
            "变现方向或长期用途",
            "每周执行资源",
            "人设 / 伦理 / 隐私红线",
            "当前最大未知",
        ]:
            self.assertIn("**%s**" % label, text)
        self.assertIn("状态（已确认事实 / 暂定假设 / 未知）", text)
        self.assertIn("下一步验证", text)
        self.assertIn("不要先重问为什么现在", read("references/11-建档诊断.md"))

    def test_behavior_release_gate_contains_all_ten_cases(self):
        text = read("tests/onboarding_behavior_cases.md")
        cases = [
            "完全不知道做什么",
            "只说「我想涨粉」",
            "目标互相冲突",
            "有能力但不知道服务谁",
            "有明确变现目标",
            "访谈中途退出、下次继续",
            "已有档案只补缺口",
            "模式 B 拒绝建档",
            "不把空话写成正式定位",
            "区分事实、假设、未知和验证动作",
        ]
        for case in cases:
            self.assertIn(case, text)
        self.assertIn("必须全部通过", text)
        self.assertIn("不用总分", text)

    def test_resume_and_gap_fixtures_expose_the_expected_state(self):
        resume = read("tests/fixtures/onboarding-resume/ip-dossier.md")
        self.assertIn("onboarding_status: in_progress", resume)
        self.assertIn("onboarding_step: audience", resume)
        gap = read("tests/fixtures/onboarding-missing-main-action/ip-dossier.md")
        self.assertIn("onboarding_status: provisional", gap)
        self.assertIn("**当前主行为**：[待诊断]", gap)

    def test_behavior_results_record_failures_fixes_and_all_pass(self):
        text = read("tests/onboarding_behavior_results.md")
        self.assertIn("十个核心用例逐项通过", text)
        self.assertIn("未通过", text)
        self.assertIn("前测发现", text)
        for number in range(1, 11):
            self.assertIn("| %d." % number, text)

    def test_empty_positioning_phrases_are_explicitly_rejected(self):
        corpus = "\n".join([
            read("SKILL.md"),
            read("references/11-建档诊断.md"),
            read("templates/dossier-template.md"),
        ])
        self.assertIn("想涨粉、帮助普通人、真诚分享", corpus)
        self.assertIn("不得把", corpus)


if __name__ == "__main__":
    unittest.main()

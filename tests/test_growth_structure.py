import pathlib
import re
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


def read(relative_path):
    return (ROOT / relative_path).read_text(encoding="utf-8")


class TestGrowthStructure(unittest.TestCase):
    def test_growth_reference_exists_and_has_navigation(self):
        text = read("references/10-增长与系列.md")
        self.assertTrue(text.startswith("---\n"))
        self.assertIn("dimension: 增长与系列", text)
        self.assertIn("## 目录", text)
        self.assertIn("增长单元四问", text)
        self.assertIn("主干 + 分支", text)
        self.assertIn("系列引擎", text)
        self.assertIn("平台事实门", text)
        self.assertIn("六项逐项标为“已有信号 / 未知 / 优先验证”", text)
        self.assertIn("最终回复必须展示完整事实卡", text)

    def test_skill_routes_growth_tasks_without_loading_ten_for_everything(self):
        text = read("SKILL.md")
        self.assertIn('version: "1.9.0"', text)
        self.assertIn("十二个维度文件（00-11）", text)
        self.assertIn("起号增长 / 播放不转粉 / 爆款系列", text)
        self.assertIn("references/10-增长与系列.md", text)
        self.assertNotIn("任何任务都要读取 10", text)

    def test_contract_keeps_seven_machine_fields_and_adds_growth_body(self):
        text = read("templates/contract-template.md")
        frontmatter = text.split("---", 2)[1]
        expected = [
            "contract_id",
            "status",
            "sign_date",
            "plan_publish_date",
            "actual_publish_date",
            "review_after_days",
            "next_review_date",
        ]
        keys = []
        for line in frontmatter.splitlines():
            match = re.match(r"^([a-z_]+):", line)
            if match:
                keys.append(match.group(1))
        self.assertEqual(expected, keys)
        for phrase in [
            "本条主验证目标",
            "当前价值",
            "未来价值",
            "主记忆资产",
            "系列位置",
        ]:
            self.assertIn(phrase, text)

    def test_dossier_and_weekly_plan_expose_growth_state(self):
        dossier = read("templates/dossier-template.md")
        weekly = read("templates/weekly-plan-template.md")
        self.assertIn("schema_version: 1.9", dossier)
        self.assertIn("### 账号记忆资产", dossier)
        self.assertIn("### 系列资产", dossier)
        self.assertIn("### 可选增长快照", dossier)
        self.assertIn("本周主验证目标", weekly)
        self.assertIn("本周主记忆资产", weekly)
        self.assertIn("系列相邻集表现", weekly)

    def test_rejected_absolutes_do_not_reenter_active_method_files(self):
        active_files = [
            "SKILL.md",
            "references/00-心法与反模式.md",
            "references/01-定位与人设.md",
            "references/02-选题方法论.md",
            "references/03-脚本骨架.md",
            "references/07-复盘与执行.md",
            "references/09-阶段与节奏.md",
            "references/10-增长与系列.md",
            "templates/contract-template.md",
            "templates/dossier-template.md",
        ]
        corpus = "\n".join(read(path) for path in active_files)
        rejected = [
            "AI只能做60分",
            "AI 只能做 60 分",
            "起号一定是一夜之间",
            "关注（最高）",
            "归属感是关注的最深层原因",
            "平台最重要的两个数据",
        ]
        for phrase in rejected:
            self.assertNotIn(phrase, corpus)

    def test_growth_core_cases_are_release_gates(self):
        cases = {
            "播放高不涨粉",
            "单条爆款做系列",
            "零基础起号",
            "平台时效说法",
            "AI一键起号",
        }
        rubric = read("tests/growth_behavior_cases.md")
        for case in cases:
            self.assertIn(case, rubric)
        self.assertIn("必须全部通过", rubric)


if __name__ == "__main__":
    unittest.main()

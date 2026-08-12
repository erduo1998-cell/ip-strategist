import pathlib
import re
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SKILL = ROOT / "SKILL.md"
CAPSULES = sorted((ROOT / "references").glob("task-*.md"))
DEEP_REFERENCE_PATTERN = re.compile(r"references/(?:0[0-9]|1[01])-")


class TestContextBudget(unittest.TestCase):
    def test_exactly_seven_task_capsules(self):
        expected = {
            "task-onboarding.md",
            "task-positioning.md",
            "task-topic.md",
            "task-script.md",
            "task-growth.md",
            "task-review.md",
            "task-monetization.md",
        }
        self.assertEqual(expected, {path.name for path in CAPSULES})

    def test_skill_and_capsule_byte_budgets(self):
        skill_size = SKILL.stat().st_size
        self.assertLessEqual(skill_size, 12_000)
        for capsule in CAPSULES:
            with self.subTest(capsule=capsule.name):
                size = capsule.stat().st_size
                self.assertLessEqual(size, 16_000)
                self.assertLessEqual(skill_size + size, 28_000)

    def test_skill_frontmatter_only_has_name_and_description(self):
        text = SKILL.read_text(encoding="utf-8")
        frontmatter = text.split("---", 2)[1]
        keys = [line.split(":", 1)[0] for line in frontmatter.splitlines() if ":" in line]
        self.assertEqual(["name", "description"], keys)

    def test_skill_is_thin(self):
        text = SKILL.read_text(encoding="utf-8")
        self.assertLessEqual(len(text.splitlines()), 180)
        self.assertNotIn("读取回执", text)
        self.assertNotIn("十二个维度文件", text)
        self.assertIn("普通任务不得默认读取", text)
        self.assertIn("一个主任务并立即执行", text)

    def test_capsules_are_closed_and_have_uniform_sections(self):
        required = [
            "## 本任务解决什么",
            "## 最少输入",
            "## 决策路径",
            "## 交付物契约",
            "## 失败与升级条件",
            "## 交付前自检",
            "## 深层查询地图",
        ]
        capsule_names = {path.name for path in CAPSULES}
        for capsule in CAPSULES:
            text = capsule.read_text(encoding="utf-8")
            with self.subTest(capsule=capsule.name):
                for heading in required:
                    self.assertIn(heading, text)
                for other in capsule_names - {capsule.name}:
                    self.assertNotIn(other, text, "胶囊不得把另一胶囊设为前置")

    def test_deep_references_are_conditional_not_default(self):
        skill = SKILL.read_text(encoding="utf-8")
        self.assertIn("条件式深层查询", skill)
        self.assertIn("普通任务不得默认读取", skill)
        for capsule in CAPSULES:
            text = capsule.read_text(encoding="utf-8")
            matches = [m.start() for m in DEEP_REFERENCE_PATTERN.finditer(text)]
            map_pos = text.index("## 深层查询地图")
            with self.subTest(capsule=capsule.name):
                self.assertTrue(all(position > map_pos for position in matches))


if __name__ == "__main__":
    unittest.main()

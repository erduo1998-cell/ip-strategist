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
                self.assertLessEqual(skill_size + size + 6_000, 28_000)

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
        self.assertIn("所有正式任务都消费", text)

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

    def test_each_business_capsule_rejects_missing_or_in_progress_dossier(self):
        for capsule in CAPSULES:
            if capsule.name == "task-onboarding.md":
                continue
            text = capsule.read_text(encoding="utf-8")
            with self.subTest(capsule=capsule.name):
                self.assertIn("已通过档案门并取得", text)
                self.assertIn("缺档案或建档为 `in_progress` 时不得执行本胶囊", text)

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

    def test_shared_direction_is_inherited_without_an_eighth_capsule(self):
        skill = SKILL.read_text(encoding="utf-8")
        self.assertIn("`shared_direction_input`", skill)
        self.assertIn("只读、不落盘、不成为第二事实源", skill)
        self.assertIn("不得因此新增确认、串行七任务或加载第二个胶囊", skill)

        business = [path for path in CAPSULES if path.name != "task-onboarding.md"]
        for capsule in business:
            with self.subTest(capsule=capsule.name):
                text = capsule.read_text(encoding="utf-8")
                self.assertIn("`shared_direction_input`", text)
                self.assertIn("局部", text)
        self.assertNotIn(
            "`shared_direction_input`",
            (ROOT / "references" / "task-onboarding.md").read_text(encoding="utf-8"),
        )

    def test_content_jobs_and_runtime_project_layer_keep_existing_state_contracts(self):
        topic = (ROOT / "references" / "task-topic.md").read_text(encoding="utf-8")
        script = (ROOT / "references" / "task-script.md").read_text(encoding="utf-8")
        growth = (ROOT / "references" / "task-growth.md").read_text(encoding="utf-8")
        review = (ROOT / "references" / "task-review.md").read_text(encoding="utf-8")
        monetization = (ROOT / "references" / "task-monetization.md").read_text(encoding="utf-8")
        for text in (topic, script):
            self.assertIn("`Audience Job`", text)
            self.assertIn("`IP Job`", text)
        self.assertIn("运行时内容项目卡", growth)
        self.assertIn("不新增 schema、持久化状态或必答问卷", growth)
        self.assertIn("局部传播成功、IP 积累失败", review)
        self.assertIn("证据断层", monetization)


if __name__ == "__main__":
    unittest.main()

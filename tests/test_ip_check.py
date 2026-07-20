#!/usr/bin/env python3
"""ip-check.py 单元测试（仅使用 Python 标准库 unittest，保持零依赖）。"""

import datetime
import contextlib
import importlib.util
import io
import os
import re
import shutil
import sys
import tempfile
import unittest

# 使用 importlib 直接加载 scripts/ip-check.py，避免依赖 __init__.py 包结构
_SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "..", "scripts", "ip-check.py")
spec = importlib.util.spec_from_file_location("ip_check", _SCRIPT_PATH)
ip_check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ip_check)


class TestIpCheck(unittest.TestCase):
    """覆盖 ip-check.py 核心校验逻辑。"""

    def setUp(self):
        """每个用例在一个独立临时目录运行。"""
        self.workdir = tempfile.mkdtemp(prefix="ip-check-test-")
        self.contracts_dir = os.path.join(self.workdir, "ip-contracts")
        os.makedirs(self.contracts_dir, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.workdir, ignore_errors=True)

    # ------------------------------------------------------------------
    # 辅助方法
    # ------------------------------------------------------------------
    def _write_contract(self, filename, frontmatter, body=""):
        """在临时 ip-contracts/ 目录写入一份契约。"""
        path = os.path.join(self.contracts_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write("---\n")
            for k, v in frontmatter.items():
                if v is None:
                    f.write("%s:\n" % k)
                else:
                    f.write("%s: %s\n" % (k, v))
            f.write("---\n\n")
            f.write(body)
        return path

    def _write_dossier(
        self,
        schema_version="1.9",
        index_rows=None,
        onboarding_status="confirmed",
        onboarding_step="execution",
        core_overrides=None,
        include_evidence_row=True,
    ):
        """写入 ip-dossier.md。index_rows 是 [(cid, title, status, next_review_date)]。"""
        core_fields = {
            "为什么现在做 IP": "业务转型需要建立稳定信任",
            "90 天唯一主要目标": "获得 10 个精准咨询线索",
            "成功标准": "90 天内有 10 个目标用户主动咨询",
            "目标用户的具体状态": "已经尝试但项目无法落地的小团队负责人",
            "用户的核心问题": "不知道如何把方法变成可执行流程",
            "信任依据": "已完成三个同类项目并有脱敏产物",
            "当前价值": "给出一个当天能执行的拆解动作",
            "未来价值": "持续获得从判断到复盘的落地方法",
            "当前主行为": "私信咨询",
            "变现方向或长期用途": "企业顾问服务",
            "每周执行资源": "每周 6 小时，一人出镜与剪辑",
            "人设 / 伦理 / 隐私红线": "不编造案例，不暴露客户身份，不承诺收益",
            "当前最大未知": "用户是否愿意为诊断付费；用首批 5 次咨询验证",
        }
        if core_overrides:
            core_fields.update(core_overrides)
        path = os.path.join(self.workdir, "ip-dossier.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write("---\nschema_version: %s\n" % schema_version)
            f.write("onboarding_status: %s\n" % onboarding_status)
            f.write("onboarding_step: %s\n---\n\n" % onboarding_step)
            f.write("# 创作者档案 · Dossier\n\n")
            f.write("## 一、底座区\n\n")
            for label, value in core_fields.items():
                f.write("**%s**：%s\n\n" % (label, value))
            f.write("### 依据账本（事实 / 假设 / 未知分开）\n\n")
            f.write("| 结论 | 状态（已确认事实 / 暂定假设 / 未知） | 依据 | 下一步验证 |\n")
            f.write("|---|---|---|---|\n")
            if include_evidence_row:
                f.write("| 用户有落地需求 | 已确认事实 | 三次同类求助 | 下一批内容评论与私信 |\n")
            f.write("\n")
            f.write("## 二、契约索引区\n\n")
            f.write("| 编号 | 选题 | 状态 | 下次复盘日 |\n")
            f.write("|------|------|------|----------|\n")
            if index_rows:
                for cid, title, status, nrd in index_rows:
                    f.write("| %s | %s | %s | %s |\n" % (cid, title, status, nrd))
        return path

    def _problem_kinds(self, problems):
        """从 problems 列表提取级别集合。"""
        return {p[0] for p in problems}

    def _has_message(self, problems, substring):
        """判断 problems 中是否有消息包含 substring。"""
        return any(substring in p[1] for p in problems)

    # ------------------------------------------------------------------
    # 用例
    # ------------------------------------------------------------------
    def test_empty_workspace_passes(self):
        """无契约、无档案时应直接通过。"""
        problems, stats = ip_check.run_checks(self.workdir, overdue_days=3)
        self.assertEqual(stats["contracts"], 0)
        self.assertFalse(stats["has_dossier"])
        self.assertEqual(problems, [])

    def test_valid_contract_passes(self):
        """正常待复盘契约不应产生任何问题。"""
        today = datetime.date.today()
        nrd = (today + datetime.timedelta(days=3)).isoformat()
        self._write_contract(
            "C-20260710-01.md",
            {
                "contract_id": "C-20260710-01",
                "status": "待复盘",
                "sign_date": today.isoformat(),
                "plan_publish_date": today.isoformat(),
                "actual_publish_date": today.isoformat(),
                "review_after_days": 3,
                "next_review_date": nrd,
            },
            "- **选题标题**：测试标题\n",
        )
        self._write_dossier(
            index_rows=[("C-20260710-01", "测试标题", "待复盘", nrd)]
        )
        problems, stats = ip_check.run_checks(self.workdir, overdue_days=3)
        self.assertEqual(stats["contracts"], 1)
        self.assertEqual(problems, [])

    def test_review_without_actual_date_error(self):
        """status=待复盘 但 actual_publish_date 为空 → 错误。"""
        self._write_contract(
            "C-20260710-02.md",
            {
                "contract_id": "C-20260710-02",
                "status": "待复盘",
                "actual_publish_date": "",
                "next_review_date": "2026-08-01",
            },
        )
        problems, _ = ip_check.run_checks(self.workdir, overdue_days=3)
        self.assertIn("错误", self._problem_kinds(problems))
        self.assertTrue(self._has_message(problems, "status=待复盘 但实际发布日为空"))

    def test_pending_with_actual_date_error(self):
        """status=待发布 但 actual_publish_date 已回填 → 错误。"""
        self._write_contract(
            "C-20260710-03.md",
            {
                "contract_id": "C-20260710-03",
                "status": "待发布",
                "plan_publish_date": "2026-08-01",
                "actual_publish_date": "2026-07-10",
                "next_review_date": "",
            },
        )
        problems, _ = ip_check.run_checks(self.workdir, overdue_days=3)
        self.assertIn("错误", self._problem_kinds(problems))
        self.assertTrue(
            self._has_message(problems, "status=待发布 但实际发布日已回填")
        )

    def test_pending_with_next_review_date_warning(self):
        """status=待发布 但 next_review_date 已填写 → 警告。"""
        self._write_contract(
            "C-20260710-18.md",
            {
                "contract_id": "C-20260710-18",
                "status": "待发布",
                "sign_date": "2026-07-10",
                "plan_publish_date": "2026-08-01",
                "actual_publish_date": "",
                "next_review_date": "2026-08-05",
            },
        )
        problems, _ = ip_check.run_checks(self.workdir, overdue_days=3)
        self.assertIn("警告", self._problem_kinds(problems))
        self.assertTrue(
            self._has_message(problems, "status=待发布 但下次复盘日已填写")
        )

    def test_done_review_with_next_date_error(self):
        """status=已复盘 但 next_review_date 未清空 → 错误。"""
        self._write_contract(
            "C-20260710-04.md",
            {
                "contract_id": "C-20260710-04",
                "status": "已复盘",
                "sign_date": "2026-07-10",
                "actual_publish_date": "2026-07-10",
                "next_review_date": "2026-08-01",
            },
        )
        problems, _ = ip_check.run_checks(self.workdir, overdue_days=3)
        self.assertIn("错误", self._problem_kinds(problems))
        self.assertTrue(
            self._has_message(problems, "status=已复盘 但下次复盘日未清空")
        )
        # 不应再报「实际发布日应清空」这种旧错误
        self.assertFalse(
            self._has_message(problems, "实际发布日仍非空")
        )

    def test_done_review_with_actual_date_and_empty_next_passes(self):
        """status=已复盘 + actual_publish_date 真实 + next_review_date 空 → 通过。"""
        self._write_contract(
            "C-20260710-13.md",
            {
                "contract_id": "C-20260710-13",
                "status": "已复盘",
                "sign_date": "2026-07-10",
                "plan_publish_date": "2026-07-10",
                "actual_publish_date": "2026-07-10",
                "review_after_days": 3,
                "next_review_date": "",
            },
        )
        problems, _ = ip_check.run_checks(self.workdir, overdue_days=3)
        self.assertEqual(problems, [])

    def test_done_review_without_actual_date_error(self):
        """status=已复盘 但实际发布日为空 → 错误（复盘应以已发布为前提）。"""
        self._write_contract(
            "C-20260710-14.md",
            {
                "contract_id": "C-20260710-14",
                "status": "已复盘",
                "sign_date": "2026-07-10",
                "actual_publish_date": "",
                "next_review_date": "",
            },
        )
        problems, _ = ip_check.run_checks(self.workdir, overdue_days=3)
        self.assertIn("错误", self._problem_kinds(problems))
        self.assertTrue(
            self._has_message(problems, "status=已复盘 但实际发布日为空")
        )

    def test_frontmatter_id_conflict_warning(self):
        """frontmatter 编号与文件名不一致 → 警告。"""
        self._write_contract(
            "C-20260710-05.md",
            {
                "contract_id": "C-20260710-99",
                "status": "待发布",
                "sign_date": "2026-07-10",
                "plan_publish_date": "2026-08-01",
                "review_after_days": 3,
            },
        )
        problems, _ = ip_check.run_checks(self.workdir, overdue_days=3)
        self.assertIn("警告", self._problem_kinds(problems))
        self.assertTrue(self._has_message(problems, "编号冲突"))
        self.assertTrue(self._has_message(problems, "C-20260710-99"))

    def test_placeholder_id_falls_back_to_filename_no_conflict(self):
        """frontmatter 为模板占位符 C-YYYYMMDD-NN → 回退文件名，不报警告。"""
        self._write_contract(
            "C-20260710-06.md",
            {
                "contract_id": "C-YYYYMMDD-NN",
                "status": "待发布",
                "sign_date": "2026-07-10",
                "plan_publish_date": "2026-08-01",
                "review_after_days": 3,
            },
        )
        problems, stats = ip_check.run_checks(self.workdir, overdue_days=3)
        self.assertNotIn("警告", self._problem_kinds(problems))
        self.assertNotIn("错误", self._problem_kinds(problems))
        # 解析出的 contract_id 应为文件名
        self.assertEqual(stats["contracts"], 1)

    def test_abandoned_excluded_from_overdue_and_unfilled(self):
        """已废弃契约不纳入逾期、待发布超期、复盘提醒。"""
        today = datetime.date.today()
        old_date = (today - datetime.timedelta(days=30)).isoformat()
        self._write_contract(
            "C-20260710-07.md",
            {
                "contract_id": "C-20260710-07",
                "status": "已废弃",
                "sign_date": "2026-07-10",
                # plan_publish_date 已过期，但已废弃不应触发「疑似漏回填」
                "plan_publish_date": old_date,
                "actual_publish_date": "",
                "review_after_days": 3,
                "next_review_date": "",
            },
            "# abandoned\n",
        )
        # 再写一份待复盘且过期的契约，确保逾期逻辑本身仍在工作
        self._write_contract(
            "C-20260710-08.md",
            {
                "contract_id": "C-20260710-08",
                "status": "待复盘",
                "actual_publish_date": "2026-07-01",
                "next_review_date": old_date,
            },
        )
        problems, stats = ip_check.run_checks(self.workdir, overdue_days=3)
        self.assertEqual(stats["abandoned_count"], 1)
        # 应只有待复盘过期那一条提醒
        self.assertEqual(len([p for p in problems if p[0] == "提醒"]), 1)
        self.assertTrue(self._has_message(problems, "C-20260710-08"))
        self.assertFalse(self._has_message(problems, "C-20260710-07"))
        self.assertFalse(self._has_message(problems, "疑似漏回填"))

    def test_index_status_mismatch_warning(self):
        """索引区状态与契约原件不一致 → 警告。"""
        self._write_contract(
            "C-20260710-09.md",
            {
                "contract_id": "C-20260710-09",
                "status": "待复盘",
                "actual_publish_date": "2026-07-10",
                "next_review_date": "2026-08-01",
            },
        )
        self._write_dossier(
            index_rows=[("C-20260710-09", "标题", "已复盘", "2026-08-01")]
        )
        problems, _ = ip_check.run_checks(self.workdir, overdue_days=3)
        self.assertIn("警告", self._problem_kinds(problems))
        self.assertTrue(self._has_message(problems, "索引脱节[状态不符]"))

    def test_index_stale_review_date_when_contract_date_empty_warns(self):
        """原件已清空复盘日但索引仍有旧值时必须报告。"""
        self._write_contract(
            "C-20260710-28.md",
            {
                "contract_id": "C-20260710-28",
                "status": "已复盘",
                "sign_date": "2026-07-10",
                "plan_publish_date": "2026-07-11",
                "actual_publish_date": "2026-07-12",
                "review_after_days": 3,
                "next_review_date": "",
            },
            "- **选题标题**：旧复盘日测试\n",
        )
        self._write_dossier(
            index_rows=[("C-20260710-28", "旧复盘日测试", "已复盘", "2026-07-15")]
        )
        problems, _ = ip_check.run_checks(self.workdir, overdue_days=3)
        self.assertTrue(self._has_message(problems, "索引脱节[复盘日不符]"))

    def test_schema_version_mismatch_warning(self):
        """档案 schema_version 与模板不一致 → 警告。"""
        self._write_dossier(schema_version="0.0")
        problems, _ = ip_check.run_checks(self.workdir, overdue_days=3)
        self.assertIn("警告", self._problem_kinds(problems))
        self.assertTrue(self._has_message(problems, "schema_version 不一致"))

    def test_single_digit_month_day_parsing(self):
        """单数字月/日（如 2026-7-10）应能正确解析。"""
        today = datetime.date.today()
        # 用一年后附近日期，避免触发逾期；不用 year= 替换防止闰年 2/29 报错
        target = today + datetime.timedelta(days=365)
        date_str = "%d-%d-%d" % (target.year, target.month, target.day)
        self._write_contract(
            "C-20260710-10.md",
            {
                "contract_id": "C-20260710-10",
                "status": "待复盘",
                "sign_date": date_str,
                "plan_publish_date": date_str,
                "actual_publish_date": date_str,
                "review_after_days": 1,
                "next_review_date": (target + datetime.timedelta(days=1)).isoformat(),
            },
        )
        problems, _ = ip_check.run_checks(self.workdir, overdue_days=3)
        self.assertEqual(problems, [])

    def test_chinese_dash_as_empty(self):
        """中文破折号 — 应被识别为空值；已复盘时 next_review_date 为空即通过。"""
        self._write_contract(
            "C-20260710-11.md",
            {
                "contract_id": "C-20260710-11",
                "status": "已复盘",
                "sign_date": "2026-07-10",
                "plan_publish_date": "2026-07-10",
                "actual_publish_date": "2026-07-10",
                "review_after_days": 3,
                "next_review_date": "—",
            },
        )
        problems, _ = ip_check.run_checks(self.workdir, overdue_days=3)
        self.assertEqual(problems, [])

    def test_abandoned_status_allowed(self):
        """已废弃是合法状态，不应报非法值错误。"""
        self._write_contract(
            "C-20260710-12.md",
            {
                "contract_id": "C-20260710-12",
                "status": "已废弃",
                "sign_date": "2026-07-10",
                "plan_publish_date": "2026-07-10",
            },
            "# abandoned\n",
        )
        problems, stats = ip_check.run_checks(self.workdir, overdue_days=3)
        self.assertEqual(stats["abandoned_count"], 1)
        self.assertFalse(self._has_message(problems, "状态非法值"))

    def test_abandoned_alias_normalized(self):
        """旧模板里的状态别名 已废弃（已取消） 应被规范化为 已废弃，不报错。"""
        self._write_contract(
            "C-20260710-19.md",
            {
                "contract_id": "C-20260710-19",
                "status": "已废弃（已取消）",
                "sign_date": "2026-07-10",
                "plan_publish_date": "2026-07-10",
            },
            "# abandoned alias\n",
        )
        problems, stats = ip_check.run_checks(self.workdir, overdue_days=3)
        self.assertEqual(stats["abandoned_count"], 1)
        self.assertFalse(self._has_message(problems, "状态非法值"))
        # 过期的 plan_publish_date 不应因已废弃而触发疑似漏回填
        self.assertFalse(self._has_message(problems, "疑似漏回填"))

    def test_frontmatter_status_fallback_to_body(self):
        """frontmatter 缺少 status 时，应从正文回退读取。"""
        self._write_contract(
            "C-20260710-15.md",
            {
                "contract_id": "C-20260710-15",
                "sign_date": "2026-07-10",
                "plan_publish_date": "2026-08-01",
            },
            "- **状态**：待发布\n- **选题标题**：正文回退标题\n",
        )
        problems, stats = ip_check.run_checks(self.workdir, overdue_days=3)
        self.assertEqual(stats["contracts"], 1)
        self.assertFalse(self._has_message(problems, "字段缺失"))
        self.assertFalse(self._has_message(problems, "状态机违规"))

    def test_schema_version_preserved_as_string(self):
        """schema_version 应保留原始字符串，避免 1.10 被解析成 1.1。"""
        self._write_dossier(schema_version="1.10")
        # 自定义模板用不同版本触发警告，验证读取到的是 "1.10" 而非 "1.1"
        skill_dir = os.path.join(self.workdir, "skill")
        tpl_dir = os.path.join(skill_dir, "templates")
        os.makedirs(tpl_dir, exist_ok=True)
        custom_tpl = os.path.join(tpl_dir, "dossier-template.md")
        with open(custom_tpl, "w", encoding="utf-8") as f:
            f.write("---\nschema_version: 1.5\n---\n\n# custom template\n")

        problems, _ = ip_check.run_checks(
            self.workdir, overdue_days=3, skill_dir=skill_dir
        )
        self.assertTrue(self._has_message(problems, "schema_version 不一致"))
        self.assertTrue(self._has_message(problems, "ip-dossier.md=1.10"))
        # 精确排除 1.1（因为 1.10 包含 1.1 子串，不能简单用 _has_message 排除）
        self.assertTrue(
            any(re.search(r"ip-dossier\.md=1\.10\b", p[1]) for p in problems)
        )

    def test_skill_dir_argument(self):
        """--skill-dir 参数应能正确定位自定义模板路径。"""
        skill_dir = os.path.join(self.workdir, "skill")
        tpl_dir = os.path.join(skill_dir, "templates")
        os.makedirs(tpl_dir, exist_ok=True)
        custom_tpl = os.path.join(tpl_dir, "dossier-template.md")
        with open(custom_tpl, "w", encoding="utf-8") as f:
            f.write("---\nschema_version: 9.9\n---\n\n# custom template\n")

        self._write_dossier(schema_version="9.9")
        problems, stats = ip_check.run_checks(
            self.workdir, overdue_days=3, skill_dir=skill_dir
        )
        self.assertEqual(stats["template_dossier"], os.path.abspath(custom_tpl))
        self.assertFalse(self._has_message(problems, "schema_version 不一致"))

    def test_sign_date_missing_warning(self):
        """sign_date 缺失时应报警告。"""
        self._write_contract(
            "C-20260710-16.md",
            {
                "contract_id": "C-20260710-16",
                "status": "待发布",
                "plan_publish_date": "2026-08-01",
            },
        )
        problems, _ = ip_check.run_checks(self.workdir, overdue_days=3)
        self.assertIn("警告", self._problem_kinds(problems))
        self.assertTrue(self._has_message(problems, "签订日期"))

    def test_sign_date_invalid_warning(self):
        """sign_date 无法解析时应报警告。"""
        self._write_contract(
            "C-20260710-17.md",
            {
                "contract_id": "C-20260710-17",
                "status": "待发布",
                "sign_date": "not-a-date",
                "plan_publish_date": "2026-08-01",
            },
        )
        problems, _ = ip_check.run_checks(self.workdir, overdue_days=3)
        self.assertIn("警告", self._problem_kinds(problems))
        self.assertTrue(self._has_message(problems, "签订日期"))

    def test_pending_missing_plan_date_error(self):
        """待发布契约缺预计发布日期应阻断。"""
        self._write_contract(
            "C-20260710-20.md",
            {
                "contract_id": "C-20260710-20",
                "status": "待发布",
                "sign_date": "2026-07-10",
                "plan_publish_date": "",
                "actual_publish_date": "",
                "review_after_days": 3,
                "next_review_date": "",
            },
        )
        problems, _ = ip_check.run_checks(self.workdir, overdue_days=3)
        self.assertTrue(self._has_message(problems, "预计发布日期为空"))

    def test_invalid_actual_date_error(self):
        """非空但无效的实际发布日期不能被当作已回填。"""
        self._write_contract(
            "C-20260710-21.md",
            {
                "contract_id": "C-20260710-21",
                "status": "待复盘",
                "sign_date": "2026-07-10",
                "plan_publish_date": "2026-07-12",
                "actual_publish_date": "not-a-date",
                "review_after_days": 3,
                "next_review_date": "2026-07-15",
            },
        )
        problems, _ = ip_check.run_checks(self.workdir, overdue_days=3)
        self.assertTrue(self._has_message(problems, "实际发布日期不是有效日期"))

    def test_inverted_dates_error(self):
        """签订日期不能晚于预计或实际发布日期。"""
        self._write_contract(
            "C-20260710-22.md",
            {
                "contract_id": "C-20260710-22",
                "status": "待复盘",
                "sign_date": "2026-07-12",
                "plan_publish_date": "2026-07-10",
                "actual_publish_date": "2026-07-11",
                "review_after_days": 3,
                "next_review_date": "2026-07-14",
            },
        )
        problems, _ = ip_check.run_checks(self.workdir, overdue_days=3)
        self.assertTrue(self._has_message(problems, "签订日期晚于预计发布日期"))
        self.assertTrue(self._has_message(problems, "签订日期晚于实际发布日期"))

    def test_abandoned_with_review_date_error(self):
        """已废弃契约必须清空下次复盘日。"""
        self._write_contract(
            "C-20260710-23.md",
            {
                "contract_id": "C-20260710-23",
                "status": "已废弃",
                "sign_date": "2026-07-10",
                "plan_publish_date": "2026-07-12",
                "actual_publish_date": "",
                "review_after_days": 3,
                "next_review_date": "2026-07-15",
            },
        )
        problems, _ = ip_check.run_checks(self.workdir, overdue_days=3)
        self.assertTrue(self._has_message(problems, "status=已废弃 但下次复盘日未清空"))

    def test_review_date_must_match_actual_plus_offset(self):
        """显式 review_after_days 时，下次复盘日必须可重算。"""
        self._write_contract(
            "C-20260710-24.md",
            {
                "contract_id": "C-20260710-24",
                "status": "待复盘",
                "sign_date": "2026-07-10",
                "plan_publish_date": "2026-07-11",
                "actual_publish_date": "2026-07-12",
                "review_after_days": 3,
                "next_review_date": "2026-07-16",
            },
        )
        problems, _ = ip_check.run_checks(self.workdir, overdue_days=3)
        self.assertTrue(self._has_message(problems, "应为实际发布日期 + 3 天"))

    def test_empty_index_with_contract_warns(self):
        """新建空索引不能掩盖已有契约。"""
        self._write_contract(
            "C-20260710-25.md",
            {
                "contract_id": "C-20260710-25",
                "status": "待发布",
                "sign_date": "2026-07-10",
                "plan_publish_date": "2099-07-12",
                "actual_publish_date": "",
                "review_after_days": 3,
                "next_review_date": "",
            },
            "- **选题标题**：索引测试\n",
        )
        self._write_dossier(index_rows=[])
        problems, _ = ip_check.run_checks(self.workdir, overdue_days=3)
        self.assertTrue(self._has_message(problems, "索引脱节[缺失]"))

    def test_sync_index_rebuilds_table_and_preserves_other_sections(self):
        """索引同步只改索引表，并保留备份和档案其它内容。"""
        self._write_contract(
            "C-20260710-26.md",
            {
                "contract_id": "C-20260710-26",
                "status": "待发布",
                "sign_date": "2026-07-10",
                "plan_publish_date": "2099-07-12",
                "actual_publish_date": "",
                "review_after_days": 3,
                "next_review_date": "",
            },
            "- **选题标题**：自动同步测试\n",
        )
        dossier_path = self._write_dossier(index_rows=[])
        with open(dossier_path, "a", encoding="utf-8") as f:
            f.write("\n## 三、数据快照区\n\n保留这段。\n")

        count = ip_check.sync_dossier_index(self.workdir)
        self.assertEqual(count, 1)
        updated = ip_check.read_text(dossier_path)
        self.assertIn("| C-20260710-26 | 自动同步测试 | 待发布 |  |", updated)
        self.assertIn("## 三、数据快照区\n\n保留这段。", updated)
        self.assertTrue(os.path.isfile(dossier_path + ".bak"))
        problems, _ = ip_check.run_checks(self.workdir, overdue_days=3)
        self.assertFalse(self._has_message(problems, "索引脱节"))

    def test_sync_index_does_not_write_when_contract_has_errors(self):
        """错误级契约存在时，CLI 不得同步派生索引。"""
        self._write_contract(
            "C-20260710-27.md",
            {
                "contract_id": "C-20260710-27",
                "status": "待复盘",
                "sign_date": "2026-07-10",
                "plan_publish_date": "2026-07-12",
                "actual_publish_date": "",
                "review_after_days": 3,
                "next_review_date": "2026-07-15",
            },
            "- **选题标题**：错误契约\n",
        )
        dossier_path = self._write_dossier(index_rows=[])
        before = ip_check.read_text(dossier_path)
        with contextlib.redirect_stdout(io.StringIO()), \
             contextlib.redirect_stderr(io.StringIO()):
            exit_code = ip_check.main([self.workdir, "3", "--sync-index"])
        self.assertEqual(exit_code, 2)
        self.assertEqual(ip_check.read_text(dossier_path), before)
        self.assertFalse(os.path.exists(dossier_path + ".bak"))

    def test_in_progress_onboarding_is_not_treated_as_complete(self):
        """in_progress 允许缺字段，但必须明确提醒按断点续访。"""
        self._write_dossier(
            onboarding_status="in_progress",
            onboarding_step="audience",
            core_overrides={"目标用户的具体状态": "[待诊断]"},
            include_evidence_row=False,
        )
        problems, stats = ip_check.run_checks(self.workdir, overdue_days=3)
        self.assertEqual(stats["onboarding_status"], "in_progress")
        self.assertEqual(stats["onboarding_step"], "audience")
        self.assertTrue(self._has_message(problems, "建档诊断进行中"))
        self.assertTrue(self._has_message(problems, "audience"))
        self.assertNotIn("错误", self._problem_kinds(problems))

    def test_provisional_missing_core_field_is_error(self):
        """provisional 缺任一核心字段不得被误判为完整档案。"""
        self._write_dossier(
            onboarding_status="provisional",
            onboarding_step="execution",
            core_overrides={"90 天唯一主要目标": "[待诊断]"},
        )
        problems, _ = ip_check.run_checks(self.workdir, overdue_days=3)
        self.assertIn("错误", self._problem_kinds(problems))
        self.assertTrue(self._has_message(problems, "90 天唯一主要目标"))

    def test_provisional_without_evidence_ledger_is_error(self):
        """完整档案必须区分事实/假设/未知，并保留依据与验证动作。"""
        self._write_dossier(
            onboarding_status="provisional",
            onboarding_step="execution",
            include_evidence_row=False,
        )
        problems, _ = ip_check.run_checks(self.workdir, overdue_days=3)
        self.assertIn("错误", self._problem_kinds(problems))
        self.assertTrue(self._has_message(problems, "建档依据账本缺失"))

    def test_confirmed_complete_onboarding_passes(self):
        """confirmed + 全部核心字段 + 依据账本应通过。"""
        self._write_dossier(
            onboarding_status="confirmed",
            onboarding_step="execution",
        )
        problems, stats = ip_check.run_checks(self.workdir, overdue_days=3)
        self.assertEqual(stats["onboarding_status"], "confirmed")
        self.assertEqual(problems, [])

    def test_invalid_onboarding_state_and_step_are_errors(self):
        """建档状态与断点都使用封闭枚举。"""
        self._write_dossier(
            onboarding_status="done",
            onboarding_step="finished",
        )
        problems, _ = ip_check.run_checks(self.workdir, overdue_days=3)
        self.assertTrue(self._has_message(problems, "建档状态非法"))
        self.assertTrue(self._has_message(problems, "建档断点非法"))

    def test_provisional_requires_execution_as_last_completed_step(self):
        """provisional 表示六模块完成，断点必须留在 execution。"""
        self._write_dossier(
            onboarding_status="provisional",
            onboarding_step="value",
        )
        problems, _ = ip_check.run_checks(self.workdir, overdue_days=3)
        self.assertTrue(self._has_message(problems, "建档状态与断点冲突"))


if __name__ == "__main__":
    unittest.main()

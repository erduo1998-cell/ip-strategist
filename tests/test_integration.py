#!/usr/bin/env python3
"""ip-check.py 集成测试：在真实 fixture workspace 上验证 CLI 行为。"""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest


class TestIpCheckIntegration(unittest.TestCase):
    """使用 tests/fixtures/sample-workspace/ 作为真实工作目录的集成测试。"""

    FIXTURE_DIR = os.path.join(
        os.path.dirname(__file__), "fixtures", "sample-workspace"
    )
    SCRIPT_PATH = os.path.join(
        os.path.dirname(__file__), "..", "scripts", "ip-check.py"
    )

    def setUp(self):
        """把静态 fixture 复制到临时目录，避免测试污染原 fixture。"""
        self.workdir = tempfile.mkdtemp(prefix="ip-check-integration-")
        for name in os.listdir(self.FIXTURE_DIR):
            src = os.path.join(self.FIXTURE_DIR, name)
            dst = os.path.join(self.workdir, name)
            if os.path.isdir(src):
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)

    def tearDown(self):
        shutil.rmtree(self.workdir, ignore_errors=True)

    def _run_check(self):
        """在临时工作目录上调用 ip-check.py CLI。"""
        cmd = [
            sys.executable,
            os.path.abspath(self.SCRIPT_PATH),
            self.workdir,
            "3",
        ]
        return subprocess.run(cmd, capture_output=True, text=True)

    def test_exit_code_and_output_contains_expected_problems(self):
        """fixture 含错误、警告、提醒三类问题，退出码应为 2。"""
        result = self._run_check()
        output = result.stdout + result.stderr

        self.assertEqual(
            result.returncode,
            2,
            "存在错误级问题，退出码应为 2。输出：\n%s" % output,
        )

        # 错误级
        self.assertIn("契约编号冲突", output)
        self.assertIn("状态非法值", output)

        # 警告级
        self.assertIn("schema_version 不一致", output)
        self.assertIn("索引脱节[状态不符]", output)
        self.assertIn("索引脱节[缺失]", output)
        self.assertIn("索引脱节[孤儿]", output)

        # 提醒级
        self.assertIn("过期待复盘", output)
        self.assertIn("疑似漏回填", output)

    def test_stats_match_fixture(self):
        """脚本应正确统计契约数量。"""
        result = self._run_check()
        output = result.stdout
        self.assertIn("契约数量：8 份", output)


if __name__ == "__main__":
    unittest.main()

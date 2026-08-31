import json
import hashlib
import re
import subprocess
import urllib.request
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
PUBLIC_DOCS = [
    "README.md",
    "README.en.md",
    "README.ja.md",
    "README.ko.md",
    "README.zh-TW.md",
    "NOTICE.md",
    "CONTRIBUTING.md",
    "SUPPORT.md",
]


class ReleaseContractTests(unittest.TestCase):
    def read(self, relative):
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_version_is_single_line_and_referenced_by_release_shell(self):
        self.assertRegex(VERSION, r"^\d+\.\d+\.\d+$")
        self.assertEqual(self.read("VERSION"), VERSION + "\n")
        for relative in ["README.md", "CHANGELOG.md", "NOTICE.md"]:
            with self.subTest(relative=relative):
                self.assertIn(VERSION, self.read(relative))

    def test_expected_release_tag_matches_version(self):
        self.assertEqual(f"v{self.read('VERSION').strip()}", f"v{VERSION}")

    def test_openai_metadata_matches_unified_entry(self):
        text = self.read("agents/openai.yaml")
        self.assertRegex(text, r'(?m)^\s*display_name: ".*ip-strategist.*"$')
        self.assertRegex(text, r'(?m)^\s*short_description: ".{25,64}"$')
        self.assertIn("default_prompt:", text)
        self.assertIn("$ip-strategist", text)

    def test_license_is_unmodified_cc_by_nc_legal_code(self):
        text = self.read("LICENSE")
        self.assertTrue(text.startswith("Attribution-NonCommercial 4.0 International\n"))
        self.assertIn(
            "Creative Commons Attribution-NonCommercial 4.0 International Public\nLicense",
            text,
        )
        self.assertIn("Section 8 -- Interpretation.", text)
        self.assertIn("Creative Commons may be contacted at creativecommons.org.", text)

    def test_license_matches_official_legalcode_when_network_is_available(self):
        try:
            with urllib.request.urlopen(
                "https://creativecommons.org/licenses/by-nc/4.0/legalcode.txt",
                timeout=5,
            ) as response:
                official = response.read().decode("utf-8")
        except Exception as exc:
            self.skipTest(f"official legal code unavailable: {exc}")
        self.assertEqual(self.read("LICENSE").rstrip("\n"), official.rstrip("\n"))

    def test_current_license_language_is_not_mit(self):
        forbidden = [
            re.compile(r"current(?:ly)?[^\n]{0,40}\bMIT\b", re.IGNORECASE),
            re.compile(r"现行[^\n]{0,20}MIT"),
            re.compile(r"当前[^\n]{0,20}MIT"),
            re.compile(r"按\s*MIT\s*(?:许可)?发布"),
        ]
        for relative in PUBLIC_DOCS:
            text = self.read(relative)
            with self.subTest(relative=relative):
                for pattern in forbidden:
                    self.assertIsNone(pattern.search(text), pattern.pattern)

    def test_historical_mit_boundary_is_explicit(self):
        notice = self.read("NOTICE.md")
        readme = self.read("README.md")
        for text in (notice, readme):
            self.assertIn("v1", text)
            self.assertIn("MIT", text)
            self.assertRegex(text, r"不追溯撤销|继续享有")

    def test_notice_covers_scope_attribution_exclusions_and_commercial_entry(self):
        notice = self.read("NOTICE.md")
        for phrase in [
            "v2.0.0",
            "标准署名",
            "第三方",
            "用户工作目录",
            "SUPPORT.md",
            "商业",
        ]:
            self.assertIn(phrase, notice)

    def test_workflow_svg_is_static_original_asset(self):
        text = self.read("assets/workflow-map.svg")
        self.assertIn("<svg", text)
        self.assertIn("viewBox=", text)
        self.assertIn("<title", text)
        self.assertIn("<desc", text)
        body = text.replace('xmlns="http://www.w3.org/2000/svg"', "")
        self.assertNotRegex(body, r"<script|javascript:|https?://", re.IGNORECASE)
        self.assertIn("档案与数据摘要", text)
        self.assertIn("根因 · 症状 · 待验证假设", text)

    def test_remotion_demo_is_reproducible_and_bounded(self):
        package = json.loads(self.read("demo/remotion/package.json"))
        self.assertEqual(package["dependencies"]["remotion"], "4.0.508")
        self.assertEqual(package["dependencies"]["@remotion/cli"], "4.0.508")
        for script in ["render", "poster", "gif", "build"]:
            self.assertIn(script, package["scripts"])
        self.assertIn("--muted", package["scripts"]["render"])
        source = self.read("demo/remotion/src/IpStrategistDemo.tsx")
        self.assertIn("虚构演示", source)
        self.assertIn("档案与历史数据", source)
        self.assertIn("问题重判", source)
        self.assertIn("表层症状", source)
        self.assertNotRegex(source, r"https?://|fetch\(|Math\.random")
        expected = {
            "assets/ip-strategist-demo.gif": 1_500_000,
            "assets/ip-strategist-demo.mp4": 2_000_000,
            "assets/ip-strategist-demo-poster.png": 500_000,
        }
        for relative, limit in expected.items():
            path = ROOT / relative
            with self.subTest(relative=relative):
                self.assertTrue(path.is_file())
                self.assertLessEqual(path.stat().st_size, limit)

    def test_public_contact_uses_the_established_personal_wechat_asset(self):
        asset = ROOT / "assets/wechat-qrcode.jpg"
        self.assertTrue(asset.is_file())
        self.assertEqual(asset.stat().st_size, 173_299)
        self.assertEqual(
            hashlib.sha256(asset.read_bytes()).hexdigest(),
            "a4f3774d284591cb6d48e94b4b6b18fb7337ef36294a07792bca80e65ed44981",
        )
        for relative in [
            "README.md",
            "README.en.md",
            "README.ja.md",
            "README.ko.md",
            "README.zh-TW.md",
            "SUPPORT.md",
        ]:
            with self.subTest(relative=relative):
                self.assertIn("assets/wechat-qrcode.jpg", self.read(relative))

    def test_private_runtime_paths_are_ignored_before_release(self):
        """Private creator state and locally installed integration packages stay unstaged."""
        private_paths = [
            "ip-dossier.md",
            "ip-dossier.md.bak-20260831-before-review",
            "ip-dossier.md.tmp",
            "ip-contracts/C-20260831-01.md",
            "ip-evidence/xiaohongshu/raw/example.json",
            "integrations/xiaohongshu-comments/node_modules/opencli/index.js",
        ]
        for relative in private_paths:
            with self.subTest(relative=relative):
                result = subprocess.run(
                    ["git", "check-ignore", "--no-index", "-q", relative],
                    cwd=ROOT,
                    check=False,
                )
                self.assertEqual(result.returncode, 0, relative)

    def test_public_tree_has_no_private_runtime_data_outside_synthetic_fixtures(self):
        forbidden_names = (
            "ip-dossier.md",
            "ip-dossier.md.bak",
            "ip-dossier.md.tmp",
        )
        tracked = subprocess.check_output(
            ["git", "ls-files", "-z"], cwd=ROOT, text=True
        ).split("\0")
        untracked_candidates = subprocess.check_output(
            ["git", "ls-files", "--others", "--exclude-standard", "-z"],
            cwd=ROOT,
            text=True,
        ).split("\0")
        for relative in filter(None, set(tracked + untracked_candidates)):
            if relative.startswith("tests/fixtures/"):
                continue
            with self.subTest(relative=relative):
                self.assertFalse(relative.startswith("ip-contracts/"))
                self.assertFalse(relative.startswith("ip-evidence/"))
                self.assertFalse("/node_modules/" in f"/{relative}")
                self.assertFalse(Path(relative).name.startswith(forbidden_names))

    def test_platform_json_fixtures_are_synthetic_and_session_free(self):
        fixture_dir = ROOT / "integrations"
        if not fixture_dir.is_dir():
            self.skipTest("platform integrations are not included in this checkout")
        forbidden = re.compile(
            r"https?://|[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}|"
            r"(?:\+?86[- ]?)?1[3-9]\d{9}|"
            r"(?:sk-|ghp_|github_pat_|AKIA|bearer\s+)|"
            r"(?:cookie|sessionid|csrf|passport)[=:]",
            re.IGNORECASE,
        )
        for path in fixture_dir.glob("*/test/fixtures/*.json"):
            with self.subTest(relative=path.relative_to(ROOT).as_posix()):
                payload = json.loads(path.read_text(encoding="utf-8"))
                serialized = json.dumps(payload, ensure_ascii=False)
                self.assertIsNone(forbidden.search(serialized))
                if path.name == "creator-notes.json":
                    title = payload["data"]["note_infos"][0]["title"]
                    self.assertRegex(title, r"测试|示例|合成|fixture")


if __name__ == "__main__":
    unittest.main()

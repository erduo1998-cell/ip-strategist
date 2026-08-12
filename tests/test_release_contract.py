import re
import urllib.request
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERSION = "2.0.0"
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
        self.assertEqual(self.read("VERSION"), VERSION + "\n")
        for relative in ["README.md", "CHANGELOG.md", "NOTICE.md"]:
            with self.subTest(relative=relative):
                self.assertIn(VERSION, self.read(relative))

    def test_expected_release_tag_matches_version(self):
        self.assertEqual(f"v{self.read('VERSION').strip()}", "v2.0.0")

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


if __name__ == "__main__":
    unittest.main()

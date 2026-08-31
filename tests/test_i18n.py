import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
READMES = [
    "README.md",
    "README.en.md",
    "README.ja.md",
    "README.ko.md",
    "README.zh-TW.md",
]
SHELLS = [
    "references/shell.zh-CN.md",
    "references/shell.en.md",
    "references/shell.ja.md",
    "references/shell.ko.md",
    "references/shell.zh-TW.md",
]
CAPABILITIES = {
    "positioning",
    "topic",
    "script",
    "growth",
    "review",
    "monetization",
    "onboarding",
}
INSTALL = "npx -y skills add erduo1998-cell/ip-strategist -g"


class I18nContractTests(unittest.TestCase):
    def read(self, relative):
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_five_readmes_and_shells_exist(self):
        for relative in READMES + SHELLS:
            with self.subTest(relative=relative):
                self.assertTrue((ROOT / relative).is_file())

    def test_readmes_have_complete_language_navigation(self):
        for relative in READMES:
            text = self.read(relative)
            with self.subTest(relative=relative):
                for target in READMES:
                    self.assertIn(f"]({target})", text)

    def test_readmes_share_release_install_and_license_contract(self):
        for relative in READMES:
            text = self.read(relative)
            with self.subTest(relative=relative):
                self.assertIn(VERSION, text)
                self.assertIn(INSTALL, text)
                self.assertIn("--agent codex --skill ip-strategist -y", text.replace("\\\n", " "))
                self.assertIn("--list", text)
                self.assertIn("CC BY-NC 4.0", text)
                self.assertIn("](LICENSE)", text)
                self.assertIn("](NOTICE.md)", text)
                self.assertIn("](SUPPORT.md)", text)
                self.assertIn("git pull --ff-only", text)
                self.assertIn("更新 ip-strategist", text)
                self.assertIn("--agent", text)
                self.assertIn("assets/ip-strategist-demo.gif", text)
                self.assertIn("assets/ip-strategist-demo.mp4", text)
                self.assertIn("demo/remotion/", text)
                self.assertIn('src="assets/wechat-qrcode.jpg"', text)

    def test_each_readme_has_exactly_seven_capability_markers(self):
        marker = re.compile(r"<!-- capability:([a-z-]+) -->")
        for relative in READMES:
            found = marker.findall(self.read(relative))
            with self.subTest(relative=relative):
                self.assertEqual(len(found), 7)
                self.assertEqual(set(found), CAPABILITIES)

    def test_readme_images_have_alt_text_and_exist(self):
        image = re.compile(r"!\[([^\]]+)\]\(([^)]+)\)")
        for relative in READMES:
            matches = image.findall(self.read(relative))
            with self.subTest(relative=relative):
                self.assertGreaterEqual(len(matches), 2)
                for alt, target in matches:
                    self.assertTrue(alt.strip())
                    if target.startswith(("http://", "https://")):
                        continue
                    self.assertTrue((ROOT / target).is_file(), target)

    def test_install_defaults_to_one_explicit_agent(self):
        for relative in READMES:
            text = self.read(relative)
            with self.subTest(relative=relative):
                scoped = text.find("--agent codex --skill ip-strategist -y")
                all_agents = text.find("-g --all")
                self.assertGreaterEqual(scoped, 0)
                self.assertGreater(all_agents, scoped)

    def test_shells_are_short_and_do_not_leak_internal_routing(self):
        for relative in SHELLS:
            data = (ROOT / relative).read_bytes()
            text = data.decode("utf-8")
            with self.subTest(relative=relative):
                limit = 8_000 if relative.endswith("shell.zh-CN.md") else 3_000
                self.assertLessEqual(len(data), limit)
                self.assertNotIn("task-", text)
                self.assertNotIn("references/", text)
                self.assertNotIn("00-11", text)

    def test_all_locales_make_dossier_first_and_problem_reframing_visible(self):
        readme_markers = {
            "README.md": ("第一次使用先完成", "根因、症状、待验证假设"),
            "README.en.md": ("First use builds", "root cause, symptom, untested hypothesis"),
            "README.ja.md": ("初回は", "根本原因、症状、未検証仮説"),
            "README.ko.md": ("첫 사용에서는", "근본 원인인지 증상인지"),
            "README.zh-TW.md": ("第一次使用先完成", "根因、症狀、待驗證假設"),
        }
        for relative, markers in readme_markers.items():
            with self.subTest(relative=relative):
                text = self.read(relative)
                for marker in markers:
                    self.assertIn(marker, text)


if __name__ == "__main__":
    unittest.main()

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
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
INSTALL = "npx -y skills add erduo1998-cell/ip-strategist -g --all"


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
                self.assertIn("2.0.0", text)
                self.assertIn(INSTALL, text)
                self.assertIn("CC BY-NC 4.0", text)
                self.assertIn("](LICENSE)", text)
                self.assertIn("](NOTICE.md)", text)
                self.assertIn("](SUPPORT.md)", text)
                self.assertIn("git pull --ff-only", text)
                self.assertIn("更新 ip-strategist", text)
                self.assertIn("--agent", text)

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
                    self.assertTrue((ROOT / target).is_file(), target)

    def test_shells_are_short_and_do_not_leak_internal_routing(self):
        for relative in SHELLS:
            data = (ROOT / relative).read_bytes()
            text = data.decode("utf-8")
            with self.subTest(relative=relative):
                self.assertLessEqual(len(data), 3000)
                self.assertNotIn("task-", text)
                self.assertNotIn("references/", text)
                self.assertNotIn("00-11", text)


if __name__ == "__main__":
    unittest.main()

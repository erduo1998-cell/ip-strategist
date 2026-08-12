#!/usr/bin/env python3
"""Tests for the official-copy-only v2 updater."""

import importlib.util
import json
import os
import shutil
import subprocess
import tempfile
import unittest


SCRIPT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts", "ip-update.py"))
spec = importlib.util.spec_from_file_location("ip_update", SCRIPT)
ip_update = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ip_update)


class FakeRunner:
    def __init__(self, install_dir, remote=ip_update.OFFICIAL_REMOTE, dirty="", counts="0 1"):
        self.install_dir = os.path.abspath(install_dir)
        self.remote = remote
        self.dirty = dirty
        self.counts = counts
        self.calls = []

    def __call__(self, command, cwd=None, **kwargs):
        command = list(command)
        self.calls.append((command, cwd))
        key = tuple(command)
        stdout = ""
        if key == ("git", "rev-parse", "--show-toplevel"):
            stdout = self.install_dir
        elif key == ("git", "remote", "get-url", "origin"):
            stdout = self.remote
        elif key == ("git", "status", "--porcelain", "--untracked-files=all"):
            stdout = self.dirty
        elif key == ("git", "symbolic-ref", "--quiet", "--short", "HEAD"):
            stdout = "main"
        elif key[:3] == ("git", "rev-list", "--left-right"):
            stdout = self.counts
        return subprocess.CompletedProcess(command, 0, stdout=stdout + ("\n" if stdout else ""), stderr="")


class TestIpUpdate(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="ip-update-test-")
        self.install = os.path.join(self.root, "ip-strategist")
        os.makedirs(self.install)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _make_git(self):
        os.mkdir(os.path.join(self.install, ".git"))

    def _lock(self, source=ip_update.OFFICIAL_SOURCE):
        path = os.path.join(self.root, "skills-lock.json")
        with open(path, "w", encoding="utf-8") as handle:
            json.dump({"version": 1, "skills": {"ip-strategist": {"source": source}}}, handle)
        return path

    def _global_lock(self, source=ip_update.OFFICIAL_SOURCE):
        path = os.path.join(self.root, ".agents", ".skill-lock.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump({"version": 1, "skills": {"ip-strategist": {"source": source}}}, handle)
        return path

    def _commands(self, runner):
        return [call[0] for call in runner.calls]

    def test_official_git_fast_forward(self):
        self._make_git()
        runner = FakeRunner(self.install, counts="0 2")
        result = ip_update.update_installation(self.install, runner=runner)
        self.assertEqual(result["status"], "updated")
        self.assertIn(["git", "merge", "--ff-only", "origin/main"], self._commands(runner))

    def test_official_git_current_does_not_merge(self):
        self._make_git()
        runner = FakeRunner(self.install, counts="0 0")
        result = ip_update.update_installation(self.install, runner=runner)
        self.assertEqual(result["status"], "current")
        self.assertFalse(any(command[:2] == ["git", "merge"] for command in self._commands(runner)))

    def test_remote_mismatch_stops_before_fetch(self):
        self._make_git()
        runner = FakeRunner(self.install, remote="https://github.com/attacker/ip-strategist.git")
        with self.assertRaisesRegex(ip_update.UpdateError, "不是官方"):
            ip_update.update_installation(self.install, runner=runner)
        self.assertFalse(any(command[:2] == ["git", "fetch"] for command in self._commands(runner)))

    def test_dirty_worktree_stops_before_fetch(self):
        self._make_git()
        runner = FakeRunner(self.install, dirty=" M SKILL.md")
        with self.assertRaisesRegex(ip_update.UpdateError, "本地修改"):
            ip_update.update_installation(self.install, runner=runner)
        self.assertFalse(any(command[:2] == ["git", "fetch"] for command in self._commands(runner)))

    def test_ahead_or_diverged_stops_without_merge(self):
        self._make_git()
        runner = FakeRunner(self.install, counts="1 1")
        with self.assertRaisesRegex(ip_update.UpdateError, "官方没有的提交"):
            ip_update.update_installation(self.install, runner=runner)
        self.assertFalse(any(command[:2] == ["git", "merge"] for command in self._commands(runner)))

    def test_non_git_official_installer_copy_uses_verified_command(self):
        lockfile = self._lock()
        runner = FakeRunner(self.install)
        result = ip_update.update_installation(self.install, runner=runner, lockfile=lockfile)
        self.assertEqual(result["install_type"], "skills-installer")
        self.assertIn(list(ip_update.INSTALL_COMMAND), self._commands(runner))

    def test_non_git_unverified_copy_degrades_to_manual_instructions(self):
        lockfile = self._lock("someone-else/ip-strategist")
        runner = FakeRunner(self.install)
        result = ip_update.update_installation(self.install, runner=runner, lockfile=lockfile)
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "manual_replacement_required")
        self.assertIn("整体替换", result["message"])
        self.assertEqual(runner.calls, [])

    def test_unrelated_parent_lock_does_not_claim_manual_copy(self):
        self._lock()
        runner = FakeRunner(self.install)
        result = ip_update.update_installation(self.install, runner=runner)
        self.assertFalse(result["ok"])
        self.assertEqual(result["install_type"], "manual")
        self.assertEqual(runner.calls, [])

    def test_global_skills_cli_lock_is_discovered_for_agents_install(self):
        install = os.path.join(self.root, ".agents", "skills", "ip-strategist")
        os.makedirs(install)
        lockfile = self._global_lock()
        runner = FakeRunner(install)
        result = ip_update.update_installation(install, runner=runner)
        self.assertEqual(result["install_type"], "skills-installer")
        self.assertEqual(result["lockfile"], lockfile)
        self.assertIn(list(ip_update.INSTALL_COMMAND), self._commands(runner))

    def test_private_state_in_install_dir_is_never_opened_or_updated(self):
        private = os.path.join(self.install, "ip-dossier.md")
        with open(private, "w", encoding="utf-8") as handle:
            handle.write("DO NOT TOUCH")
        before = os.stat(private)
        runner = FakeRunner(self.install)
        with self.assertRaisesRegex(ip_update.UpdateError, "私人状态"):
            ip_update.update_installation(self.install, runner=runner, lockfile=self._lock())
        after = os.stat(private)
        self.assertEqual((before.st_size, before.st_mtime_ns), (after.st_size, after.st_mtime_ns))
        self.assertEqual(runner.calls, [])
        with open(private, "r", encoding="utf-8") as handle:
            self.assertEqual(handle.read(), "DO NOT TOUCH")

    def test_remote_normalization_supports_https_and_ssh_only_for_official(self):
        self.assertEqual(ip_update.normalize_remote(ip_update.OFFICIAL_REMOTE), ip_update.OFFICIAL_SOURCE)
        self.assertEqual(ip_update.normalize_remote("git@github.com:erduo1998-cell/ip-strategist.git"), ip_update.OFFICIAL_SOURCE)
        self.assertEqual(ip_update.normalize_remote("ssh://git@github.com/erduo1998-cell/ip-strategist.git"), ip_update.OFFICIAL_SOURCE)
        self.assertNotEqual(ip_update.normalize_remote("http://github.com/erduo1998-cell/ip-strategist.git"), ip_update.OFFICIAL_SOURCE)
        self.assertNotEqual(ip_update.normalize_remote("git://github.com/erduo1998-cell/ip-strategist.git"), ip_update.OFFICIAL_SOURCE)
        self.assertNotEqual(ip_update.normalize_remote("https://example.com/erduo1998-cell/ip-strategist.git"), ip_update.OFFICIAL_SOURCE)


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Safely update only the official ip-strategist installation.

Git clones are fast-forwarded only after remote and worktree validation.
Installer-managed copies are reinstalled only when an official lock entry is
present.  Manual/ZIP copies receive deterministic replacement instructions.
User dossier and contract data is never read, moved, or modified.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys


OFFICIAL_SOURCE = "erduo1998-cell/ip-strategist"
OFFICIAL_REMOTE = "https://github.com/erduo1998-cell/ip-strategist.git"
INSTALL_COMMAND = (
    "npx", "-y", "skills", "add", OFFICIAL_SOURCE, "-g", "--all",
)
PRIVATE_NAMES = ("ip-dossier.md", "ip-contracts")


class UpdateError(RuntimeError):
    """A safe, expected refusal to update."""


def _run(command, cwd=None, runner=subprocess.run):
    completed = runner(
        list(command), cwd=cwd, capture_output=True, text=True, check=False,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "命令失败").strip()
        raise UpdateError("%s：%s" % (" ".join(command[:3]), detail))
    return (completed.stdout or "").strip()


def normalize_remote(value):
    value = (value or "").strip().rstrip("/")
    prefixes = (
        "https://github.com/", "ssh://git@github.com/", "git@github.com:",
    )
    matched = False
    for prefix in prefixes:
        if value.lower().startswith(prefix):
            value = value[len(prefix):]
            matched = True
            break
    if not matched:
        return ""
    if value.endswith(".git"):
        value = value[:-4]
    return value.lower()


def _private_state_present(install_dir):
    # Existence only: never open or enumerate these user-owned paths.
    return [name for name in PRIVATE_NAMES if os.path.lexists(os.path.join(install_dir, name))]


def _git_install(install_dir, runner):
    root = _run(("git", "rev-parse", "--show-toplevel"), install_dir, runner)
    if os.path.realpath(root) != os.path.realpath(install_dir):
        raise UpdateError("安装目录不是独立 Git 仓库根，已停止更新")
    remote = _run(("git", "remote", "get-url", "origin"), install_dir, runner)
    if normalize_remote(remote) != OFFICIAL_SOURCE.lower():
        raise UpdateError("origin 不是官方 %s，已停止更新" % OFFICIAL_SOURCE)
    dirty = _run(("git", "status", "--porcelain", "--untracked-files=all"), install_dir, runner)
    if dirty:
        raise UpdateError("工作树有本地修改或未跟踪文件，已停止更新；请先自行备份或提交")
    branch = _run(("git", "symbolic-ref", "--quiet", "--short", "HEAD"), install_dir, runner)
    _run(("git", "fetch", "--prune", "origin", branch), install_dir, runner)
    counts = _run(
        ("git", "rev-list", "--left-right", "--count", "HEAD...origin/%s" % branch),
        install_dir, runner,
    ).split()
    if len(counts) != 2 or not all(part.isdigit() for part in counts):
        raise UpdateError("无法确认本地与官方分支的 fast-forward 关系")
    ahead, behind = map(int, counts)
    if ahead:
        raise UpdateError("本地分支包含官方没有的提交，已停止更新")
    if behind:
        _run(("git", "merge", "--ff-only", "origin/%s" % branch), install_dir, runner)
        status = "updated"
    else:
        status = "current"
    return {"ok": True, "install_type": "git", "status": status, "branch": branch}


def _lock_candidates(install_dir, lockfile=None, path_module=os.path):
    if lockfile:
        return [path_module.abspath(lockfile)]
    candidates = []
    cursor = path_module.abspath(install_dir)
    normalized_install = path_module.normcase(path_module.normpath(cursor))
    while True:
        for container in (".agents/skills", ".claude/skills", ".codex/skills"):
            managed_root = path_module.normcase(
                path_module.normpath(path_module.join(cursor, container))
            )
            try:
                common_root = path_module.normcase(
                    path_module.normpath(
                        path_module.commonpath((normalized_install, managed_root))
                    )
                )
                in_managed_root = common_root == managed_root
            except ValueError:
                in_managed_root = False
            if in_managed_root:
                candidates.extend((
                    path_module.join(cursor, "skills-lock.json"),
                    path_module.join(cursor, ".agents", ".skill-lock.json"),
                ))
                break
        parent = path_module.dirname(cursor)
        if parent == cursor:
            break
        cursor = parent
    # Stable de-duplication.
    return list(dict.fromkeys(candidates))


def _official_lock(lockfiles):
    for path in lockfiles:
        try:
            with open(path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except (OSError, UnicodeDecodeError, ValueError):
            continue
        entry = payload.get("skills", {}).get("ip-strategist", {})
        if str(entry.get("source", "")).lower() == OFFICIAL_SOURCE.lower():
            return path
    return None


def _installer_command(os_name=os.name, which=shutil.which):
    if os_name != "nt":
        return INSTALL_COMMAND
    executable = which(INSTALL_COMMAND[0])
    if not executable:
        raise UpdateError("Windows 上未找到 npx.cmd；请确认 Node.js/npm 已安装并已加入 PATH")
    return (executable,) + INSTALL_COMMAND[1:]


def _non_git_install(install_dir, runner, lockfile=None):
    official_lock = _official_lock(_lock_candidates(install_dir, lockfile))
    if not official_lock:
        return {
            "ok": False,
            "install_type": "manual",
            "status": "manual_replacement_required",
            "message": "未证明此副本由官方 skills 安装器管理；请整体替换 Skill 目录，不要只替换 SKILL.md。",
        }
    _run(_installer_command(), None, runner)
    return {
        "ok": True,
        "install_type": "skills-installer",
        "status": "updated",
        "lockfile": official_lock,
    }


def update_installation(install_dir, runner=subprocess.run, lockfile=None):
    """Update an installation and return a machine-testable result dictionary."""
    install_dir = os.path.abspath(install_dir)
    if not os.path.isdir(install_dir):
        raise UpdateError("安装目录不存在：%s" % install_dir)
    private = _private_state_present(install_dir)
    if private:
        raise UpdateError(
            "安装目录内发现私人状态（%s）；为避免覆盖已停止。请先移出并备份。"
            % ", ".join(private)
        )
    if os.path.isdir(os.path.join(install_dir, ".git")):
        return _git_install(install_dir, runner)
    return _non_git_install(install_dir, runner, lockfile)


def main(argv=None):
    default_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    parser = argparse.ArgumentParser(description="安全更新官方 ip-strategist 副本。")
    parser.add_argument("install_dir", nargs="?", default=default_dir, help="Skill 安装目录")
    args = parser.parse_args(argv)
    try:
        result = update_installation(args.install_dir)
    except UpdateError as exc:
        print("[停止] %s" % exc, file=sys.stderr)
        return 2
    print("安装类型：%s" % result["install_type"])
    if not result["ok"]:
        print("[需要手动更新] %s" % result["message"])
        return 1
    if result["status"] == "current":
        print("[完成] 已是官方最新版本。")
    else:
        print("[完成] ip-strategist 已安全更新。")
    print("请新建会话使用新版；当前会话不会自动重载 Skill。")
    return 0


if __name__ == "__main__":
    sys.exit(main())

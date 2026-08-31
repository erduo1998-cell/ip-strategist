#!/usr/bin/env python3
"""Synchronize only mapped, review-due self-owned works, then merge evidence.

Without --sync this is a no-write due-date inspection.  It does not edit a
contract, mark a review complete, or call any platform account write action.
"""

import argparse
import datetime
import importlib.util
import json
import os
import subprocess
import sys

from ip_review_evidence import (
    EVIDENCE_RELATIVE_PATH, atomic_private_json, build_contract_evidence, due_contracts,
)


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.dirname(SCRIPT_DIR)
INTEGRATIONS = {
    "douyin": ("douyin-comments", "--item-ids"),
    "xiaohongshu": ("xiaohongshu-comments", "--note"),
    "weixin-channels": ("weixin-channels-comments", "--object-ids"),
}


def _load_context():
    path = os.path.join(SCRIPT_DIR, "ip-context.py")
    spec = importlib.util.spec_from_file_location("ip_strategist_ip_context", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


IP_CONTEXT = _load_context()


def _profile_args(platform, args):
    profile = getattr(args, "%s_profile" % platform.replace("-", "_"))
    return ["--profile", profile] if profile else []


def _command(platform, workdir, mappings, args):
    directory, selector = INTEGRATIONS[platform]
    integration = os.path.join(REPO_DIR, "integrations", directory)
    if not os.path.isdir(integration) or os.path.islink(integration):
        raise ValueError("未安装 %s 本地只读适配器" % platform)
    ids = [row["work_id"] for row in mappings]
    command = ["npm", "run", "sync", "--", "--workdir", workdir, *_profile_args(platform, args)]
    if platform == "weixin-channels":
        command.extend([selector, ",".join(ids)])
    elif platform == "xiaohongshu":
        for work_id in ids:
            command.extend([selector, work_id])
    else:
        command.extend([selector, ",".join(ids)])
    return command, integration


def _summary(due):
    return [{
        "contract_id": row["contract"].get("contract_id", ""),
        "next_review_date": row["contract"].get("next_review_date", ""),
        "mappings": row["mappings"],
        "status": "ready" if row["mappings"] else "awaiting_mapping",
    } for row in due]


def main(argv=None):
    parser = argparse.ArgumentParser(description="只读同步到期契约已映射的三平台作品。")
    parser.add_argument("workdir")
    parser.add_argument("--today", help="YYYY-MM-DD；默认今天")
    parser.add_argument("--sync", action="store_true", help="实际调用本地只读平台采集器并写入私有证据")
    parser.add_argument("--douyin-profile")
    parser.add_argument("--xiaohongshu-profile")
    parser.add_argument("--weixin-channels-profile")
    args = parser.parse_args(argv)
    workdir = os.path.realpath(args.workdir)
    today = datetime.date.fromisoformat(args.today) if args.today else datetime.date.today()
    due = due_contracts(IP_CONTEXT._contracts(workdir), today)
    result = {"today": str(today), "due_contracts": _summary(due), "synced": [], "failed": []}
    if not args.sync:
        result["mode"] = "inspection_only"
        print(json.dumps(result, ensure_ascii=False))
        return 0

    grouped = {platform: [] for platform in INTEGRATIONS}
    for row in due:
        for mapping in row["mappings"]:
            grouped[mapping["platform"]].append(mapping)
    succeeded = set()
    for platform, mappings in grouped.items():
        if not mappings:
            continue
        try:
            command, cwd = _command(platform, workdir, mappings, args)
            completed = subprocess.run(
                command, cwd=cwd, stdin=subprocess.DEVNULL, text=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=15 * 60,
                check=False,
            )
            if completed.returncode != 0:
                raise RuntimeError("采集器退出码 %s" % completed.returncode)
            succeeded.add(platform)
            result["synced"].append({"platform": platform, "works": len(mappings)})
        except (OSError, ValueError, subprocess.SubprocessError, RuntimeError) as exc:
            result["failed"].append({"platform": platform, "reason": str(exc)[:240]})

    payload = build_contract_evidence(workdir, due, platforms=succeeded)
    output = os.path.join(workdir, EVIDENCE_RELATIVE_PATH)
    atomic_private_json(output, payload)
    result["mode"] = "synced_read_only"
    result["evidence_file"] = output
    result["evidence_status"] = payload["meta"]["status"]
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())

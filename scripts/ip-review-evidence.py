#!/usr/bin/env python3
"""Generate contract-scoped review evidence from already-fetched local data."""

import argparse
import datetime
import importlib.util
import json
import os
import sys

from ip_review_evidence import (
    EVIDENCE_RELATIVE_PATH, atomic_private_json, build_contract_evidence, due_contracts,
)


def _load_context():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ip-context.py")
    spec = importlib.util.spec_from_file_location("ip_strategist_ip_context", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


IP_CONTEXT = _load_context()


def main(argv=None):
    parser = argparse.ArgumentParser(description="合并到期契约的本地只读平台证据。")
    parser.add_argument("workdir")
    parser.add_argument("--today", help="YYYY-MM-DD；默认今天")
    parser.add_argument("--write", action="store_true", help="写入私有 contract-evidence.json")
    args = parser.parse_args(argv)
    today = datetime.date.fromisoformat(args.today) if args.today else datetime.date.today()
    workdir = os.path.realpath(args.workdir)
    due = due_contracts(IP_CONTEXT._contracts(workdir), today)
    payload = build_contract_evidence(workdir, due)
    if args.write:
        atomic_private_json(os.path.join(workdir, EVIDENCE_RELATIVE_PATH), payload)
    print(json.dumps({
        "due_contracts": len(due),
        "status": payload["meta"]["status"],
        "evidence_file": os.path.join(workdir, EVIDENCE_RELATIVE_PATH) if args.write else None,
        "contracts": [{
            "contract_id": row["contract_id"],
            "evidence_status": row["evidence_status"],
            "works": len(row["works"]),
        } for row in payload["contracts"]],
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())

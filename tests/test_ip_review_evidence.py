#!/usr/bin/env python3
"""Synthetic tests for the local-only contract evidence bridge."""

import datetime
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest


SCRIPTS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts"))
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import ip_review_evidence as review_evidence


class TestReviewEvidence(unittest.TestCase):
    def setUp(self):
        self.workdir = tempfile.mkdtemp(prefix="ip-review-evidence-test-")
        self.contracts = os.path.join(self.workdir, "ip-contracts")
        os.makedirs(self.contracts)

    def tearDown(self):
        shutil.rmtree(self.workdir, ignore_errors=True)

    def _contract(self, contract_id="C-SYNTH-01", status="待复盘", review_date="2026-08-01", works=None):
        works = works if works is not None else [{"platform": "douyin", "work_id": "synthetic-work-1"}]
        path = os.path.join(self.contracts, "%s.md" % contract_id)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("""---
contract_id: %s
status: %s
sign_date: 2026-07-01
plan_publish_date: 2026-07-02
actual_publish_date: 2026-07-02
review_after_days: 30
next_review_date: %s
---

<!-- ip-platform-works
%s
-->
""" % (contract_id, status, review_date, json.dumps({"schema_version": 1, "works": works})))
        return path

    def _evidence(self, platform, works):
        path = os.path.join(self.workdir, "ip-evidence", platform, "comments-evidence.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump({"meta": {"platform": platform}, "works": works}, handle)

    def test_mapping_is_strict_and_deduplicated(self):
        text = "<!-- ip-platform-works\n" + json.dumps({
            "schema_version": 1,
            "works": [
                {"platform": "douyin", "work_id": "item_01", "aweme_id": "aweme-01"},
                {"platform": "douyin", "work_id": "item_01", "aweme_id": "aweme-01"},
            ],
        }) + "\n-->"
        self.assertEqual(review_evidence.parse_platform_works(text), [{
            "platform": "douyin", "work_id": "item_01", "aweme_id": "aweme-01",
        }])
        with self.assertRaisesRegex(ValueError, "work_id"):
            review_evidence.parse_platform_works(
                '<!-- ip-platform-works\n{"schema_version":1,"works":[{"platform":"douyin","work_id":"https://not-an-id"}]}\n-->'
            )

    def test_due_selection_never_changes_contract_state(self):
        due_path = self._contract()
        future_path = self._contract("C-SYNTH-02", review_date="2026-09-01")
        contracts = [
            {"contract_id": "C-SYNTH-02", "status": "待复盘", "next_review_date": "2026-09-01", "path": future_path},
            {"contract_id": "C-SYNTH-01", "status": "待复盘", "next_review_date": "2026-08-01", "path": due_path},
        ]
        due = review_evidence.due_contracts(contracts, datetime.date(2026, 8, 31))
        self.assertEqual([row["contract"]["contract_id"] for row in due], ["C-SYNTH-01"])
        self.assertEqual(contracts[1]["status"], "待复盘")

    def test_merge_uses_only_exact_mapping_and_preserves_partial_status(self):
        path = self._contract()
        self._evidence("douyin", [{
            "item_id": "synthetic-work-1", "title": "合成作品", "completeness": "complete",
            "metrics": {"view_count": 42, "ignored": {"nested": True}},
            "comments": [{"text": "请继续讲这个合成话题", "digg_count": 3}],
        }, {
            "item_id": "unmapped-work", "title": "不可被标题猜测的作品", "completeness": "complete",
        }])
        due = review_evidence.due_contracts([{
            "contract_id": "C-SYNTH-01", "status": "待复盘", "next_review_date": "2026-08-01", "path": path,
        }], datetime.date(2026, 8, 31))
        payload = review_evidence.build_contract_evidence(self.workdir, due, generated_at="2026-08-31T00:00:00Z")
        self.assertEqual(payload["meta"]["status"], "complete")
        work = payload["contracts"][0]["works"][0]
        self.assertEqual(work["title"], "合成作品")
        self.assertEqual(work["metrics"], {"view_count": 42})
        self.assertNotIn("unmapped-work", json.dumps(payload, ensure_ascii=False))

        no_mapping = self._contract("C-SYNTH-EMPTY", works=[])
        empty_due = review_evidence.due_contracts([{
            "contract_id": "C-SYNTH-EMPTY", "status": "待复盘", "next_review_date": "2026-08-01", "path": no_mapping,
        }], datetime.date(2026, 8, 31))
        self.assertEqual(review_evidence.build_contract_evidence(self.workdir, empty_due)["contracts"][0]["evidence_status"], "awaiting_mapping")

    def test_read_only_clis_inspect_due_mapping_without_writing_or_platform_calls(self):
        self._contract()
        review_script = os.path.join(SCRIPTS, "ip-review-evidence.py")
        sync_script = os.path.join(SCRIPTS, "ip-review-sync.py")
        command = [sys.executable, review_script, self.workdir, "--today", "2026-08-31"]
        inspected = json.loads(subprocess.check_output(command, text=True))
        self.assertEqual(inspected["due_contracts"], 1)
        self.assertIsNone(inspected["evidence_file"])
        self.assertFalse(os.path.exists(os.path.join(self.workdir, review_evidence.EVIDENCE_RELATIVE_PATH)))
        sync = json.loads(subprocess.check_output([
            sys.executable, sync_script, self.workdir, "--today", "2026-08-31",
        ], text=True))
        self.assertEqual(sync["mode"], "inspection_only")
        self.assertEqual(sync["due_contracts"][0]["status"], "ready")


if __name__ == "__main__":
    unittest.main()

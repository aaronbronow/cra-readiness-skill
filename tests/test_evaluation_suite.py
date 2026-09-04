"""
Automated Test Suite evaluating the 3-Tier Headless CRA Readiness Skill
across synthetic archetypes, real repositories, and GitHub Actions integration.
Compatible with both unittest and pytest (zero external dependencies).
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tests.evaluator.harness import (
    ClaudeRunner,
    GeminiRunner,
    SyntheticRepoFactory,
    ALL_40_CANONICAL_IDS,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
CLAUDE_SCRIPT = REPO_ROOT / "scripts" / "collect.py"
COLLECTOR_SCRIPT = REPO_ROOT / "scripts" / "collector.py"
MATRIX_JSON = REPO_ROOT / "references" / "cra_matrix_40.json"


class BaseTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.claude = ClaudeRunner(CLAUDE_SCRIPT) if CLAUDE_SCRIPT.exists() else None
        cls.gemini = GeminiRunner(COLLECTOR_SCRIPT, MATRIX_JSON)

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="cra_test_"))

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)


class TestErrorHandlingAndEdgeCases(BaseTestCase):
    def test_invalid_path(self):
        invalid_path = self.temp_dir / "does_not_exist"

        if self.claude:
            c_res = self.claude.run(invalid_path)
            self.assertEqual(c_res.grade, "D")

        g_res = self.gemini.run(invalid_path)
        self.assertEqual(g_res.grade, "D")

    def test_empty_repository(self):
        empty_path = SyntheticRepoFactory.create_empty(self.temp_dir / "empty")

        if self.claude:
            c_res = self.claude.run(empty_path)
            self.assertEqual(c_res.grade, "D")

        g_res = self.gemini.run(empty_path)
        self.assertEqual(g_res.grade, "D")


class TestThreeTierScanArchitecture(BaseTestCase):
    def test_tiered_status_classification(self):
        target = SyntheticRepoFactory.create_minimal_code(self.temp_dir / "tiered_test")
        (target / "SECURITY.md").write_text("# Security\nContact us at info@example.com\n", encoding="utf-8")

        res = self.gemini.run(target)
        raw = res.raw_json
        self.assertIsNotNone(raw)

        self.assertIn("needs_explanation_count", raw)
        self.assertIn("needs_user_input_count", raw)
        self.assertIn("pass_count", raw)
        self.assertIn("fail_count", raw)

        self.assertGreater(raw["needs_explanation_count"], 0)
        self.assertGreater(raw["needs_user_input_count"], 0)

    def test_github_action_step_summary_output(self):
        target = SyntheticRepoFactory.create_minimal_code(self.temp_dir / "action_test")
        summary_file = self.temp_dir / "step_summary.md"
        output_file = self.temp_dir / "github_output.txt"

        env = os.environ.copy()
        env["GITHUB_STEP_SUMMARY"] = str(summary_file)
        env["GITHUB_OUTPUT"] = str(output_file)

        cmd = [
            sys.executable,
            str(COLLECTOR_SCRIPT),
            str(target),
            "--matrix",
            str(MATRIX_JSON),
            "--github-action",
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, env=env)
        self.assertEqual(proc.returncode, 0)

        self.assertTrue(summary_file.exists())
        summary_txt = summary_file.read_text(encoding="utf-8")
        self.assertIn("# CRA Manufacturer Readiness Scorecard", summary_txt)
        self.assertIn("Overall Result", summary_txt)

        self.assertTrue(output_file.exists())
        output_txt = output_file.read_text(encoding="utf-8")
        self.assertIn("grade=", output_txt)
        self.assertIn("passed_items=", output_txt)

    def test_graceful_token_handling(self):
        target = SyntheticRepoFactory.create_minimal_code(self.temp_dir / "token_test")
        cmd = [
            sys.executable,
            str(COLLECTOR_SCRIPT),
            str(target),
            "--matrix",
            str(MATRIX_JSON),
            "--token",
            "dummy_invalid_token_12345",
            "--repo-slug",
            "dummy/repo",
            "--format",
            "json",
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0)

    def test_action_yml_metadata_validity(self):
        action_file = REPO_ROOT / "action.yml"
        self.assertTrue(action_file.exists())
        txt = action_file.read_text(encoding="utf-8")
        self.assertIn("inputs:", txt)
        self.assertIn("repo-path:", txt)
        self.assertIn("outputs:", txt)
        self.assertIn("grade:", txt)

    def test_interview_guide_exists(self):
        guide_file = REPO_ROOT / "references" / "interview_guide.md"
        self.assertTrue(guide_file.exists())
        txt = guide_file.read_text(encoding="utf-8")
        self.assertIn("Founder Interview Guide", txt)
        self.assertIn("NEEDS_USER_INPUT", txt)


class TestArchetypeProgression(BaseTestCase):
    def test_minimal_code_repo(self):
        target = SyntheticRepoFactory.create_minimal_code(self.temp_dir / "minimal")
        g_res = self.gemini.run(target)
        self.assertIn(g_res.grade, ("C", "D"))

    def test_automation_heavy_repo(self):
        target = SyntheticRepoFactory.create_automation_heavy(self.temp_dir / "auto_heavy")
        g_res = self.gemini.run(target)
        self.assertEqual(g_res.items["R1"].status, "PASS")
        self.assertEqual(g_res.items["B6"].status, "PASS")
        self.assertNotEqual(g_res.grade, "A")

    def test_policy_heavy_repo(self):
        target = SyntheticRepoFactory.create_policy_heavy(self.temp_dir / "policy_heavy")
        g_res = self.gemini.run(target)
        self.assertEqual(g_res.items["R12"].status, "PASS")
        self.assertIn(g_res.grade, ("B", "C"))

    def test_fully_compliant_repo(self):
        target = SyntheticRepoFactory.create_full_compliance(self.temp_dir / "full")
        g_res = self.gemini.run(target)
        self.assertEqual(g_res.grade, "A")
        self.assertGreaterEqual(g_res.passed_count, 30)


class TestSchemaAndCompleteness(BaseTestCase):
    def test_all_40_items_enriched(self):
        with open(MATRIX_JSON, "r", encoding="utf-8") as f:
            matrix = json.load(f)

        item_ids = []
        for stage in matrix["stages"]:
            for item in stage["items"]:
                iid = item["id"]
                item_ids.append(iid)
                self.assertIn("tier", item)
                self.assertIn(item["tier"], ("deterministic", "inferrable", "attestation"))
                self.assertIn("primary_doc", item)
                self.assertIn("inference_criteria", item)
                self.assertIn("interview_prompt", item)

        self.assertEqual(len(item_ids), 40)


class TestPerformanceBenchmarks(BaseTestCase):
    def test_latency_limits(self):
        target = SyntheticRepoFactory.create_full_compliance(self.temp_dir / "full")
        g_res = self.gemini.run(target)
        self.assertLess(g_res.duration_ms, 500)


if __name__ == "__main__":
    unittest.main()

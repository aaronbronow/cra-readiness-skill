"""
Evaluation harness for comparing Claude Fable 5.1 and Gemini 3.8 Flash CRA collectors.
Zero external dependencies (pure standard library).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

AUTO_ITEMS_CLAUDE = {"D2", "D3", "D4", "R1", "R2", "P2", "P7"}
GATE_ITEMS_CLAUDE = {
    "F1", "B1", "B2", "B3", "B9", "D3", "D4", "R1", "R2",
    "R5", "R6", "R7", "R8", "R9", "R11", "R12", "P2", "P3", "P8"
}

ALL_40_CANONICAL_IDS = [
    "F1", "F2", "F3", "F4",
    "B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B9",
    "D1", "D2", "D3", "D4", "D5",
    "R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8", "R9", "R10", "R11", "R12",
    "P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8", "P9", "P10"
]


def c_to_g(cid: str) -> str:
    """Map Claude ID (e.g. F1, P2) to Gemini ID (e.g. F.1, A.2)."""
    prefix = cid[0]
    num = cid[1:]
    if prefix == "P":
        prefix = "A"
    return f"{prefix}.{num}"


def g_to_c(gid: str) -> str:
    """Map Gemini ID (e.g. F.1, A.2) to Claude ID (e.g. F1, P2)."""
    parts = gid.split(".")
    prefix = parts[0]
    num = parts[1]
    if prefix == "A":
        prefix = "P"
    return f"{prefix}{num}"


def score_claude_evidence(evidence: Dict[str, Any]) -> Tuple[str, str]:
    """
    Computes Grade (A, B, C, D) using the exact mechanical rubric
    from references/scoring.md (rubric 2026.09.1).
    """
    access = evidence.get("access", {})
    if not access.get("local_files") and not access.get("api"):
        return "D", "Repository not accessed"

    checks = {c["id"]: c["status"] for c in evidence.get("checks", [])}
    if not checks:
        return "D", "No checks recorded in evidence"

    applicable = {k: v for k, v in checks.items() if v != "NA"}
    unknown_count = sum(1 for v in applicable.values() if v == "UNKNOWN")

    auto_gap = any(checks.get(item) in ("NOT_MET", "PARTIAL") for item in AUTO_ITEMS_CLAUDE if checks.get(item) != "NA")

    policy_items = [k for k in applicable if k not in AUTO_ITEMS_CLAUDE]
    policy_not_met = any(checks.get(item) == "NOT_MET" for item in policy_items)
    policy_partial_count = sum(1 for item in policy_items if checks.get(item) == "PARTIAL")
    policy_gap = policy_not_met or (policy_partial_count > 3)

    gate_fail = any(checks.get(item) in ("NOT_MET", "PARTIAL", "UNKNOWN") for item in GATE_ITEMS_CLAUDE if checks.get(item) != "NA")

    if unknown_count >= 10:
        return "D", f"Insufficient information (unknown_count={unknown_count} >= 10)"
    if not gate_fail and not auto_gap and not policy_gap:
        return "A", "Ready for EU launch (all gates, auto, and policy met)"
    if not policy_gap and auto_gap:
        return "B", "Needs automation work (policy baseline met)"
    return "C", f"Needs automation & policy work (gate_fail={gate_fail}, auto_gap={auto_gap}, policy_gap={policy_gap})"


@dataclass
class SingleCheckResult:
    canonical_id: str
    gemini_id: str
    title: str
    status: str
    raw_status: str
    matched_signal: Optional[str] = None


@dataclass
class CollectorRunResult:
    implementation: str
    repo_path: str
    duration_ms: float
    exit_code: int
    grade: str
    grade_reason: str
    items: Dict[str, SingleCheckResult] = field(default_factory=dict)
    passed_count: int = 0
    failed_count: int = 0
    raw_json: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@dataclass
class DivergenceItem:
    canonical_id: str
    gemini_id: str
    title: str
    claude_status: str
    gemini_status: str
    claude_evidence: Optional[str]
    gemini_evidence: Optional[str]


@dataclass
class RepoComparisonResult:
    repo_name: str
    repo_path: str
    claude: CollectorRunResult
    gemini: CollectorRunResult
    agreement_rate: float
    strict_agreement_rate: float
    divergences: List[DivergenceItem] = field(default_factory=list)


class ClaudeRunner:
    def __init__(self, script_path: Path):
        self.script_path = Path(script_path).resolve()
        if not self.script_path.exists():
            raise FileNotFoundError(f"Claude script not found: {self.script_path}")

    def run(self, target_dir: Path) -> CollectorRunResult:
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp_file:
            tmp_path = tmp_file.name

        start_time = time.perf_counter()
        try:
            cmd = [
                "python3",
                str(self.script_path),
                "--path",
                str(target_dir),
                "--no-api",
                "--out",
                tmp_path,
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True)
            duration_ms = (time.perf_counter() - start_time) * 1000.0

            if not os.path.exists(tmp_path) or os.path.getsize(tmp_path) == 0:
                return CollectorRunResult(
                    implementation="Claude Fable 5.1",
                    repo_path=str(target_dir),
                    duration_ms=duration_ms,
                    exit_code=proc.returncode,
                    grade="D",
                    grade_reason="Collector produced no output file",
                    error=proc.stderr or proc.stdout,
                )

            with open(tmp_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            grade, grade_reason = score_claude_evidence(data)
            items: Dict[str, SingleCheckResult] = {}
            passed_cnt = 0
            failed_cnt = 0

            for check in data.get("checks", []):
                cid = check["id"]
                raw_st = check["status"]
                norm_st = "PASS" if raw_st == "MET" else ("PARTIAL" if raw_st == "PARTIAL" else "FAIL")
                if norm_st in ("PASS", "PARTIAL"):
                    passed_cnt += 1
                else:
                    failed_cnt += 1

                matched_sig = None
                evidence_dict = check.get("evidence", {})
                if isinstance(evidence_dict, dict):
                    matched_sig = next((f"{k}={v}" for k, v in evidence_dict.items() if v), None)

                items[cid] = SingleCheckResult(
                    canonical_id=cid,
                    gemini_id=c_to_g(cid),
                    title=check.get("title", ""),
                    status=norm_st,
                    raw_status=raw_st,
                    matched_signal=matched_sig,
                )

            return CollectorRunResult(
                implementation="Claude Fable 5.1",
                repo_path=str(target_dir),
                duration_ms=duration_ms,
                exit_code=proc.returncode,
                grade=grade,
                grade_reason=grade_reason,
                items=items,
                passed_count=passed_cnt,
                failed_count=failed_cnt,
                raw_json=data,
            )

        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            return CollectorRunResult(
                implementation="Claude Fable 5.1",
                repo_path=str(target_dir),
                duration_ms=duration_ms,
                exit_code=-1,
                grade="D",
                grade_reason=f"Execution exception: {exc}",
                error=str(exc),
            )
        finally:
            if os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass


class GeminiRunner:
    def __init__(self, script_path: Path, matrix_path: Optional[Path] = None):
        self.script_path = Path(script_path).resolve()
        if not self.script_path.exists():
            raise FileNotFoundError(f"Gemini script not found: {self.script_path}")
        self.matrix_path = Path(matrix_path).resolve() if matrix_path else self.script_path.parent.parent / "references" / "cra_matrix_40.json"

    def run(self, target_dir: Path) -> CollectorRunResult:
        start_time = time.perf_counter()
        try:
            cmd = [
                "python3",
                str(self.script_path),
                str(target_dir),
                "--format",
                "json",
            ]
            if self.matrix_path and self.matrix_path.exists():
                cmd.extend(["--matrix", str(self.matrix_path)])

            proc = subprocess.run(cmd, capture_output=True, text=True)
            duration_ms = (time.perf_counter() - start_time) * 1000.0

            if proc.returncode != 0 and not proc.stdout.strip().startswith("{"):
                return CollectorRunResult(
                    implementation="Gemini 3.8 Flash",
                    repo_path=str(target_dir),
                    duration_ms=duration_ms,
                    exit_code=proc.returncode,
                    grade="D",
                    grade_reason="Collector exited with error",
                    error=proc.stderr or proc.stdout,
                )

            data = json.loads(proc.stdout)
            grade = data.get("grade", "D")
            grade_reason = data.get("grade_description", "")

            items: Dict[str, SingleCheckResult] = {}
            passed_cnt = 0
            failed_cnt = 0

            item_list = data.get("item_details", [])
            if not item_list and data.get("grade") == "D":
                # Repo was unassessed or empty; populate 40 unassessed failing items
                for cid in ALL_40_CANONICAL_IDS:
                    gid = c_to_g(cid)
                    items[cid] = SingleCheckResult(
                        canonical_id=cid,
                        gemini_id=gid,
                        title="Unassessed item",
                        status="FAIL",
                        raw_status="UNASSESSED",
                        matched_signal=None,
                    )
                failed_cnt = 40
            else:
                for it in item_list:
                    gid = it["id"]
                    cid = g_to_c(gid)
                    st = it.get("status", "FAIL")
                    if st == "PASS":
                        passed_cnt += 1
                    else:
                        failed_cnt += 1

                    items[cid] = SingleCheckResult(
                        canonical_id=cid,
                        gemini_id=gid,
                        title=it.get("title", ""),
                        status=st,
                        raw_status=st,
                        matched_signal=it.get("matched_signal"),
                    )

            return CollectorRunResult(
                implementation="Gemini 3.8 Flash",
                repo_path=str(target_dir),
                duration_ms=duration_ms,
                exit_code=proc.returncode,
                grade=grade,
                grade_reason=grade_reason,
                items=items,
                passed_count=passed_cnt,
                failed_count=failed_cnt,
                raw_json=data,
            )

        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            return CollectorRunResult(
                implementation="Gemini 3.8 Flash",
                repo_path=str(target_dir),
                duration_ms=duration_ms,
                exit_code=-1,
                grade="D",
                grade_reason=f"Execution exception: {exc}",
                error=str(exc),
            )


def compare_collectors_on_repo(
    repo_name: str,
    repo_path: Path,
    claude_runner: ClaudeRunner,
    gemini_runner: GeminiRunner,
) -> RepoComparisonResult:
    c_res = claude_runner.run(repo_path)
    g_res = gemini_runner.run(repo_path)

    divergences: List[DivergenceItem] = []
    agreed_lenient = 0
    agreed_strict = 0
    total_evaluated = 0

    for cid in ALL_40_CANONICAL_IDS:
        c_item = c_res.items.get(cid)
        g_item = g_res.items.get(cid)

        if not c_item or not g_item:
            continue

        total_evaluated += 1
        c_pass = c_item.status in ("PASS", "PARTIAL")
        g_pass = g_item.status == "PASS"

        if c_pass == g_pass:
            agreed_lenient += 1
        else:
            divergences.append(
                DivergenceItem(
                    canonical_id=cid,
                    gemini_id=c_item.gemini_id,
                    title=c_item.title or g_item.title,
                    claude_status=c_item.raw_status,
                    gemini_status=g_item.raw_status,
                    claude_evidence=c_item.matched_signal,
                    gemini_evidence=g_item.matched_signal,
                )
            )

        c_strict_pass = c_item.status == "PASS"
        if c_strict_pass == g_pass:
            agreed_strict += 1

    agreement_rate = (agreed_lenient / total_evaluated * 100.0) if total_evaluated > 0 else 0.0
    strict_agreement_rate = (agreed_strict / total_evaluated * 100.0) if total_evaluated > 0 else 0.0

    return RepoComparisonResult(
        repo_name=repo_name,
        repo_path=str(repo_path),
        claude=c_res,
        gemini=g_res,
        agreement_rate=agreement_rate,
        strict_agreement_rate=strict_agreement_rate,
        divergences=divergences,
    )


class SyntheticRepoFactory:
    """Builds synthetic git repository fixtures simulating varied compliance states."""

    @staticmethod
    def create_empty(target_dir: Path) -> Path:
        target_dir.mkdir(parents=True, exist_ok=True)
        return target_dir

    @staticmethod
    def create_minimal_code(target_dir: Path) -> Path:
        target_dir.mkdir(parents=True, exist_ok=True)
        (target_dir / "src").mkdir(exist_ok=True)
        (target_dir / "src" / "main.py").write_text("print('Hello startup')\n", encoding="utf-8")
        (target_dir / "README.md").write_text("# My Startup App\nA minimal application without security documentation.\n", encoding="utf-8")
        (target_dir / "pyproject.toml").write_text("[project]\nname='minimal'\nversion='0.1.0'\n", encoding="utf-8")
        return target_dir

    @staticmethod
    def create_automation_heavy(target_dir: Path) -> Path:
        target_dir.mkdir(parents=True, exist_ok=True)
        (target_dir / "src").mkdir(exist_ok=True)
        (target_dir / "src" / "main.py").write_text("print('Secure runtime')\n", encoding="utf-8")
        (target_dir / "README.md").write_text("# High Automation Project\nStrong CI/CD guardrails, zero legal docs.\n", encoding="utf-8")

        wf_dir = target_dir / ".github" / "workflows"
        wf_dir.mkdir(parents=True, exist_ok=True)

        (wf_dir / "tests.yml").write_text(
            "name: Tests\non: [push, pull_request]\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - run: pytest\n",
            encoding="utf-8",
        )
        (wf_dir / "codeql.yml").write_text(
            "name: CodeQL\non: [push]\njobs:\n  analyze:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: github/codeql-action/analyze@v3\n",
            encoding="utf-8",
        )
        (wf_dir / "release.yml").write_text(
            "name: Release SBOM\non: [push]\njobs:\n  release:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: anchore/sbom-action@v0\n        with:\n          format: cyclonedx-json\n",
            encoding="utf-8",
        )
        (target_dir / ".github" / "dependabot.yml").write_text(
            "version: 2\nupdates:\n  - package-ecosystem: pip\n    directory: '/'\n    schedule:\n      interval: daily\n",
            encoding="utf-8",
        )
        (target_dir / "Dockerfile").write_text(
            "FROM alpine:3.20\nUSER 10001\nENTRYPOINT ['/app']\n",
            encoding="utf-8",
        )
        return target_dir

    @staticmethod
    def create_policy_heavy(target_dir: Path) -> Path:
        target_dir.mkdir(parents=True, exist_ok=True)
        (target_dir / "README.md").write_text("# Policy Compliant App\nDocumentation and legal coverage, no CI.\n", encoding="utf-8")

        (target_dir / "SECURITY.md").write_text(
            "# Security Policy\n"
            "Contact: security@example.com\n"
            "Vulnerability reporting: reports acknowledged within 24 hours.\n"
            "Article 14 24h CSIRT notification protocol for actively exploited vulnerabilities.\n"
            "72h technical assessment.\n"
            "14-day remediation report.\n"
            "Free security updates provided for 5 years.\n",
            encoding="utf-8",
        )
        (target_dir / "CRA.md").write_text(
            "# CRA Compliance Declaration\n"
            "Classification: Default Product with Digital Elements.\n"
            "Conformity Route: Module A (Internal Control / Annex VIII).\n"
            "Declaration of Conformity signed.\n"
            "End-of-Life: declared 5 years of security updates.\n"
            "10 years retention policy for technical file.\n",
            encoding="utf-8",
        )
        docs_dir = target_dir / "docs"
        docs_dir.mkdir(parents=True, exist_ok=True)
        (docs_dir / "SDL.md").write_text("# Security Development Lifecycle\nDocumented secure design.\n", encoding="utf-8")
        (docs_dir / "threat-model.md").write_text("# Threat Model\nRisk assessment documented.\n", encoding="utf-8")
        return target_dir

    @staticmethod
    def create_full_compliance(target_dir: Path) -> Path:
        SyntheticRepoFactory.create_automation_heavy(target_dir)
        SyntheticRepoFactory.create_policy_heavy(target_dir)
        docs_dir = target_dir / "docs"
        docs_dir.mkdir(parents=True, exist_ok=True)
        (docs_dir / "sdl-audit.md").write_text("# SDL Audit\nAudited conformant.\n", encoding="utf-8")
        (docs_dir / "secure-by-design.md").write_text("# Secure by Design\nAttack surface minimized.\n", encoding="utf-8")
        (docs_dir / "dependencies.md").write_text("# Third-party Policy\nVetting and screening.\n", encoding="utf-8")
        (docs_dir / "encryption.md").write_text("# Encryption\nStorage and transit encrypted.\n", encoding="utf-8")
        (docs_dir / "credentials.md").write_text("# Credentials\nZero default passwords.\n", encoding="utf-8")
        (docs_dir / "architecture.md").write_text("# Architecture\nMinimal connections.\n", encoding="utf-8")
        (docs_dir / "privacy.md").write_text("# Data Minimisation\nNo excess data retained.\n", encoding="utf-8")
        (docs_dir / "authentication.md").write_text("# Authentication\nZero default passwords.\n", encoding="utf-8")
        (target_dir / ".env.example").write_text("API_SECRET=your-secure-secret-here\n", encoding="utf-8")
        (target_dir / "pyproject.toml").write_text("[project]\nname='full-app'\nversion='1.0.0'\n", encoding="utf-8")
        return target_dir

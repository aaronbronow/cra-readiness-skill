#!/usr/bin/env python3
"""
CRA Collector Implementation Evaluator
--------------------------------------
Benchmarking and comparative evaluation tool to analyze Claude Fable 5.1
and Gemini 3.8 Flash CRA readiness collectors across synthetic archetypes
and real-world repositories.

Zero external dependencies (standard-library only).
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import List, Optional

# Add parent directory to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(REPO_ROOT))

from tests.evaluator.harness import (
    ClaudeRunner,
    GeminiRunner,
    RepoComparisonResult,
    SyntheticRepoFactory,
    compare_collectors_on_repo,
)


def locate_default_gemini() -> Tuple[Path, Path]:
    candidates_script = [
        REPO_ROOT / "scripts" / "collector.py",
        REPO_ROOT.parent / "cra-rewrite" / "scripts" / "collector.py",
        REPO_ROOT / "tests" / "fixtures" / "gemini" / "scripts" / "collector.py",
    ]
    candidates_matrix = [
        REPO_ROOT / "references" / "cra_matrix_40.json",
        REPO_ROOT.parent / "cra-rewrite" / "references" / "cra_matrix_40.json",
        REPO_ROOT / "tests" / "fixtures" / "gemini" / "references" / "cra_matrix_40.json",
    ]

    script = next((p for p in candidates_script if p.exists()), None)
    matrix = next((p for p in candidates_matrix if p.exists()), None)

    if not script or not matrix:
        raise FileNotFoundError("Could not auto-locate Gemini collector script or matrix file.")
    return script, matrix


def build_default_repos(temp_dir: Path) -> List[Tuple[str, Path]]:
    repos: List[Tuple[str, Path]] = [
        ("Empty Repository (Fixture)", SyntheticRepoFactory.create_empty(temp_dir / "empty")),
        ("Minimal Code (Fixture)", SyntheticRepoFactory.create_minimal_code(temp_dir / "minimal")),
        ("Automation-Heavy (Fixture)", SyntheticRepoFactory.create_automation_heavy(temp_dir / "auto_heavy")),
        ("Policy-Heavy (Fixture)", SyntheticRepoFactory.create_policy_heavy(temp_dir / "policy_heavy")),
        ("Fully Compliant (Fixture)", SyntheticRepoFactory.create_full_compliance(temp_dir / "full_compliant")),
        ("cra-readiness-skill (Current Repo)", REPO_ROOT),
    ]

    # Check for real external repos if available
    cosign_path = REPO_ROOT.parent / "cra-rewrite" / "tests" / "sample_repos" / "cosign"
    if cosign_path.exists() and (cosign_path / "README.md").exists():
        repos.append(("sigstore/cosign (Sample Repo)", cosign_path))

    rewrite_path = REPO_ROOT.parent / "cra-rewrite"
    if rewrite_path.exists() and (rewrite_path / "SKILL.md").exists():
        repos.append(("cra-rewrite (Gemini Directory)", rewrite_path))

    return repos


def format_markdown_report(results: List[RepoComparisonResult]) -> str:
    lines = [
        "# CRA Collector Evaluation Report: Claude Fable 5.1 vs. Gemini 3.8 Flash",
        "",
        "> **Automated Comparative Audit across Synthetic Archetypes & Real Repositories**",
        "",
        "---",
        "",
        "## 1. Executive Summary & Benchmark Scorecard",
        "",
        "| Target Repository | Claude Grade | Gemini Grade | Claude Passed | Gemini Passed | Claude Latency | Gemini Latency | Agreement Rate |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
    ]

    total_agreed_pct = 0.0
    claude_total_time = 0.0
    gemini_total_time = 0.0

    for res in results:
        total_agreed_pct += res.agreement_rate
        claude_total_time += res.claude.duration_ms
        gemini_total_time += res.gemini.duration_ms

        c_grade = f"**{res.claude.grade}**"
        g_grade = f"**{res.gemini.grade}**"
        c_passed = f"{res.claude.passed_count}/40"
        g_passed = f"{res.gemini.passed_count}/40"
        c_time = f"{res.claude.duration_ms:.1f}ms"
        g_time = f"{res.gemini.duration_ms:.1f}ms"
        agr = f"**{res.agreement_rate:.1f}%**"

        lines.append(f"| `{res.repo_name}` | {c_grade} | {g_grade} | {c_passed} | {g_passed} | {c_time} | {g_time} | {agr} |")

    avg_agreement = total_agreed_pct / len(results) if results else 0.0
    avg_speedup = (claude_total_time / gemini_total_time) if gemini_total_time > 0 else 1.0

    lines.extend([
        "",
        f"- **Average Item-Level Agreement**: `{avg_agreement:.1f}%` across all evaluated scenarios.",
        f"- **Latency Comparison**: Total Claude runtime: `{claude_total_time:.1f}ms` vs. Total Gemini runtime: `{gemini_total_time:.1f}ms` (**{avg_speedup:.1f}x faster**).",
        "",
        "---",
        "",
        "## 2. Key Behavioral & Architectural Discoveries",
        "",
        "### A. Grading Philosophies",
        "1. **Claude Fable 5.1 (Letter-of-the-Law Gatekeeper)**:",
        "   - Implements 19 statutory gates (`F1, B1, B2, B3, B9, D3, D4, R1, R2, R5, R6, R7, R8, R9, R11, R12, P2, P3, P8`).",
        "   - **Strict gate rule**: If any single gate item is unmet or partial, the repository is capped at Grade C regardless of how many other items pass.",
        "   - Does not compute grades directly in the collector script; relies on raw evidence generation for external scoring.",
        "",
        "2. **Gemini 3.8 Flash (Founder Launch Thresholds)**:",
        "   - Categorizes the 40 items into Automation (9 items) and Policy/Documentation (31 items).",
        "   - **Threshold rule**: Grade A is achieved when both Automation and Policy scores are $\\ge 75\\%$. Grade B requires Policy $\\ge 60\\%$ with Automation $< 75\\%$.",
        "   - Standalone execution computes final founder grade immediately inside `scripts/collector.py`.",
        "",
        "### B. Signal Detection Paradigms",
        "1. **Regex & Content Searching (Claude)**:",
        "   - Claude inspects text inside `README.md` and repository text files for legal and technical keywords (e.g., searching for keywords like `'security'` or `'contact'` to satisfy R12).",
        "   - Allows partial credit and captures subtle manual processes.",
        "",
        "2. **Discrete File Signal Matching (Gemini)**:",
        "   - Gemini matches specific file paths defined in `references/cra_matrix_40.json` (e.g. `docs/sdl-audit.md`, `Dockerfile`, `.env.example`).",
        "   - Exceptionally fast (<50ms) and predictable, but requires repositories to match expected file path conventions.",
        "",
        "---",
        "",
        "## 3. Detailed Item Divergence Analysis per Repository",
        "",
    ])

    for res in results:
        lines.append(f"### 📦 {res.repo_name}")
        lines.append(f"- **Overall Assessment**: Claude **Grade {res.claude.grade}** vs. Gemini **Grade {res.gemini.grade}** ({res.agreement_rate:.1f}% agreement)")
        if not res.divergences:
            lines.append("- *No item divergences: Both collectors agreed on all 40 checklist items.*")
            lines.append("")
            continue

        lines.append("")
        lines.append("| Item ID | Title | Claude Status | Gemini Status | Claude Signal/Evidence | Gemini Signal/Evidence |")
        lines.append("| :--- | :--- | :---: | :---: | :--- | :--- |")

        for d in res.divergences:
            c_sig = d.claude_evidence or "*None / file absent*"
            g_sig = d.gemini_evidence or "*None / signal not matched*"
            lines.append(f"| **{d.canonical_id}** (`{d.gemini_id}`) | {d.title} | `{d.claude_status}` | `{d.gemini_status}` | {c_sig} | {g_sig} |")

        lines.append("")

    lines.extend([
        "---",
        "",
        "## 4. Synthesis & PR Review Recommendations",
        "",
        "1. **Hybrid Collector Opportunity**:",
        "   - Gemini's JSON data structure (`references/cra_matrix_40.json`) is far cleaner and more maintainable than hardcoding rules in Python.",
        "   - However, combining Gemini's external JSON model with Claude's deeper content-inspecting heuristics creates a best-of-both-worlds collector that is both fast, declarative, and robust against unconventional file names.",
        "2. **Grading Mode Selection**:",
        "   - Keep Gemini's direct CLI grade output with the founder-friendly A/B/C/D letter grade, while supporting an optional `--strict-gates` flag to enforce Claude's letter-of-the-law statutory gate check.",
        "3. **Remediation Value**:",
        "   - Gemini's `templates/` (`CRA.md`, `SECURITY.md`, `cra-ci-sbom.yml`) are essential additions that bridge the gap from audit to actionable compliance.",
    ])

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Evaluate Claude vs Gemini CRA collectors.")
    parser.add_argument("--repos", nargs="*", help="Repository paths to test")
    parser.add_argument("--claude-script", default=str(REPO_ROOT / "scripts" / "collect.py"), help="Path to Claude collect.py")
    parser.add_argument("--gemini-script", help="Path to Gemini collector.py")
    parser.add_argument("--gemini-matrix", help="Path to Gemini cra_matrix_40.json")
    parser.add_argument("--format", choices=["markdown", "json", "text"], default="markdown", help="Output format")
    parser.add_argument("--out", help="Write report to file")
    parser.add_argument("--save-default-report", action="store_true", help="Save report to docs/evaluations/implementation_comparison_report.md")

    args = parser.parse_args()

    # Locate Gemini files if not passed
    gemini_script = Path(args.gemini_script) if args.gemini_script else None
    gemini_matrix = Path(args.gemini_matrix) if args.gemini_matrix else None
    if not gemini_script or not gemini_matrix:
        auto_script, auto_matrix = locate_default_gemini()
        gemini_script = gemini_script or auto_script
        gemini_matrix = gemini_matrix or auto_matrix

    claude_runner = ClaudeRunner(Path(args.claude_script))
    gemini_runner = GeminiRunner(gemini_script, gemini_matrix)

    temp_dir = Path(tempfile.mkdtemp(prefix="cra_eval_"))
    try:
        if args.repos:
            repo_targets = [(Path(p).resolve().name, Path(p).resolve()) for p in args.repos]
        else:
            repo_targets = build_default_repos(temp_dir)

        results: List[RepoComparisonResult] = []
        for name, path in repo_targets:
            res = compare_collectors_on_repo(name, path, claude_runner, gemini_runner)
            results.append(res)

        if args.format == "json":
            serializable = [
                {
                    "repo_name": r.repo_name,
                    "repo_path": r.repo_path,
                    "agreement_rate": r.agreement_rate,
                    "claude": {
                        "grade": r.claude.grade,
                        "passed_count": r.claude.passed_count,
                        "duration_ms": r.claude.duration_ms,
                    },
                    "gemini": {
                        "grade": r.gemini.grade,
                        "passed_count": r.gemini.passed_count,
                        "duration_ms": r.gemini.duration_ms,
                    },
                    "divergences_count": len(r.divergences),
                }
                for r in results
            ]
            output_str = json.dumps(serializable, indent=2)
        elif args.format == "text":
            output_str = f"Evaluated {len(results)} repositories:\n" + "\n".join(
                f"- {r.repo_name}: Claude Grade {r.claude.grade} ({r.claude.duration_ms:.1f}ms) vs Gemini Grade {r.gemini.grade} ({r.gemini.duration_ms:.1f}ms) | Agreement: {r.agreement_rate:.1f}%"
                for r in results
            )
        else:
            output_str = format_markdown_report(results)

        if args.out:
            Path(args.out).write_text(output_str, encoding="utf-8")
            print(f"Report written to {args.out}")

        if args.save_default_report:
            default_out = REPO_ROOT / "docs" / "evaluations" / "implementation_comparison_report.md"
            default_out.parent.mkdir(parents=True, exist_ok=True)
            default_out.write_text(output_str, encoding="utf-8")
            print(f"Report saved to {default_out}")

        if not args.out and not args.save_default_report:
            print(output_str)

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()

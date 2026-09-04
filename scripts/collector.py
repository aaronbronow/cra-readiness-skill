#!/usr/bin/env python3
"""
EU Cyber Resilience Act (CRA) Readiness Collector & Engine
----------------------------------------------------------
Headless, deterministic, zero-dependency audit tool evaluating repositories
against the 40-item CRA Manufacturer Compliance Matrix (Regulation EU 2024/2847).

Supports 3 execution tiers:
- Tier 1: Deterministic file/workflow/API checks (PASS / FAIL)
- Tier 2: Inferrable checks requiring agent semantic review (NEEDS_EXPLANATION)
- Tier 3: Organizational governance requiring human attestation (NEEDS_USER_INPUT)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT_DEFAULT = Path.cwd()
MATRIX_FILE_DEFAULT = SCRIPT_DIR.parent / "references" / "cra_matrix_40.json"


def load_matrix(matrix_path: Path) -> Dict[str, Any]:
    candidates = [
        matrix_path,
        SCRIPT_DIR.parent / "references" / "cra_matrix_40.json",
        Path("references/cra_matrix_40.json"),
        SCRIPT_DIR.parent / "tests" / "fixtures" / "gemini" / "references" / "cra_matrix_40.json",
    ]
    for p in candidates:
        if p and p.exists():
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
    raise FileNotFoundError(f"Cannot locate CRA matrix file at any candidate path: {candidates}")


def check_file_signals(repo_path: Path, signals: List[str]) -> Tuple[bool, Optional[str]]:
    """Checks if any file or directory matching the signals exists and is non-empty."""
    for pattern in signals:
        target = repo_path / pattern
        if target.exists():
            if target.is_dir():
                return True, str(pattern)
            elif target.is_file() and target.stat().st_size > 5:
                return True, str(pattern)

        # Glob match if pattern contains wildcards
        if "*" in pattern or "/" in pattern:
            try:
                for match in repo_path.glob(pattern):
                    if match.is_dir():
                        return True, str(match.relative_to(repo_path))
                    elif match.is_file() and match.stat().st_size > 5:
                        return True, str(match.relative_to(repo_path))
            except Exception:
                continue
    return False, None


def query_github_api(repo_slug: str, token: str, endpoint: str) -> Optional[Dict[str, Any]]:
    """Graceful GitHub API query; returns None on any network or auth failure."""
    url = f"https://api.github.com/repos/{repo_slug}/{endpoint}"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "CRA-Readiness-Skill",
        "Authorization": f"Bearer {token}",
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                return json.loads(response.read().decode("utf-8"))
    except Exception:
        return None
    return None


def inspect_repository(
    repo_path: Path,
    matrix: Dict[str, Any],
    github_token: Optional[str] = None,
    repo_slug: Optional[str] = None,
) -> Dict[str, Any]:
    results: Dict[str, Any] = {
        "repo_path": str(repo_path.resolve()),
        "total_items": 40,
        "assessed_items": 0,
        "pass_count": 0,
        "fail_count": 0,
        "needs_explanation_count": 0,
        "needs_user_input_count": 0,
        "na_count": 0,
        "automation_met": 0,
        "automation_total": 0,
        "policy_met": 0,
        "policy_total": 0,
        "stage_breakdowns": {},
        "item_details": [],
        "grade": "D",
        "grade_description": "",
        "missing_automation": [],
        "missing_policy": [],
        "unassessed_reasons": [],
        "api_accessed": False,
    }

    if not repo_path.exists() or not repo_path.is_dir():
        results["grade"] = "D"
        results["grade_description"] = "Directory is inaccessible or does not exist."
        results["unassessed_reasons"].append(f"Directory {repo_path} is inaccessible.")
        return results

    try:
        entries = list(repo_path.iterdir())
        if not entries:
            results["grade"] = "D"
            results["grade_description"] = "Repository is empty; cannot assess compliance."
            results["unassessed_reasons"].append("Repository directory has no files.")
            return results
    except PermissionError:
        results["grade"] = "D"
        results["grade_description"] = "Permission denied when reading repository directory."
        results["unassessed_reasons"].append("Permission denied.")
        return results

    # Deep inspection candidate files
    security_md = repo_path / "SECURITY.md"
    security_content = security_md.read_text(encoding="utf-8", errors="ignore").lower() if security_md.exists() else ""

    cra_md = repo_path / "CRA.md"
    cra_content = cra_md.read_text(encoding="utf-8", errors="ignore").lower() if cra_md.exists() else ""

    readme_md = repo_path / "README.md"
    readme_content = readme_md.read_text(encoding="utf-8", errors="ignore").lower() if readme_md.exists() else ""

    workflows_dir = repo_path / ".github" / "workflows"
    has_workflows = workflows_dir.exists() and any(workflows_dir.iterdir())
    wf_texts = ""
    if has_workflows:
        wf_files = list(workflows_dir.glob("*.yml")) + list(workflows_dir.glob("*.yaml"))
        wf_texts = " ".join(f.read_text(encoding="utf-8", errors="ignore").lower() for f in wf_files)

    # Optional GitHub API integration
    api_branch_protection = None
    if github_token and repo_slug:
        api_data = query_github_api(repo_slug, github_token, "branches/main/protection")
        if api_data:
            results["api_accessed"] = True
            api_branch_protection = api_data

    all_items = []
    for stage in matrix.get("stages", []):
        stage_name = stage["name"]
        results["stage_breakdowns"][stage_name] = {
            "pass": 0,
            "fail": 0,
            "needs_explanation": 0,
            "needs_user_input": 0,
            "total": len(stage["items"]),
        }

        for item in stage["items"]:
            item_id = item["id"]
            tier = item.get("tier", "inferrable")
            cat = item.get("category", "policy_document")
            signals = item.get("signals", [])
            primary_doc = item.get("primary_doc", "README.md")
            found, matched_signal = check_file_signals(repo_path, signals)

            status = "FAIL"
            explanation_reason = None

            # --- TIER 1: DETERMINISTIC ITEMS ---
            if tier == "deterministic":
                if item_id in ("R.1", "R.2"):  # SBOM generation and machine-readable format
                    sbom_files = list(repo_path.glob("*sbom*")) + list(repo_path.glob("*cyclonedx*")) + list(repo_path.glob("*spdx*"))
                    if any(f.is_file() for f in sbom_files):
                        status, matched_signal = "PASS", "SBOM file in repository"
                    elif "sbom" in wf_texts or "cyclonedx" in wf_texts or "syft" in wf_texts or "spdx" in wf_texts:
                        status, matched_signal = "PASS", "CI workflow generates/attests SBOM"
                    else:
                        status = "FAIL"

                elif item_id in ("B.6", "A.2", "A.7"):  # Dependency scanning and auto-patching
                    dep_files = (repo_path / ".github" / "dependabot.yml").exists() or (repo_path / "renovate.json").exists()
                    if dep_files or "dependabot" in wf_texts or "trivy" in wf_texts or "snyk" in wf_texts:
                        status, matched_signal = "PASS", "Automated dependency review/scanner active"
                    else:
                        status = "FAIL"

                elif item_id == "B.8":  # Minimal attack surface
                    dockerfile = repo_path / "Dockerfile"
                    if dockerfile.exists():
                        d_txt = dockerfile.read_text(encoding="utf-8", errors="ignore").lower()
                        if "user " in d_txt and not "user root" in d_txt:
                            status, matched_signal = "PASS", "Dockerfile with unprivileged USER"
                        else:
                            status, matched_signal = "PASS", "Dockerfile container specification"
                    elif (repo_path / "docker-compose.yml").exists():
                        status, matched_signal = "PASS", "docker-compose service specification"
                    else:
                        status = "FAIL"

                elif item_id == "D.1":  # Cybersecurity test plan
                    if "test" in wf_texts or (repo_path / "tests").exists() or (repo_path / "test").exists():
                        status, matched_signal = "PASS", "Automated test suite / workflow"
                    else:
                        status = "FAIL"

                elif item_id == "D.3":  # Vulnerability & SAST screening
                    if "codeql" in wf_texts or "semgrep" in wf_texts or "trivy" in wf_texts or "snyk" in wf_texts or "gitleaks" in wf_texts:
                        status, matched_signal = "PASS", "SAST / vulnerability scanner in CI"
                    else:
                        status = "FAIL"

                elif item_id == "D.4":  # Secure update / release mechanism
                    if "release" in wf_texts or "goreleaser" in wf_texts or (repo_path / ".goreleaser.yml").exists():
                        status, matched_signal = "PASS", "Automated release pipeline in CI"
                    else:
                        status = "FAIL"

            # --- TIER 3: ATTESTATION / FOUNDER INTERVIEW ---
            elif tier == "attestation":
                if item_id == "F.4":  # EU Representative
                    if "representative" in cra_content or "eu authorised" in cra_content or "established in the eu" in cra_content:
                        status, matched_signal = "PASS", "CRA.md (Authorised Representative declared)"
                    else:
                        status = "NEEDS_USER_INPUT"
                        explanation_reason = item.get("interview_prompt")
                elif item_id == "D.2":  # Evidence of SDL compliance in PRs
                    if api_branch_protection:
                        status, matched_signal = "PASS", "GitHub API: Branch protection verified"
                    elif (repo_path / ".github" / "PULL_REQUEST_TEMPLATE.md").exists() or (repo_path / ".github" / "pull_request_template.md").exists():
                        status, matched_signal = "PASS", "PR review checklist template"
                    else:
                        status = "NEEDS_USER_INPUT"
                        explanation_reason = item.get("interview_prompt")
                else:
                    if found:
                        status = "PASS"
                    else:
                        status = "NEEDS_USER_INPUT"
                        explanation_reason = item.get("interview_prompt")

            # --- TIER 2: INFERRABLE ITEMS ---
            else:
                if item_id == "R.12":  # Vulnerability disclosure contact
                    if security_md.exists() and ("security@" in security_content or "contact" in security_content or "mailto:" in security_content):
                        status, matched_signal = "PASS", "SECURITY.md (contact verified)"
                    elif security_md.exists():
                        status = "NEEDS_EXPLANATION"
                        explanation_reason = "SECURITY.md exists but contact email or PVR channel requires semantic verification."
                    else:
                        status = "FAIL"

                elif item_id in ("A.3", "A.4", "A.5", "A.6"):  # Article 14 reporting SLAs
                    if ("24" in security_content and "csirt" in security_content) or ("article 14" in cra_content):
                        status, matched_signal = "PASS", "SECURITY.md / CRA.md (Art. 14 protocol)"
                    elif security_md.exists() or cra_md.exists():
                        status = "NEEDS_EXPLANATION"
                        explanation_reason = "Security/CRA policy present; requires semantic check for 24h/72h reporting commitments."
                    else:
                        status = "FAIL"

                elif item_id in ("B.1", "B.2", "R.6", "R.7"):  # Classification & DoC
                    if "module a" in cra_content or "declaration of conformity" in cra_content:
                        status, matched_signal = "PASS", "CRA.md (Module A / DoC record)"
                    elif cra_md.exists():
                        status = "NEEDS_EXPLANATION"
                        explanation_reason = "CRA.md present; requires semantic check for Module A Declaration of Conformity."
                    else:
                        status = "FAIL"

                elif item_id in ("R.5", "A.8", "A.9"):  # EOL support & free updates
                    if "end-of-life" in cra_content or "5 years" in cra_content or "free of charge" in security_content:
                        status, matched_signal = "PASS", "CRA.md / SECURITY.md (EOL & free updates declared)"
                    elif cra_md.exists() or security_md.exists():
                        status = "NEEDS_EXPLANATION"
                        explanation_reason = "Support policy present; requires semantic verification of 5-year free update guarantee."
                    else:
                        status = "FAIL"

                elif item_id in ("R.3", "R.4"):  # Inbound/Outbound connections
                    if "inbound" in readme_content or "port" in readme_content or "endpoint" in readme_content:
                        status, matched_signal = "PASS", "README.md (connection/port descriptions)"
                    elif readme_md.exists():
                        status = "NEEDS_EXPLANATION"
                        explanation_reason = "README present; inspect for documented ports or network endpoints."
                    else:
                        status = "FAIL"

                else:
                    if found:
                        status = "PASS"
                    else:
                        status = "FAIL"

            # Count totals
            if status == "PASS":
                results["pass_count"] += 1
                results["stage_breakdowns"][stage_name]["pass"] += 1
                if cat == "automation":
                    results["automation_met"] += 1
                else:
                    results["policy_met"] += 1
            elif status == "NEEDS_EXPLANATION":
                results["needs_explanation_count"] += 1
                results["stage_breakdowns"][stage_name]["needs_explanation"] += 1
            elif status == "NEEDS_USER_INPUT":
                results["needs_user_input_count"] += 1
                results["stage_breakdowns"][stage_name]["needs_user_input"] += 1
            else:
                results["fail_count"] += 1
                results["stage_breakdowns"][stage_name]["fail"] += 1
                if cat == "automation":
                    results["missing_automation"].append(f"{item_id}: {item['title']}")
                else:
                    results["missing_policy"].append(f"{item_id}: {item['title']}")

            if cat == "automation":
                results["automation_total"] += 1
            else:
                results["policy_total"] += 1

            all_items.append({
                "id": item_id,
                "title": item["title"],
                "article": item.get("article", ""),
                "tier": tier,
                "category": cat,
                "stage": stage_name,
                "status": status,
                "primary_doc": primary_doc,
                "matched_signal": matched_signal,
                "explanation_reason": explanation_reason,
            })

    results["assessed_items"] = len(all_items)
    results["item_details"] = all_items

    # Compute Founder Grade
    auto_ratio = results["automation_met"] / max(results["automation_total"], 1)
    # Give partial provisional weight to items awaiting explanation
    effective_policy = results["policy_met"] + (results["needs_explanation_count"] * 0.5)
    policy_ratio = effective_policy / max(results["policy_total"], 1)

    if auto_ratio >= 0.75 and policy_ratio >= 0.75:
        results["grade"] = "A"
        results["grade_description"] = "Ready for EU launch: Core automated CI/CD guardrails and manufacturer documentation are verified."
    elif policy_ratio >= 0.55 and auto_ratio < 0.75:
        results["grade"] = "B"
        results["grade_description"] = "Need automation work: Policies exist, but automated CI/CD guardrails (SBOM generation, CVE screening) are missing."
    elif auto_ratio < 0.75 and policy_ratio < 0.55:
        results["grade"] = "C"
        results["grade_description"] = "Need automation and policy work: Missing technical CI/CD automation and essential CRA declarations."
    else:
        results["grade"] = "C"
        results["grade_description"] = "Need automation work and policy/document work to reach launch readiness."

    return results


def format_markdown_report(results: Dict[str, Any]) -> str:
    grade = results["grade"]
    badge = {
        "A": "🟢 **Grade A (Ready for EU Launch)**",
        "B": "🟡 **Grade B (Need Automation Work)**",
        "C": "🟠 **Grade C (Need Automation & Policy Work)**",
        "D": "🔴 **Grade D (Incomplete / Needs Work)**",
    }.get(grade, f"**Grade {grade}**")

    lines = [
        "# CRA Manufacturer Readiness Scorecard",
        "",
        f"**Target Repository**: `{results['repo_path']}`  ",
        f"**Overall Result**: {badge}  ",
        f"**Assessment**: {results['grade_description']}",
        "",
        "---",
        "",
        "## 1. 3-Tier Scan Overview",
        "",
        "| Category | Progress | Status |",
        "| :--- | :---: | :--- |",
        f"| **Technical Automation** (CI/CD, SBOM, Scans) | `{results['automation_met']}/{results['automation_total']}` ({results['automation_met']/max(results['automation_total'],1)*100:.0f}%) | {'✅ Met' if results['automation_met'] >= 7 else '⚠️ Needs Setup'} |",
        f"| **Policies & Governance** | `{results['policy_met']}/{results['policy_total']}` ({results['policy_met']/max(results['policy_total'],1)*100:.0f}%) | {'✅ Met' if results['policy_met'] >= 20 else '⚠️ Needs Setup'} |",
        f"| **Items Requiring Agent Review (`NEEDS_EXPLANATION`)** | `{results['needs_explanation_count']}` items | 🤖 AI Agent Semantic Inspection |",
        f"| **Items Requiring Founder Input (`NEEDS_USER_INPUT`)** | `{results['needs_user_input_count']}` items | 👤 Founder Attestation Needed |",
        f"| **Total 40-Item Matrix Coverage** | `{results['pass_count']}/40` verified | Evaluated against EU Regulation 2024/2847 |",
        "",
        "---",
        "",
        "## 2. Lifecycle Stage Breakdown",
        "",
        "| Lifecycle Stage | Verified / Total | Awaiting Review | Awaiting Founder Input | Status |",
        "| :--- | :---: | :---: | :---: | :--- |",
    ]

    for stage_name, counts in results["stage_breakdowns"].items():
        p = counts["pass"]
        tot = counts["total"]
        pct = (p / max(tot, 1)) * 100
        status_str = "🟢 Satisfactory" if pct >= 75 else ("🟡 Partial" if pct >= 40 else "🔴 Deficient")
        lines.append(f"| **{stage_name}** | `{p}/{tot}` ({pct:.0f}%) | `{counts['needs_explanation']}` | `{counts['needs_user_input']}` | {status_str} |")

    lines.extend([
        "",
        "---",
        "",
        "## 3. Action Items & Remediation",
        "",
    ])

    if results["missing_automation"]:
        lines.append("### ⚙️ Automation Deficits (Action required for Grade B/A):")
        for item in results["missing_automation"][:5]:
            lines.append(f"- [ ] **{item}**")
        lines.append("> *Quick Fix: Copy `templates/github-actions/cra-ci-sbom.yml` to `.github/workflows/cra-ci.yml`.*")
        lines.append("")

    if results["needs_explanation_count"] > 0:
        lines.append("### 🤖 Candidate Documents Awaiting Semantic Review (`NEEDS_EXPLANATION`):")
        for item in results["item_details"]:
            if item["status"] == "NEEDS_EXPLANATION":
                lines.append(f"- **{item['id']}**: {item['title']} (`{item['primary_doc']}`) — *{item.get('explanation_reason')}*")
        lines.append("")

    if results["needs_user_input_count"] > 0:
        lines.append("### 👤 Founder Attestations Needed (`NEEDS_USER_INPUT`):")
        for item in results["item_details"]:
            if item["status"] == "NEEDS_USER_INPUT":
                lines.append(f"- **{item['id']}**: {item['title']} — *\"{item.get('explanation_reason')}\"*")
        lines.append("")

    lines.append("---")
    lines.append("*Generated by CRA Readiness Skill (3-Tier Headless Engine).*")
    return "\n".join(lines)


def write_github_action_summary(results: Dict[str, Any], markdown_content: str):
    """Writes report to GITHUB_STEP_SUMMARY and sets GITHUB_OUTPUT."""
    step_summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if step_summary_path:
        try:
            with open(step_summary_path, "a", encoding="utf-8") as f:
                f.write("\n" + markdown_content + "\n")
        except Exception as e:
            print(f"::warning::Failed to write to GITHUB_STEP_SUMMARY: {e}", file=sys.stderr)

    github_output_path = os.environ.get("GITHUB_OUTPUT")
    if github_output_path:
        try:
            with open(github_output_path, "a", encoding="utf-8") as f:
                f.write(f"grade={results['grade']}\n")
                f.write(f"passed_items={results['pass_count']}\n")
                f.write(f"automation_met={results['automation_met']}\n")
                f.write(f"policy_met={results['policy_met']}\n")
        except Exception as e:
            print(f"::warning::Failed to write to GITHUB_OUTPUT: {e}", file=sys.stderr)

    # Workflow command annotations
    print(f"::notice title=CRA Readiness Grade::{results['grade']} - {results['grade_description']}")
    if results["missing_automation"]:
        print(f"::warning title=Missing CRA Automation::{len(results['missing_automation'])} CI checks missing")


def main():
    parser = argparse.ArgumentParser(description="Deterministic 3-Tier CRA Readiness Audit Engine.")
    parser.add_argument("repo_path", nargs="?", default=".", help="Target repository directory path")
    parser.add_argument("--format", choices=["json", "markdown", "summary", "text"], default="markdown", help="Output format")
    parser.add_argument("--matrix", default=str(MATRIX_FILE_DEFAULT), help="Path to CRA matrix JSON")
    parser.add_argument("--token", default=os.environ.get("GITHUB_TOKEN"), help="GitHub token for optional API checks")
    parser.add_argument("--repo-slug", default=os.environ.get("GITHUB_REPOSITORY"), help="GitHub owner/repo slug")
    parser.add_argument("--github-action", action="store_true", help="Format and export outputs for GitHub Actions CI")
    parser.add_argument("--output", help="Path to write output file")
    parser.add_argument("--fail-on", help="Fail with non-zero code if grade matches or falls below (e.g. D or C)")

    args = parser.parse_args()
    target_path = Path(args.repo_path).resolve()
    matrix_path = Path(args.matrix).resolve()

    try:
        matrix = load_matrix(matrix_path)
    except Exception as e:
        err_data = {"error": str(e), "grade": "D"}
        if args.format == "json":
            print(json.dumps(err_data, indent=2))
        else:
            print(f"Error loading matrix: {e}", file=sys.stderr)
        sys.exit(1)

    results = inspect_repository(target_path, matrix, github_token=args.token, repo_slug=args.repo_slug)

    markdown_report = format_markdown_report(results)

    if args.github_action:
        write_github_action_summary(results, markdown_report)

    if args.format == "json":
        output_str = json.dumps(results, indent=2)
    elif args.format == "text":
        output_str = f"CRA Grade: {results['grade']} ({results['pass_count']}/40 passed)\n" \
                     f"Automation: {results['automation_met']}/{results['automation_total']} | " \
                     f"Needs Explanation: {results['needs_explanation_count']} | " \
                     f"Needs User Input: {results['needs_user_input_count']}"
    elif args.format == "summary":
        output_str = f"Grade {results['grade']}: {results['grade_description']}"
    else:
        output_str = markdown_report

    if args.output:
        Path(args.output).write_text(output_str, encoding="utf-8")

    print(output_str)

    if args.fail_on:
        grade_order = {"D": 1, "C": 2, "B": 3, "A": 4}
        current_val = grade_order.get(results["grade"], 0)
        fail_val = grade_order.get(args.fail_on.upper(), 0)
        if current_val <= fail_val:
            print(f"::error::Audit failed: Grade {results['grade']} is at or below threshold {args.fail_on.upper()}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()

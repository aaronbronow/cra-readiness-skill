#!/usr/bin/env python3
"""
CRA Readiness Collector Script
------------------------------
Lightweight, zero-external-dependency collector for inspecting a repository
against the 40-item Cyber Resilience Act (CRA) Manufacturer Compliance Matrix.

Outputs structured JSON or Markdown scorecard with founder-grade ratings:
- A: Ready for EU launch
- B: Need automation work
- C: Need automation work and policy/document work
- D: Incomplete assessment / insufficient info & needs B + C
"""

import os
import sys
import json
import argparse
from pathlib import Path

# Load matrix definitions
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT_DEFAULT = Path.cwd()
MATRIX_FILE = SCRIPT_DIR.parent / "references" / "cra_matrix_40.json"


def load_matrix(matrix_path: Path):
    if not matrix_path.exists():
        # Fallback to relative or current directory
        alt_path = Path("references/cra_matrix_40.json")
        if alt_path.exists():
            matrix_path = alt_path
        else:
            raise FileNotFoundError(f"Cannot locate CRA matrix file at {matrix_path}")
    with open(matrix_path, "r", encoding="utf-8") as f:
        return json.load(f)


def check_file_signals(repo_path: Path, signals: list) -> tuple:
    """Checks if any file matching the signal patterns exists and is non-empty."""
    for pattern in signals:
        target = repo_path / pattern
        if target.exists() and (target.is_file() or target.is_dir()):
            if target.is_dir():
                return True, str(pattern)
            elif target.stat().st_size > 10:
                return True, str(pattern)
        # Check glob if pattern contains wildcards or directories
        if "*" in pattern or "/" in pattern:
            matches = list(repo_path.glob(pattern))
            for m in matches:
                if m.is_dir():
                    return True, str(m.relative_to(repo_path))
                elif m.is_file() and m.stat().st_size > 10:
                    return True, str(m.relative_to(repo_path))
    return False, None


def inspect_repository(repo_path: Path, matrix: dict) -> dict:
    results = {
        "repo_path": str(repo_path),
        "total_items": 40,
        "assessed_items": 0,
        "automation_met": 0,
        "automation_total": 0,
        "policy_met": 0,
        "policy_total": 0,
        "unassessed_count": 0,
        "stage_breakdowns": {},
        "item_details": [],
        "grade": "D",
        "grade_description": "",
        "missing_automation": [],
        "missing_policy": [],
        "unassessed_reasons": []
    }

    if not repo_path.exists() or not repo_path.is_dir():
        results["grade"] = "D"
        results["grade_description"] = "Need automation work (B), policy/document work (C), and repository path could not be accessed or does not exist."
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

    # Specific deep file content checks
    security_md = repo_path / "SECURITY.md"
    security_content = security_md.read_text(encoding="utf-8", errors="ignore").lower() if security_md.exists() else ""

    cra_md = repo_path / "CRA.md"
    cra_content = cra_md.read_text(encoding="utf-8", errors="ignore").lower() if cra_md.exists() else ""

    workflows_dir = repo_path / ".github" / "workflows"
    has_workflows = workflows_dir.exists() and any(workflows_dir.iterdir())

    all_items = []
    for stage in matrix.get("stages", []):
        stage_name = stage["name"]
        results["stage_breakdowns"][stage_name] = {"met": 0, "total": len(stage["items"])}

        for item in stage["items"]:
            item_id = item["id"]
            cat = item["category"]
            signals = item.get("signals", [])
            found, matched_signal = check_file_signals(repo_path, signals)

            # Heuristics for specific matrix obligations
            if item_id == "R.12":  # Vulnerability disclosure contact
                if security_md.exists() and ("security@" in security_content or "contact" in security_content):
                    found, matched_signal = True, "SECURITY.md (contact verified)"
                else:
                    found, matched_signal = False, None

            elif item_id in ["A.3", "A.4", "A.5", "A.6"]:  # Article 14 reporting timeline
                if "24" in security_content or "csirt" in security_content or "enisa" in security_content:
                    found, matched_signal = True, "SECURITY.md (Art. 14 notification clause)"
                elif "article 14" in cra_content or "24 hours" in cra_content:
                    found, matched_signal = True, "CRA.md (Art. 14 notification clause)"

            elif item_id in ["B.1", "B.2", "R.6", "R.7"]:  # Classification & Conformity Route
                if "module a" in cra_content or "declaration of conformity" in cra_content or "default" in cra_content:
                    found, matched_signal = True, "CRA.md (Module A / DoC record)"

            elif item_id in ["R.5", "A.8", "A.9"]:  # EOL declaration & support
                if "end-of-life" in cra_content or "support" in security_content or "5 years" in cra_content:
                    found, matched_signal = True, "CRA.md / SECURITY.md (EOL support declaration)"

            elif item_id in ["R.1", "R.2"]:  # SBOM checks
                sbom_files = list(repo_path.glob("*sbom*")) + list(repo_path.glob("*cyclonedx*")) + list(repo_path.glob("*spdx*"))
                if any(f.is_file() for f in sbom_files):
                    found, matched_signal = True, "SBOM artifact located"
                elif has_workflows:
                    wf_files = list(workflows_dir.glob("*.yml")) + list(workflows_dir.glob("*.yaml"))
                    wf_texts = " ".join(f.read_text(encoding="utf-8", errors="ignore").lower() for f in wf_files)
                    if "sbom" in wf_texts or "cyclonedx" in wf_texts or "syft" in wf_texts or "spdx" in wf_texts or "attest" in wf_texts:
                        found, matched_signal = True, "CI workflow generates/attests SBOM"

            elif item_id in ["B.6", "A.2", "A.7"]:  # Dependency scanning & auto-patching
                dep_config = (repo_path / ".github" / "dependabot.yml").exists() or (repo_path / "renovate.json").exists()
                if dep_config:
                    found, matched_signal = True, "Dependabot/Renovate configuration"

            # Tally counts
            if cat == "automation":
                results["automation_total"] += 1
                if found:
                    results["automation_met"] += 1
                else:
                    results["missing_automation"].append(f"{item_id}: {item['title']}")
            else:
                results["policy_total"] += 1
                if found:
                    results["policy_met"] += 1
                else:
                    results["missing_policy"].append(f"{item_id}: {item['title']}")

            if found:
                results["stage_breakdowns"][stage_name]["met"] += 1

            all_items.append({
                "id": item_id,
                "title": item["title"],
                "article": item["article"],
                "category": cat,
                "stage": stage_name,
                "status": "PASS" if found else "FAIL",
                "matched_signal": matched_signal
            })

    results["assessed_items"] = len(all_items)
    results["item_details"] = all_items

    # Compute Founder Grade (A, B, C, D)
    auto_ratio = results["automation_met"] / max(results["automation_total"], 1)
    policy_ratio = results["policy_met"] / max(results["policy_total"], 1)

    if auto_ratio >= 0.75 and policy_ratio >= 0.75:
        results["grade"] = "A"
        results["grade_description"] = "Ready for EU launch: Both automated security pipelines and manufacturer governance/policies are established."
    elif policy_ratio >= 0.60 and auto_ratio < 0.75:
        results["grade"] = "B"
        results["grade_description"] = "Need automation work: Policies and legal documentation exist, but automated CI/CD guardrails (SBOM generation, automated CVE screening) are missing."
    elif auto_ratio < 0.75 and policy_ratio < 0.60:
        results["grade"] = "C"
        results["grade_description"] = "Need automation work and policy/document work: Missing both technical CI/CD automation and essential CRA compliance declarations."
    else:
        results["grade"] = "C"
        results["grade_description"] = "Need automation work and policy/document work to reach launch readiness."

    return results


def format_markdown_report(results: dict) -> str:
    g = results["grade"]
    desc = results["grade_description"]
    a_met, a_tot = results["automation_met"], results["automation_total"]
    p_met, p_tot = results["policy_met"], results["policy_total"]

    badge = {"A": "🟢 Grade A (Ready for EU Launch)",
             "B": "🟡 Grade B (Need Automation Work)",
             "C": "🟠 Grade C (Need Automation & Policy Work)",
             "D": "🔴 Grade D (Incomplete / Needs B & C)"}.get(g, g)

    lines = [
        f"# CRA Manufacturer Readiness Scorecard",
        f"",
        f"**Repository**: `{results['repo_path']}`  ",
        f"**Overall Result**: **{badge}**  ",
        f"**Founder Assessment**: {desc}",
        f"",
        f"---",
        f"",
        f"## 1. Compliance Metric Overview",
        f"",
        f"| Category | Progress | Status |",
        f"| :--- | :---: | :--- |",
        f"| **Technical Automation** (CI/CD, SBOM, Scans) | `{a_met}/{a_tot}` ({int(a_met/max(a_tot,1)*100)}%) | {'✅ Met' if a_met >= a_tot*0.75 else '⚠️ Requires Setup'} |",
        f"| **Policies & Technical Documentation** | `{p_met}/{p_tot}` ({int(p_met/max(p_tot,1)*100)}%) | {'✅ Met' if p_met >= p_tot*0.60 else '⚠️ Requires Setup'} |",
        f"| **40-Item Matrix Coverage** | `{a_met + p_met}/40` ({int((a_met+p_met)/40*100)}%) | Evaluated against EU Regulation 2024/2847 |",
        f"",
        f"---",
        f"",
        f"## 2. Lifecycle Stage Breakdown",
        f"",
        f"| Stage | Met / Total | Status |",
        f"| :--- | :---: | :--- |"
    ]

    for stage, counts in results["stage_breakdowns"].items():
        pct = int(counts["met"] / max(counts["total"], 1) * 100)
        st = "🟢 Satisfactory" if pct >= 70 else ("🟡 Partial" if pct >= 40 else "🔴 Deficient")
        lines.append(f"| **{stage}** | `{counts['met']}/{counts['total']}` ({pct}%) | {st} |")

    lines.extend([
        f"",
        f"---",
        f"",
        f"## 3. High-Priority Founder Action Items",
        f""
    ])

    if results["missing_automation"]:
        lines.append(f"### ⚙️ Automation Deficits (Action required for Grade B/A):")
        for item in results["missing_automation"][:5]:
            lines.append(f"- [ ] **{item}**")
        lines.append(f"> *Quick Fix: Copy `templates/github-actions/cra-ci-sbom.yml` to `.github/workflows/cra-ci.yml`.*")
        lines.append("")

    if results["missing_policy"]:
        lines.append(f"### 📜 Policy & Documentation Deficits (Action required for Grade C):")
        for item in results["missing_policy"][:5]:
            lines.append(f"- [ ] **{item}**")
        lines.append(f"> *Quick Fix: Copy `templates/SECURITY.md` and `templates/CRA.md` into your repo root.*")
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Audit a repository against the 40-item CRA Manufacturer Matrix.")
    parser.add_argument("repo_path", nargs="?", default=".", help="Target repository directory path")
    parser.add_argument("--format", choices=["json", "markdown", "text"], default="markdown", help="Output format")
    parser.add_argument("--matrix", default=str(MATRIX_FILE), help="Path to CRA matrix JSON")

    args = parser.parse_args()
    target_path = Path(args.repo_path).resolve()
    matrix_path = Path(args.matrix).resolve()

    try:
        matrix = load_matrix(matrix_path)
    except Exception as e:
        print(json.dumps({"error": str(e), "grade": "D"}) if args.format == "json" else f"Error loading matrix: {e}", file=sys.stderr)
        sys.exit(1)

    results = inspect_repository(target_path, matrix)

    if args.format == "json":
        print(json.dumps(results, indent=2))
    elif args.format == "text":
        print(f"CRA Grade: {results['grade']} - {results['grade_description']}")
        print(f"Automation: {results['automation_met']}/{results['automation_total']}")
        print(f"Policies: {results['policy_met']}/{results['policy_total']}")
    else:
        print(format_markdown_report(results))


if __name__ == "__main__":
    main()

#!/usr/bin/env bash
# ==============================================================================
# install_skill.sh - Multi-Agent Skill Adapter & Installer
#
# Sets up symbolic links / pointers so cra-readiness-skill can be discovered
# and invoked natively across supported agent environments:
#   1. Claude Code CLI (~/.claude/skills/ or .claude/skills/)
#   2. Antigravity / Gemini CLI (~/.gemini/antigravity-cli/skills/ or local)
#   3. Cursor IDE (.cursor/rules/)
#   4. GitHub Copilot (.github/copilot-instructions.md)
# ==============================================================================

set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_DIR="${1:-$PWD}"

echo "🔧 Installing cra-readiness-skill adapters..."
echo "   Source Skill Directory: ${SKILL_DIR}"
echo "   Target Project Directory: ${TARGET_DIR}"
echo ""

# ------------------------------------------------------------------------------
# 1. Claude Code CLI Adapter
# ------------------------------------------------------------------------------
CLAUDE_SKILLS_DIR="${TARGET_DIR}/.claude/skills"
mkdir -p "${CLAUDE_SKILLS_DIR}"
ln -sfn "${SKILL_DIR}" "${CLAUDE_SKILLS_DIR}/cra-readiness"
echo "✅ Claude Code: Linked to ${CLAUDE_SKILLS_DIR}/cra-readiness"

# ------------------------------------------------------------------------------
# 2. Cursor IDE Rule Adapter
# ------------------------------------------------------------------------------
CURSOR_RULES_DIR="${TARGET_DIR}/.cursor/rules"
mkdir -p "${CURSOR_RULES_DIR}"
cat << 'EOF' > "${CURSOR_RULES_DIR}/cra-readiness.mdc"
---
description: Evaluates software repositories against EU Cyber Resilience Act (Regulation EU 2024/2847)
globs: *
alwaysApply: false
---

When the user asks to evaluate CRA compliance, audit EU readiness, or remediate CRA gaps:
1. Refer to the canonical skill instructions at [SKILL.md](../../SKILL.md) (or the installed cra-readiness-skill directory).
2. Execute Tier 1 deterministic evaluation: `python3 scripts/collector.py . --format json`.
3. Check `SECURITY.md` and `CRA.md` for Tier 2 semantic validation.
4. Follow drop-in template standards in `templates/` for any remediation tasks.
EOF
echo "✅ Cursor IDE: Generated rule at ${CURSOR_RULES_DIR}/cra-readiness.mdc"

# ------------------------------------------------------------------------------
# 3. GitHub Copilot Instructions Adapter
# ------------------------------------------------------------------------------
GITHUB_DIR="${TARGET_DIR}/.github"
mkdir -p "${GITHUB_DIR}"
COPILOT_INSTRUCTIONS="${GITHUB_DIR}/copilot-instructions.md"
if [ ! -f "${COPILOT_INSTRUCTIONS}" ]; then
  cat << 'EOF' > "${COPILOT_INSTRUCTIONS}"
# GitHub Copilot Custom Instructions

## EU Cyber Resilience Act (CRA) Auditing
When asked to evaluate EU CRA compliance:
- Follow the 3-Tier Scan Control Architecture specified in `cra-readiness-skill/SKILL.md`.
- Deterministic scans: `python3 scripts/collector.py . --format json`.
- Drop-in templates: consult `templates/CRA.md` and `templates/SECURITY.md`.
EOF
  echo "✅ GitHub Copilot: Created ${COPILOT_INSTRUCTIONS}"
else
  echo "ℹ️  GitHub Copilot: ${COPILOT_INSTRUCTIONS} already exists (skipping overwrite)"
fi

# ------------------------------------------------------------------------------
# 4. Antigravity / Gemini CLI (Global User Skill Directory)
# ------------------------------------------------------------------------------
GEMINI_SKILLS_DIR="${HOME}/.gemini/skills"
if [ -d "${HOME}/.gemini" ]; then
  mkdir -p "${GEMINI_SKILLS_DIR}"
  ln -sfn "${SKILL_DIR}" "${GEMINI_SKILLS_DIR}/cra-readiness"
  echo "✅ Antigravity/Gemini CLI: Linked to ${GEMINI_SKILLS_DIR}/cra-readiness"
fi

echo ""
echo "🎉 All agent adapters successfully configured for ${TARGET_DIR}!"

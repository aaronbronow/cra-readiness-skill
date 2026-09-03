#!/usr/bin/env python3
"""
CRA Readiness evidence collector.

Gathers repository evidence for the 40-item CRA readiness checklist and emits JSON
that an agent (or a human) can turn into A/B/C/D grade using references/scoring.md.

Design constraints
- Python 3.8+, standard library only. No pip installs.
- Talks only to api.github.com and github.com (clone). Nothing is uploaded anywhere.
- Every network or permission failure is recorded, never hidden, so the report can say
  exactly why an item is "could not check".
- Optional. The skill works without this script; it just produces more UNKNOWNs.

Usage
  python3 collect.py --repo OWNER/NAME                 # API + shallow clone into a temp dir
  python3 collect.py --path /path/to/checkout          # local files only, no network
  python3 collect.py --repo OWNER/NAME --path .        # API settings + local files
  python3 collect.py --path . --summary                # also print a human-readable summary
  python3 collect.py --repo OWNER/NAME --out evidence.json

Token: --token, else $GITHUB_TOKEN, else $GH_TOKEN, else `gh auth token` if gh is installed.
Without a token, public repos work but admin-only settings show permission errors.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from datetime import datetime, timezone

CHECKLIST_VERSION = "2026.09.1"
API = "https://api.github.com"
MAX_TEXT_BYTES = 512 * 1024
MAX_DOC_FILES = 600
# Directories that hold reports *about* compliance rather than the product's own documents.
# Assessment reports written by this skill go here by convention (see SKILL.md Step 7).
DEFAULT_EXCLUDES = ("docs/compliance/reports",)
SKIP_DIRS = {
    ".git", "node_modules", "vendor", "dist", "build", "out", ".venv", "venv", "env",
    "__pycache__", ".tox", ".mypy_cache", "target", ".next", ".nuxt", "coverage",
    ".terraform", "Pods", ".gradle", ".idea", ".vscode",
}

# ----------------------------------------------------------------------------- helpers


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def read_text(path, limit=MAX_TEXT_BYTES):
    try:
        with open(path, "rb") as fh:
            data = fh.read(limit)
        return data.decode("utf-8", errors="replace")
    except OSError:
        return ""


def run(cmd, cwd=None, timeout=120, env=None):
    try:
        proc = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout, env=env
        )
        return proc.returncode, proc.stdout, proc.stderr
    except (OSError, subprocess.TimeoutExpired) as exc:
        return -1, "", str(exc)


def rel(root, path):
    return os.path.relpath(path, root).replace(os.sep, "/")


def any_match(patterns, text, flags=re.I):
    return [p for p in patterns if re.search(p, text, flags)]


# ----------------------------------------------------------------------------- GitHub API


class GitHub:
    def __init__(self, token):
        self.token = token
        self.calls = {}

    def get(self, path, key=None, accept="application/vnd.github+json"):
        key = key or path
        url = API + path
        req = urllib.request.Request(url)
        req.add_header("Accept", accept)
        req.add_header("X-GitHub-Api-Version", "2022-11-28")
        req.add_header("User-Agent", "cra-readiness-collector")
        if self.token:
            req.add_header("Authorization", "Bearer " + self.token)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read()
                body = json.loads(raw) if raw else None
                self.calls[key] = {"status": "ok", "http": resp.status}
                return "ok", body
        except urllib.error.HTTPError as exc:
            status = "error"
            if exc.code == 401:
                status = "bad_token"
            elif exc.code == 403:
                remaining = exc.headers.get("X-RateLimit-Remaining")
                status = "rate_limited" if remaining == "0" else "permission_denied"
            elif exc.code == 404:
                status = "not_found"
            self.calls[key] = {"status": status, "http": exc.code}
            return status, None
        except (urllib.error.URLError, OSError, ValueError) as exc:
            self.calls[key] = {"status": "network_error", "detail": str(exc)}
            return "network_error", None


def resolve_token(explicit):
    if explicit:
        return explicit, "flag"
    for var in ("GITHUB_TOKEN", "GH_TOKEN"):
        if os.environ.get(var):
            return os.environ[var], var
    if shutil.which("gh"):
        code, out, _ = run(["gh", "auth", "token"], timeout=20)
        if code == 0 and out.strip():
            return out.strip(), "gh_cli"
    return None, "none"


def collect_api(gh, owner, name):
    """Repository settings and release data that only the API can show."""
    sig = {}
    base = "/repos/{}/{}".format(owner, name)

    status, meta = gh.get(base, "repo")
    sig["repo_meta"] = {"status": status}
    default_branch = "main"
    if meta:
        default_branch = meta.get("default_branch") or "main"
        saa = meta.get("security_and_analysis") or {}
        sig["repo_meta"].update({
            "private": meta.get("private"),
            "archived": meta.get("archived"),
            "default_branch": default_branch,
            "license": (meta.get("license") or {}).get("spdx_id"),
            "pushed_at": meta.get("pushed_at"),
            "html_url": meta.get("html_url"),
            "secret_scanning": (saa.get("secret_scanning") or {}).get("status"),
            "secret_scanning_push_protection": (saa.get("secret_scanning_push_protection") or {}).get("status"),
            "dependabot_security_updates": (saa.get("dependabot_security_updates") or {}).get("status"),
            "security_and_analysis_visible": bool(saa),
        })

    status, body = gh.get(base + "/private-vulnerability-reporting", "pvr")
    sig["private_vulnerability_reporting"] = {
        "status": status, "enabled": body.get("enabled") if body else None
    }

    status, _ = gh.get(base + "/vulnerability-alerts", "dependabot_alerts")
    # 204 => enabled; 404 => disabled OR no admin permission (GitHub does not distinguish)
    sig["dependabot_alerts"] = {
        "status": status,
        "enabled": True if status == "ok" else (None if status in ("not_found", "permission_denied") else False),
        "note": "404 means disabled or insufficient permission; needs admin to be sure" if status == "not_found" else None,
    }

    status, body = gh.get("{}/branches/{}/protection".format(base, default_branch), "branch_protection")
    bp = {"status": status, "branch": default_branch}
    if body:
        prr = body.get("required_pull_request_reviews") or {}
        rsc = body.get("required_status_checks") or {}
        bp.update({
            "protected": True,
            "required_reviews": prr.get("required_approving_review_count"),
            "required_status_checks": bool(rsc.get("contexts") or rsc.get("checks")),
            "allow_force_pushes": (body.get("allow_force_pushes") or {}).get("enabled"),
            "required_signatures": (body.get("required_signatures") or {}).get("enabled"),
        })
    elif status == "not_found":
        bp["protected"] = None
        bp["note"] = "404 means branch not protected or no permission to read protection"
    sig["branch_protection"] = bp

    status, body = gh.get(base + "/rulesets", "rulesets")
    sig["rulesets"] = {"status": status, "count": len(body) if isinstance(body, list) else None}

    status, body = gh.get(base + "/releases?per_page=10", "releases")
    rel_sig = {"status": status, "count": 0, "latest_tag": None, "assets": [], "dates": []}
    if isinstance(body, list):
        rel_sig["count"] = len(body)
        if body:
            rel_sig["latest_tag"] = body[0].get("tag_name")
            rel_sig["assets"] = [a.get("name") for a in (body[0].get("assets") or [])]
            rel_sig["dates"] = [r.get("published_at") for r in body if r.get("published_at")]
    sig["releases"] = rel_sig

    status, body = gh.get(base + "/tags?per_page=5", "tags")
    sig["tags"] = {"status": status, "count": len(body) if isinstance(body, list) else None}

    status, body = gh.get(base + "/security-advisories?per_page=20", "advisories")
    sig["security_advisories"] = {
        "status": status,
        "published": len([a for a in body if a.get("state") == "published"]) if isinstance(body, list) else None,
    }

    status, _ = gh.get(base + "/dependency-graph/sbom", "dependency_graph_sbom")
    sig["dependency_graph"] = {"status": status, "enabled": True if status == "ok" else None}

    status, body = gh.get(base + "/code-scanning/default-setup", "code_scanning_default_setup")
    sig["code_scanning_default_setup"] = {
        "status": status, "state": body.get("state") if isinstance(body, dict) else None
    }

    status, body = gh.get(base + "/code-scanning/analyses?per_page=1", "code_scanning_analyses")
    sig["code_scanning_analyses"] = {
        "status": status, "present": bool(body) if isinstance(body, list) else None
    }

    return sig, default_branch


# ----------------------------------------------------------------------------- clone


def shallow_clone(owner, name, token, dest):
    if not shutil.which("git"):
        return {"status": "git_not_installed"}
    url = "https://github.com/{}/{}.git".format(owner, name)
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0")
    attempts = [("anonymous", ["git", "clone", "--quiet", "--depth", "50", url, dest])]
    if token:
        # Token is passed as a header, not in the URL, so it never appears in the process list.
        attempts.append(("token", ["git", "-c", "http.extraheader=AUTHORIZATION: bearer " + token,
                                   "clone", "--quiet", "--depth", "50", url, dest]))
    last_err = ""
    for label, cmd in attempts:
        code, _, err = run(cmd, timeout=300, env=env)
        if code == 0:
            run(["git", "fetch", "--quiet", "--tags", "--depth", "1"], cwd=dest, timeout=120, env=env)
            return {"status": "ok", "auth": label}
        last_err = err.strip()[-300:]
        shutil.rmtree(dest, ignore_errors=True)
        os.makedirs(dest, exist_ok=True)
    return {"status": "clone_failed", "detail": last_err}


# ----------------------------------------------------------------------------- file scan

DOC_CATEGORIES = {
    # category: (filename patterns, content patterns)
    "sdl": ([r"sdl", r"secure[-_ ]?dev", r"security[-_ ]?policy", r"secure[-_ ]?sdlc", r"development[-_ ]?lifecycle"],
            [r"security development lifecycle", r"secure development", r"\bSDL\b", r"secure sdlc"]),
    "risk_assessment": ([r"risk[-_ ]?assess", r"risk[-_ ]?register", r"risk[-_ ]?analysis"],
                        [r"risk assessment", r"risk register"]),
    "threat_model": ([r"threat[-_ ]?model"], [r"threat model", r"\bSTRIDE\b", r"\bPASTA\b", r"\bLINDDUN\b", r"attack tree"]),
    "incident_response": ([r"incident", r"vulnerability[-_ ]?(handling|management|response|disclosure)", r"\bcvd\b", r"security[-_ ]?response"],
                          [r"incident response", r"vulnerability handling", r"coordinated vulnerability disclosure"]),
    "test_plan": ([r"test[-_ ]?plan", r"security[-_ ]?test"], [r"test plan", r"security testing"]),
    "pentest": ([r"pentest", r"penetration", r"pen[-_ ]?test"], [r"penetration test", r"pentest"]),
    "dependency_policy": ([r"depend", r"third[-_ ]?party", r"oss[-_ ]?policy", r"open[-_ ]?source[-_ ]?policy"],
                          [r"third[- ]party components?", r"dependency policy", r"open[- ]source (component )?policy", r"approved (libraries|dependencies)"]),
    "support_policy": ([r"^support", r"lifecycle", r"\beol\b", r"end[-_ ]?of[-_ ]?life", r"supported[-_ ]?versions", r"maintenance"],
                       [r"supported versions", r"end[- ]of[- ]life", r"support period", r"security updates? (are|will be) (provided|available)"]),
    "network": ([r"network", r"ports?\b", r"inbound", r"outbound", r"connections?", r"firewall", r"egress"],
                [r"inbound", r"outbound", r"listening port", r"open ports?", r"egress", r"external services? (called|used)"]),
    "privacy": ([r"privacy", r"data[-_ ]?(handling|inventory|protection|retention)", r"telemetry", r"gdpr"],
                [r"telemetry", r"opt[- ]?in", r"data minimi[sz]ation", r"we (collect|store)"]),
    "hardening": ([r"harden", r"secure[-_ ]?config", r"deployment[-_ ]?security", r"security[-_ ]?guide"],
                  [r"attack surface", r"hardening", r"secure by default", r"disabled by default", r"least privilege"]),
    "compliance": ([r"complian", r"conformity", r"declaration", r"technical[-_ ]?file", r"ce[-_ ]?mark", r"classification", r"retention", r"\bcra\b"],
                   [r"declaration of conformity", r"CE marking", r"notified body", r"technical documentation", r"Annex VII", r"conformity assessment", r"cyber resilience act"]),
}

DOC_EXT = {".md", ".markdown", ".txt", ".rst", ".adoc", ".asciidoc"}
LOCKFILES = {
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "bun.lockb", "bun.lock", "poetry.lock",
    "uv.lock", "Pipfile.lock", "pdm.lock", "requirements.txt", "go.sum", "Cargo.lock",
    "Gemfile.lock", "composer.lock", "packages.lock.json", "gradle.lockfile", "mix.lock",
    "pubspec.lock", "Podfile.lock", "flake.lock",
}
MANIFESTS = {
    "package.json", "pyproject.toml", "setup.py", "Pipfile", "requirements.in", "go.mod",
    "Cargo.toml", "Gemfile", "composer.json", "pom.xml", "build.gradle", "build.gradle.kts",
    "mix.exs", "pubspec.yaml", "Podfile", "*.csproj",
}
RUNTIME_PINS = {
    ".nvmrc", ".node-version", ".python-version", ".tool-versions", ".ruby-version",
    ".go-version", ".java-version", "global.json", "rust-toolchain", "rust-toolchain.toml",
    ".terraform-version", ".sdkmanrc",
}
SBOM_FILE_RE = re.compile(r"(\.spdx(\.json|\.yml|\.yaml|\.xml|\.rdf)?$|\.cdx\.(json|xml)$|^bom\.(json|xml)$|sbom.*\.(json|xml)$)", re.I)
SIG_ASSET_RE = re.compile(r"(\.sig$|\.asc$|\.pem$|\.sigstore(\.json)?$|\.bundle$|\.intoto\.jsonl$|attestation|provenance|\.minisig$)", re.I)
CHECKSUM_ASSET_RE = re.compile(r"(checksums?|sha256|sha512|\.sha256$|\.sha512$|SHASUMS)", re.I)

WORKFLOW_TOOLS = {
    "sast": [r"github/codeql-action", r"codeql", r"semgrep", r"sonar(cloud|qube|source)", r"\bbandit\b", r"\bgosec\b", r"brakeman", r"snyk.*code", r"psalm", r"phpstan.*security", r"njsscan", r"horusec"],
    "secrets": [r"gitleaks", r"trufflehog", r"detect-secrets", r"ggshield", r"gitguardian", r"secretlint"],
    "sbom": [r"anchore/sbom-action", r"\bsyft\b", r"cyclonedx", r"\bspdx\b", r"cdxgen", r"sbom-tool", r"\bsbom\b", r"trivy.*sbom", r"bom\.json"],
    "sbom_format": [r"spdx-?json", r"cyclonedx-?json", r"cyclonedx-?xml", r"spdx", r"cyclonedx"],
    "vuln_scan": [r"anchore/scan-action", r"\bgrype\b", r"aquasecurity/trivy-action", r"\btrivy\b", r"osv-scanner", r"google/osv-scanner", r"\bsnyk\b", r"dependency-review-action", r"dependency-check", r"pip-audit", r"npm audit", r"cargo audit", r"govulncheck", r"bundler-audit", r"safety check", r"nancy"],
    "dependency_review": [r"actions/dependency-review-action"],
    "signing": [r"\bcosign\b", r"sigstore", r"slsa-framework", r"attest-build-provenance", r"actions/attest", r"gpg .*--(detach-)?sign", r"--provenance", r"minisign", r"signpath", r"notary"],
    "checksums": [r"sha256sum", r"shasum", r"checksums?\.txt", r"sha512sum"],
    "trusted_publishing": [r"pypa/gh-action-pypi-publish", r"id-token:\s*write", r"npm publish.*--provenance"],
    "eol": [r"\bxeol\b", r"endoflife", r"end-of-life"],
    "release_automation": [r"release-please", r"semantic-release", r"goreleaser", r"softprops/action-gh-release", r"ncipollo/release-action", r"gh release create", r"changesets/action", r"cargo-release", r"electron-builder.*publish", r"actions/create-release"],
    "tests": [r"\bpytest\b", r"npm (run )?test", r"yarn test", r"pnpm test", r"go test", r"cargo test", r"mvn .*test", r"gradle.*test", r"\bjest\b", r"\bvitest\b", r"make test", r"dotnet test", r"phpunit", r"\brspec\b", r"bundle exec rake", r"mix test", r"flutter test", r"tox", r"nox"],
    "dast": [r"zaproxy", r"owasp.*zap", r"\bnuclei\b", r"nikto"],
    "container_scan": [r"trivy image", r"grype .*image", r"docker scout", r"snyk container"],
    "codeowners": [],
}

DEFAULT_CRED_RE = re.compile(
    r"(?i)\b([A-Z0-9_]*(PASSWORD|PASSWD|_PASS|SECRET|_PWD)[A-Z0-9_]*)\s*[:=]\s*[\"']?(admin|password|passw0rd|changeme|change_me|secret|root|toor|123456|12345678|test|default|letmein|pass|qwerty|guest|welcome)[\"']?\s*(#|$|,|\")"
)
CONFIG_EXT = {".yml", ".yaml", ".json", ".toml", ".ini", ".env", ".properties", ".cfg", ".conf", ".xml"}
TELEMETRY_LIBS = [r"@sentry/", r"sentry-sdk", r"posthog", r"mixpanel", r"segment", r"analytics-node", r"amplitude", r"google-analytics", r"gtag\(", r"datadog", r"newrelic", r"opentelemetry", r"applicationinsights", r"bugsnag", r"rollbar", r"hotjar", r"intercom"]


def analyze_security_md(path_label, txt):
    return {
        "path": path_label,
        "has_contact": bool(re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+|security/advisories/new|private vulnerability reporting|report a vulnerability.*(https?://|form)|https?://\S+(report|security|disclos)", txt, re.I)),
        "has_response_time": bool(re.search(r"(within|in)\s+\d+\s*(business |working )?(hours|days)|acknowledge|respond(s)? (to|within)|response time|\d+\s*(h|hrs|hours)\b", txt, re.I)),
        "has_supported_versions": bool(re.search(r"supported versions", txt, re.I)),
        "has_dates": bool(re.search(r"\b20[2-4]\d[-/.](0[1-9]|1[0-2])|until (20[2-4]\d|[A-Z][a-z]+ 20[2-4]\d)|\b(until|through)\s+20[2-4]\d", txt)),
        "mentions_cvd_policy": bool(re.search(r"coordinated|disclosure policy|embargo|90 days", txt, re.I)),
        "mentions_encryption": bool(re.search(r"pgp|gpg|public key", txt, re.I)),
    }


def collect_org_security_policy(gh, owner):
    """GitHub shows an org-wide SECURITY.md from OWNER/.github when the repo has none."""
    import base64
    for path in ("SECURITY.md", "security.md", ".github/SECURITY.md", "docs/SECURITY.md"):
        status, body = gh.get("/repos/{}/.github/contents/{}".format(owner, path), "org_security_policy")
        if status == "ok" and isinstance(body, dict) and body.get("content"):
            try:
                txt = base64.b64decode(body["content"]).decode("utf-8", errors="replace")
            except (ValueError, TypeError):
                continue
            info = analyze_security_md("{}/.github/{} (org-level default)".format(owner, path), txt)
            info["org_level"] = True
            return info
        if status not in ("ok", "not_found"):
            return {"status": status}
    return None


def scan_files(root, excludes=None):
    """Walk a local checkout and extract evidence signals.

    excludes: iterable of repo-relative directory prefixes to skip (e.g. "examples", "docs/vendor").
    Useful when a repo contains documents *about* compliance (templates, fixtures) that should not
    count as the product's own policy documents.
    """
    excludes = set(e.strip("/").replace(os.sep, "/") for e in (excludes or []) if e.strip("/"))
    excludes |= set(DEFAULT_EXCLUDES)
    sig = {
        "root": root,
        "excluded": excludes,
        "files_scanned": 0,
        "key_files": {},
        "lockfiles": [],
        "manifests": [],
        "runtime_pins": [],
        "sbom_files": [],
        "docs": {cat: [] for cat in DOC_CATEGORIES},
        "doc_hits": {},          # relpath -> categories
        "security_md": None,
        "readme": None,
        "workflows": [],
        "workflow_tools": {k: [] for k in WORKFLOW_TOOLS},
        "workflow_triggers": {"pull_request": [], "push": [], "schedule": [], "release": [], "workflow_dispatch": []},
        "dependabot_config": None,
        "renovate_config": None,
        "pr_template": None,
        "pr_template_security_checklist": False,
        "dockerfiles": [],
        "docker_expose_total": 0,
        "docker_unpinned_base": [],
        "compose_files": [],
        "compose_ports": 0,
        "default_credential_hits": [],
        "test_dirs": [],
        "security_test_files": [],
        "telemetry_libs": [],
        "security_txt": None,
        "user_docs_signals": {},
    }

    doc_files = []
    for dirpath, dirnames, filenames in os.walk(root):
        here = rel(root, dirpath)
        here = "" if here == "." else here
        dirnames[:] = [
            d for d in dirnames
            if (d in (".github", ".well-known") or (d not in SKIP_DIRS and not d.startswith(".")))
            and (here + "/" + d if here else d) not in excludes
        ]
        depth = here.count("/") if here else 0
        if depth > 6:
            dirnames[:] = []
            continue
        for fn in filenames:
            full = os.path.join(dirpath, fn)
            r = rel(root, full)
            if r in excludes:
                continue
            low = fn.lower()
            sig["files_scanned"] += 1

            if fn in LOCKFILES:
                sig["lockfiles"].append(r)
            if fn in MANIFESTS or fn.endswith(".csproj"):
                sig["manifests"].append(r)
            if fn in RUNTIME_PINS:
                sig["runtime_pins"].append(r)
            if SBOM_FILE_RE.search(fn):
                sig["sbom_files"].append(r)

            if depth == 0 or dirpath.endswith(".github") or "/docs" in dirpath.replace(os.sep, "/") or dirpath.rstrip("/").endswith("docs"):
                for key, names in (
                    ("security_md", ("security.md", "security.rst", "security.txt", "security")),
                    ("support_md", ("support.md",)),
                    ("readme", ("readme.md", "readme.rst", "readme.txt", "readme")),
                    ("contributing", ("contributing.md",)),
                    ("changelog", ("changelog.md", "changes.md", "history.md", "releases.md")),
                    ("license", ("license", "license.md", "license.txt", "copying")),
                    ("codeowners", ("codeowners",)),
                ):
                    if low in names and key not in sig["key_files"]:
                        sig["key_files"][key] = r

            if low == "pull_request_template.md" or (low.endswith(".md") and "pull_request_template" in dirpath.lower()):
                sig["pr_template"] = r
                txt = read_text(full)
                if re.search(r"security|threat|secret|vulnerab", txt, re.I) and re.search(r"- \[[ x]\]", txt):
                    sig["pr_template_security_checklist"] = True

            if low == "dependabot.yml" or low == "dependabot.yaml":
                sig["dependabot_config"] = r
            if low in ("renovate.json", "renovate.json5", ".renovaterc", ".renovaterc.json") or (low == "renovate.json" and ".github" in dirpath):
                sig["renovate_config"] = r
            if low == "security.txt" and ".well-known" in dirpath:
                sig["security_txt"] = r

            if "/.github/workflows" in ("/" + r) and (low.endswith(".yml") or low.endswith(".yaml")):
                txt = read_text(full)
                sig["workflows"].append(r)
                for tool, pats in WORKFLOW_TOOLS.items():
                    if pats and any_match(pats, txt):
                        sig["workflow_tools"][tool].append(r)
                on_block = re.search(r"(?ms)^on:\s*(.*?)(?=^\w|\Z)", txt)
                on_txt = on_block.group(0) if on_block else txt[:800]
                for trig in sig["workflow_triggers"]:
                    if re.search(r"\b" + trig + r"\b", on_txt):
                        sig["workflow_triggers"][trig].append(r)

            if low.startswith("dockerfile") or low.endswith(".dockerfile"):
                txt = read_text(full)
                sig["dockerfiles"].append(r)
                sig["docker_expose_total"] += len(re.findall(r"(?im)^\s*EXPOSE\b", txt))
                for m in re.finditer(r"(?im)^\s*FROM\s+([^\s]+)", txt):
                    img = m.group(1)
                    if img.lower().endswith(":latest") or (":" not in img.split("/")[-1] and "@" not in img and not img.startswith("$")):
                        sig["docker_unpinned_base"].append("{}: {}".format(r, img))
            if re.match(r"(docker-)?compose.*\.ya?ml$", low):
                txt = read_text(full)
                sig["compose_files"].append(r)
                sig["compose_ports"] += len(re.findall(r'^\s*-\s*"?\d+:\d+', txt, re.M))

            ext = os.path.splitext(low)[1]
            if ext in CONFIG_EXT or low.startswith(".env") or low.startswith("dockerfile") or low.startswith("docker-compose"):
                if os.path.getsize(full) < MAX_TEXT_BYTES and fn not in LOCKFILES:
                    txt = read_text(full)
                    for i, line in enumerate(txt.splitlines(), 1):
                        m = DEFAULT_CRED_RE.search(line)
                        if m:
                            sig["default_credential_hits"].append("{}:{} ({})".format(r, i, m.group(1)))
                            if len(sig["default_credential_hits"]) > 25:
                                break

            if re.search(r"(^|/)(tests?|spec|__tests__|e2e|integration[-_]tests?)(/|$)", r, re.I) or re.search(r"(_test\.go|\.test\.[jt]sx?|\.spec\.[jt]sx?|^test_.*\.py|_test\.py|_spec\.rb|Tests?\.(cs|java|kt|swift))$", fn, re.I):
                d = r.split("/")[0] if "/" in r else "."
                if d not in sig["test_dirs"]:
                    sig["test_dirs"].append(d)
                if re.search(r"auth|authz|authn|login|permission|inject|xss|csrf|crypto|encrypt|secur|sanitiz|valid", low):
                    if len(sig["security_test_files"]) < 30:
                        sig["security_test_files"].append(r)

            if ext in DOC_EXT and len(doc_files) < MAX_DOC_FILES:
                doc_files.append((full, r))

            if ext in (".js", ".ts", ".tsx", ".jsx", ".py", ".go", ".rb", ".java", ".kt", ".swift", ".cs", ".php", ".rs", ".dart") or fn in ("package.json", "requirements.txt", "pyproject.toml", "go.mod", "Cargo.toml", "Gemfile", "pubspec.yaml"):
                if fn in ("package.json", "requirements.txt", "pyproject.toml", "go.mod", "Cargo.toml", "Gemfile", "pubspec.yaml") and os.path.getsize(full) < MAX_TEXT_BYTES:
                    txt = read_text(full)
                    for pat in TELEMETRY_LIBS:
                        if re.search(pat, txt, re.I) and pat not in sig["telemetry_libs"]:
                            sig["telemetry_libs"].append(pat)

    # document classification
    for full, r in doc_files:
        txt = read_text(full)
        base = os.path.basename(r).lower()
        stem = os.path.splitext(base)[0]
        cats = []
        for cat, (fpats, cpats) in DOC_CATEGORIES.items():
            fname_hit = any(re.search(p, stem, re.I) for p in fpats)
            content_hits = len(any_match(cpats, txt))
            if (fname_hit and content_hits >= 1) or content_hits >= 2:
                cats.append(cat)
                sig["docs"][cat].append(r)
        if cats:
            sig["doc_hits"][r] = cats

    # SECURITY.md analysis (org-level fallback is added later by collect_org_security_policy)
    sec_path = sig["key_files"].get("security_md")
    if sec_path:
        sig["security_md"] = analyze_security_md(sec_path, read_text(os.path.join(root, sec_path)))

    # Corpus of user-facing docs (README, support/hardening/privacy/compliance docs, SECURITY.md)
    corpus = ""
    if sig["key_files"].get("readme"):
        corpus += read_text(os.path.join(root, sig["key_files"]["readme"])) + "\n"
    for cat in ("support_policy", "hardening", "privacy", "compliance"):
        for r in sig["docs"][cat][:5]:
            corpus += read_text(os.path.join(root, r)) + "\n"
    if sec_path:
        corpus += read_text(os.path.join(root, sec_path))
    changelog = read_text(os.path.join(root, sig["key_files"]["changelog"])) if sig["key_files"].get("changelog") else ""

    # Annex II points (R11). Point 6 (DoC URL) is "where applicable"; point 9 optional.
    sig["annex_ii_signals"] = {
        "1_manufacturer_identity": bool(re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", corpus)) and bool(re.search(r"(?im)^(#+\s*)?(about|contact|maintainer|author|company|manufacturer|imprint|legal)|copyright|\(c\)|©|registered (office|address)|\b(ltd|gmbh|inc|llc|sas|bv|ab|oy|s\.?r\.?l|s\.?a\.?)\b", corpus)),
        "2_vulnerability_contact_and_cvd": bool(re.search(r"report(ing)? (a |security )?vulnerabilit|security@|SECURITY\.md|security policy|disclosure", corpus, re.I)),
        "3_product_identification": bool(re.search(r"\bversion\b|\bv\d+\.\d+|release", corpus, re.I)),
        "4_intended_purpose_and_security_properties": bool(re.search(r"intended (use|purpose)|is (a|an) .{3,80} (for|that)|purpose of", corpus, re.I)) and bool(re.search(r"security (features|properties|model|considerations)|encrypt|authenticat|what (it|the \w+) does (and does )?not", corpus, re.I)),
        "5_known_risks": bool(re.search(r"known (limitation|issue|risk)|security consideration|threat|misuse|do not (use|run) .{0,40}(untrusted|production|internet)|risk", corpus, re.I)),
        "6_doc_url": bool(re.search(r"declaration of conformity", corpus, re.I)),
        "7_support_and_end_date": bool(re.search(r"support(ed)? (period|until|window|policy|versions)|end[- ]of[- ](life|support)|security updates? (until|through|for)", corpus, re.I)),
        "8_secure_use_instructions": bool(re.search(r"install|setup|set up|configur|upgrade|updat|uninstall|decommission|remov(e|ing) (all )?data", corpus, re.I)) and bool(re.search(r"secur|harden|token|permission|verify", corpus, re.I)),
    }

    # support policy specifics (R5, P8, P9)
    support_corpus = ""
    for r in sig["docs"]["support_policy"][:5]:
        support_corpus += read_text(os.path.join(root, r)) + "\n"
    if sig["key_files"].get("support_md"):
        support_corpus += read_text(os.path.join(root, sig["key_files"]["support_md"]))
    if sec_path:
        support_corpus += read_text(os.path.join(root, sec_path))
    sig["support_signals"] = {
        "has_support_doc": bool(sig["docs"]["support_policy"] or sig["key_files"].get("support_md")),
        "has_dates": bool(re.search(r"\b20[2-4]\d[-/.](0[1-9]|1[0-2])|\b(until|through|to)\s+(\w+\s+)?20[2-4]\d|\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+20[2-4]\d", support_corpus, re.I)),
        "has_reasoning": bool(re.search(r"(how|why) (we|this) (decid|determin|chose)|expected (use|lifetime)|based on .{0,60}(lifetime|dependenc|runtime)|support period (is|was) (set|determined|chosen)", support_corpus, re.I)),
        "supported_versions_table": bool(re.search(r"supported versions|\|\s*version\s*\|", support_corpus, re.I)),
        "free_security_updates": bool(re.search(r"(free|no (additional )?(cost|charge)|without charge).{0,80}(security )?(update|patch|fix)(e?s)?|(security )?(update|patch|fix)(e?s)?.{0,80}(free|no (additional )?(cost|charge)|without charge)", support_corpus, re.I)),
        "updates_kept_available": bool(re.search(r"(remain|kept|stay|available).{0,60}(10|ten) years|(10|ten) years.{0,60}(remain|kept|stay|available)|never (delete|remove)d? (release|artefact|artifact)", support_corpus, re.I)),
        "eol_notification": bool(re.search(r"(notif|announc|inform|tell|warn).{0,80}(end[- ]of[- ](support|life)|eol|final (security )?update)|(end[- ]of[- ](support|life)|eol).{0,80}(notif|announc|inform|warn)", support_corpus, re.I)),
        "twelve_month_notice": bool(re.search(r"(12|twelve)[- ]months?.{0,80}(notice|advance|before|announce)|(notice|advance|announce).{0,80}(12|twelve)[- ]months?", support_corpus, re.I)),
        "component_eol_considered": bool(re.search(r"\b(dependenc\w*|runtime\w*|component\w*|librar\w*|base images?|python|node\.?js|\.net|golang|kernel|database)\b.{0,80}\b(end[- ]of[- ]life|eol|supported until|maintained until|support(ed)? (period|window)s?)\b|\b(end[- ]of[- ]life|eol)\b.{0,80}\b(dependenc\w*|runtime\w*|component\w*|librar\w*)\b", support_corpus + "".join(read_text(os.path.join(root, r)) for r in sig["docs"]["dependency_policy"][:3]), re.I)),
    }

    # incident response specifics (P3-P6, P10)
    ir_corpus = ""
    for r in sig["docs"]["incident_response"][:5]:
        ir_corpus += read_text(os.path.join(root, r)) + "\n"
    sig["incident_signals"] = {
        "has_doc": bool(sig["docs"]["incident_response"]),
        "mentions_enisa": bool(re.search(r"\bENISA\b|single reporting platform", ir_corpus)),
        "mentions_24h": bool(re.search(r"24[- ]?(hours|hrs|h)\b", ir_corpus, re.I)),
        "mentions_72h": bool(re.search(r"72[- ]?(hours|hrs|h)\b", ir_corpus, re.I)),
        "mentions_14_days": bool(re.search(r"14[- ]?days|fourteen days", ir_corpus, re.I)),
        "mentions_one_month": bool(re.search(r"(one|1)[- ]month|30[- ]days|within a month", ir_corpus, re.I)),
        "mentions_csirt": bool(re.search(r"\bCSIRT\b", ir_corpus)),
        "defines_actively_exploited": bool(re.search(r"actively exploited|reliable evidence.{0,60}exploit", ir_corpus, re.I)),
        "covers_incidents": bool(re.search(r"\bincident", ir_corpus, re.I)),
        "severity_criteria": bool(re.search(r"severe|availability, authenticity, integrity|malicious code|Art(icle|\.) ?14\(5\)", ir_corpus, re.I)),
        "informs_users": bool(re.search(r"(inform|notify|tell|advis).{0,60}(users|customers)|(users|customers).{0,60}(informed|notified)|advisory", ir_corpus, re.I)),
        "content_72h": bool(re.search(r"nature of the (exploit|vulnerability|incident)|corrective|mitigat", ir_corpus, re.I)),
        "content_final": bool(re.search(r"severity|impact|root cause|malicious actor|details? (of|about) the (security )?update", ir_corpus, re.I)),
        "corrective_measures": bool(re.search(r"recall|withdraw|corrective (measure|action)", ir_corpus, re.I)),
        "authority_cooperation": bool(re.search(r"market surveillance|competent authorit|national authorit", ir_corpus, re.I)),
        "cessation_plan": bool(re.search(r"ceas(e|ing) (operations|trading|business)|wind[- ]down|shut ?down of the company|company (closes|is dissolved)", ir_corpus + support_corpus, re.I)),
        "named_owner": bool(re.search(r"owner|on[- ]call|responsible|@[\w-]+|security lead|CISO|CTO", ir_corpus, re.I)),
    }

    # risk / threat / sdl specifics
    risk_corpus = "".join(read_text(os.path.join(root, r)) for r in sig["docs"]["risk_assessment"][:3])
    sig["risk_signals"] = {
        "has_doc": bool(sig["docs"]["risk_assessment"]),
        "use_context": bool(re.search(r"intended (purpose|use)|foreseeable (use|misuse)|operating environment|conditions of use|assets? to be protected", risk_corpus, re.I)),
        "maps_annex_i": len(re.findall(r"\(2\)\(([a-m])\)|Part I|Annex I|secure by default|known exploitable|data minimi|attack surface|confidentiality|integrity|availability|unauthori[sz]ed access|logging|remov(e|al) .{0,20}data", risk_corpus, re.I)) >= 5,
        "justifies_na": bool(re.search(r"not applicable|does not apply|n/?a\b", risk_corpus, re.I)),
        "has_ratings": bool(re.search(r"likelihood|impact|severity|probability", risk_corpus, re.I)),
        "has_mitigations": bool(re.search(r"mitigat|control|treatment|remediat|implemented (by|via|through)", risk_corpus, re.I)),
        "identifies_threats": bool(re.search(r"threat|attacker|adversar|attack (vector|surface)|entry point|trust boundar", risk_corpus, re.I)),
        "has_history_section": bool(re.search(r"change ?log|revision history|version history|review trigger|last reviewed", risk_corpus, re.I)),
        "secure_by_default": bool(re.search(r"secure[- ]by[- ]default|default (configuration|settings)", risk_corpus, re.I)),
        "attack_surface": bool(re.search(r"attack surface|external interface", risk_corpus, re.I)),
    }
    tm_corpus = "".join(read_text(os.path.join(root, r)) for r in sig["docs"]["threat_model"][:3])
    sig["threat_model_signals"] = {
        "has_doc": bool(sig["docs"]["threat_model"]),
        "method_named": bool(re.search(r"\bSTRIDE\b|\bPASTA\b|\bLINDDUN\b|attack tree|kill chain|MITRE ATT&CK", tm_corpus)),
        "has_attack_surface": bool(re.search(r"attack surface|entry point|trust boundar", tm_corpus, re.I)),
        "has_threats": bool(re.search(r"threat|attacker|adversar", tm_corpus, re.I)),
    }
    sdl_corpus = "".join(read_text(os.path.join(root, r)) for r in sig["docs"]["sdl"][:3])
    sig["sdl_signals"] = {
        "has_doc": bool(sig["docs"]["sdl"]),
        "has_phases": bool(re.search(r"phase|stage|design|implement|test|release|deploy", sdl_corpus, re.I)),
        "has_roles": bool(re.search(r"role|owner|responsib|RACI|security champion|approver", sdl_corpus, re.I)),
        "covers_vuln_handling": bool(re.search(r"vulnerab|incident|disclos|triage", sdl_corpus, re.I)),
        "secure_by_default": bool(re.search(r"secure[- ]by[- ]default|attack surface|secure[- ]by[- ]design|default (configuration|settings)", sdl_corpus, re.I)),
        "mentions_certification": bool(re.search(r"ISO/?IEC 27001|IEC 62443|SOC ?2", sdl_corpus + corpus, re.I)),
        "release_signoff": bool(re.search(r"review record|sign[- ]off|release checklist|approval", sdl_corpus, re.I)),
    }
    tp_corpus = "".join(read_text(os.path.join(root, r)) for r in sig["docs"]["test_plan"][:3])
    sig["test_plan_signals"] = {
        "has_doc": bool(sig["docs"]["test_plan"]),
        "covers_areas": len(any_match([r"authenticat", r"access control|authori[sz]", r"input validation|injection", r"encrypt|crypto", r"error handling"], tp_corpus)),
    }
    net_corpus = "".join(read_text(os.path.join(root, r)) for r in sig["docs"]["network"][:5]) + "".join(read_text(os.path.join(root, r)) for r in sig["docs"]["hardening"][:3]) + risk_corpus
    sig["network_signals"] = {
        "has_doc": bool(sig["docs"]["network"]),
        "inbound_documented": bool(re.search(r"inbound|listen|open port|exposes? port|no (listening|open) ports|does not listen", net_corpus, re.I)),
        "inbound_justified": bool(re.search(r"inbound|listen|open port|exposes? port", net_corpus, re.I)) and bool(re.search(r"\b\d{2,5}(/tcp|/udp)?\b", net_corpus)) and bool(re.search(r"purpose|reason|why|required for|needed for", net_corpus, re.I)),
        "outbound_documented": bool(re.search(r"outbound|egress|connects to|contacts only|talks to|calls (out|the following)|external (service|endpoint)|api\.\w+\.\w+", net_corpus + corpus, re.I)),
    }
    priv_corpus = "".join(read_text(os.path.join(root, r)) for r in sig["docs"]["privacy"][:5])
    sig["privacy_signals"] = {
        "has_doc": bool(sig["docs"]["privacy"]),
        "telemetry_opt_in_or_off": bool(re.search(r"opt[- ]?in|disabled by default|off by default|no telemetry|does not collect|collects nothing|no data is (sent|collected|uploaded)", priv_corpus + corpus, re.I)),
        "telemetry_on_by_default": bool(re.search(r"enabled by default|on by default|opt[- ]?out", priv_corpus, re.I)),
        "data_inventory": bool(re.search(r"we (collect|store|process)|data (we|that is) (collect|process|store)|retention|reads? .{0,40}(files|settings)|writes? (only|nothing)", priv_corpus + corpus, re.I)),
    }
    comp_corpus_paths = sig["docs"]["compliance"][:10]
    comp_corpus = "".join(read_text(os.path.join(root, r)) for r in comp_corpus_paths)
    sig["compliance_signals"] = {
        "docs": comp_corpus_paths,
        "scope_decision": bool(re.search(r"(in|out of|outside|within) (the )?scope|not (a )?(product with digital elements|placed on the market)|commercial activity", comp_corpus, re.I)),
        "classification": bool(re.search(r"(default|important|critical) (product|class)|Annex III|Annex IV|classif", comp_corpus, re.I)),
        "conformity_route": bool(re.search(r"module A|self[- ]assessment|internal control|notified body|Annex VIII|conformity assessment (route|procedure)", comp_corpus, re.I)),
        "declaration_of_conformity": bool(re.search(r"declaration of conformity|Annex V\b", comp_corpus, re.I)),
        "ce_marking": bool(re.search(r"CE mark", comp_corpus, re.I)),
        "technical_file": bool(re.search(r"technical (file|documentation)|Annex VII", comp_corpus, re.I)),
        "retention": bool(re.search(r"(10|ten)[- ]years?.{0,60}(retain|retention|keep|archive|available)|(retain|retention|keep|archive).{0,60}(10|ten)[- ]years?|support period, whichever is longer", comp_corpus + support_corpus, re.I)),
        "authorised_representative": bool(re.search(r"authori[sz]ed representative", comp_corpus, re.I)),
    }
    dep_corpus = "".join(read_text(os.path.join(root, r)) for r in sig["docs"]["dependency_policy"][:3])
    sig["dependency_policy_signals"] = {
        "has_doc": bool(sig["docs"]["dependency_policy"]),
        "covers_eol": bool(re.search(r"end[- ]of[- ]life|EOL|maintained|last release", dep_corpus, re.I)),
        "covers_vuln_response": bool(re.search(r"vulnerab|CVE|patch|update within", dep_corpus, re.I)),
        "covers_selection": bool(re.search(r"licen[cs]e|approv|criteria|evaluat|select", dep_corpus, re.I)),
        "covers_upstream_reporting": bool(re.search(r"upstream|report(ed)? (it )?to the (maintainer|project|vendor)|maintainer", dep_corpus, re.I)),
    }
    hard_corpus = "".join(read_text(os.path.join(root, r)) for r in sig["docs"]["hardening"][:5])
    sig["hardening_signals"] = {
        "has_doc": bool(sig["docs"]["hardening"]),
        "first_run_credentials": bool(re.search(r"first (run|login|start|boot|use).{0,80}(password|credential|set ?up)|(password|credential).{0,80}first (run|login|start|boot|use)|initial (admin )?password", corpus + hard_corpus, re.I)),
        "no_authentication": bool(re.search(r"no (user )?accounts|no authentication|has no login|does not authenticate|no credentials of its own|authentication:? none", corpus + hard_corpus, re.I)),
    }
    sig["advisory_signals"] = {
        "changelog_security_entries": bool(re.search(r"(?im)^.*\b(security|cve-\d{4}-\d+|vulnerab|ghsa-)", changelog)),
        "security_md_describes_disclosure": bool(sec_path and re.search(r"advisor|publish|disclos|announce", read_text(os.path.join(root, sec_path)), re.I)),
    }
    return sig


def scan_git(root):
    if not shutil.which("git") or not os.path.isdir(os.path.join(root, ".git")):
        return {"status": "not_a_git_checkout"}
    out = {"status": "ok"}
    code, tags, _ = run(["git", "tag", "--sort=-creatordate"], cwd=root)
    tag_list = [t for t in tags.split() if t] if code == 0 else []
    out["tag_count"] = len(tag_list)
    out["latest_tag"] = tag_list[0] if tag_list else None
    out["latest_tag_signed"] = None
    if tag_list:
        code, body, _ = run(["git", "cat-file", "-p", tag_list[0]], cwd=root)
        if code == 0:
            out["latest_tag_signed"] = "BEGIN PGP SIGNATURE" in body or "BEGIN SSH SIGNATURE" in body
    code, sigflag, _ = run(["git", "log", "-1", "--format=%G?"], cwd=root)
    out["head_commit_signed"] = (sigflag.strip() not in ("", "N")) if code == 0 else None
    code, cnt, _ = run(["git", "rev-list", "--count", "--since=90.days", "HEAD"], cwd=root)
    out["commits_last_90_days"] = int(cnt.strip()) if code == 0 and cnt.strip().isdigit() else None
    code, shallow, _ = run(["git", "rev-parse", "--is-shallow-repository"], cwd=root)
    out["shallow"] = shallow.strip() == "true"
    return out


def doc_revision_count(root, relpath):
    if not shutil.which("git") or not os.path.isdir(os.path.join(root, ".git")):
        return None
    code, out, _ = run(["git", "log", "--oneline", "--", relpath], cwd=root)
    return len([l for l in out.splitlines() if l.strip()]) if code == 0 else None


# ----------------------------------------------------------------------------- check mapping

AUTO_ITEMS = {"D2", "D3", "D4", "R1", "R2", "P2", "P7"}
GATES = {"F1", "B1", "B2", "B3", "B9", "D3", "D4", "R1", "R2", "R5", "R6", "R7", "R8", "R9", "R11", "R12", "P2", "P3", "P8"}
ITEM_NAMES = {
    "F1": "Documented secure development process", "F2": "Evidence the process is followed", "F3": "Secure-by-design/default addressed",
    "F4": "EU authorised representative (optional)", "B1": "Product classification", "B2": "Conformity assessment route",
    "B3": "Risk assessment", "B4": "Threat analysis", "B5": "Third-party component due diligence",
    "B6": "Component/runtime EOL considered", "B7": "Confidentiality of data", "B8": "Minimal attack surface",
    "B9": "No universal default credentials", "D1": "Security testing with retained results", "D2": "Process evidence from the repository",
    "D3": "Regular security testing and review", "D4": "Secure distribution of updates", "D5": "Data minimisation",
    "R1": "SBOM and no known exploitable vulns", "R2": "SBOM machine-readable", "R3": "Inbound interfaces documented",
    "R4": "Outbound connections documented", "R5": "Support period and end date", "R6": "Conformity assessment",
    "R7": "EU Declaration of Conformity", "R8": "CE marking", "R9": "Technical documentation", "R10": "Retention",
    "R11": "Information to the user (Annex II)", "R12": "Point of contact and CVD policy", "P1": "Risk assessment kept current",
    "P2": "Ongoing vulnerability identification", "P3": "24h early warning (vulnerability)", "P4": "72h notification",
    "P5": "14-day final report", "P6": "Severe incident reporting", "P7": "Remediation and delivery of updates",
    "P8": "Free updates, kept available", "P9": "End-of-support notification", "P10": "Corrective measures",
}
ITEM_ORDER = ["F1", "F2", "F3", "F4", "B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B9", "D1", "D2", "D3", "D4", "D5",
              "R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8", "R9", "R10", "R11", "R12", "P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8", "P9", "P10"]


def check(cid, status, evidence, hint=None, practices=None):
    """One checklist item.

    status/evidence/hint describe the CRA *baseline* layer (scored).
    practices is the *beyond the letter* layer (reported, never scored):
      list of {"name", "source", "adopted": True|False|None, "evidence"}.
    """
    return {
        "id": cid,
        "name": ITEM_NAMES[cid],
        "track": "AUTO" if cid in AUTO_ITEMS else "POLICY",
        "gate": cid in GATES,
        "status": status,
        "evidence": [e for e in evidence if e],
        "hint": hint,
        "practices": practices or [],
    }


def practice(name, source, adopted, evidence=None):
    return {"name": name, "source": source, "adopted": adopted, "evidence": [e for e in (evidence or []) if e]}


NO_REPO = "no_repo_evidence: absence in repo is not proof; confirm via intake before marking NOT_MET"
INTAKE = "intake_only: cannot be assessed from a repository"


def map_checks(files, api, git, org_security=None):
    """Preliminary baseline statuses + practice adoption from repo evidence only.

    Baseline rules follow the letter of Regulation (EU) 2024/2847 as set out in
    references/checklist.md (rubric 2026.09.1). Intake answers are applied by the agent.
    """
    c = {}
    f = files or {}
    a = api or {}
    g = git or {}
    have_files = bool(f)
    sec = (f.get("security_md") if have_files else None) or org_security or {}
    wf = f.get("workflow_tools", {}) if have_files else {}
    workflows = f.get("workflows", []) if have_files else []
    trig = f.get("workflow_triggers", {}) if have_files else {}
    docs = f.get("docs", {}) if have_files else {}
    comp = f.get("compliance_signals", {}) if have_files else {}
    sdl = f.get("sdl_signals", {}) if have_files else {}
    risk = f.get("risk_signals", {}) if have_files else {}
    tm = f.get("threat_model_signals", {}) if have_files else {}
    dep = f.get("dependency_policy_signals", {}) if have_files else {}
    sup = f.get("support_signals", {}) if have_files else {}
    ir = f.get("incident_signals", {}) if have_files else {}
    hard = f.get("hardening_signals", {}) if have_files else {}
    priv = f.get("privacy_signals", {}) if have_files else {}
    net = f.get("network_signals", {}) if have_files else {}
    tp = f.get("test_plan_signals", {}) if have_files else {}
    adv = f.get("advisory_signals", {}) if have_files else {}
    a2 = f.get("annex_ii_signals", {}) if have_files else {}
    bp = a.get("branch_protection", {})
    rel = a.get("releases", {})
    rel_assets = rel.get("assets", []) or []
    releases_known = rel.get("status") == "ok"
    has_releases = (rel.get("count") or 0) > 0 or (g.get("tag_count") or 0) > 0
    dep_alerts = a.get("dependabot_alerts", {}).get("enabled")
    pvr = a.get("private_vulnerability_reporting", {})
    advisories_published = a.get("security_advisories", {}).get("published")
    root = f.get("root") if have_files else None

    def rt(relpath):
        return read_text(os.path.join(root, relpath)) if root and relpath else ""

    def nofiles(cid):
        return check(cid, "UNKNOWN", [], "repository files not available")

    # ------------------------------------------------------------------ F1
    pr_f1 = [
        practice("Named phases with roles and owners", "SSDF PO.2", bool(sdl.get("has_roles")) if sdl.get("has_doc") else None),
        practice("Alignment with IEC 62443-4-1 / ISO 27001", "Matrix", bool(sdl.get("mentions_certification")) if have_files else None),
    ]
    if not have_files:
        c["F1"] = nofiles("F1")
    elif sdl.get("has_doc") and sdl.get("has_phases") and sdl.get("covers_vuln_handling"):
        c["F1"] = check("F1", "MET", docs.get("sdl", [])[:3], None, pr_f1)
    elif sdl.get("has_doc"):
        c["F1"] = check("F1", "PARTIAL", docs.get("sdl", [])[:3], "process document found but does not describe both development and vulnerability handling", pr_f1)
    elif f.get("key_files", {}).get("contributing") and re.search(r"security", rt(f["key_files"]["contributing"]), re.I):
        c["F1"] = check("F1", "PARTIAL", [f["key_files"]["contributing"]], "informal security guidance only", pr_f1)
    else:
        c["F1"] = check("F1", "UNKNOWN", [], NO_REPO, pr_f1)

    # ------------------------------------------------------------------ F2
    forms = []
    if trig.get("pull_request"):
        forms.append("CI on pull_request: " + ", ".join(trig["pull_request"][:3]))
    if f.get("pr_template_security_checklist"):
        forms.append("PR template security checklist: " + f["pr_template"])
    if bp.get("protected") and (bp.get("required_reviews") or 0) >= 1:
        forms.append("required reviews on {} ({})".format(bp.get("branch"), bp.get("required_reviews")))
    if sdl.get("release_signoff"):
        forms.append("release sign-off/review records referenced in process doc")
    pr_f2 = [
        practice("Two independent forms of evidence", "Practice", len(forms) >= 2 if have_files else None),
        practice("PR template with security checklist", "Practice", bool(f.get("pr_template_security_checklist")) if have_files else None),
        practice("Required code review before merge", "Scorecard Code-Review", (bool(bp.get("protected")) and (bp.get("required_reviews") or 0) >= 1) if bp.get("protected") is not None else None),
    ]
    if not have_files and not bp:
        c["F2"] = nofiles("F2")
    elif forms:
        c["F2"] = check("F2", "MET", forms, None, pr_f2)
    else:
        c["F2"] = check("F2", "UNKNOWN", [], NO_REPO + " (records may live outside the repo)", pr_f2)

    # ------------------------------------------------------------------ F3
    sbd = bool(sdl.get("secure_by_default") or risk.get("secure_by_default") or hard.get("has_doc"))
    asf = bool(risk.get("attack_surface") or tm.get("has_attack_surface") or (sdl.get("secure_by_default") and re.search(r"attack surface", "".join(rt(r) for r in docs.get("sdl", [])[:3]), re.I)))
    ev_f3 = (docs.get("sdl", [])[:2] + docs.get("risk_assessment", [])[:2] + docs.get("hardening", [])[:1]) if have_files else []
    pr_f3 = [practice("Default-configuration review step per release", "Practice", bool(sdl.get("release_signoff") and sbd) if sdl.get("has_doc") else None),
             practice("Published hardening guide", "ETSI EN 303 645 5.6", bool(hard.get("has_doc")) if have_files else None)]
    if not have_files:
        c["F3"] = nofiles("F3")
    elif sbd and asf:
        c["F3"] = check("F3", "MET", ev_f3, None, pr_f3)
    elif sbd or asf:
        c["F3"] = check("F3", "PARTIAL", ev_f3, "only one of secure-by-default / attack-surface limitation is addressed", pr_f3)
    elif sdl.get("has_doc") or risk.get("has_doc"):
        c["F3"] = check("F3", "NOT_MET", ev_f3, "process/risk documents exist but do not address Annex I Pt I(2)(b) and (j)", pr_f3)
    else:
        c["F3"] = check("F3", "UNKNOWN", [], NO_REPO, pr_f3)

    # ------------------------------------------------------------------ F4 (optional under Art. 18)
    c["F4"] = check("F4", "MET" if comp.get("authorised_representative") else "NA",
                    comp.get("docs", [])[:2] if comp.get("authorised_representative") else [],
                    "Art. 18(1): appointing a representative is optional; recorded for information" if comp.get("authorised_representative") else "Art. 18(1): optional ('may'); NA unless appointed. Recommended for non-EU manufacturers.",
                    [practice("Non-EU manufacturer appoints an EU representative", "Matrix", True if comp.get("authorised_representative") else None)])

    # ------------------------------------------------------------------ B1 / B2 (intake)
    c["B1"] = check("B1", "UNKNOWN", comp.get("docs", [])[:2] if comp.get("classification") else [],
                    INTAKE + ("; a document discusses classification" if comp.get("classification") else "") + ("; a scope decision document exists" if comp.get("scope_decision") else ""),
                    [practice("Written comparison against each Annex III/IV category", "Practice", bool(comp.get("classification")) if have_files else None)])
    c["B2"] = check("B2", "UNKNOWN", comp.get("docs", [])[:2] if comp.get("conformity_route") else [],
                    INTAKE + ("; a document discusses the conformity route" if comp.get("conformity_route") else ""),
                    [practice("Early contact with a Notified Body (Class I+)", "Practice", None)])

    # ------------------------------------------------------------------ B3
    pr_b3 = [practice("Likelihood/impact ratings", "Practice (ISO 27005)", bool(risk.get("has_ratings")) if risk.get("has_doc") else None),
             practice("Asset/threat/control table", "Practice", bool(risk.get("has_mitigations") and risk.get("identifies_threats")) if risk.get("has_doc") else None)]
    if not have_files:
        c["B3"] = nofiles("B3")
    elif risk.get("has_doc") and risk.get("use_context") and risk.get("maps_annex_i"):
        c["B3"] = check("B3", "MET", docs["risk_assessment"][:3], None, pr_b3)
    elif risk.get("has_doc"):
        missing = [x for x, ok in (("intended purpose / foreseeable use / conditions of use", risk.get("use_context")), ("mapping to Annex I Pt I(2)(a)-(m)", risk.get("maps_annex_i"))) if not ok]
        c["B3"] = check("B3", "PARTIAL", docs["risk_assessment"][:3], "risk document lacks: " + "; ".join(missing), pr_b3)
    else:
        c["B3"] = check("B3", "UNKNOWN", [], NO_REPO, pr_b3)

    # ------------------------------------------------------------------ B4
    pr_b4 = [practice("Named methodology (STRIDE/PASTA/LINDDUN)", "Matrix; SSDF PW.1", bool(tm.get("method_named")) if (tm.get("has_doc") or risk.get("has_doc")) else None),
             practice("Data-flow diagram with trust boundaries", "Practice", bool(tm.get("has_attack_surface")) if tm.get("has_doc") else None)]
    ev_b4 = (docs.get("threat_model", [])[:2] + docs.get("risk_assessment", [])[:2]) if have_files else []
    if not have_files:
        c["B4"] = nofiles("B4")
    elif (tm.get("has_doc") and tm.get("has_threats")) or (risk.get("has_doc") and risk.get("identifies_threats") and (risk.get("attack_surface") or tm.get("has_attack_surface"))):
        c["B4"] = check("B4", "MET", ev_b4, None, pr_b4)
    elif tm.get("has_doc") or (risk.get("has_doc") and risk.get("identifies_threats")):
        c["B4"] = check("B4", "PARTIAL", ev_b4, "threats mentioned but attack surface not identified", pr_b4)
    else:
        c["B4"] = check("B4", "UNKNOWN", [], NO_REPO, pr_b4)

    # ------------------------------------------------------------------ B5
    dep_review = wf.get("dependency_review", [])
    pr_b5 = [practice("License allow-list", "OSPS", bool(dep.get("covers_selection") and re.search(r"licen[cs]e", "".join(rt(r) for r in docs.get("dependency_policy", [])[:3]), re.I)) if dep.get("has_doc") else None),
             practice("dependency-review gate on pull requests", "GitHub", bool(dep_review) if have_files else None)]
    if not have_files:
        c["B5"] = nofiles("B5")
    elif dep.get("has_doc") and dep.get("covers_selection") and dep.get("covers_vuln_response") and dep.get("covers_upstream_reporting"):
        c["B5"] = check("B5", "MET", docs["dependency_policy"][:3] + dep_review[:1], None, pr_b5)
    elif dep.get("has_doc") or dep_review:
        missing = [x for x, ok in (("selection criteria", dep.get("covers_selection")), ("vulnerability response", dep.get("covers_vuln_response")), ("upstream reporting (Art. 13(6))", dep.get("covers_upstream_reporting"))) if not ok]
        c["B5"] = check("B5", "PARTIAL", docs.get("dependency_policy", [])[:3] + dep_review[:1], ("undocumented: enforcement gate only" if not dep.get("has_doc") else "policy lacks: " + "; ".join(missing)), pr_b5)
    else:
        c["B5"] = check("B5", "UNKNOWN", [], NO_REPO, pr_b5)

    # ------------------------------------------------------------------ B6 (POLICY at baseline)
    locks, pins, manifests = (f.get("lockfiles", []), f.get("runtime_pins", []), f.get("manifests", [])) if have_files else ([], [], [])
    unpinned = f.get("docker_unpinned_base", []) if have_files else []
    eol_tools = wf.get("eol", []) if have_files else []
    pr_b6 = [practice("Lockfiles committed", "Scorecard Pinned-Dependencies", bool(locks) if (manifests or locks) else None),
             practice("Runtime versions pinned", "Practice", bool(pins) if have_files else None),
             practice("Base images pinned (no :latest)", "SLSA", (not unpinned) if f.get("dockerfiles") else None),
             practice("Scheduled EOL tooling (endoflife.date / xeol)", "Practice", bool(eol_tools) if have_files else None)]
    if not have_files:
        c["B6"] = nofiles("B6")
    elif sup.get("component_eol_considered") or dep.get("covers_eol") or eol_tools:
        c["B6"] = check("B6", "MET", (docs.get("support_policy", [])[:1] if sup.get("component_eol_considered") else []) + (docs.get("dependency_policy", [])[:1] if dep.get("covers_eol") else []) + eol_tools[:2], None, pr_b6)
    elif locks or pins:
        c["B6"] = check("B6", "PARTIAL", locks[:3] + pins[:3], "dependencies pinned but component/runtime EOL not recorded in the support-period reasoning (Art. 13(8), Annex VII(4))", pr_b6)
    elif not manifests:
        c["B6"] = check("B6", "UNKNOWN", [], "no dependency manifests detected; confirm the stack and whether component EOL was considered", pr_b6)
    else:
        c["B6"] = check("B6", "UNKNOWN", manifests[:3], NO_REPO, pr_b6)

    # ------------------------------------------------------------------ B7 (intake)
    c["B7"] = check("B7", "UNKNOWN", [], INTAKE + "; NA if the product stores/transmits no data", [practice("Hardware-backed key storage", "ETSI EN 303 645 5.4", None)])

    # ------------------------------------------------------------------ B8
    low_expose = bool(f.get("dockerfiles")) and f.get("docker_expose_total", 0) <= 2 if have_files else False
    documented = bool(hard.get("has_doc") or risk.get("attack_surface") or net.get("inbound_documented"))
    pr_b8 = [practice("Every interface individually justified", "Matrix", bool(net.get("inbound_justified")) if have_files else None),
             practice("Published hardening guide", "ETSI EN 303 645 5.6", bool(hard.get("has_doc")) if have_files else None)]
    if not have_files:
        c["B8"] = nofiles("B8")
    elif documented and (low_expose or not f.get("dockerfiles")):
        c["B8"] = check("B8", "MET", docs.get("hardening", [])[:2] + docs.get("risk_assessment", [])[:1] + docs.get("network", [])[:1] + (["Dockerfile EXPOSE count: {}".format(f["docker_expose_total"])] if f.get("dockerfiles") else []), None, pr_b8)
    elif documented or low_expose:
        c["B8"] = check("B8", "PARTIAL", docs.get("hardening", [])[:2] + docs.get("network", [])[:1], "documentation or minimal configuration found, not both", pr_b8)
    else:
        c["B8"] = check("B8", "UNKNOWN", [], NO_REPO, pr_b8)

    # ------------------------------------------------------------------ B9
    hits = f.get("default_credential_hits", []) if have_files else []
    secrets_ci = wf.get("secrets", []) if have_files else []
    gh_secret_scan = a.get("repo_meta", {}).get("secret_scanning") == "enabled"
    pr_b9 = [practice("Secret scanning in CI or platform", "GitHub; Scorecard", bool(secrets_ci or gh_secret_scan) if (have_files or a) else None),
             practice("Per-device unique credentials / forced first-use setup", "ETSI EN 303 645 5.1-1", bool(hard.get("first_run_credentials")) if have_files else None)]
    if not have_files:
        c["B9"] = nofiles("B9")
    elif hits and hard.get("first_run_credentials"):
        c["B9"] = check("B9", "PARTIAL", hits[:10], "default-looking credentials found, but a first-use credential change is documented", pr_b9)
    elif hits:
        c["B9"] = check("B9", "NOT_MET", hits[:10], "default-looking credentials in configuration; verify each hit (may be test fixtures)", pr_b9)
    elif hard.get("no_authentication"):
        c["B9"] = check("B9", "NA", ["docs state the product has no authentication"], None, pr_b9)
    elif hard.get("first_run_credentials"):
        c["B9"] = check("B9", "MET", ["no default credentials detected in configuration", "first-use credential setup documented"], None, pr_b9)
    else:
        c["B9"] = check("B9", "PARTIAL", ["no default credentials detected in configuration"], "confirm whether the product has accounts and how first credentials are set; NA if no authentication", pr_b9)

    # ------------------------------------------------------------------ D1
    tests_in_ci = bool(wf.get("tests"))
    sec_tests = f.get("security_test_files", []) if have_files else []
    pr_d1 = [practice("Written security test plan covering auth, access control, input validation, crypto, error handling", "Matrix; SSDF PW.8", (tp.get("covers_areas", 0) >= 3) if tp.get("has_doc") else (False if have_files else None))]
    if not have_files:
        c["D1"] = nofiles("D1")
    elif tests_in_ci and (sec_tests or wf.get("sast") or tp.get("has_doc")):
        c["D1"] = check("D1", "MET", wf["tests"][:2] + sec_tests[:3] + docs.get("test_plan", [])[:1], None, pr_d1)
    elif tests_in_ci or f.get("test_dirs") or tp.get("has_doc"):
        c["D1"] = check("D1", "PARTIAL", wf.get("tests", [])[:2] + docs.get("test_plan", [])[:1] + (["test dirs: " + ", ".join(f["test_dirs"][:5])] if f.get("test_dirs") else []), "tests exist but are not evidently security-focused, or results are not retained in CI", pr_d1)
    elif wf.get("sast"):
        c["D1"] = check("D1", "PARTIAL", wf["sast"][:2], "static analysis only; no functional security tests (authentication, access control, input handling) found", pr_d1)
    else:
        c["D1"] = check("D1", "UNKNOWN", [], NO_REPO, pr_d1)

    # ------------------------------------------------------------------ D2 (AUTO)
    ci_on_pr = bool(trig.get("pull_request"))
    bp_readable = bp.get("protected") is not None
    pr_d2 = [practice("Protected default branch, force-push blocked", "Scorecard Branch-Protection", (bool(bp.get("protected")) and bp.get("allow_force_pushes") is False) if bp_readable else None),
             practice("Required status checks before merge", "Scorecard Branch-Protection", bool(bp.get("required_status_checks")) if bp_readable else None),
             practice("At least one required review (solo maintainers: document an exception)", "Scorecard Code-Review", ((bp.get("required_reviews") or 0) >= 1) if bp_readable else None),
             practice("Signed commits or tags", "Scorecard Signed-Releases", bool(g.get("latest_tag_signed") or g.get("head_commit_signed") or bp.get("required_signatures")) if (g.get("status") == "ok" or bp_readable) else None)]
    if not have_files and not bp:
        c["D2"] = nofiles("D2")
    elif ci_on_pr:
        c["D2"] = check("D2", "MET", ["CI on pull_request: " + ", ".join(trig["pull_request"][:3])] + (["branch protection on {}".format(bp["branch"])] if bp.get("protected") else []), None, pr_d2)
    elif workflows:
        c["D2"] = check("D2", "PARTIAL", ["workflows present but none trigger on pull_request: " + ", ".join(workflows[:3])], "checks do not run on every change", pr_d2)
    elif bp.get("protected"):
        c["D2"] = check("D2", "PARTIAL", ["branch protection on {}".format(bp["branch"])], "protection without CI leaves no retained check records", pr_d2)
    else:
        c["D2"] = check("D2", "UNKNOWN", [], NO_REPO + " (review/release records may live outside the repo)", pr_d2)

    # ------------------------------------------------------------------ D3 (AUTO)
    sast = list(wf.get("sast", [])) if have_files else []
    if a.get("code_scanning_default_setup", {}).get("state") == "configured":
        sast.append("code scanning default setup: configured")
    elif a.get("code_scanning_analyses", {}).get("present"):
        sast.append("code scanning analyses present")
    secrets = list(secrets_ci) + (["GitHub secret scanning: enabled"] if gh_secret_scan else [])
    dast = wf.get("dast", []) if have_files else []
    vuln_ci = wf.get("vuln_scan", []) if have_files else []
    pentest_docs = docs.get("pentest", []) if have_files else []
    regular = [x for x in (sast + secrets + dast + vuln_ci) if x]
    pr_d3 = [practice("SAST in CI", "Scorecard SAST", bool(sast) if (workflows or a) else None),
             practice("Secret scanning", "GitHub", bool(secrets) if (workflows or a) else None),
             practice("DAST", "Practice", bool(dast) if workflows else None),
             practice("Independent penetration test within 12 months", "Matrix; Practice", bool(pentest_docs) if have_files else None),
             practice("Fuzzing", "Scorecard Fuzzing", bool(re.search(r"fuzz", " ".join(workflows), re.I)) if workflows else None)]
    if not have_files and not a:
        c["D3"] = nofiles("D3")
    elif regular:
        c["D3"] = check("D3", "MET", regular[:4] + pentest_docs[:1], None, pr_d3)
    elif pentest_docs:
        c["D3"] = check("D3", "PARTIAL", pentest_docs[:2], "one-off test evidence only; Annex I Pt II(3) requires regular testing", pr_d3)
    elif workflows:
        c["D3"] = check("D3", "NOT_MET", ["workflows present: {}".format(len(workflows))], "no recurring security testing found", pr_d3)
    else:
        c["D3"] = check("D3", "UNKNOWN", [], "no workflows readable; recurring manual review may exist (intake)", pr_d3)

    # ------------------------------------------------------------------ D4 (AUTO)
    sig_assets = [x for x in rel_assets if SIG_ASSET_RE.search(x)]
    sum_assets = [x for x in rel_assets if CHECKSUM_ASSET_RE.search(x)]
    signing = (wf.get("signing", []) + wf.get("trusted_publishing", []) if have_files else []) + sig_assets
    if g.get("latest_tag_signed"):
        signing.append("latest tag signed: " + str(g.get("latest_tag")))
    checks_only = (wf.get("checksums", []) if have_files else []) + sum_assets
    readme_txt = rt(f.get("key_files", {}).get("readme")) if have_files else ""
    install_doc = bool(re.search(r"install|upgrade|updat|how to (get|apply) (the )?(latest|update|release)", readme_txt + corpus_or_empty(f), re.I))
    verify_doc = bool(re.search(r"verify|signature|checksum|provenance|cosign|attestation", readme_txt, re.I))
    signing_txt = "".join(rt(w) for w in (wf.get("signing", []) + wf.get("trusted_publishing", []) if have_files else [])) + " ".join(sig_assets)
    pr_d4 = [practice("Build provenance attestation", "SLSA L2+; Scorecard Signed-Releases", bool(re.search(r"attest|slsa|provenance|intoto", signing_txt, re.I)) if (workflows or releases_known) else None),
             practice("Sigstore/cosign signing", "Practice", bool(re.search(r"cosign|sigstore", signing_txt, re.I)) if (workflows or releases_known) else None),
             practice("Verification steps documented for users", "Practice", verify_doc if readme_txt else None)]
    if not have_files and not a:
        c["D4"] = nofiles("D4")
    elif signing and install_doc:
        c["D4"] = check("D4", "MET", signing[:4] + ["install/update instructions in docs"], None, pr_d4)
    elif signing:
        c["D4"] = check("D4", "PARTIAL", signing[:4], "artefacts protected but no install/update instructions (Annex II(8)(c))", pr_d4)
    elif checks_only:
        c["D4"] = check("D4", "PARTIAL", checks_only[:4], "checksums only; authenticity not verifiable (Annex I Pt II(7))", pr_d4)
    elif has_releases:
        c["D4"] = check("D4", "NOT_MET", ["releases/tags exist: {}".format(rel.get("latest_tag") or g.get("latest_tag"))], "releases are unsigned and no provenance is generated", pr_d4)
    elif releases_known or g.get("status") == "ok":
        c["D4"] = check("D4", "NOT_MET", [], "no releases or tags; no update distribution path evidenced", pr_d4)
    else:
        c["D4"] = check("D4", "UNKNOWN", [], "release data not readable", pr_d4)

    # ------------------------------------------------------------------ D5
    pr_d5 = [practice("Telemetry opt-in rather than opt-out", "Practice", bool(priv.get("telemetry_opt_in_or_off")) if (priv.get("has_doc") or f.get("telemetry_libs")) else None),
             practice("Data inventory with retention periods", "Practice (GDPR)", bool(priv.get("data_inventory") and re.search(r"retention|retain|how long", "".join(rt(r) for r in docs.get("privacy", [])[:3]), re.I)) if priv.get("has_doc") else None)]
    if not have_files:
        c["D5"] = nofiles("D5")
    elif (priv.get("has_doc") or priv.get("data_inventory")) and not (f.get("telemetry_libs") and not priv.get("has_doc")):
        c["D5"] = check("D5", "MET", docs.get("privacy", [])[:3] or [f["key_files"]["readme"]], None if priv.get("has_doc") else "data handling described in README; a dedicated note is clearer", pr_d5)
    elif f.get("telemetry_libs"):
        c["D5"] = check("D5", "NOT_MET", ["telemetry/analytics libraries in manifests: " + ", ".join(f["telemetry_libs"][:5])], "data collection libraries present with no documentation of what is processed and why", pr_d5)
    else:
        c["D5"] = check("D5", "UNKNOWN", [], NO_REPO, pr_d5)

    # ------------------------------------------------------------------ R1 / R2 (AUTO)
    sbom_ci = wf.get("sbom", []) if have_files else []
    sbom_assets = [x for x in rel_assets if SBOM_FILE_RE.search(x)]
    sbom_files = f.get("sbom_files", [])[:3] if have_files else []
    dg = a.get("dependency_graph", {}).get("enabled")
    gen = sbom_ci + sbom_assets + sbom_files
    scan = vuln_ci + (["Dependabot alerts enabled"] if dep_alerts else [])
    pr_r1 = [practice("SBOM generated in CI for every release and attached as an asset", "OSPS; Practice", (bool(sbom_ci and sbom_assets) if releases_known else (None if sbom_ci else False)) if workflows else None),
             practice("Scan gate fails the build on known vulnerabilities", "Practice", bool(vuln_ci and re.search(r"fail-build:\s*true|--fail|exit-code:? ?1|fail-on", "".join(rt(w) for w in vuln_ci), re.I)) if vuln_ci else (False if workflows else None)),
             practice("VEX statements for non-exploitable findings", "Practice", bool(re.search(r"\bvex\b|openvex", " ".join(rel_assets + workflows), re.I)) if (workflows or releases_known) else None)]
    if not have_files and not a:
        c["R1"] = nofiles("R1")
        c["R2"] = nofiles("R2")
    else:
        if gen and scan:
            c["R1"] = check("R1", "MET", gen[:4] + scan[:3], None, pr_r1)
        elif gen or scan or dg:
            c["R1"] = check("R1", "PARTIAL", gen[:4] + scan[:3] + (["dependency graph enabled"] if dg else []), "missing: " + ", ".join(x for x, ok in (("SBOM for the released version", gen), ("pre-release check for known exploitable vulnerabilities", scan)) if not ok), pr_r1)
        elif workflows or releases_known:
            c["R1"] = check("R1", "NOT_MET", [], "no SBOM and no vulnerability check found", pr_r1)
        else:
            c["R1"] = check("R1", "UNKNOWN", [], "workflows and releases not readable", pr_r1)
        fmt = (wf.get("sbom_format", []) if have_files else []) + sbom_assets + sbom_files
        pr_r2 = [practice("Component hashes and licenses included (NTIA minimum elements)", "Practice", None)]
        if fmt:
            c["R2"] = check("R2", "MET", fmt[:5], None, pr_r2)
        elif gen:
            c["R2"] = check("R2", "PARTIAL", gen[:4], "SBOM produced but SPDX/CycloneDX format not confirmed", pr_r2)
        elif c["R1"]["status"] == "UNKNOWN":
            c["R2"] = check("R2", "UNKNOWN", [], "follows R1", pr_r2)
        else:
            c["R2"] = check("R2", "NOT_MET", [], "no SBOM (follows R1)", pr_r2)

    # ------------------------------------------------------------------ R3 / R4
    cfg_ports = ((f.get("docker_expose_total", 0) + f.get("compose_ports", 0)) > 0) if have_files else False
    pr_r3 = [practice("Per-interface justification and default on/off", "Matrix", bool(net.get("inbound_justified")) if have_files else None)]
    pr_r4 = [practice("Each destination justified; third-party library egress audited", "Matrix", None)]
    ev_net = (docs.get("network", [])[:2] + docs.get("hardening", [])[:1] + docs.get("risk_assessment", [])[:1]) if have_files else []
    if not have_files:
        c["R3"] = nofiles("R3")
        c["R4"] = nofiles("R4")
    else:
        if net.get("inbound_documented"):
            c["R3"] = check("R3", "MET", ev_net or [f["key_files"].get("readme", "README")], None, pr_r3)
        elif cfg_ports:
            c["R3"] = check("R3", "PARTIAL", ["Dockerfile EXPOSE: {}".format(f["docker_expose_total"]), "compose ports: {}".format(f["compose_ports"])], "listeners visible in configuration but not documented", pr_r3)
        else:
            c["R3"] = check("R3", "UNKNOWN", [], NO_REPO + "; NA if the product opens no listening ports", pr_r3)
        if net.get("outbound_documented"):
            c["R4"] = check("R4", "MET", ev_net or [f["key_files"].get("readme", "README")], None, pr_r4)
        elif priv.get("has_doc"):
            c["R4"] = check("R4", "PARTIAL", docs["privacy"][:2], "telemetry documented; other outbound connections not", pr_r4)
        else:
            c["R4"] = check("R4", "UNKNOWN", [], NO_REPO, pr_r4)

    # ------------------------------------------------------------------ R5 / P8 / P9
    sup_ev = ((docs.get("support_policy", [])[:3]) + ([f["key_files"]["support_md"]] if f.get("key_files", {}).get("support_md") else []) + ([sec["path"]] if sec.get("has_supported_versions") and sec.get("path") else [])) if have_files else ([sec["path"]] if sec.get("path") else [])
    has_dates = bool(sup.get("has_dates") or sec.get("has_dates"))
    has_sup = bool(sup.get("has_support_doc") or sec.get("has_supported_versions"))
    pr_r5 = [practice("Per-version support table", "Practice", bool(sup.get("supported_versions_table")) if has_sup else None),
             practice("Support period cross-checked against dependency EOL", "Practice", bool(sup.get("component_eol_considered")) if has_sup else None)]
    if not have_files and not sec:
        for cid in ("R5", "P8", "P9"):
            c[cid] = nofiles(cid)
    else:
        if has_sup and has_dates and sup.get("has_reasoning"):
            c["R5"] = check("R5", "MET", sup_ev, None, pr_r5)
        elif has_sup and has_dates:
            c["R5"] = check("R5", "PARTIAL", sup_ev, "end date published but the reasoning behind the support period is not recorded (Art. 13(8), Annex VII(4))", pr_r5)
        elif has_sup:
            c["R5"] = check("R5", "PARTIAL", sup_ev, "supported-versions information without a dated end of support (Art. 13(19))", pr_r5)
        else:
            c["R5"] = check("R5", "UNKNOWN", [], NO_REPO, pr_r5)
        pr_p8 = [practice("Stated in terms of sale as well as in docs", "Practice", None)]
        if sup.get("free_security_updates") and sup.get("updates_kept_available"):
            c["P8"] = check("P8", "MET", sup_ev, None, pr_p8)
        elif sup.get("free_security_updates"):
            c["P8"] = check("P8", "PARTIAL", sup_ev, "free updates stated; availability of each update for 10 years / rest of support period (Art. 13(9)) not stated", pr_p8)
        elif sup_ev:
            c["P8"] = check("P8", "PARTIAL", sup_ev, "support policy does not state that security updates are free (Annex I Pt II(8))", pr_p8)
        else:
            c["P8"] = check("P8", "UNKNOWN", [], NO_REPO, pr_p8)
        pr_p9 = [practice("Announce end of support at least 12 months ahead", "Matrix", bool(sup.get("twelve_month_notice")) if has_sup else None),
                 practice("In-product end-of-support banner", "Practice", None)]
        if has_dates and (sup.get("eol_notification") or sup.get("twelve_month_notice")):
            c["P9"] = check("P9", "MET", sup_ev, None, pr_p9)
        elif has_dates:
            c["P9"] = check("P9", "PARTIAL", sup_ev, "end date published; no commitment to notify users at end of support (Art. 13(19))", pr_p9)
        elif sup_ev:
            c["P9"] = check("P9", "PARTIAL", sup_ev, "no end date and no notification commitment", pr_p9)
        else:
            c["P9"] = check("P9", "UNKNOWN", [], NO_REPO, pr_p9)

    # ------------------------------------------------------------------ R6 / R7 / R8 / R9 / R10
    c["R6"] = check("R6", "UNKNOWN", comp.get("docs", [])[:2] if comp.get("conformity_route") else [], INTAKE, [practice("Third-party review of a Module A self-assessment", "Practice", None)])
    c["R7"] = check("R7", "PARTIAL" if comp.get("declaration_of_conformity") else "UNKNOWN",
                    comp.get("docs", [])[:2] if comp.get("declaration_of_conformity") else [],
                    "a document references a DoC; signature and Annex V content cannot be verified from the repo" if comp.get("declaration_of_conformity") else (NO_REPO if have_files else "repository files not available"),
                    [practice("DoC published at a stable URL", "Practice", bool(a2.get("6_doc_url")) if have_files else None)])
    c["R8"] = check("R8", "UNKNOWN", comp.get("docs", [])[:2] if comp.get("ce_marking") else [], INTAKE + ("; a document mentions CE marking" if comp.get("ce_marking") else "") + "; for software the mark goes on the DoC or the website (Art. 30(1))", [practice("CE mark also shown in the product's about screen", "Practice", None)])
    c["R9"] = check("R9", "PARTIAL" if comp.get("technical_file") else "UNKNOWN",
                    comp.get("docs", [])[:2] if comp.get("technical_file") else [],
                    "technical file referenced; verify every Annex VII(1)-(8) element is present" if comp.get("technical_file") else (NO_REPO if have_files else "repository files not available"),
                    [practice("Version-controlled technical-file index with links", "Practice", bool(comp.get("technical_file")) if have_files else None)])
    pr_r10 = [practice("Every SBOM version archived", "Matrix", bool(sbom_assets) if releases_known else None),
              practice("Off-platform mirror of documentation and artefacts", "Practice", None)]
    if not have_files and not a:
        c["R10"] = nofiles("R10")
    elif comp.get("retention") or sup.get("updates_kept_available"):
        c["R10"] = check("R10", "MET", (comp.get("docs", [])[:2] if comp.get("retention") else []) + (sup_ev[:1] if sup.get("updates_kept_available") else []), None, pr_r10)
    elif sbom_assets or has_releases:
        c["R10"] = check("R10", "PARTIAL", sbom_assets[:2] or ["releases retained on GitHub"], "artefacts retained by default but no retention commitment (Art. 13(13): 10 years or support period, whichever is longer)", pr_r10)
    else:
        c["R10"] = check("R10", "UNKNOWN", [], NO_REPO, pr_r10)

    # ------------------------------------------------------------------ R11 (repo) Annex II
    pr_r11 = [practice("Single 'Security' page grouping the Annex II content", "Practice", bool(hard.get("has_doc") or re.search(r"(?im)^#+\s*security", readme_txt)) if readme_txt else None),
              practice("security.txt", "RFC 9116", bool(f.get("security_txt")) if have_files else None)]
    if not have_files or not f.get("key_files", {}).get("readme"):
        c["R11"] = check("R11", "UNKNOWN", [], "README not readable", pr_r11)
    else:
        mandatory = {k: v for k, v in a2.items() if not k.startswith("6_")}
        present = [k for k, v in mandatory.items() if v]
        missing = [k for k, v in mandatory.items() if not v]
        st = "MET" if len(present) == len(mandatory) else ("PARTIAL" if len(present) >= 4 else "NOT_MET")
        c["R11"] = check("R11", st, ["Annex II points present: " + ", ".join(present)], ("missing Annex II points: " + ", ".join(missing) + ("; point 6 (DoC URL) applies once a DoC exists" if not a2.get("6_doc_url") else "")) if missing else None, pr_r11)

    # ------------------------------------------------------------------ R12 (repo)
    pr_r12 = [practice("Response-time commitment", "Practice (ISO 29147)", bool(sec.get("has_response_time")) if sec else None),
              practice("GitHub private vulnerability reporting enabled", "GitHub", pvr.get("enabled") if pvr.get("enabled") is not None else None),
              practice(".well-known/security.txt", "RFC 9116", bool(f.get("security_txt")) if have_files else None),
              practice("PGP key for encrypted reports", "Practice", bool(sec.get("mentions_encryption")) if sec else None)]
    if not have_files and not a and not sec:
        c["R12"] = nofiles("R12")
    elif sec.get("has_contact") and sec.get("mentions_cvd_policy"):
        c["R12"] = check("R12", "MET", [sec.get("path")] + (["private vulnerability reporting: enabled"] if pvr.get("enabled") else []), None, pr_r12)
    elif sec.get("has_contact"):
        c["R12"] = check("R12", "PARTIAL", [sec.get("path")], "contact published but no coordinated vulnerability disclosure policy text (Annex I Pt II(5), Annex II(2))", pr_r12)
    elif pvr.get("enabled") is True:
        c["R12"] = check("R12", "PARTIAL", ["private vulnerability reporting: enabled"], "reporting channel exists but no SECURITY.md naming the contact and policy; Art. 13(17) says users may not be limited to automated tools", pr_r12)
    elif have_files or org_security is not None:
        c["R12"] = check("R12", "NOT_MET", [], "no published vulnerability contact (repo or org-level)", pr_r12)
    else:
        c["R12"] = check("R12", "UNKNOWN", [], "files not readable", pr_r12)

    # ------------------------------------------------------------------ P1
    pr_p1 = [practice("Explicit review triggers (major change, new threat, exploited vulnerability)", "Matrix", bool(re.search(r"trigger", "".join(rt(r) for r in docs.get("risk_assessment", [])[:2]), re.I)) if risk.get("has_doc") else None),
             practice("Reviewed at every release", "Practice", None)]
    if not have_files:
        c["P1"] = nofiles("P1")
    elif risk.get("has_doc"):
        revs = doc_revision_count(root, docs["risk_assessment"][0])
        if risk.get("has_history_section") or (revs or 0) >= 2:
            c["P1"] = check("P1", "MET", docs["risk_assessment"][:2] + (["git revisions: {}".format(revs)] if revs else []), None, pr_p1)
        else:
            c["P1"] = check("P1", "PARTIAL", docs["risk_assessment"][:2], "risk assessment has neither an update rule nor update history (Art. 13(3), 13(7))", pr_p1)
    else:
        c["P1"] = check("P1", "UNKNOWN", [], NO_REPO, pr_p1)

    # ------------------------------------------------------------------ P2 (AUTO)
    cfg = [x for x in (f.get("dependabot_config"), f.get("renovate_config")) if x] if have_files else []
    scheduled_scan = [w for w in vuln_ci if w in trig.get("schedule", [])]
    mech = (["Dependabot alerts enabled"] if dep_alerts else []) + cfg + scheduled_scan
    pr_p2 = [practice("Automated alerts plus a scheduled scan against live feeds", "Matrix; OSPS", len(mech) >= 2 if (have_files or dep_alerts is not None) else None),
             practice("Daily or better scan frequency", "Practice", bool(re.search(r"cron:\s*['\"]?\S+\s+\S+\s+\*\s+\*\s+\*", "".join(rt(w) for w in scheduled_scan))) if scheduled_scan else (False if have_files else None))]
    if not have_files and not a:
        c["P2"] = nofiles("P2")
    elif mech:
        c["P2"] = check("P2", "MET", mech[:5], None if dep_alerts is not None or len(mech) >= 2 else "Dependabot alert setting not readable; config present", pr_p2)
    elif dep_alerts is None and have_files:
        c["P2"] = check("P2", "UNKNOWN", [], "no monitoring config found and Dependabot alert setting not readable (needs admin token); a documented recurring manual review would also satisfy the baseline (intake)", pr_p2)
    else:
        c["P2"] = check("P2", "NOT_MET", [], "no vulnerability-identification process found for shipped components", pr_p2)

    # ------------------------------------------------------------------ P3-P6, P10
    ir_docs = docs.get("incident_response", [])[:3] if have_files else []
    pr_p3 = [practice("Named on-call owner and backup", "Practice", bool(ir.get("named_owner")) if ir.get("has_doc") else None),
             practice("Pre-registered on the ENISA single reporting platform", "Practice", None),
             practice("Report templates for 24h/72h/final", "Practice", bool(ir.get("content_72h") and ir.get("content_final")) if ir.get("has_doc") else None)]
    if not have_files:
        for cid in ("P3", "P4", "P5", "P6", "P10"):
            c[cid] = nofiles(cid)
    elif ir.get("has_doc"):
        route = bool(ir.get("mentions_enisa") or ir.get("mentions_csirt"))
        p3_ok = route and ir.get("mentions_24h") and ir.get("informs_users")
        c["P3"] = check("P3", "MET" if p3_ok else "PARTIAL", ir_docs, None if p3_ok else "procedure lacks: " + ", ".join(x for x, ok in (("ENISA/CSIRT reporting route", route), ("24h early warning", ir.get("mentions_24h")), ("informing users (Art. 14(8))", ir.get("informs_users")), ("definition of actively exploited (Art. 3(42))", ir.get("defines_actively_exploited"))) if not ok), pr_p3)
        p4_ok = ir.get("mentions_72h") and ir.get("content_72h")
        c["P4"] = check("P4", "MET" if p4_ok else "PARTIAL", ir_docs, None if p4_ok else ("72h step present without its content (Art. 14(2)(b))" if ir.get("mentions_72h") else "no 72h notification step"), [practice("72h report template", "Practice", bool(p4_ok) if ir.get("has_doc") else None)])
        p5_ok = ir.get("mentions_14_days") and ir.get("content_final")
        c["P5"] = check("P5", "MET" if p5_ok else "PARTIAL", ir_docs, None if p5_ok else ("14-day step present without its content (Art. 14(2)(c))" if ir.get("mentions_14_days") else "no 14-day final report step"), [])
        p6_ok = ir.get("covers_incidents") and ir.get("severity_criteria") and ir.get("mentions_one_month")
        c["P6"] = check("P6", "MET" if p6_ok else "PARTIAL", ir_docs, None if p6_ok else "incident coverage lacks: " + ", ".join(x for x, ok in (("severe-incident criteria (Art. 14(5))", ir.get("severity_criteria")), ("one-month final report (Art. 14(4)(c))", ir.get("mentions_one_month")), ("incidents at all", ir.get("covers_incidents"))) if not ok), [practice("Annual tabletop exercise", "Practice", None)])
        p10_ok = ir.get("corrective_measures") and ir.get("cessation_plan")
        c["P10"] = check("P10", "MET" if p10_ok else "PARTIAL", ir_docs, None if p10_ok else "lacks: " + ", ".join(x for x, ok in (("corrective measures / withdrawal / recall (Art. 13(21))", ir.get("corrective_measures")), ("cessation-of-operations plan (Art. 13(23))", ir.get("cessation_plan"))) if not ok),
                        [practice("Proactively notify market surveillance of significant non-conformity", "Matrix", bool(ir.get("authority_cooperation")) if ir.get("has_doc") else None)])
    else:
        for cid in ("P3", "P4", "P5", "P6", "P10"):
            c[cid] = check(cid, "UNKNOWN", [], NO_REPO, pr_p3 if cid == "P3" else [])

    # ------------------------------------------------------------------ P7 (AUTO)
    dsu = a.get("repo_meta", {}).get("dependabot_security_updates") == "enabled"
    auto_deps = cfg + (["Dependabot security updates enabled"] if dsu else [])
    rel_auto = wf.get("release_automation", []) if have_files else []
    ship_path = rel_auto or (["releases exist: {}".format(rel.get("latest_tag") or g.get("latest_tag"))] if has_releases else [])
    disclosure = ([("published advisories: {}".format(advisories_published))] if advisories_published else []) + (["CHANGELOG has security entries"] if adv.get("changelog_security_entries") else []) + (["SECURITY.md describes disclosure/advisories"] if adv.get("security_md_describes_disclosure") else [])
    pr_p7 = [practice("Automated dependency update PRs (Dependabot/Renovate)", "Practice", bool(auto_deps) if (have_files or a) else None),
             practice("Release automation from tags", "Practice", bool(rel_auto) if workflows else None),
             practice("CVE IDs / GitHub Security Advisories for fixed vulnerabilities", "Practice", True if advisories_published else None),
             practice("Machine-readable advisories (CSAF/OSV)", "Practice", None)]
    if not have_files and not a:
        c["P7"] = nofiles("P7")
    elif ship_path and disclosure:
        c["P7"] = check("P7", "MET", ship_path[:2] + disclosure[:2] + auto_deps[:1], None, pr_p7)
    elif ship_path or disclosure:
        c["P7"] = check("P7", "PARTIAL", ship_path[:2] + disclosure[:2], "missing: " + ("public disclosure of fixed vulnerabilities (Annex I Pt II(4)) - no advisories, changelog security entries or disclosure statement" if not disclosure else "a release path that can ship a security-only update"), pr_p7)
    elif workflows or releases_known:
        c["P7"] = check("P7", "NOT_MET", [], "no release path and no disclosure practice", pr_p7)
    else:
        c["P7"] = check("P7", "UNKNOWN", [], "workflows and releases not readable", pr_p7)

    return [c[k] for k in ITEM_ORDER]


def corpus_or_empty(f):
    """Support/hardening doc text used for install-instruction detection in D4."""
    if not f or not f.get("root"):
        return ""
    out = ""
    for cat in ("support_policy", "hardening"):
        for r in f.get("docs", {}).get(cat, [])[:2]:
            out += read_text(os.path.join(f["root"], r))
    if f.get("security_md") and isinstance(f["security_md"], dict) and f["security_md"].get("path") and not f["security_md"].get("org_level"):
        out += read_text(os.path.join(f["root"], f["security_md"]["path"]))
    return out


def summarize(checks):
    counts = {"MET": 0, "PARTIAL": 0, "NOT_MET": 0, "UNKNOWN": 0, "NA": 0}
    practices = {"adopted": 0, "not_adopted": 0, "unknown": 0}
    for ch in checks:
        counts[ch["status"]] += 1
        for p in ch.get("practices", []):
            if p["adopted"] is True:
                practices["adopted"] += 1
            elif p["adopted"] is False:
                practices["not_adopted"] += 1
            else:
                practices["unknown"] += 1
    counts["practices"] = practices
    return counts


def print_summary(result):
    print("\nCRA readiness evidence summary (preliminary, before intake answers)  rubric {}\n".format(CHECKLIST_VERSION))
    print("Repo: {}   Collected: {}".format(result["meta"].get("repo") or result["meta"].get("path"), result["meta"]["collected_at"]))
    acc = result["access"]
    print("Token: {}   Clone: {}   Local files: {}".format(acc.get("token_source"), acc.get("clone", {}).get("status", "n/a"), "yes" if acc.get("local_files") else "no"))
    denied = [k for k, v in acc.get("api_calls", {}).items() if v.get("status") in ("permission_denied", "not_found", "bad_token")]
    if denied:
        print("API calls not authoritative: " + ", ".join(denied))
    print("\nBASELINE (letter of the law; this layer is scored)\n")
    print("{:<4} {:<7} {:<5} {:<9} {}".format("ID", "Track", "Gate", "Status", "Item / evidence"))
    for ch in result["checks"]:
        ev = "; ".join(ch["evidence"][:2])
        print("{:<4} {:<7} {:<5} {:<9} {}".format(ch["id"], ch["track"], "yes" if ch["gate"] else "", ch["status"], ch["name"]))
        if ev:
            print(" " * 28 + "evidence: " + ev[:110])
        if ch.get("hint"):
            print(" " * 28 + "note: " + ch["hint"][:110])
    cts = result["counts"]
    print("\nMET {MET}  PARTIAL {PARTIAL}  NOT_MET {NOT_MET}  UNKNOWN {UNKNOWN}  NA {NA}  (intake answers will resolve most UNKNOWNs)".format(**cts))
    pr = cts["practices"]
    print("\nBEYOND THE LETTER (recommended practices; reported, never scored)\n")
    print("adopted {adopted}  not adopted {not_adopted}  not assessable {unknown}".format(**pr))
    gaps = [(ch["id"], p) for ch in result["checks"] for p in ch.get("practices", []) if p["adopted"] is False]
    for cid, p in gaps[:12]:
        print("  {:<4} {}  [{}]".format(cid, p["name"], p["source"]))
    if len(gaps) > 12:
        print("  ... {} more in the JSON output".format(len(gaps) - 12))
    print("\nThis is evidence, not a grade. Apply references/scoring.md after intake.\n")


# ----------------------------------------------------------------------------- main


def parse_repo(spec):
    spec = spec.strip()
    m = re.match(r"^(?:https?://github\.com/)?([\w.-]+)/([\w.-]+?)(?:\.git)?/?$", spec)
    if not m:
        raise SystemExit("--repo must be OWNER/NAME or a github.com URL")
    return m.group(1), m.group(2)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Collect CRA readiness evidence from a GitHub repository.")
    ap.add_argument("--repo", help="OWNER/NAME or https://github.com/OWNER/NAME")
    ap.add_argument("--path", help="Local checkout to scan (skips clone)")
    ap.add_argument("--token", help="GitHub token (else GITHUB_TOKEN / GH_TOKEN / gh auth token)")
    ap.add_argument("--out", help="Write JSON here instead of stdout")
    ap.add_argument("--summary", action="store_true", help="Print a human-readable summary to stderr-friendly stdout")
    ap.add_argument("--no-api", action="store_true", help="Do not call the GitHub API")
    ap.add_argument("--no-clone", action="store_true", help="Do not clone; scan only --path")
    ap.add_argument("--keep-clone", action="store_true", help="Keep the temporary clone directory")
    ap.add_argument("--exclude", action="append", default=[], metavar="DIR",
                    help="Repo-relative directory or file to skip (repeatable), e.g. --exclude examples --exclude docs/templates. docs/compliance/reports is always skipped.")
    args = ap.parse_args(argv)

    if not args.repo and not args.path:
        ap.error("provide --repo and/or --path")

    result = {
        "meta": {"collector_version": CHECKLIST_VERSION, "collected_at": now_iso(), "repo": None, "path": args.path},
        "access": {"token_source": None, "api_calls": {}, "clone": {}, "local_files": False},
        "signals": {"api": None, "files": None, "git": None},
        "checks": [],
        "counts": {},
    }

    owner = name = None
    if args.repo:
        owner, name = parse_repo(args.repo)
        result["meta"]["repo"] = "{}/{}".format(owner, name)

    token, source = (None, "disabled") if args.no_api and not args.repo else resolve_token(args.token)
    result["access"]["token_source"] = source

    api_sig = None
    if args.repo and not args.no_api:
        gh = GitHub(token)
        api_sig, _ = collect_api(gh, owner, name)
        result["access"]["api_calls"] = gh.calls
        result["signals"]["api"] = api_sig

    tmpdir = None
    scan_path = args.path
    if not scan_path and args.repo and not args.no_clone:
        tmpdir = tempfile.mkdtemp(prefix="cra-collect-")
        clone = shallow_clone(owner, name, token, tmpdir)
        result["access"]["clone"] = clone
        if clone["status"] == "ok":
            scan_path = tmpdir
        else:
            shutil.rmtree(tmpdir, ignore_errors=True)
            tmpdir = None

    files_sig = None
    git_sig = None
    if scan_path and os.path.isdir(scan_path):
        scan_path = os.path.abspath(scan_path)
        result["access"]["local_files"] = True
        files_sig = scan_files(scan_path, args.exclude)
        git_sig = scan_git(scan_path)
        result["signals"]["files"] = files_sig
        result["signals"]["git"] = git_sig
    elif scan_path:
        result["access"]["local_files_error"] = "path does not exist: " + scan_path

    # Org-level SECURITY.md fallback (GitHub displays OWNER/.github/SECURITY.md when the repo has none)
    if args.repo and not args.no_api and (files_sig is None or not files_sig.get("security_md")):
        org_sec = collect_org_security_policy(gh, owner)
        result["access"]["api_calls"] = gh.calls
        if org_sec and org_sec.get("has_contact") is not None:
            result["signals"]["org_security_policy"] = org_sec
        else:
            org_sec = None
    else:
        org_sec = None

    result["checks"] = map_checks(files_sig, api_sig, git_sig, org_sec)
    result["counts"] = summarize(result["checks"])

    if tmpdir and not args.keep_clone:
        shutil.rmtree(tmpdir, ignore_errors=True)
    elif tmpdir:
        result["access"]["clone"]["kept_at"] = tmpdir

    payload = json.dumps(result, indent=2, default=str)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(payload)
        print("wrote {}".format(args.out))
    elif not args.summary:
        print(payload)
    if args.summary:
        print_summary(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())

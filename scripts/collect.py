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

CHECKLIST_VERSION = "2026.09"
API = "https://api.github.com"
MAX_TEXT_BYTES = 512 * 1024
MAX_DOC_FILES = 600
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
    excludes = [e.strip("/").replace(os.sep, "/") for e in (excludes or []) if e.strip("/")]
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

    # README + docs user-facing signals (R11)
    corpus = ""
    if sig["key_files"].get("readme"):
        corpus += read_text(os.path.join(root, sig["key_files"]["readme"])) + "\n"
    for cat in ("support_policy", "hardening", "privacy", "compliance"):
        for r in sig["docs"][cat][:5]:
            corpus += read_text(os.path.join(root, r)) + "\n"
    if sec_path:
        corpus += read_text(os.path.join(root, sec_path))
    sig["user_docs_signals"] = {
        "intended_use": bool(re.search(r"intended (use|purpose)|is (a|an) .{3,80} (for|that)|purpose of", corpus, re.I)),
        "security_properties": bool(re.search(r"security (features|properties|model|considerations)|encrypt|authenticat", corpus, re.I)),
        "secure_configuration": bool(re.search(r"(secure|hardening|production) (configuration|setup|deployment)|configur.{0,40}secur|secur.{0,40}configur", corpus, re.I)),
        "support_period": bool(re.search(r"support(ed)? (period|until|window|policy)|end[- ]of[- ]life|security updates? (until|through|for)", corpus, re.I)),
        "vulnerability_reporting": bool(re.search(r"report(ing)? (a |security )?vulnerabilit|security@|SECURITY\.md|security policy", corpus, re.I)),
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
        "has_dates": bool(re.search(r"\b20[2-4]\d[-/.](0[1-9]|1[0-2])|\b(until|through|to)\s+(\w+\s+)?20[2-4]\d|\b\d+\s*years?\b", support_corpus)),
        "supported_versions_table": bool(re.search(r"supported versions|\|\s*version\s*\|", support_corpus, re.I)),
        "free_security_updates": bool(re.search(r"(free|no (additional )?(cost|charge)|without charge).{0,80}(security )?(update|patch|fix)|(security )?(update|patch|fix)es?.{0,80}(free|no (additional )?(cost|charge))", support_corpus, re.I)),
        "twelve_month_notice": bool(re.search(r"(12|twelve)[- ]months?.{0,80}(notice|advance|before|announce)|(notice|advance|announce).{0,80}(12|twelve)[- ]months?", support_corpus, re.I)),
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
        "mentions_csirt": bool(re.search(r"\bCSIRT\b", ir_corpus)),
        "covers_incidents": bool(re.search(r"\bincident", ir_corpus, re.I)),
        "corrective_measures": bool(re.search(r"recall|withdraw|corrective (measure|action)|market surveillance", ir_corpus, re.I)),
        "named_owner": bool(re.search(r"owner|on[- ]call|responsible|@[\w-]+|security lead|CISO|CTO", ir_corpus, re.I)),
    }

    # risk / threat / sdl specifics
    risk_corpus = "".join(read_text(os.path.join(root, r)) for r in sig["docs"]["risk_assessment"][:3])
    sig["risk_signals"] = {
        "has_doc": bool(sig["docs"]["risk_assessment"]),
        "has_ratings": bool(re.search(r"likelihood|impact|severity|probability", risk_corpus, re.I)),
        "has_mitigations": bool(re.search(r"mitigat|control|treatment|remediat", risk_corpus, re.I)),
        "has_history_section": bool(re.search(r"change ?log|revision history|version history|review trigger|last reviewed", risk_corpus, re.I)),
    }
    tm_corpus = "".join(read_text(os.path.join(root, r)) for r in sig["docs"]["threat_model"][:3])
    sig["threat_model_signals"] = {
        "has_doc": bool(sig["docs"]["threat_model"]),
        "method_named": bool(re.search(r"\bSTRIDE\b|\bPASTA\b|\bLINDDUN\b|attack tree|kill chain|MITRE ATT&CK", tm_corpus)),
        "has_attack_surface": bool(re.search(r"attack surface|entry point|trust boundar", tm_corpus, re.I)),
    }
    sdl_corpus = "".join(read_text(os.path.join(root, r)) for r in sig["docs"]["sdl"][:3])
    sig["sdl_signals"] = {
        "has_doc": bool(sig["docs"]["sdl"]),
        "has_phases": bool(re.search(r"phase|stage|design|implement|test|release|deploy", sdl_corpus, re.I)),
        "has_roles": bool(re.search(r"role|owner|responsib|RACI|security champion|approver", sdl_corpus, re.I)),
        "secure_by_default": bool(re.search(r"secure[- ]by[- ]default|attack surface|secure[- ]by[- ]design|default (configuration|settings)", sdl_corpus, re.I)),
        "mentions_certification": bool(re.search(r"ISO/?IEC 27001|IEC 62443|SOC ?2", sdl_corpus + corpus, re.I)),
    }
    tp_corpus = "".join(read_text(os.path.join(root, r)) for r in sig["docs"]["test_plan"][:3])
    sig["test_plan_signals"] = {
        "has_doc": bool(sig["docs"]["test_plan"]),
        "covers_areas": len(any_match([r"authenticat", r"access control|authori[sz]", r"input validation|injection", r"encrypt|crypto", r"error handling"], tp_corpus)),
    }
    net_corpus = "".join(read_text(os.path.join(root, r)) for r in sig["docs"]["network"][:5])
    sig["network_signals"] = {
        "has_doc": bool(sig["docs"]["network"]),
        "inbound_listed": bool(re.search(r"inbound|listen|open port|exposes? port", net_corpus, re.I)) and bool(re.search(r"\b\d{2,5}(/tcp|/udp)?\b", net_corpus)),
        "outbound_listed": bool(re.search(r"outbound|egress|connects to|calls (out|the following)|external (service|endpoint)", net_corpus, re.I)),
    }
    priv_corpus = "".join(read_text(os.path.join(root, r)) for r in sig["docs"]["privacy"][:5])
    sig["privacy_signals"] = {
        "has_doc": bool(sig["docs"]["privacy"]),
        "telemetry_opt_in_or_off": bool(re.search(r"opt[- ]?in|disabled by default|off by default|no telemetry|does not collect", priv_corpus, re.I)),
        "telemetry_on_by_default": bool(re.search(r"enabled by default|on by default|opt[- ]?out", priv_corpus, re.I)),
        "data_inventory": bool(re.search(r"we (collect|store)|data (we|that is) (collect|process|store)|retention", priv_corpus, re.I)),
    }
    comp_corpus_paths = sig["docs"]["compliance"][:10]
    comp_corpus = "".join(read_text(os.path.join(root, r)) for r in comp_corpus_paths)
    sig["compliance_signals"] = {
        "docs": comp_corpus_paths,
        "classification": bool(re.search(r"(default|important|critical) (product|class)|Annex III|Annex IV|classif", comp_corpus, re.I)),
        "conformity_route": bool(re.search(r"module A|self[- ]assessment|notified body|Annex VIII|conformity assessment (route|procedure)", comp_corpus, re.I)),
        "declaration_of_conformity": bool(re.search(r"declaration of conformity|Annex V\b", comp_corpus, re.I)),
        "ce_marking": bool(re.search(r"CE mark", comp_corpus, re.I)),
        "technical_file": bool(re.search(r"technical (file|documentation)|Annex VII", comp_corpus, re.I)),
        "retention": bool(re.search(r"(10|ten)[- ]years?.{0,60}(retain|retention|keep|archive)|(retain|retention|keep|archive).{0,60}(10|ten)[- ]years?", comp_corpus, re.I)),
        "authorised_representative": bool(re.search(r"authori[sz]ed representative", comp_corpus, re.I)),
    }
    dep_corpus = "".join(read_text(os.path.join(root, r)) for r in sig["docs"]["dependency_policy"][:3])
    sig["dependency_policy_signals"] = {
        "has_doc": bool(sig["docs"]["dependency_policy"]),
        "covers_eol": bool(re.search(r"end[- ]of[- ]life|EOL|maintained|last release", dep_corpus, re.I)),
        "covers_vuln_response": bool(re.search(r"vulnerab|CVE|patch|update within", dep_corpus, re.I)),
        "covers_selection": bool(re.search(r"licen[cs]e|approv|criteria|evaluat|select", dep_corpus, re.I)),
    }
    hard_corpus = "".join(read_text(os.path.join(root, r)) for r in sig["docs"]["hardening"][:5])
    sig["hardening_signals"] = {
        "has_doc": bool(sig["docs"]["hardening"]),
        "first_run_credentials": bool(re.search(r"first (run|login|start|boot|use).{0,80}(password|credential|set ?up)|(password|credential).{0,80}first (run|login|start|boot|use)|initial (admin )?password", corpus + hard_corpus, re.I)),
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

TRACK = {
    "AUTO": {"B6", "D2", "D3", "D4", "R1", "R2", "P2", "P7"},
}
GATES = {"F1", "F4", "B1", "B2", "B3", "B9", "D3", "D4", "R1", "R2", "R5", "R6", "R7", "R8", "R9", "R11", "R12", "P2", "P3", "P8"}
ITEM_NAMES = {
    "F1": "Documented SDL", "F2": "Evidence of conformity with SDL", "F3": "SDL covers secure-by-design/default",
    "F4": "EU Authorised Representative", "B1": "Product classification", "B2": "Conformity assessment route",
    "B3": "Risk assessment", "B4": "Threat modelling", "B5": "Third-party component policy",
    "B6": "EOL check for tools/dependencies", "B7": "Storage encryption feasibility", "B8": "Minimal attack-surface design",
    "B9": "Default credential policy", "D1": "Cybersecurity test plan", "D2": "Evidence of SDL compliance",
    "D3": "Pen testing / vulnerability assessment", "D4": "Secure update mechanism", "D5": "Data minimisation",
    "R1": "SBOM prepared and screened", "R2": "SBOM machine-readable", "R3": "Inbound connections list",
    "R4": "Outbound connections list", "R5": "Declare EOL", "R6": "Conformity assessment completed",
    "R7": "EU Declaration of Conformity", "R8": "CE marking", "R9": "Technical file", "R10": "10-year retention",
    "R11": "User-facing documentation", "R12": "Vulnerability disclosure contact", "P1": "Update risk assessment on change",
    "P2": "Automated SBOM vuln monitoring", "P3": "24h initial report", "P4": "72h technical report",
    "P5": "Final report 14 days", "P6": "Severe incident reporting", "P7": "Automatic update for 3rd-party vulns",
    "P8": "Security updates free of charge", "P9": "Advance notice of EOL", "P10": "Corrective measures",
}


def check(cid, status, evidence, hint=None):
    return {
        "id": cid,
        "name": ITEM_NAMES[cid],
        "track": "AUTO" if cid in TRACK["AUTO"] else "POLICY",
        "gate": cid in GATES,
        "status": status,
        "evidence": [e for e in evidence if e],
        "hint": hint,
    }


NO_REPO = "no_repo_evidence: absence in repo is not proof; confirm via intake before marking NOT_MET"
INTAKE = "intake_only: cannot be assessed from a repository"


def map_checks(files, api, git, org_security=None):
    """Preliminary statuses from repo evidence only. Intake answers are applied by the agent."""
    c = {}
    f = files or {}
    a = api or {}
    g = git or {}
    have_files = bool(f)
    # SECURITY.md: in-repo file wins; else the org-level default GitHub displays for the repo
    sec = (f.get("security_md") if have_files else None) or org_security or {}
    wf = f.get("workflow_tools", {}) if have_files else {}
    workflows = f.get("workflows", []) if have_files else []
    trig = f.get("workflow_triggers", {}) if have_files else {}
    docs = f.get("docs", {}) if have_files else {}

    def unknown_if_no_files(cid, reason="repository files not available"):
        return check(cid, "UNKNOWN", [], reason)

    # ---- F1
    s = f.get("sdl_signals", {})
    if not have_files:
        c["F1"] = unknown_if_no_files("F1")
    elif s.get("has_doc") and s.get("has_phases") and s.get("has_roles"):
        c["F1"] = check("F1", "MET", docs.get("sdl", [])[:3])
    elif s.get("has_doc"):
        c["F1"] = check("F1", "PARTIAL", docs.get("sdl", [])[:3], "SDL document found but phases or roles not clearly described")
    elif f.get("key_files", {}).get("contributing") and re.search(r"security review|security", read_text(os.path.join(f["root"], f["key_files"]["contributing"])), re.I):
        c["F1"] = check("F1", "PARTIAL", [f["key_files"]["contributing"]], "informal security guidance only")
    else:
        c["F1"] = check("F1", "UNKNOWN", [], NO_REPO)

    # ---- F2
    bp = a.get("branch_protection", {})
    forms = []
    if f.get("pr_template_security_checklist"):
        forms.append("PR template security checklist: " + f["pr_template"])
    if bp.get("protected") and (bp.get("required_reviews") or 0) >= 1:
        forms.append("required reviews on {} ({})".format(bp.get("branch"), bp.get("required_reviews")))
    if docs.get("sdl") and re.search(r"review record|sign[- ]off|release checklist", "".join(read_text(os.path.join(f["root"], r)) for r in docs["sdl"][:3]), re.I):
        forms.append("release sign-off/review records referenced in SDL doc")
    if not have_files:
        c["F2"] = unknown_if_no_files("F2")
    elif len(forms) >= 2:
        c["F2"] = check("F2", "MET", forms)
    elif len(forms) == 1:
        c["F2"] = check("F2", "PARTIAL", forms, "one form of recurring evidence found; two are needed")
    else:
        c["F2"] = check("F2", "UNKNOWN", [], NO_REPO)

    # ---- F3
    if not have_files:
        c["F3"] = unknown_if_no_files("F3")
    elif s.get("has_doc") and s.get("secure_by_default"):
        c["F3"] = check("F3", "MET", docs.get("sdl", [])[:3])
    elif s.get("has_doc"):
        c["F3"] = check("F3", "PARTIAL", docs.get("sdl", [])[:3], "SDL found; no explicit secure-by-design/default section")
    else:
        c["F3"] = check("F3", "UNKNOWN", [], NO_REPO)

    # ---- intake-only items, with any compliance doc hints
    comp = f.get("compliance_signals", {}) if have_files else {}
    c["F4"] = check("F4", "UNKNOWN", comp.get("docs", []) if comp.get("authorised_representative") else [], INTAKE + ("; a document mentions an authorised representative" if comp.get("authorised_representative") else ""))
    c["B1"] = check("B1", "UNKNOWN", comp.get("docs", []) if comp.get("classification") else [], INTAKE + ("; a document discusses classification" if comp.get("classification") else ""))
    c["B2"] = check("B2", "UNKNOWN", comp.get("docs", []) if comp.get("conformity_route") else [], INTAKE + ("; a document discusses the conformity route" if comp.get("conformity_route") else ""))
    c["B7"] = check("B7", "UNKNOWN", [], INTAKE)
    c["R6"] = check("R6", "UNKNOWN", [], INTAKE)
    c["R8"] = check("R8", "UNKNOWN", comp.get("docs", []) if comp.get("ce_marking") else [], INTAKE + ("; a document mentions CE marking" if comp.get("ce_marking") else ""))

    # ---- B3
    r = f.get("risk_signals", {})
    if not have_files:
        c["B3"] = unknown_if_no_files("B3")
    elif r.get("has_doc"):
        revs = doc_revision_count(f["root"], docs["risk_assessment"][0])
        if r.get("has_ratings") and r.get("has_mitigations") and (revs is None or revs >= 1):
            c["B3"] = check("B3", "MET", docs["risk_assessment"][:3] + (["git revisions: {}".format(revs)] if revs else []))
        else:
            c["B3"] = check("B3", "PARTIAL", docs["risk_assessment"][:3], "risk document found without ratings or mitigations")
    else:
        c["B3"] = check("B3", "UNKNOWN", [], NO_REPO)

    # ---- B4
    t = f.get("threat_model_signals", {})
    if not have_files:
        c["B4"] = unknown_if_no_files("B4")
    elif t.get("has_doc") and t.get("method_named") and t.get("has_attack_surface"):
        c["B4"] = check("B4", "MET", docs["threat_model"][:3])
    elif t.get("has_doc"):
        c["B4"] = check("B4", "PARTIAL", docs["threat_model"][:3], "threat model found; methodology or attack surface not explicit")
    else:
        c["B4"] = check("B4", "UNKNOWN", [], NO_REPO)

    # ---- B5
    d = f.get("dependency_policy_signals", {})
    dep_review = wf.get("dependency_review", [])
    if not have_files:
        c["B5"] = unknown_if_no_files("B5")
    elif d.get("has_doc") and d.get("covers_eol") and d.get("covers_vuln_response"):
        c["B5"] = check("B5", "MET", docs["dependency_policy"][:3] + dep_review)
    elif d.get("has_doc") or dep_review:
        c["B5"] = check("B5", "PARTIAL", docs.get("dependency_policy", [])[:3] + dep_review, "policy or enforcement found, not both (or policy lacks EOL/vulnerability terms)")
    else:
        c["B5"] = check("B5", "UNKNOWN", [], NO_REPO)

    # ---- B6 (AUTO, repo)
    if not have_files:
        c["B6"] = unknown_if_no_files("B6")
    else:
        locks, pins, manifests = f.get("lockfiles", []), f.get("runtime_pins", []), f.get("manifests", [])
        unpinned = f.get("docker_unpinned_base", [])
        eol_tools = wf.get("eol", []) + ([f["renovate_config"]] if f.get("renovate_config") else []) + ([f["dependabot_config"]] if f.get("dependabot_config") and "docker" in read_text(os.path.join(f["root"], f["dependabot_config"])).lower() else [])
        ev = locks[:5] + pins[:5] + eol_tools[:3]
        if not manifests and not locks:
            c["B6"] = check("B6", "UNKNOWN", [], "no dependency manifests detected; confirm the stack manually")
        elif locks and (pins or (f.get("dockerfiles") and not unpinned)) and eol_tools and not unpinned:
            c["B6"] = check("B6", "MET", ev)
        elif locks:
            hint = []
            if not pins and not f.get("dockerfiles"):
                hint.append("no runtime version pin files")
            if unpinned:
                hint.append("unpinned base images: " + "; ".join(unpinned[:3]))
            if not eol_tools:
                hint.append("no EOL tooling (xeol/endoflife/Renovate docker)")
            c["B6"] = check("B6", "PARTIAL", ev, "; ".join(hint))
        else:
            c["B6"] = check("B6", "NOT_MET", manifests[:5], "manifests present but no lockfiles committed")

    # ---- B8
    h = f.get("hardening_signals", {})
    if not have_files:
        c["B8"] = unknown_if_no_files("B8")
    else:
        low_expose = bool(f.get("dockerfiles")) and f.get("docker_expose_total", 0) <= 2
        if h.get("has_doc") and (low_expose or not f.get("dockerfiles")):
            c["B8"] = check("B8", "MET", docs["hardening"][:3] + (["Dockerfile EXPOSE count: {}".format(f["docker_expose_total"])] if f.get("dockerfiles") else []))
        elif h.get("has_doc") or low_expose:
            c["B8"] = check("B8", "PARTIAL", docs.get("hardening", [])[:3], "documentation or minimal config found, not both")
        else:
            c["B8"] = check("B8", "UNKNOWN", [], NO_REPO)

    # ---- B9
    hits = f.get("default_credential_hits", []) if have_files else []
    if not have_files:
        c["B9"] = unknown_if_no_files("B9")
    elif hits and h.get("first_run_credentials"):
        c["B9"] = check("B9", "PARTIAL", hits[:10], "default-looking credentials found, but first-run credential change is documented")
    elif hits:
        c["B9"] = check("B9", "NOT_MET", hits[:10], "default-looking credentials in config; verify each hit (may be test fixtures)")
    elif h.get("first_run_credentials"):
        c["B9"] = check("B9", "MET", ["no default credentials detected in config", "first-run credential setup documented"])
    else:
        c["B9"] = check("B9", "PARTIAL", ["no default credentials detected in config"], "confirm whether the product has accounts and how first credentials are set; NA if no authentication")

    # ---- D1
    tp = f.get("test_plan_signals", {})
    tests_in_ci = bool(wf.get("tests"))
    if not have_files:
        c["D1"] = unknown_if_no_files("D1")
    elif tp.get("has_doc") and tests_in_ci:
        c["D1"] = check("D1", "MET", docs["test_plan"][:3] + wf["tests"][:3])
    elif tp.get("has_doc") or tests_in_ci or f.get("test_dirs"):
        ev = docs.get("test_plan", [])[:3] + wf.get("tests", [])[:3] + (["test dirs: " + ", ".join(f["test_dirs"][:5])] if f.get("test_dirs") else [])
        c["D1"] = check("D1", "PARTIAL", ev, "tests without a written security test plan, or plan without CI tests")
    else:
        c["D1"] = check("D1", "UNKNOWN", [], NO_REPO)

    # ---- D2 (AUTO, repo)
    ci_on_pr = bool(trig.get("pull_request"))
    if not have_files and not bp:
        c["D2"] = unknown_if_no_files("D2")
    elif bp.get("protected") and (bp.get("required_reviews") or 0) >= 1 and bp.get("required_status_checks") and ci_on_pr:
        c["D2"] = check("D2", "MET", ["branch protection on {}: {} review(s), status checks required".format(bp["branch"], bp["required_reviews"]), "CI on pull_request: " + ", ".join(trig["pull_request"][:3])])
    elif bp.get("status") in ("permission_denied", "not_found", "network_error", "bad_token", None) and bp.get("protected") is None:
        st = "PARTIAL" if ci_on_pr else "UNKNOWN"
        c["D2"] = check("D2", st, (["CI on pull_request: " + ", ".join(trig["pull_request"][:3])] if ci_on_pr else []) + (["rulesets: {}".format(a.get("rulesets", {}).get("count"))] if a.get("rulesets", {}).get("count") else []), "branch protection could not be read (needs admin token); CI-on-PR {}".format("present" if ci_on_pr else "absent or unreadable"))
    elif ci_on_pr or bp.get("protected"):
        c["D2"] = check("D2", "PARTIAL", (["CI on pull_request: " + ", ".join(trig["pull_request"][:3])] if ci_on_pr else []) + (["protection present but reviews/status checks incomplete"] if bp.get("protected") else []), "protection incomplete")
    else:
        c["D2"] = check("D2", "NOT_MET", [], "no CI on pull requests and no branch protection")

    # ---- D3 (AUTO)
    sast = wf.get("sast", []) or (["code scanning default setup: " + str(a.get("code_scanning_default_setup", {}).get("state"))] if a.get("code_scanning_default_setup", {}).get("state") == "configured" else []) or (["code scanning analyses present"] if a.get("code_scanning_analyses", {}).get("present") else [])
    secrets = wf.get("secrets", []) or (["GitHub secret scanning: enabled"] if a.get("repo_meta", {}).get("secret_scanning") == "enabled" else [])
    pentest_docs = docs.get("pentest", []) if have_files else []
    if not have_files and not a:
        c["D3"] = unknown_if_no_files("D3")
    elif sast and secrets:
        c["D3"] = check("D3", "MET" if pentest_docs else "PARTIAL", sast[:3] + secrets[:3] + pentest_docs[:2], None if pentest_docs else "automated scanning in place; pentest within 12 months not evidenced in repo (confirm via intake Q2.4 to upgrade to MET)")
    elif sast or secrets or pentest_docs:
        c["D3"] = check("D3", "PARTIAL", sast[:3] + secrets[:3] + pentest_docs[:2], "missing: " + ", ".join(x for x, ok in (("SAST", sast), ("secret scanning", secrets), ("pentest evidence", pentest_docs)) if not ok))
    elif workflows:
        c["D3"] = check("D3", "NOT_MET", ["workflows present: {}".format(len(workflows))], "no SAST or secret scanning in CI")
    else:
        c["D3"] = check("D3", "UNKNOWN", [], "no workflows readable")

    # ---- D4 (AUTO)
    rel_assets = a.get("releases", {}).get("assets", []) or []
    sig_assets = [x for x in rel_assets if SIG_ASSET_RE.search(x)]
    sum_assets = [x for x in rel_assets if CHECKSUM_ASSET_RE.search(x)]
    signing = wf.get("signing", []) + wf.get("trusted_publishing", []) + sig_assets
    if g.get("latest_tag_signed"):
        signing.append("latest tag signed: " + str(g.get("latest_tag")))
    checks_only = wf.get("checksums", []) + sum_assets
    verify_doc = bool(re.search(r"verify|signature|checksum|provenance|cosign|attestation", (read_text(os.path.join(f["root"], f["key_files"]["readme"])) if have_files and f.get("key_files", {}).get("readme") else ""), re.I))
    releases_known = a.get("releases", {}).get("status") == "ok"
    has_releases = (a.get("releases", {}).get("count") or 0) > 0 or (g.get("tag_count") or 0) > 0
    if not have_files and not a:
        c["D4"] = unknown_if_no_files("D4")
    elif signing and verify_doc:
        c["D4"] = check("D4", "MET", signing[:4] + ["README documents verification"])
    elif signing:
        c["D4"] = check("D4", "PARTIAL", signing[:4], "signing/provenance found; user verification steps not documented in README")
    elif checks_only:
        c["D4"] = check("D4", "PARTIAL", checks_only[:4], "checksums only; no signatures or provenance")
    elif has_releases:
        c["D4"] = check("D4", "NOT_MET", ["releases/tags exist: {}".format(a.get("releases", {}).get("latest_tag") or g.get("latest_tag"))], "releases are unsigned and no provenance is generated")
    elif releases_known or g.get("status") == "ok":
        c["D4"] = check("D4", "NOT_MET", [], "no releases or tags found; no update distribution path evidenced")
    else:
        c["D4"] = check("D4", "UNKNOWN", [], "release data not readable")

    # ---- D5
    p = f.get("privacy_signals", {})
    if not have_files:
        c["D5"] = unknown_if_no_files("D5")
    elif p.get("has_doc") and p.get("telemetry_opt_in_or_off") and p.get("data_inventory"):
        c["D5"] = check("D5", "MET", docs["privacy"][:3])
    elif p.get("has_doc"):
        c["D5"] = check("D5", "PARTIAL", docs["privacy"][:3], "privacy/telemetry doc found; opt-in default or data inventory not explicit")
    elif f.get("telemetry_libs"):
        c["D5"] = check("D5", "NOT_MET", ["telemetry/analytics libraries in manifests: " + ", ".join(f["telemetry_libs"][:5])], "telemetry libraries present with no documentation")
    else:
        c["D5"] = check("D5", "UNKNOWN", [], NO_REPO)

    # ---- R1 / R2 (AUTO)
    sbom_ci = wf.get("sbom", [])
    vuln_ci = wf.get("vuln_scan", [])
    dep_alerts = a.get("dependabot_alerts", {}).get("enabled")
    sbom_assets = [x for x in rel_assets if SBOM_FILE_RE.search(x)]
    dg = a.get("dependency_graph", {}).get("enabled")
    if not have_files and not a:
        c["R1"] = unknown_if_no_files("R1")
        c["R2"] = unknown_if_no_files("R2")
    else:
        gen = sbom_ci + sbom_assets + (f.get("sbom_files", [])[:3] if have_files else [])
        scan = vuln_ci + (["Dependabot alerts enabled"] if dep_alerts else [])
        if gen and scan:
            c["R1"] = check("R1", "MET", gen[:4] + scan[:4], None if sbom_ci else "SBOM artefacts exist but no CI job generates them per release; verify")
        elif gen or scan or dg:
            c["R1"] = check("R1", "PARTIAL", gen[:4] + scan[:4] + (["dependency graph enabled"] if dg else []), "missing: " + ", ".join(x for x, ok in (("SBOM generation", gen), ("vulnerability scan gate", scan)) if not ok))
        elif workflows or releases_known:
            c["R1"] = check("R1", "NOT_MET", [], "no SBOM generation or vulnerability scanning found")
        else:
            c["R1"] = check("R1", "UNKNOWN", [], "workflows and releases not readable")

        fmt = wf.get("sbom_format", []) + sbom_assets + (f.get("sbom_files", [])[:3] if have_files else [])
        if fmt:
            c["R2"] = check("R2", "MET", fmt[:5])
        elif gen:
            c["R2"] = check("R2", "PARTIAL", gen[:4], "SBOM produced but SPDX/CycloneDX format not confirmed")
        elif c["R1"]["status"] == "UNKNOWN":
            c["R2"] = check("R2", "UNKNOWN", [], "follows R1")
        else:
            c["R2"] = check("R2", "NOT_MET", [], "no SBOM (follows R1)")

    # ---- R3 / R4
    n = f.get("network_signals", {})
    if not have_files:
        c["R3"] = unknown_if_no_files("R3")
        c["R4"] = unknown_if_no_files("R4")
    else:
        cfg_ports = (f.get("docker_expose_total", 0) + f.get("compose_ports", 0)) > 0
        if n.get("inbound_listed"):
            c["R3"] = check("R3", "MET", docs["network"][:3])
        elif cfg_ports:
            c["R3"] = check("R3", "PARTIAL", ["Dockerfile EXPOSE: {}".format(f["docker_expose_total"]), "compose ports: {}".format(f["compose_ports"])], "ports visible in config but not documented with justification")
        else:
            c["R3"] = check("R3", "UNKNOWN", [], NO_REPO + "; NA if the product opens no listening ports")
        if n.get("outbound_listed"):
            c["R4"] = check("R4", "MET", docs["network"][:3])
        elif p.get("has_doc"):
            c["R4"] = check("R4", "PARTIAL", docs["privacy"][:2], "telemetry documented; full outbound list not found")
        else:
            c["R4"] = check("R4", "UNKNOWN", [], NO_REPO)

    # ---- R5 / P8 / P9
    sp = f.get("support_signals", {})
    sup_ev = (docs.get("support_policy", [])[:3] if have_files else []) + ([f["key_files"]["support_md"]] if have_files and f.get("key_files", {}).get("support_md") else []) + ([sec["path"]] if sec.get("has_supported_versions") else [])
    if not have_files:
        for cid in ("R5", "P8", "P9"):
            c[cid] = unknown_if_no_files(cid)
    else:
        if (sp.get("has_support_doc") or sec.get("has_supported_versions")) and (sp.get("has_dates") or sec.get("has_dates")):
            c["R5"] = check("R5", "MET", sup_ev)
        elif sp.get("has_support_doc") or sec.get("has_supported_versions"):
            c["R5"] = check("R5", "PARTIAL", sup_ev, "supported-versions info without a dated support period")
        else:
            c["R5"] = check("R5", "UNKNOWN", [], NO_REPO)
        if sp.get("free_security_updates"):
            c["P8"] = check("P8", "MET", sup_ev)
        elif sup_ev:
            c["P8"] = check("P8", "PARTIAL", sup_ev, "support policy does not state security updates are free")
        else:
            c["P8"] = check("P8", "UNKNOWN", [], NO_REPO)
        if sp.get("twelve_month_notice"):
            c["P9"] = check("P9", "MET", sup_ev)
        elif sup_ev:
            c["P9"] = check("P9", "PARTIAL", sup_ev, "no 12-month end-of-support notice commitment")
        else:
            c["P9"] = check("P9", "UNKNOWN", [], NO_REPO)

    # ---- R7 / R9 / R10
    if not have_files:
        for cid in ("R7", "R9", "R10"):
            c[cid] = unknown_if_no_files(cid)
    else:
        c["R7"] = check("R7", "PARTIAL" if comp.get("declaration_of_conformity") else "UNKNOWN", comp.get("docs", [])[:3] if comp.get("declaration_of_conformity") else [], "document references a DoC; signature cannot be verified from the repo" if comp.get("declaration_of_conformity") else NO_REPO)
        c["R9"] = check("R9", "PARTIAL" if comp.get("technical_file") else "UNKNOWN", comp.get("docs", [])[:3] if comp.get("technical_file") else [], "technical file index referenced; verify every Annex VII element is present" if comp.get("technical_file") else NO_REPO)
        if comp.get("retention") and sbom_assets:
            c["R10"] = check("R10", "MET", comp["docs"][:2] + sbom_assets[:2])
        elif comp.get("retention") or sbom_assets:
            c["R10"] = check("R10", "PARTIAL", (comp.get("docs", [])[:2] if comp.get("retention") else []) + sbom_assets[:2], "retention policy or archived SBOMs found, not both")
        else:
            c["R10"] = check("R10", "UNKNOWN", [], NO_REPO)

    # ---- R11 (repo)
    u = f.get("user_docs_signals", {})
    if not have_files or not f.get("key_files", {}).get("readme"):
        c["R11"] = check("R11", "UNKNOWN", [], "README not readable")
    else:
        present = [k for k, v in u.items() if v]
        missing = [k for k, v in u.items() if not v]
        st = "MET" if len(present) == 5 else ("PARTIAL" if len(present) >= 3 else "NOT_MET")
        c["R11"] = check("R11", st, ["README/docs cover: " + ", ".join(present)], ("missing: " + ", ".join(missing)) if missing else None)

    # ---- R12 (repo)
    pvr = a.get("private_vulnerability_reporting", {})
    if not have_files and not a:
        c["R12"] = unknown_if_no_files("R12")
    elif sec.get("has_contact") and sec.get("has_response_time") and pvr.get("enabled") is True:
        c["R12"] = check("R12", "MET", [sec["path"], "private vulnerability reporting: enabled"])
    elif sec.get("has_contact"):
        hint = []
        if not sec.get("has_response_time"):
            hint.append("no response-time expectation in SECURITY.md")
        if pvr.get("enabled") is False:
            hint.append("private vulnerability reporting disabled")
        elif pvr.get("enabled") is None:
            hint.append("private vulnerability reporting not readable ({})".format(pvr.get("status")))
        c["R12"] = check("R12", "PARTIAL", [sec["path"]] + ([f["security_txt"]] if f.get("security_txt") else []), "; ".join(hint))
    elif pvr.get("enabled") is True:
        c["R12"] = check("R12", "PARTIAL", ["private vulnerability reporting: enabled"], "no SECURITY.md with a contact (repo or org-level)")
    elif have_files or org_security is not None:
        c["R12"] = check("R12", "NOT_MET", [], "no SECURITY.md contact found (repo or org-level)" + ("" if pvr.get("enabled") is not None else "; PVR setting not readable"))
    else:
        c["R12"] = check("R12", "UNKNOWN", [], "files not readable")

    # ---- P1
    if not have_files:
        c["P1"] = unknown_if_no_files("P1")
    elif r.get("has_doc"):
        revs = doc_revision_count(f["root"], docs["risk_assessment"][0])
        if r.get("has_history_section") or (revs or 0) >= 2:
            c["P1"] = check("P1", "MET", docs["risk_assessment"][:2] + (["git revisions: {}".format(revs)] if revs else []))
        else:
            c["P1"] = check("P1", "PARTIAL", docs["risk_assessment"][:2], "risk assessment has no review-trigger or change history section")
    else:
        c["P1"] = check("P1", "UNKNOWN", [], NO_REPO)

    # ---- P2 (AUTO)
    scheduled_scan = [w for w in vuln_ci if w in trig.get("schedule", [])]
    cfg = [x for x in (f.get("dependabot_config"), f.get("renovate_config")) if x] if have_files else []
    mech = ([ "Dependabot alerts enabled"] if dep_alerts else []) + cfg + scheduled_scan
    if not have_files and not a:
        c["P2"] = unknown_if_no_files("P2")
    elif dep_alerts and (cfg or scheduled_scan):
        c["P2"] = check("P2", "MET", mech[:5])
    elif len(mech) >= 2:
        c["P2"] = check("P2", "MET", mech[:5], "Dependabot alert status not readable; two other mechanisms present")
    elif mech:
        c["P2"] = check("P2", "PARTIAL", mech[:5], "single monitoring mechanism" + ("; Dependabot alerts not readable (needs admin)" if dep_alerts is None else ""))
    elif dep_alerts is None and have_files:
        c["P2"] = check("P2", "UNKNOWN", [], "no config found and Dependabot alert setting not readable (needs admin token)")
    else:
        c["P2"] = check("P2", "NOT_MET", [], "no automated vulnerability monitoring found")

    # ---- P3-P6, P10
    ir = f.get("incident_signals", {})
    ir_docs = docs.get("incident_response", [])[:3] if have_files else []
    if not have_files:
        for cid in ("P3", "P4", "P5", "P6", "P10"):
            c[cid] = unknown_if_no_files(cid)
    elif ir.get("has_doc"):
        base_ok = ir.get("mentions_enisa") and ir.get("mentions_24h")
        c["P3"] = check("P3", "MET" if base_ok and ir.get("named_owner") else "PARTIAL", ir_docs, None if base_ok and ir.get("named_owner") else "incident doc lacks " + ", ".join(x for x, ok in (("ENISA reference", ir.get("mentions_enisa")), ("24h timeline", ir.get("mentions_24h")), ("named owner", ir.get("named_owner"))) if not ok))
        c["P4"] = check("P4", "MET" if base_ok and ir.get("mentions_72h") else "PARTIAL", ir_docs, None if base_ok and ir.get("mentions_72h") else "no 72h report step")
        c["P5"] = check("P5", "MET" if base_ok and ir.get("mentions_14_days") else "PARTIAL", ir_docs, None if base_ok and ir.get("mentions_14_days") else "no 14-day final report step")
        c["P6"] = check("P6", "MET" if base_ok and ir.get("covers_incidents") else "PARTIAL", ir_docs, None if base_ok and ir.get("covers_incidents") else "procedure does not explicitly cover severe incidents")
        c["P10"] = check("P10", "MET" if ir.get("corrective_measures") else "PARTIAL", ir_docs, None if ir.get("corrective_measures") else "no corrective measures / market surveillance notification step")
    else:
        for cid in ("P3", "P4", "P5", "P6", "P10"):
            c[cid] = check(cid, "UNKNOWN", [], NO_REPO)

    # ---- P7 (AUTO)
    dsu = a.get("repo_meta", {}).get("dependabot_security_updates") == "enabled"
    auto_deps = cfg + (["Dependabot security updates enabled"] if dsu else [])
    rel_auto = wf.get("release_automation", [])
    if not have_files and not a:
        c["P7"] = unknown_if_no_files("P7")
    elif auto_deps and rel_auto:
        c["P7"] = check("P7", "MET", auto_deps[:3] + rel_auto[:3])
    elif auto_deps or rel_auto:
        c["P7"] = check("P7", "PARTIAL", auto_deps[:3] + rel_auto[:3], "missing: " + ("release automation" if not rel_auto else "automated dependency updates"))
    elif workflows:
        c["P7"] = check("P7", "NOT_MET", [], "manual dependency updates and manual releases")
    else:
        c["P7"] = check("P7", "UNKNOWN", [], "workflows not readable")

    ordered = ["F1", "F2", "F3", "F4", "B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B9", "D1", "D2", "D3", "D4", "D5",
               "R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8", "R9", "R10", "R11", "R12", "P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8", "P9", "P10"]
    return [c[k] for k in ordered]


def summarize(checks):
    counts = {"MET": 0, "PARTIAL": 0, "NOT_MET": 0, "UNKNOWN": 0, "NA": 0}
    for ch in checks:
        counts[ch["status"]] += 1
    return counts


def print_summary(result):
    print("\nCRA readiness evidence summary (preliminary, before intake answers)\n")
    print("Repo: {}   Collected: {}".format(result["meta"].get("repo") or result["meta"].get("path"), result["meta"]["collected_at"]))
    acc = result["access"]
    print("Token: {}   Clone: {}   Local files: {}".format(acc.get("token_source"), acc.get("clone", {}).get("status", "n/a"), "yes" if acc.get("local_files") else "no"))
    denied = [k for k, v in acc.get("api_calls", {}).items() if v.get("status") in ("permission_denied", "not_found", "bad_token")]
    if denied:
        print("API calls not authoritative: " + ", ".join(denied))
    print()
    print("{:<4} {:<7} {:<5} {:<9} {}".format("ID", "Track", "Gate", "Status", "Item / evidence"))
    for ch in result["checks"]:
        ev = "; ".join(ch["evidence"][:2])
        line = "{:<4} {:<7} {:<5} {:<9} {}".format(ch["id"], ch["track"], "yes" if ch["gate"] else "", ch["status"], ch["name"])
        print(line)
        if ev:
            print(" " * 28 + "evidence: " + ev[:110])
        if ch.get("hint"):
            print(" " * 28 + "note: " + ch["hint"][:110])
    cts = result["counts"]
    print("\nMET {MET}  PARTIAL {PARTIAL}  NOT_MET {NOT_MET}  UNKNOWN {UNKNOWN}  (intake answers will resolve most UNKNOWNs)".format(**cts))
    print("This is evidence, not a grade. Apply references/scoring.md after intake.\n")


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
                    help="Repo-relative directory to skip (repeatable), e.g. --exclude examples --exclude docs/templates")
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

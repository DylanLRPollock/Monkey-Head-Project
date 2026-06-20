#!/usr/bin/env bash
set -u

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

EXIT_CODE=0
RUN_OUTDATED=0
if [[ "${1:-}" == "--outdated" ]]; then
  RUN_OUTDATED=1
fi

have_cmd() { command -v "$1" >/dev/null 2>&1; }

print_header() {
  printf '\n== %s ==\n' "$1"
}

fail_step() {
  EXIT_CODE=1
  printf '❌ %s\n' "$1"
}

warn_step() {
  printf '⚠️  %s\n' "$1"
}

ok_step() {
  printf '✅ %s\n' "$1"
}

print_header "Local security checks"
printf 'Repository: %s\n' "$ROOT_DIR"

if [[ -f requirements.txt ]]; then
  print_header "pip-audit"
  if have_cmd pip-audit; then
    if pip-audit -r requirements.txt; then
      ok_step "pip-audit found no known vulnerable packages in requirements.txt"
    else
      fail_step "pip-audit reported vulnerable packages"
    fi
  else
    warn_step "pip-audit is not installed. Install it with: python -m pip install pip-audit"
  fi
else
  warn_step "requirements.txt not found; skipping pip-audit"
fi

print_header "bandit"
if have_cmd bandit; then
  BANDIT_JSON="$(mktemp)"
  if bandit -r src scripts -f json -o "$BANDIT_JSON" >/dev/null 2>&1; then
    ok_step "bandit completed"
  else
    warn_step "bandit reported findings; analyzing severity/confidence"
  fi

  HIGH_COUNT="$(python - "$BANDIT_JSON" <<'PY'
import json, sys
path = sys.argv[1]
try:
    data = json.load(open(path, encoding='utf-8'))
except Exception:
    print(-1)
    raise SystemExit(0)
count = 0
for issue in data.get('results', []):
    if issue.get('issue_severity') == 'HIGH' and issue.get('issue_confidence') == 'HIGH':
        count += 1
print(count)
PY
)"

  if [[ "$HIGH_COUNT" == "-1" ]]; then
    fail_step "unable to parse bandit output"
  elif [[ "$HIGH_COUNT" -gt 0 ]]; then
    fail_step "bandit found $HIGH_COUNT HIGH severity / HIGH confidence issue(s)"
  else
    ok_step "no HIGH severity / HIGH confidence bandit findings"
  fi

  rm -f "$BANDIT_JSON"
else
  warn_step "bandit is not installed. Install it with: python -m pip install bandit"
fi

print_header "secret scanner"
SECRET_CONFIG=""
SECRET_TOOL=""

if [[ -f .gitleaks.toml || -f gitleaks.toml ]]; then
  SECRET_CONFIG="gitleaks"
  SECRET_TOOL="gitleaks"
elif [[ -f .secrets.baseline ]]; then
  SECRET_CONFIG="detect-secrets"
  SECRET_TOOL="detect-secrets"
fi

if [[ -n "$SECRET_CONFIG" ]]; then
  if have_cmd "$SECRET_TOOL"; then
    if [[ "$SECRET_TOOL" == "gitleaks" ]]; then
      if gitleaks detect --no-git --source . --redact; then
        ok_step "gitleaks completed with no leaks"
      else
        fail_step "gitleaks reported potential secrets (output is redacted)"
      fi
    else
      if detect-secrets scan --baseline .secrets.baseline >/dev/null; then
        ok_step "detect-secrets baseline check completed"
      else
        fail_step "detect-secrets baseline check reported issues"
      fi
    fi
  else
    warn_step "secret scanner configuration detected ($SECRET_CONFIG) but $SECRET_TOOL is not installed"
  fi
else
  warn_step "no secret scanner configuration detected (.gitleaks.toml, gitleaks.toml, or .secrets.baseline)"
fi

if [[ "$RUN_OUTDATED" -eq 1 ]]; then
  print_header "pip list --outdated"
  if have_cmd pip; then
    if pip list --outdated; then
      ok_step "listed outdated packages"
    else
      warn_step "unable to list outdated packages (check environment/network)"
    fi
  else
    warn_step "pip not found; cannot list outdated packages"
  fi
else
  warn_step "skip outdated package report (run with --outdated to enable)"
fi

exit "$EXIT_CODE"

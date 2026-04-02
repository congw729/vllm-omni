#!/usr/bin/env bash
# Resolve whether this build should skip the main CI image step (skip-ci) using only the GitHub label `skip-ci`.
# Priority: GET commits/{sha}/pulls (labels on PRs) -> BUILDKITE_PULL_REQUEST + issues/{pr}/labels.
# Prints a single digit to stdout: 1 = skip image CI, 0 = run. Logs go to stderr.
# Requires: curl, python3. Optional: GITHUB_TOKEN for GitHub API.
set -euo pipefail

SKIP_LABEL='skip-ci'

parse_github_owner_repo() {
  local r="${BUILDKITE_REPO:?BUILDKITE_REPO must be set}"
  if [[ "$r" =~ github\.com[:/]([^/]+)/([^/.]+)(\.git)?$ ]]; then
    GITHUB_OWNER="${BASH_REMATCH[1]}"
    GITHUB_REPO="${BASH_REMATCH[2]%.git}"
    return 0
  fi
  echo "resolve_skip_ci: cannot parse owner/repo from BUILDKITE_REPO=$r" >&2
  return 1
}

sha="${BUILDKITE_COMMIT:?BUILDKITE_COMMIT must be set}"

if [[ -n "${GITHUB_TOKEN:-}" ]]; then
  auth_hdr=( -H "Authorization: Bearer ${GITHUB_TOKEN}" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" )
  if parse_github_owner_repo; then
    base_url="https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}"
    pulls_json=""
    if pulls_json="$(curl -sf "${auth_hdr[@]}" "${base_url}/commits/${sha}/pulls" 2>/dev/null)"; then
      if python3 -c "
import json, sys
label = 'skip-ci'
data = json.loads(sys.stdin.read() or '[]')
if not isinstance(data, list):
    sys.exit(1)
for pr in data:
    for lb in pr.get('labels') or []:
        if lb.get('name') == label:
            sys.exit(0)
sys.exit(1)
" <<< "${pulls_json}" 2>/dev/null; then
        echo "resolve_skip_ci: label ${SKIP_LABEL} found on PR linked to commit ${sha}; skip-ci=1" >&2
        echo -n 1
        exit 0
      fi
      echo "resolve_skip_ci: no ${SKIP_LABEL} on PR(s) from commits/${sha}/pulls" >&2
    else
      echo "resolve_skip_ci: GET commits/${sha}/pulls failed; trying BUILDKITE_PULL_REQUEST fallback" >&2
    fi
  else
    echo "resolve_skip_ci: cannot parse repo URL; trying BUILDKITE_PULL_REQUEST fallback" >&2
  fi
else
  echo "resolve_skip_ci: GITHUB_TOKEN unset; skipping GitHub API for commit/PR" >&2
fi

if [[ "${BUILDKITE_PULL_REQUEST:-false}" != "false" && -n "${BUILDKITE_PULL_REQUEST:-}" && -n "${GITHUB_TOKEN:-}" ]]; then
  auth_hdr=( -H "Authorization: Bearer ${GITHUB_TOKEN}" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" )
  if parse_github_owner_repo; then
    base_url="https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}"
    pr="${BUILDKITE_PULL_REQUEST}"
    if labels_json="$(curl -sf "${auth_hdr[@]}" "${base_url}/issues/${pr}/labels" 2>/dev/null)"; then
      if python3 -c "import json,sys; a=json.load(sys.stdin); sys.exit(0 if any(x.get('name')=='${SKIP_LABEL}' for x in a) else 1)" <<< "${labels_json}" 2>/dev/null; then
        echo "resolve_skip_ci: label ${SKIP_LABEL} on PR #${pr} (fallback); skip-ci=1" >&2
        echo -n 1
        exit 0
      fi
    fi
  fi
fi

echo "resolve_skip_ci: skip-ci=0" >&2
echo -n 0

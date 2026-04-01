#!/usr/bin/env bash
# Trigger vllm-omni-kanban repository_dispatch after nightly perf distribution.
# Requires (Buildkite-provided): BUILDKITE_BUILD_NUMBER, BUILDKITE_BUILD_URL, BUILDKITE_COMMIT,
#   BUILDKITE_ORGANIZATION_SLUG, BUILDKITE_PIPELINE_SLUG
# Requires (secret): KANBAN_REPO_DISPATCH_TOKEN — GitHub PAT with repo scope for the kanban repo
# Optional: KANBAN_REPO_OWNER (default: same as org guess), KANBAN_REPO_NAME (default: vllm-omni-kanban)

set -euo pipefail

if [[ -z "${KANBAN_REPO_DISPATCH_TOKEN:-}" ]]; then
  echo "KANBAN_REPO_DISPATCH_TOKEN is not set; skipping kanban dispatch."
  exit 0
fi

OWNER="${KANBAN_REPO_OWNER:-${BUILDKITE_ORGANIZATION_SLUG:-}}"
REPO="${KANBAN_REPO_NAME:-vllm-omni-kanban}"

if [[ -z "$OWNER" ]]; then
  echo "Cannot resolve GitHub owner: set KANBAN_REPO_OWNER or BUILDKITE_ORGANIZATION_SLUG."
  exit 1
fi

BN="${BUILDKITE_BUILD_NUMBER:-}"
URL="${BUILDKITE_BUILD_URL:-}"
SHA="${BUILDKITE_COMMIT:-}"
ORG_SLUG="${BUILDKITE_ORGANIZATION_SLUG:-}"
PIPE_SLUG="${BUILDKITE_PIPELINE_SLUG:-}"
BUILD_ID="${BUILDKITE_BUILD_ID:-}"

if [[ -z "$BN" || -z "$ORG_SLUG" || -z "$PIPE_SLUG" ]]; then
  echo "Missing Buildkite metadata (BUILDKITE_BUILD_NUMBER / ORGANIZATION_SLUG / PIPELINE_SLUG)."
  exit 1
fi

payload=$(
  python3 - <<'PY' "$BN" "$URL" "$SHA" "$ORG_SLUG" "$PIPE_SLUG" "$BUILD_ID"
import json, sys
bn, url, sha, org_s, pipe_s, bid = sys.argv[1:7]
client = {
    "build_number": bn,
    "build_url": url,
    "commit": sha,
    "org_slug": org_s,
    "pipeline_slug": pipe_s,
}
if bid:
    client["build_id"] = bid
body = {"event_type": "buildkite_nightly_perf", "client_payload": client}
print(json.dumps(body))
PY
)

api_url="https://api.github.com/repos/${OWNER}/${REPO}/dispatches"
http_code=$(curl -sS -o /tmp/kanban_dispatch_resp.txt -w '%{http_code}' \
  -X POST \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer ${KANBAN_REPO_DISPATCH_TOKEN}" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  "$api_url" \
  -d "$payload")

if [[ "$http_code" != "204" ]]; then
  echo "GitHub dispatch failed: HTTP $http_code"
  cat /tmp/kanban_dispatch_resp.txt >&2 || true
  exit 1
fi

echo "repository_dispatch buildkite_nightly_perf sent to ${OWNER}/${REPO} (HTTP ${http_code})."

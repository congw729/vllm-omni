#!/usr/bin/env bash
# Match PR title to label `skip-ci`: append/remove " [skip vllm-omni ci]" via GitHub API.
# Buildkite: set GITHUB_TOKEN (repo PR write scope) on the pipeline; agent needs curl + python3.
set -euo pipefail

MARKER=' [skip vllm-omni ci]'
SKIP_LABEL='skip-ci'

if [[ "${BUILDKITE_PULL_REQUEST:-false}" == "false" || -z "${BUILDKITE_PULL_REQUEST:-}" ]]; then
  echo "Not a pull request build (BUILDKITE_PULL_REQUEST=${BUILDKITE_PULL_REQUEST:-}); skipping."
  exit 0
fi

if [[ -z "${GITHUB_TOKEN:-}" ]]; then
  echo "GITHUB_TOKEN is not set; skipping PR title sync. Add it in Buildkite pipeline secrets when ready." >&2
  exit 0
fi

parse_github_owner_repo() {
  local r="${BUILDKITE_REPO:?}"
  if [[ "$r" =~ github\.com[:/]([^/]+)/([^/.]+)(\.git)?$ ]]; then
    GITHUB_OWNER="${BASH_REMATCH[1]}"
    GITHUB_REPO="${BASH_REMATCH[2]%.git}"
  else
    echo "Cannot parse owner/repo from BUILDKITE_REPO=$r" >&2
    exit 1
  fi
}

parse_github_owner_repo
pr="${BUILDKITE_PULL_REQUEST}"
base_url="https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}"
auth_hdr=( -H "Authorization: Bearer ${GITHUB_TOKEN}" -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" )

labels_json="$(curl -sf "${auth_hdr[@]}" "${base_url}/issues/${pr}/labels")"
has_skip="$(python3 -c "import json,sys; a=json.load(sys.stdin); print('yes' if any(x.get('name')=='${SKIP_LABEL}' for x in a) else 'no')" <<< "${labels_json}")"

title_json="$(curl -sf "${auth_hdr[@]}" "${base_url}/pulls/${pr}")"
title="$(python3 -c "import json,sys; print(json.load(sys.stdin)['title'])" <<< "${title_json}")"

if [[ "${has_skip}" == "yes" ]]; then
  case "${title}" in
    *"${MARKER}"*)
      echo "Label ${SKIP_LABEL} present and title already contains marker; nothing to do."
      exit 0
      ;;
  esac
  new_title="${title}${MARKER}"
else
  new_title="${title//"${MARKER}"/}"
  new_title="$(printf '%s' "${new_title}" | tr -s ' ' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
  if [[ "${new_title}" == "${title}" ]]; then
    echo "No label ${SKIP_LABEL} and title has no marker; nothing to do."
    exit 0
  fi
  if [[ -z "${new_title}" ]]; then
    echo "Refusing to set empty PR title after marker removal." >&2
    exit 1
  fi
fi

payload="$(python3 -c "import json,sys; print(json.dumps({'title': sys.argv[1]}))" "${new_title}")"
curl -sf -X PATCH "${auth_hdr[@]}" -H "Content-Type: application/json" -d "${payload}" "${base_url}/pulls/${pr}" >/dev/null
echo "Updated PR #${pr} title to match label ${SKIP_LABEL} state."

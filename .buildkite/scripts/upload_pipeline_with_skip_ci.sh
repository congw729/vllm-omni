#!/usr/bin/env bash
# Evaluate skip-ci via GitHub (commit -> PRs -> labels) then upload continuation steps from the same
# `.buildkite/pipeline.yml` (YAML document after the first `---`). Buildkite `if` is evaluated at upload time.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PIPELINE_YML="${ROOT}/.buildkite/pipeline.yml"
SKIP_CI="$(bash "${ROOT}/.buildkite/scripts/resolve_skip_ci_from_commit.sh")"

if [[ ! -f "${PIPELINE_YML}" ]]; then
  echo "upload_pipeline_with_skip_ci: missing ${PIPELINE_YML}" >&2
  exit 1
fi

export ROOT SKIP_CI PIPELINE_YML
python3 <<'PY' | buildkite-agent pipeline upload
import os
import pathlib

path = pathlib.Path(os.environ["PIPELINE_YML"])
text = path.read_text(encoding="utf-8")
sep = "\n---\n"
if sep not in text:
    raise SystemExit(
        "upload_pipeline_with_skip_ci: .buildkite/pipeline.yml must contain a '\\n---\\n' separator "
        "(document 1 = bootstrap, document 2 = uploaded steps)"
    )
_, continuation = text.split(sep, 1)

skip = os.environ.get("SKIP_CI") == "1"
# When skip-ci: skip default CI image, but still build for L4 nightly (PR label nightly-test or main NIGHTLY=1),
# otherwise upload-nightly (depends_on image-build) would be skipped with test-ready/test-merge.
nightly_only = (
    '(build.pull_request.labels includes "nightly-test") '
    '|| (build.branch == "main" && build.env("NIGHTLY") == "1")'
)
# Placeholder in pipeline.yml is `if: __IMAGE_BUILD_IF__` (valid YAML); replace value only.
if skip:
    rep = f"'{nightly_only}'"
else:
    rep = (
        '\'('
        f"({nightly_only}) || "
        '((build.branch != "main" && !(build.pull_request.labels includes "skip-ci")) '
        '|| build.branch == "main"))\''
    )
print(continuation.replace("__IMAGE_BUILD_IF__", rep), end="")
PY

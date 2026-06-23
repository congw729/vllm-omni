#!/usr/bin/env python3
"""Omni serving benchmark client that does not require the ``vllm`` CLI on PATH.

Invokes ``python -m vllm_omni.entrypoints.cli.main bench serve --omni`` so
cross-framework CI images can drive SGLang-Omni servers without installing the
``vllm`` console script. The driver script itself only uses the stdlib.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_RESULT_TEMPLATE = _REPO_ROOT / "tests/dfx/perf/scripts/result_omni_template.json"


def resolve_vllm_omni_python() -> str:
    """Return a Python executable that can import ``vllm_omni`` for ``bench serve --omni``."""
    configured = os.environ.get("VLLM_OMNI_PYTHON")
    if configured:
        path = Path(configured)
        if path.is_file():
            return str(path)

    candidates = (
        _REPO_ROOT.parent / ".venv" / "bin" / "python",
        _REPO_ROOT / ".venv" / "bin" / "python",
    )
    for candidate in candidates:
        if candidate.is_file():
            # Keep the venv shim path; resolving symlinks drops venv site-packages.
            return str(candidate)

    return sys.executable


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-file",
        required=True,
        help="Path where benchmark metrics JSON is written.",
    )
    parser.add_argument(
        "--perf-dump-dir",
        default=None,
        help="Directory for per-request SGLang-Omni perf dumps (sets VLLM_OMNI_BENCH_PERF_DUMP_DIR).",
    )
    parser.add_argument(
        "--request-backend",
        default="sglang_omni",
        choices=["sglang_omni", "vllm_omni"],
        help=argparse.SUPPRESS,
    )
    return parser


def main() -> None:
    parser = _build_parser()
    args, bench_args = parser.parse_known_args()

    output_file = Path(args.output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    prev_perf_dump_dir = os.environ.get("VLLM_OMNI_BENCH_PERF_DUMP_DIR")
    if args.perf_dump_dir:
        os.environ["VLLM_OMNI_BENCH_PERF_DUMP_DIR"] = str(Path(args.perf_dump_dir).resolve())

    cmd = [
        resolve_vllm_omni_python(),
        "-u",
        "-m",
        "vllm_omni.entrypoints.cli.main",
        "bench",
        "serve",
        "--omni",
        *bench_args,
        "--num-warmups",
        "2",
        "--save-result",
        "--result-dir",
        str(output_file.parent),
        "--result-filename",
        output_file.name,
    ]

    print("Running:", " ".join(cmd))
    proc = subprocess.CompletedProcess(args=cmd, returncode=1)
    try:
        proc = subprocess.run(cmd, cwd=str(_REPO_ROOT))
    finally:
        if args.perf_dump_dir:
            if prev_perf_dump_dir is None:
                os.environ.pop("VLLM_OMNI_BENCH_PERF_DUMP_DIR", None)
            else:
                os.environ["VLLM_OMNI_BENCH_PERF_DUMP_DIR"] = prev_perf_dump_dir

    if proc.returncode != 0:
        raise SystemExit(proc.returncode)

    if output_file.exists():
        return

    with open(_RESULT_TEMPLATE, encoding="utf-8") as f:
        payload = json.load(f)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print(f"Benchmark result file not generated, fallback to template: {output_file}")


if __name__ == "__main__":
    main()

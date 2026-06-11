"""Helpers for collecting SGLang per-stage perf dumps written via perf_dump_path."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np


def _stage_durations_from_dump(data: dict[str, Any]) -> dict[str, float]:
    """Parse stage durations from a SGLang perf dump JSON (values in seconds)."""
    stages: dict[str, float] = {}
    for entry in data.get("steps", []):
        if not isinstance(entry, dict):
            continue
        name = entry.get("name")
        duration_ms = entry.get("duration_ms")
        if name is None or duration_ms is None:
            continue
        try:
            stages[str(name)] = float(duration_ms) / 1000.0
        except (TypeError, ValueError):
            continue
    return stages


def load_sglang_perf_dump(path: Path) -> dict[str, float] | None:
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    stages = _stage_durations_from_dump(data)
    return stages or None


def aggregate_stage_durations(stage_lists: dict[str, list[float]]) -> dict[str, dict[str, float]]:
    return {
        "stage_durations_mean": {s: float(np.mean(v)) for s, v in stage_lists.items()},
        "stage_durations_p50": {s: float(np.percentile(v, 50)) for s, v in stage_lists.items()},
        "stage_durations_p99": {s: float(np.percentile(v, 99)) for s, v in stage_lists.items()},
    }


def merge_sglang_perf_dumps_into_metrics(
    perf_dump_dir: str | Path,
    metrics: dict[str, Any],
) -> dict[str, Any]:
    """Read per-request SGLang perf dumps and merge stage aggregates into metrics."""
    dump_dir = Path(perf_dump_dir)
    if not dump_dir.is_dir():
        return metrics

    stage_duration_lists: dict[str, list[float]] = {}
    for dump_path in sorted(dump_dir.glob("req_*.json")):
        stages = load_sglang_perf_dump(dump_path)
        if not stages:
            continue
        for stage, duration_s in stages.items():
            stage_duration_lists.setdefault(stage, []).append(duration_s)

    if not stage_duration_lists:
        return metrics

    merged = dict(metrics)
    merged.update(aggregate_stage_durations(stage_duration_lists))
    merged["sglang_perf_dump_dir"] = str(dump_dir.resolve())
    merged["sglang_perf_dump_count"] = len(list(dump_dir.glob("req_*.json")))
    return merged

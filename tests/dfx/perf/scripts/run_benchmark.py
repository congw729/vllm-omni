import json
import os
import subprocess
import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

from tests.dfx.conftest import (
    create_benchmark_indices,
    create_test_parameter_mapping,
    create_unique_server_params,
    get_benchmark_params_for_server,
    load_configs,
    resolve_baseline_value,
)
from tests.dfx.perf.scripts.sglang_omni_server import (
    SglangOmniServer,
    unique_sglang_omni_server_params,
)

pytestmark = [pytest.mark.full_model]

# Compare metrics to each test JSON ``baseline`` block only when pytest is run with ``--assert-baseline``
# (registered in ``tests/dfx/conftest.py``; default: off).

if os.environ.get("VLLM_WORKER_MULTIPROC_METHOD") is None:
    os.environ["VLLM_WORKER_MULTIPROC_METHOD"] = "spawn"

_REPO_ROOT = Path(__file__).resolve().parents[4]
OMNI_BENCHMARK_SCRIPT = str(_REPO_ROOT / "benchmarks" / "omni" / "omni_benchmark_serving.py")
OMNI_RESULT_TEMPLATE_PATH = Path(__file__).resolve().parent / "result_omni_template.json"


def _get_config_file_from_argv() -> str | None:
    """Read ``--test-config-file`` from ``sys.argv`` at import time so parametrization can use it."""
    for i, arg in enumerate(sys.argv):
        if arg == "--test-config-file" and i + 1 < len(sys.argv):
            return sys.argv[i + 1]
        if arg.startswith("--test-config-file="):
            return arg.split("=", 1)[1]
    return None


_PERF_TESTS_DIR = Path(__file__).resolve().parent.parent / "tests"
_DEFAULT_CONFIG_FILE = str(_PERF_TESTS_DIR / "test_qwen_omni.json")

CONFIG_FILE_PATH = _get_config_file_from_argv()
if CONFIG_FILE_PATH is None:
    print(
        "No --test-config-file in argv, using default: tests/dfx/perf/tests/test_qwen_omni.json "
        "(override with e.g. --test-config-file tests/dfx/perf/tests/test_tts.json)"
    )
    CONFIG_FILE_PATH = _DEFAULT_CONFIG_FILE

BENCHMARK_CONFIGS = load_configs(CONFIG_FILE_PATH)


def _server_mode(configs: list[dict[str, Any]]) -> str:
    server_types = {cfg.get("server_type", "vllm-omni") for cfg in configs}
    if len(server_types) != 1:
        raise ValueError(
            "Mixed server_type values in one benchmark config file are unsupported: "
            f"{sorted(server_types)}. Split vLLM-Omni and sglang-omni into separate JSON files."
        )
    return next(iter(server_types))


SERVER_MODE = _server_mode(BENCHMARK_CONFIGS)
BENCHMARK_RESULT_DIR = Path(os.environ.get("BENCHMARK_DIR", "tests/dfx/perf/results"))

DEPLOY_CONFIGS_DIR = Path(__file__).parent.parent / "deploy"
server_to_benchmark_mapping = create_test_parameter_mapping(BENCHMARK_CONFIGS)

if SERVER_MODE == "sglang-omni":
    test_params = unique_sglang_omni_server_params(BENCHMARK_CONFIGS)
else:
    test_params = create_unique_server_params(BENCHMARK_CONFIGS, DEPLOY_CONFIGS_DIR)

benchmark_indices = create_benchmark_indices(BENCHMARK_CONFIGS, server_to_benchmark_mapping)

_server_lock = threading.Lock()


def _server_cfg_for_test(test_name: str) -> dict[str, Any] | None:
    if SERVER_MODE != "sglang-omni":
        return None
    for cfg in test_params:
        if cfg["test_name"] == test_name:
            return cfg
    return None


def _safe_filename_token(value: Any | None, *, default: str = "na") -> str:
    if value is None:
        return default
    s = str(value).strip()
    for bad in ("/", "\\", ":", "*", "?", '"', "<", ">", "|"):
        s = s.replace(bad, "_")
    return s if s else default


def _baseline_thresholds_for_step(
    baseline_data: dict[str, Any],
    *,
    sweep_index: int | None = None,
    max_concurrency: Any = None,
    request_rate: Any = None,
) -> dict[str, Any]:
    return {
        metric_name: resolve_baseline_value(
            baseline_raw,
            sweep_index=sweep_index,
            max_concurrency=max_concurrency,
            request_rate=request_rate,
        )
        for metric_name, baseline_raw in baseline_data.items()
    }


def run_sglang_omni_benchmark(
    args: list[str],
    test_name: str,
    flow: Any,
    dataset_name: str,
    num_prompt: int,
    *,
    baseline_config: dict[str, Any] | None = None,
    sweep_index: int | None = None,
    request_rate: Any | None = None,
    max_concurrency: Any | None = None,
    random_input_len: Any | None = None,
    random_output_len: Any | None = None,
    server_cfg: dict[str, Any] | None = None,
    perf_dump_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Run ``omni_benchmark_serving.py`` (no ``vllm`` CLI) and return parsed metrics."""
    server_cfg = server_cfg or {}
    server_type = str(server_cfg.get("server_type", "sglang-omni"))
    request_backend = "sglang_omni"
    perf_dump_path: Path | None = None
    if perf_dump_dir is not None:
        perf_dump_path = Path(perf_dump_dir)
        perf_dump_path.mkdir(parents=True, exist_ok=True)

    current_dt = datetime.now().strftime("%Y%m%d-%H%M%S")
    ri = _safe_filename_token(random_input_len)
    ro = _safe_filename_token(random_output_len)
    result_filename = f"result_{test_name}_{dataset_name}_{flow}_{num_prompt}_in{ri}_out{ro}_{current_dt}.json"
    result_dir = Path(os.environ.get("BENCHMARK_DIR", "tests/dfx/perf/results"))
    result_dir.mkdir(parents=True, exist_ok=True)
    result_path = result_dir / result_filename

    log_dir = BENCHMARK_RESULT_DIR / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{test_name}_{dataset_name}_{flow}_{num_prompt}_{current_dt}.log"

    cmd = [
        sys.executable,
        "-u",
        OMNI_BENCHMARK_SCRIPT,
        "--request-backend",
        request_backend,
        "--output-file",
        str(result_path),
        *args,
    ]
    if perf_dump_path is not None:
        cmd.extend(["--perf-dump-dir", str(perf_dump_path.resolve())])

    print(f"\nRunning SGLang-Omni benchmark: {' '.join(cmd)}")
    print(f"  Log file: {log_file}")

    with open(log_file, "w", encoding="utf-8") as log_fh:
        log_fh.write(f"cmd: {' '.join(cmd)}\n\n")
        log_fh.flush()
        process = subprocess.Popen(
            cmd,
            stdout=log_fh,
            stderr=log_fh,
            cwd=str(_REPO_ROOT),
        )
        process.wait()

    with open(log_file, encoding="utf-8") as log_fh:
        print(log_fh.read(), end="")

    if process.returncode != 0:
        print(f"ERROR: omni benchmark script exited with code {process.returncode}")

    if not result_path.exists():
        with open(OMNI_RESULT_TEMPLATE_PATH, encoding="utf-8") as f:
            template_result: dict[str, Any] = json.load(f)
        with open(result_path, "w", encoding="utf-8") as f:
            json.dump(template_result, f, ensure_ascii=False, indent=2)
        print(f"Benchmark result file not generated, fallback to template: {result_path}")
        result = template_result
    else:
        with open(result_path, encoding="utf-8") as f:
            result = json.load(f)

    if perf_dump_path is not None:
        from benchmarks.diffusion.sglang_perf import merge_sglang_perf_dumps_into_metrics

        result = merge_sglang_perf_dumps_into_metrics(perf_dump_path, result)

    result["framework"] = server_type
    result["request_backend"] = request_backend
    result["log_file"] = str(log_file)

    if baseline_config:
        result["baseline"] = _baseline_thresholds_for_step(
            baseline_config,
            sweep_index=sweep_index,
            request_rate=request_rate,
            max_concurrency=max_concurrency,
        )
    else:
        result["baseline"] = {}
    if random_input_len is not None:
        result["random_input_len"] = random_input_len
    if random_output_len is not None:
        result["random_output_len"] = random_output_len
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    return result


if SERVER_MODE != "sglang-omni":
    from tests.dfx.conftest import run_benchmark as run_vllm_omni_benchmark


@pytest.fixture(scope="module")
def omni_server(request):
    """Start vLLM-Omni or SGLang-Omni server as a subprocess with actual model weights."""
    with _server_lock:
        if SERVER_MODE == "sglang-omni":
            server_cfg: dict[str, Any] = request.param
            test_name = server_cfg["test_name"]
            print(f"Starting SglangOmniServer with test: {test_name}, model: {server_cfg['model']}")
            with SglangOmniServer(server_cfg) as server:
                server.test_name = test_name
                print("SglangOmniServer started successfully")
                yield server
                print("SglangOmniServer stopping...")
            print("SglangOmniServer stopped")
            return

        from tests.helpers.runtime import OmniServer

        test_name, model, stage_config_path, stage_overrides, extra_cli_args, use_omni = request.param

        print(f"Starting OmniServer with test: {test_name}, model: {model}")

        server_args: list[str] = []
        if use_omni:
            server_args += ["--stage-init-timeout", "600", "--init-timeout", "900"]
        if stage_config_path:
            server_args = ["--deploy-config", stage_config_path] + server_args
        if stage_overrides:
            server_args = ["--stage-overrides", stage_overrides] + server_args
        if extra_cli_args:
            server_args = list(extra_cli_args) + server_args
        with OmniServer(model, server_args, use_omni=use_omni) as server:
            server.test_name = test_name
            print("OmniServer started successfully")
            yield server
            print("OmniServer stopping...")

        print("OmniServer stopped")


@pytest.fixture
def benchmark_params(request, omni_server):
    """Benchmark parameters fixture with proper parametrization"""
    test_name, param_index = request.param

    if test_name != omni_server.test_name:
        pytest.skip(f"Skipping parameter for {test_name} - current server is {omni_server.test_name}")

    all_params = get_benchmark_params_for_server(test_name, server_to_benchmark_mapping)

    if not all_params:
        raise ValueError(f"No benchmark parameters found for test: {test_name}")

    if param_index >= len(all_params):
        raise ValueError(f"No benchmark parameters found for index {param_index} in test: {test_name}")

    current = param_index + 1
    total = len(all_params)
    print(f"\n  Running benchmark {current}/{total} for {test_name}")

    return {
        "test_name": test_name,
        "params": all_params[param_index],
    }


def assert_result(
    result,
    params,
    num_prompt,
    *,
    assert_baseline: bool,
    sweep_index: int | None = None,
    max_concurrency: Any | None = None,
    request_rate: Any | None = None,
) -> None:
    assert result["completed"] == num_prompt, "Request failures exist"
    if not assert_baseline:
        return
    baseline_data = params.get("baseline", {})
    for metric_name, baseline_raw in baseline_data.items():
        current_value = result[metric_name]
        baseline_value = resolve_baseline_value(
            baseline_raw,
            sweep_index=sweep_index,
            max_concurrency=max_concurrency,
            request_rate=request_rate,
        )
        if "throughput" in metric_name:
            if current_value <= baseline_value:
                print(
                    f"ERROR: Throughput test results were below baseline: {metric_name}: {current_value} > {baseline_value}"
                )
        else:
            if current_value >= baseline_value:
                print(f"ERROR: Test results exceeded baseline: {metric_name}: {current_value} < {baseline_value}")


def _resolve_perf_dump_dir(test_name: str, dataset_name: str, flow: Any, num_prompt: int) -> Path | None:
    if SERVER_MODE != "sglang-omni":
        return None
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    dump_dir = (
        BENCHMARK_RESULT_DIR / "sglang_omni_perf_dumps" / f"{test_name}_{dataset_name}_{flow}_{num_prompt}_{timestamp}"
    )
    dump_dir.mkdir(parents=True, exist_ok=True)
    return dump_dir


def _dispatch_run_benchmark(**kwargs: Any) -> dict[str, Any]:
    if SERVER_MODE == "sglang-omni":
        return run_sglang_omni_benchmark(**kwargs)
    return run_vllm_omni_benchmark(**kwargs)


@pytest.mark.benchmark
@pytest.mark.parametrize("omni_server", test_params, indirect=True)
@pytest.mark.parametrize("benchmark_params", benchmark_indices, indirect=True)
def test_performance_benchmark(omni_server, benchmark_params, request):
    test_name = benchmark_params["test_name"]
    params = benchmark_params["params"]
    dataset_name = params.get("dataset_name", "")

    host = omni_server.host
    port = omni_server.port
    model = getattr(omni_server, "model_id", omni_server.model)
    server_cfg = _server_cfg_for_test(test_name)

    print(f"Running benchmark for model: {model} (server_mode={SERVER_MODE})")
    print(f"Benchmark parameters: {benchmark_params}")

    assert_baseline = request.config.getoption("--assert-baseline", default=False)

    def to_list(value, default=None):
        if value is None:
            return [] if default is None else [default]
        return [value] if not isinstance(value, (list, tuple)) else list(value)

    qps_list = to_list(params.get("request_rate"))
    num_prompt_list = to_list(params.get("num_prompts"))
    max_concurrency_list = to_list(params.get("max_concurrency"))

    max_len = max(len(qps_list), len(max_concurrency_list))
    if len(num_prompt_list) == 1 and max_len > 1:
        num_prompt_list = num_prompt_list * max_len
    elif max_len == 1 and len(num_prompt_list) > 1:
        if len(qps_list) == 1:
            qps_list = qps_list * len(num_prompt_list)
        if len(max_concurrency_list) == 1:
            max_concurrency_list = max_concurrency_list * len(num_prompt_list)
        max_len = max(len(qps_list), len(max_concurrency_list))
    elif len(num_prompt_list) != max_len and max_len > 0:
        raise ValueError("The number of prompts does not match the QPS or max_concurrency")

    args = ["--host", host, "--port", str(port), "--model", model]
    exclude_keys = {
        "request_rate",
        "baseline",
        "num_prompts",
        "max_concurrency",
        "task",
        "enabled",
        "eval_phase",
        "trust_remote_code",
    }

    for key, value in params.items():
        if key in exclude_keys or value is None:
            continue

        arg_name = f"--{key.replace('_', '-')}"

        if isinstance(value, bool) and value:
            args.append(arg_name)
        elif isinstance(value, dict):
            json_str = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
            args.extend([arg_name, json_str])
        elif not isinstance(value, bool):
            args.extend([arg_name, str(value)])

    for config in BENCHMARK_CONFIGS:
        if config.get("test_name") != test_name:
            continue
        server_params = config.get("server_params") or {}
        if server_params.get("trust_remote_code") or params.get("trust_remote_code"):
            args.append("--trust-remote-code")
        break

    base_args = list(args)

    # QPS / request-rate sweep
    for i, (qps, num_prompt) in enumerate(zip(qps_list, num_prompt_list)):
        sweep_args = base_args + ["--request-rate", str(qps), "--num-prompts", str(num_prompt)]
        result = _dispatch_run_benchmark(
            args=sweep_args,
            test_name=test_name,
            flow=qps,
            dataset_name=dataset_name,
            num_prompt=num_prompt,
            baseline_config=params.get("baseline"),
            sweep_index=i,
            request_rate=qps,
            max_concurrency=None,
            random_input_len=params.get("random_input_len"),
            random_output_len=params.get("random_output_len"),
            server_cfg=server_cfg,
            perf_dump_dir=_resolve_perf_dump_dir(test_name, dataset_name, qps, num_prompt),
        )
        assert_result(
            result,
            params,
            num_prompt,
            assert_baseline=assert_baseline,
            sweep_index=i,
            request_rate=qps,
        )

    # concurrency test
    for i, (concurrency, num_prompt) in enumerate(zip(max_concurrency_list, num_prompt_list)):
        sweep_args = base_args + [
            "--max-concurrency",
            str(concurrency),
            "--num-prompts",
            str(num_prompt),
            "--request-rate",
            "inf",
        ]
        result = _dispatch_run_benchmark(
            args=sweep_args,
            test_name=test_name,
            flow=concurrency,
            dataset_name=dataset_name,
            num_prompt=num_prompt,
            baseline_config=params.get("baseline"),
            sweep_index=i,
            request_rate=None,
            max_concurrency=concurrency,
            random_input_len=params.get("random_input_len"),
            random_output_len=params.get("random_output_len"),
            server_cfg=server_cfg,
            perf_dump_dir=_resolve_perf_dump_dir(test_name, dataset_name, concurrency, num_prompt),
        )
        assert_result(
            result,
            params,
            num_prompt,
            assert_baseline=assert_baseline,
            sweep_index=i,
            max_concurrency=concurrency,
        )

"""SGLang-Omni server launcher for DFX omni perf benchmarks."""

from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import psutil

_REPO_ROOT = Path(__file__).resolve().parents[4]
_PATH_SERVE_ARG_KEYS = frozenset({"config"})


def resolve_sglang_omni_root() -> Path:
    """Return the sglang-omni repo root used for ``sgl-omni serve`` cwd and config paths."""
    configured = os.environ.get("SGLANG_OMNI_ROOT")
    if configured:
        return Path(configured).resolve()
    sibling = _REPO_ROOT.parent / "sglang-omni"
    if sibling.is_dir():
        return sibling.resolve()
    return _REPO_ROOT.resolve()


def _resolve_serve_arg_value(key: str, value: Any, *, root: Path) -> str:
    if key not in _PATH_SERVE_ARG_KEYS:
        return str(value)
    path = Path(str(value))
    if not path.is_absolute():
        path = root / path
    if not path.is_file():
        raise FileNotFoundError(f"SGLang-Omni serve arg --{key} path not found: {path}")
    return str(path)


def resolve_sglang_omni_config_root() -> Path:
    """Return the repo root used to resolve relative ``--config`` paths."""
    configured = os.environ.get("VLLM_OMNI_ROOT")
    if configured:
        return Path(configured).resolve()
    return _REPO_ROOT.resolve()


def _get_open_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def _wait_for_port(host: str, port: int, *, proc: subprocess.Popen | None = None, timeout: int = 900) -> None:
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                if s.connect_ex((host, port)) == 0:
                    return
        except OSError:
            pass
        if proc is not None:
            ret = proc.poll()
            if ret is not None:
                raise RuntimeError(f"SGLang-Omni server exited with code {ret} before port {host}:{port} became ready")
        time.sleep(2)
    raise RuntimeError(f"SGLang-Omni server did not start on {host}:{port} within {timeout}s")


def _kill_process_tree(pid: int) -> None:
    try:
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)
        for child in children:
            try:
                child.terminate()
            except psutil.NoSuchProcess:
                pass
        gone, alive = psutil.wait_procs(children, timeout=10)
        for child in alive:
            try:
                child.kill()
            except psutil.NoSuchProcess:
                pass
        try:
            parent.terminate()
            parent.wait(timeout=10)
        except (psutil.NoSuchProcess, psutil.TimeoutExpired):
            try:
                parent.kill()
            except psutil.NoSuchProcess:
                pass
    except psutil.NoSuchProcess:
        pass


def resolve_sglang_omni_executable() -> str:
    configured = os.environ.get("SGLANG_OMNI_EXECUTABLE")
    if configured:
        return configured
    for name in ("sgl-omni", "sglang-omni"):
        sibling = Path(sys.executable).with_name(name)
        if sibling.is_file():
            return str(sibling)
        discovered = shutil.which(name)
        if discovered:
            return discovered
    return "sgl-omni"


def build_sglang_omni_serve_args(serve_args_dict: dict[str, Any]) -> list[str]:
    config_root = resolve_sglang_omni_config_root()
    args: list[str] = []
    for key, value in serve_args_dict.items():
        flag = f"--{key}"
        if isinstance(value, bool):
            args.extend([flag, str(value).lower()])
        elif isinstance(value, dict):
            args.extend([flag, json.dumps(value, separators=(",", ":"))])
        elif value is not None:
            args.extend([flag, _resolve_serve_arg_value(key, value, root=config_root)])
    return args


def unique_sglang_omni_server_params(configs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for cfg in configs:
        test_name = cfg["test_name"]
        if test_name in seen:
            continue
        seen.add(test_name)
        server_type = cfg.get("server_type", "vllm-omni")
        if server_type != "sglang-omni":
            raise ValueError(f"Expected server_type=sglang-omni, got {server_type!r} in {test_name}")
        serve_args_dict = cfg["server_params"].get("serve_args", {})
        out.append(
            {
                "test_name": test_name,
                "server_type": server_type,
                "model": cfg["server_params"]["model"],
                "serve_args_dict": serve_args_dict,
                "serve_args": build_sglang_omni_serve_args(serve_args_dict),
                "env_overrides": cfg["server_params"].get("env", {}),
                "server_params": cfg["server_params"],
            }
        )
    return out


class SglangOmniServer:
    """Launch ``sgl-omni serve`` for Qwen3-Omni chat + speech benchmarks."""

    server_type = "sglang-omni"

    def __init__(self, server_cfg: dict[str, Any], *, port: int | None = None) -> None:
        self.server_cfg = server_cfg
        self.model = server_cfg["model"]
        self.serve_args = server_cfg["serve_args"]
        self.host = "127.0.0.1"
        self.port = port if port is not None else _get_open_port()
        self.env_overrides = server_cfg.get("env_overrides", {})
        self.proc: subprocess.Popen | None = None
        self.test_name: str = ""

    @property
    def model_id(self) -> str:
        return self.model

    def _start_server(self) -> None:
        env = os.environ.copy()
        env.update(self.env_overrides)
        cmd = [
            resolve_sglang_omni_executable(),
            "serve",
            "--model-path",
            self.model,
            "--host",
            self.host,
            "--port",
            str(self.port),
        ] + self.serve_args
        print(f"Launching SglangOmniServer: {' '.join(cmd)}")
        if self.env_overrides:
            print(f"  Extra env: {self.env_overrides}")
        self.proc = subprocess.Popen(cmd, env=env, cwd=str(resolve_sglang_omni_root()))
        _wait_for_port(self.host, self.port, proc=self.proc)
        print(f"SglangOmniServer ready on {self.host}:{self.port}")

    def __enter__(self):
        self._start_server()
        return self

    def __exit__(self, *_):
        if self.proc:
            _kill_process_tree(self.proc.pid)

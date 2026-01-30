# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright contributors to the vLLM project
"""
Common fixtures and utilities for offline inference example tests.
"""

import os
import subprocess
import sys
from pathlib import Path

# --- Constants ---

REPO_ROOT = Path(__file__).parent.parent.parent.parent
EXAMPLES_DIR = REPO_ROOT / "examples" / "offline_inference"

# Default stage configs located in vllm_omni package (same as used by examples)
STAGE_CONFIGS_DIR = REPO_ROOT / "vllm_omni" / "model_executor" / "stage_configs"

# Script execution timeout (seconds)
DEFAULT_TIMEOUT = 600


# --- Helper Functions ---


def get_stage_config_path(model_name: str) -> str:
    """Get the appropriate stage config path based on model.

    Uses the same default configs as the example scripts in
    vllm_omni/model_executor/stage_configs/.
    """
    if "qwen3" in model_name.lower():
        config_name = "qwen3_omni_moe.yaml"
    else:
        config_name = "qwen2_5_omni.yaml"

    config_path = STAGE_CONFIGS_DIR / config_name
    return str(config_path)


def run_end2end_script(
    model_dir: str,
    query_type: str,
    output_dir: str,
    stage_config_path: str,
    timeout: int = DEFAULT_TIMEOUT,
    modalities: str = None,
) -> subprocess.CompletedProcess:
    """
    Run the end2end.py script with specified parameters.

    Args:
        model_dir: Directory name under examples/offline_inference/ (e.g., "qwen3_omni")
        query_type: Query type to test (e.g., "text", "use_audio")
        output_dir: Directory to save output files
        stage_config_path: Path to the stage config YAML file
        timeout: Script execution timeout in seconds
        modalities: Output modalities (optional, e.g., "text" for text-only output)

    Returns:
        CompletedProcess instance with returncode, stdout, and stderr
    """
    script_path = EXAMPLES_DIR / model_dir / "end2end.py"

    cmd = [
        sys.executable,
        str(script_path),
        "--query-type",
        query_type,
        "--output-wav",
        output_dir,
        "--stage-configs-path",
        stage_config_path,
    ]

    if modalities:
        cmd.extend(["--modalities", modalities])

    env = os.environ.copy()
    env["VLLM_WORKER_MULTIPROC_METHOD"] = "spawn"

    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
        cwd=str(REPO_ROOT),
    )


def verify_output_files(output_dir: str, expect_audio: bool = True) -> None:
    """
    Verify that expected output files were generated.

    Args:
        output_dir: Directory containing output files
        expect_audio: Whether to expect audio output files
    """
    output_path = Path(output_dir)

    # Check for text output files
    txt_files = list(output_path.glob("*.txt"))
    assert len(txt_files) > 0, f"No text output files found in {output_dir}"

    # Check for audio output files if expected
    if expect_audio:
        wav_files = list(output_path.glob("*.wav"))
        assert len(wav_files) > 0, f"No audio output files found in {output_dir}"


def check_shell_script_syntax(script_path: Path) -> None:
    """Check shell script syntax using bash -n."""
    if script_path.exists():
        result = subprocess.run(
            ["bash", "-n", str(script_path)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Shell script syntax error in {script_path.name}: {result.stderr}"

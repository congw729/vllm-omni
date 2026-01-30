# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright contributors to the vLLM project
"""
E2E tests for offline inference example scripts under examples/offline_inference/.

These tests verify that the example scripts (end2end.py) work correctly
with different query types for both Qwen3-Omni and Qwen2.5-Omni models.
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
from vllm.platforms import current_platform

# --- Constants ---

REPO_ROOT = Path(__file__).parent.parent.parent
EXAMPLES_DIR = REPO_ROOT / "examples" / "offline_inference"

# CI stage configs for different platforms
STAGE_CONFIGS_DIR = REPO_ROOT / "tests" / "e2e" / "offline_inference" / "stage_configs"

# Model configurations
QWEN3_OMNI_MODEL = "Qwen/Qwen3-Omni-30B-A3B-Instruct"
QWEN2_5_OMNI_MODEL = "Qwen/Qwen2.5-Omni-7B"

# Query types supported by each model
QWEN3_OMNI_QUERY_TYPES = ["text", "use_audio", "use_image", "use_video"]
QWEN2_5_OMNI_QUERY_TYPES = ["text", "use_audio", "use_mixed_modalities"]

# Script execution timeout (seconds)
DEFAULT_TIMEOUT = 600


# --- Helper Functions ---

if current_platform.is_rocm():
    is_rocm = True
else:
    is_rocm = False


def get_stage_config_path(model_name: str) -> str:
    """Get the appropriate stage config path based on model and platform."""
    if "qwen3" in model_name.lower():
        config_name = "qwen3_omni_ci.yaml"
    else:
        config_name = "qwen2_5_omni_ci.yaml"

    if is_rocm():
        config_path = STAGE_CONFIGS_DIR / "rocm" / config_name
    else:
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


# --- Test Cases for Qwen3-Omni ---


@pytest.mark.omni
@pytest.mark.parametrize("query_type", QWEN3_OMNI_QUERY_TYPES)
def test_qwen3_omni_end2end(query_type: str) -> None:
    """Test qwen3_omni end2end.py with different query types."""
    stage_config_path = get_stage_config_path(QWEN3_OMNI_MODEL)

    with tempfile.TemporaryDirectory() as tmp_dir:
        result = run_end2end_script(
            model_dir="qwen3_omni",
            query_type=query_type,
            output_dir=tmp_dir,
            stage_config_path=stage_config_path,
        )

        # Verify script executed successfully
        assert result.returncode == 0, (
            f"qwen3_omni end2end.py failed with query_type={query_type}\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )

        # Verify output files were generated
        verify_output_files(tmp_dir, expect_audio=True)


@pytest.mark.omni
@pytest.mark.parametrize("query_type", ["text"])
def test_qwen3_omni_text_only_output(query_type: str) -> None:
    """Test qwen3_omni end2end.py with text-only output modality."""
    stage_config_path = get_stage_config_path(QWEN3_OMNI_MODEL)

    with tempfile.TemporaryDirectory() as tmp_dir:
        result = run_end2end_script(
            model_dir="qwen3_omni",
            query_type=query_type,
            output_dir=tmp_dir,
            stage_config_path=stage_config_path,
            modalities="text",
        )

        # Verify script executed successfully
        assert result.returncode == 0, (
            f"qwen3_omni end2end.py (text-only) failed\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )

        # Verify text output exists (no audio expected)
        verify_output_files(tmp_dir, expect_audio=False)


# --- Test Cases for Qwen2.5-Omni ---


@pytest.mark.omni
@pytest.mark.parametrize("query_type", QWEN2_5_OMNI_QUERY_TYPES)
def test_qwen2_5_omni_end2end(query_type: str) -> None:
    """Test qwen2_5_omni end2end.py with different query types."""
    stage_config_path = get_stage_config_path(QWEN2_5_OMNI_MODEL)

    with tempfile.TemporaryDirectory() as tmp_dir:
        result = run_end2end_script(
            model_dir="qwen2_5_omni",
            query_type=query_type,
            output_dir=tmp_dir,
            stage_config_path=stage_config_path,
        )

        # Verify script executed successfully
        assert result.returncode == 0, (
            f"qwen2_5_omni end2end.py failed with query_type={query_type}\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )

        # Verify output files were generated
        verify_output_files(tmp_dir, expect_audio=True)


@pytest.mark.omni
@pytest.mark.parametrize("query_type", ["text"])
def test_qwen2_5_omni_text_only_output(query_type: str) -> None:
    """Test qwen2_5_omni end2end.py with text-only output modality."""
    stage_config_path = get_stage_config_path(QWEN2_5_OMNI_MODEL)

    with tempfile.TemporaryDirectory() as tmp_dir:
        result = run_end2end_script(
            model_dir="qwen2_5_omni",
            query_type=query_type,
            output_dir=tmp_dir,
            stage_config_path=stage_config_path,
            modalities="text",
        )

        # Verify script executed successfully
        assert result.returncode == 0, (
            f"qwen2_5_omni end2end.py (text-only) failed\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )

        # Verify text output exists (no audio expected)
        verify_output_files(tmp_dir, expect_audio=False)


# --- Shell Script Tests ---


@pytest.mark.omni
def test_qwen3_omni_shell_scripts_syntax() -> None:
    """Verify qwen3_omni shell scripts have valid syntax."""
    shell_scripts = [
        "run_single_prompt.sh",
        "run_single_prompt_tp.sh",
        "run_multiple_prompts.sh",
    ]

    for script_name in shell_scripts:
        script_path = EXAMPLES_DIR / "qwen3_omni" / script_name
        if script_path.exists():
            # Check shell script syntax using bash -n
            result = subprocess.run(
                ["bash", "-n", str(script_path)],
                capture_output=True,
                text=True,
            )
            assert result.returncode == 0, f"Shell script syntax error in {script_name}: {result.stderr}"


@pytest.mark.omni
def test_qwen2_5_omni_shell_scripts_syntax() -> None:
    """Verify qwen2_5_omni shell scripts have valid syntax."""
    shell_scripts = [
        "run_single_prompt.sh",
        "run_multiple_prompts.sh",
    ]

    for script_name in shell_scripts:
        script_path = EXAMPLES_DIR / "qwen2_5_omni" / script_name
        if script_path.exists():
            # Check shell script syntax using bash -n
            result = subprocess.run(
                ["bash", "-n", str(script_path)],
                capture_output=True,
                text=True,
            )
            assert result.returncode == 0, f"Shell script syntax error in {script_name}: {result.stderr}"

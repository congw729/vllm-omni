# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright contributors to the vLLM project
"""
E2E tests for Qwen2.5-Omni offline inference examples.

Tests verify that examples/offline_inference/qwen2_5_omni/end2end.py works correctly
with different query types and output modalities.
"""

import tempfile

import pytest

from .conftest import (
    EXAMPLES_DIR,
    check_shell_script_syntax,
    get_stage_config_path,
    run_end2end_script,
    verify_output_files,
)

# Model configuration
MODEL_NAME = "Qwen/Qwen2.5-Omni-7B"
MODEL_DIR = "qwen2_5_omni"

# Query types supported by Qwen2.5-Omni (must match query_map in end2end.py)
QUERY_TYPES = [
    "text",
    "use_audio",
    "use_image",
    "use_video",
    "use_multi_audios",
    "use_mixed_modalities",
    "use_audio_in_video",
]

# Shell scripts to verify
SHELL_SCRIPTS = [
    "run_single_prompt.sh",
    "run_multiple_prompts.sh",
]


# --- Test Cases ---


@pytest.mark.omni
@pytest.mark.parametrize("query_type", QUERY_TYPES)
def test_end2end(query_type: str) -> None:
    """Test qwen2_5_omni end2end.py with different query types."""
    stage_config_path = get_stage_config_path(MODEL_NAME)

    with tempfile.TemporaryDirectory() as tmp_dir:
        result = run_end2end_script(
            model_dir=MODEL_DIR,
            query_type=query_type,
            output_dir=tmp_dir,
            stage_config_path=stage_config_path,
        )

        assert result.returncode == 0, (
            f"qwen2_5_omni end2end.py failed with query_type={query_type}\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )

        verify_output_files(tmp_dir, expect_audio=True)


@pytest.mark.omni
@pytest.mark.parametrize("query_type", ["text"])
def test_text_only_output(query_type: str) -> None:
    """Test qwen2_5_omni end2end.py with text-only output modality."""
    stage_config_path = get_stage_config_path(MODEL_NAME)

    with tempfile.TemporaryDirectory() as tmp_dir:
        result = run_end2end_script(
            model_dir=MODEL_DIR,
            query_type=query_type,
            output_dir=tmp_dir,
            stage_config_path=stage_config_path,
            modalities="text",
        )

        assert result.returncode == 0, (
            f"qwen2_5_omni end2end.py (text-only) failed\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )

        verify_output_files(tmp_dir, expect_audio=False)


@pytest.mark.omni
def test_shell_scripts_syntax() -> None:
    """Verify qwen2_5_omni shell scripts have valid syntax."""
    for script_name in SHELL_SCRIPTS:
        script_path = EXAMPLES_DIR / MODEL_DIR / script_name
        check_shell_script_syntax(script_path)

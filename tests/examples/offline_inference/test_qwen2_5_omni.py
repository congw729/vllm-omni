"""
Example Offline tests for Qwen2.5-Omni model.
Test cases based on run_single_prompt.sh and run_multiple_prompts.sh
"""

import os
import subprocess
from pathlib import Path

os.environ["VLLM_WORKER_MULTIPROC_METHOD"] = "spawn"

# Example directory path
EXAMPLE_DIR = Path(__file__).parent.parent.parent.parent / "examples" / "offline_inference" / "qwen2_5_omni"


def run_cmd(command, timeout=600, cwd=None):
    """Run command and return output."""
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=cwd,
    )

    if result.returncode != 0:
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        raise subprocess.CalledProcessError(result.returncode, command)

    print(f"STDOUT:\n{result.stdout}")
    return result.stdout


def test_run_single_prompt() -> None:
    """Test single prompt with mixed modalities.

    Equivalent to run_single_prompt.sh:
        python end2end.py --output-wav output_audio --query-type use_mixed_modalities
    """
    command = [
        "python",
        "end2end.py",
        "--output-wav",
        "output_audio",
        "--query-type",
        "use_mixed_modalities",
    ]

    run_cmd(command, cwd=str(EXAMPLE_DIR))

    # Verify output files were created
    output_dir = EXAMPLE_DIR / "output_audio"
    assert output_dir.exists(), f"Output directory {output_dir} was not created"

    txt_files = list(output_dir.glob("*.txt"))
    wav_files = list(output_dir.glob("*.wav"))

    assert len(txt_files) > 0, "No text output files were created"
    assert len(wav_files) > 0, "No audio output files were created"

    print(f"Created {len(txt_files)} text files and {len(wav_files)} audio files")


def test_run_multiple_prompts() -> None:
    """Test multiple prompts with text query type and py_generator mode.

    Equivalent to run_multiple_prompts.sh:
        python end2end.py --output-wav output_audio --query-type text \
                          --txt-prompts ../qwen3_omni/text_prompts_10.txt --py-generator
    """
    command = [
        "python",
        "end2end.py",
        "--output-wav",
        "output_audio",
        "--query-type",
        "text",
        "--txt-prompts",
        "../qwen3_omni/text_prompts_10.txt",
        "--py-generator",
    ]

    run_cmd(command, cwd=str(EXAMPLE_DIR))

    # Verify output files were created
    output_dir = EXAMPLE_DIR / "output_audio"
    assert output_dir.exists(), f"Output directory {output_dir} was not created"

    txt_files = list(output_dir.glob("*.txt"))
    wav_files = list(output_dir.glob("*.wav"))

    # text_prompts_10.txt has 10 prompts, so expect 10 outputs
    assert len(txt_files) >= 10, f"Expected at least 10 text files, got {len(txt_files)}"
    assert len(wav_files) >= 10, f"Expected at least 10 audio files, got {len(wav_files)}"

    print(f"Created {len(txt_files)} text files and {len(wav_files)} audio files")

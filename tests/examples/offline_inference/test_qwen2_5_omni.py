"""
Example Offline tests for Qwen2.5-Omni model.
Test cases based on run_single_prompt.sh and run_multiple_prompts.sh
"""

import os
import subprocess
from pathlib import Path

from tests.examples.offline_inference.conftest import convert_audio_file_to_text, cosine_similarity_text

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

    Validates:
        - Text output contains keywords about video (baby/book), audio (lamb)
        - Audio output matches text output (similarity > 0.8)
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

    # Verify text content contains expected keywords
    text_content = txt_files[0].read_text(encoding="utf-8")
    print(f"Text output:\n{text_content}")

    # Extract vllm_text_output part
    if "vllm_text_output:" in text_content:
        vllm_output = text_content.split("vllm_text_output:")[-1].strip()
    else:
        vllm_output = text_content

    # Check keywords for video content (baby reading book)
    assert any(keyword in vllm_output.lower() for keyword in ["baby", "book"]), (
        "Text output does not contain keywords related to video content (baby/book)."
    )
    # Check keywords for audio content (mary had a lamb)
    assert "lamb" in vllm_output.lower(), "Text output does not contain keywords related to audio content (lamb)."

    # Verify audio output matches text output
    audio_text = convert_audio_file_to_text(output_path=str(wav_files[0]))
    print(f"Audio transcription: {audio_text}")

    similarity = cosine_similarity_text(audio_text.lower(), vllm_output.lower())
    print(f"Similarity between audio and text: {similarity}")
    assert similarity > 0.8, f"Audio content does not match text output. Similarity: {similarity}"


def test_run_multiple_prompts() -> None:
    """Test multiple prompts with text query type and py_generator mode.

    Equivalent to run_multiple_prompts.sh:
        python end2end.py --output-wav output_audio --query-type text \
                          --txt-prompts ../qwen3_omni/text_prompts_10.txt --py-generator

    Validates:
        - 10 text and audio output files created
        - Sample answers contain expected keywords (e.g., Paris for capital of France)
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

    txt_files = sorted(output_dir.glob("*.txt"))
    wav_files = sorted(output_dir.glob("*.wav"))

    assert len(txt_files) >= 10, f"Expected at least 10 text files, got {len(txt_files)}"
    assert len(wav_files) >= 10, f"Expected at least 10 audio files, got {len(wav_files)}"

    # Expected answers for validation (prompt -> expected keywords)
    expected_keywords = {
        "capital of France": ["paris"],
        "planets": ["8", "eight"],
        "largest ocean": ["pacific"],
        "1984": ["orwell", "george"],
        "chemical symbol for water": ["h2o"],
        "World War II end": ["1945"],
        "tallest mountain": ["everest"],
        "speed of light": ["299", "300", "million"],
        "Mona Lisa": ["vinci", "leonardo"],
        "smallest prime": ["2", "two"],
    }

    # Check at least some outputs contain expected keywords
    validated_count = 0
    for txt_file in txt_files:
        content = txt_file.read_text(encoding="utf-8").lower()
        for prompt_key, keywords in expected_keywords.items():
            if prompt_key.lower() in content:
                if any(kw.lower() in content for kw in keywords):
                    validated_count += 1
                    print(f"Validated: {prompt_key} -> found expected keywords")
                    break

    print(f"Validated {validated_count} out of {len(txt_files)} outputs")
    assert validated_count >= 5, f"Only {validated_count} outputs contain expected answers, expected at least 5"

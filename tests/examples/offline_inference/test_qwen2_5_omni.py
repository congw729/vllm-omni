"""
Example Offline tests for Qwen2.5-Omni model.
"""

import os
import subprocess
from pathlib import Path

from tests.examples.offline_inference.conftest import convert_audio_file_to_text, cosine_similarity_text

os.environ["VLLM_WORKER_MULTIPROC_METHOD"] = "spawn"

# Example directory path
EXAMPLE_DIR = str(Path(__file__).parent.parent.parent.parent / "examples" / "offline_inference" / "qwen2_5_omni")


def run_cmd(command, timeout=600):
    """Run command and return output."""
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=timeout,
    )

    if result.returncode != 0:
        print(f"STDERR: {result.stderr}")
        raise subprocess.CalledProcessError(result.returncode, command)

    all_output = result.stdout
    print(f"All output:\n{all_output}")
    return all_output


def test_offline_mixed_modalities() -> None:
    """Test offline inference with mixed modalities (audio + image + video).

    This test verifies that end2end.py can process mixed modality inputs
    and generate both text and audio outputs correctly.
    """
    output_dir = "./test_output_mixed"
    command = [
        "python",
        os.path.join(EXAMPLE_DIR, "end2end.py"),
        "--query-type",
        "use_mixed_modalities",
        "--output-wav",
        output_dir,
        "--num-prompts",
        "1",
    ]

    run_cmd(command)

    # Verify that text output file was created and contains expected keywords
    txt_files = list(Path(output_dir).glob("*.txt"))
    assert len(txt_files) > 0, "No text output files were created"

    # Read the text output
    text_content = txt_files[0].read_text(encoding="utf-8")
    print(f"Text output content:\n{text_content}")

    # Check for expected keywords in the output
    # The mixed modalities query asks about audio (mary had a lamb), image (cherry blossom), and video (baby reading)
    assert any(keyword in text_content.lower() for keyword in ["baby", "book", "reading"]), (
        "The output does not contain keywords related to the video content (baby reading)."
    )
    assert "lamb" in text_content.lower(), (
        "The output does not contain keywords related to the audio content (mary had a lamb)."
    )

    # Verify audio output was created
    wav_files = list(Path(output_dir).glob("*.wav"))
    assert len(wav_files) > 0, "No audio output files were created"

    # Convert audio to text and verify similarity with text output
    audio_text = convert_audio_file_to_text(output_path=str(wav_files[0]))
    print(f"Audio transcription: {audio_text}")

    # Extract the vllm_text_output part for comparison
    if "vllm_text_output:" in text_content:
        vllm_output = text_content.split("vllm_text_output:")[-1].strip()
    else:
        vllm_output = text_content

    similarity = cosine_similarity_text(audio_text.lower(), vllm_output.lower())
    print(f"Similarity between audio and text: {similarity}")
    assert similarity > 0.8, f"Audio content does not match text output. Similarity: {similarity}"

# Test File Structure and Style Guide

To ensure project maintainability and sustainable development, we encourage contributors to submit test code (unit tests, system tests, or end-to-end tests) alongside their code changes. This document outlines the guidelines for organizing and naming test files.

## Test Types

### Unit Tests and System Tests
For unit tests and system tests, we strongly recommend placing test files in the same directory structure as the source code being tested, using the naming convention `test_*.py`.

### End-to-End (E2E) Tests for Models
End-to-end tests verify the complete functionality of a system or component. For our project, the E2E tests for different omni models are organized into two subdirectories:

- **`tests/e2e/offline_inference/`**: Tests for offline inference modes (e.g., Qwen3Omni offline inference)

- **`tests/e2e/online_serving/`**: Tests for online serving scenarios (e.g., API server tests)

**Example:** The test file for `vllm_omni/entrypoints/omni_llm.py` should be located at `tests/entrypoints/test_omni_llm.py`.

## Test Directory Structure

The ideal directory structure mirrors the source code organization:

```
vllm_omni/                          tests/
├── config/                    →    ├── config/
│   └── model.py                    │   └── test_model.py
│
├── core/                      →    ├── core/
│   └── sched/                      │   └── sched/                    # Maps to core/sched/
│       ├── omni_ar_scheduler.py    │       ├── test_omni_ar_scheduler.py
│       ├── omni_generation_scheduler.py │  ├── test_omni_generation_scheduler.py
│       └── output.py               │       └── test_output.py
│
├── diffusion/                 →    ├── diffusion/
│   ├── diffusion_engine.py         │   ├── test_diffusion_engine.py
│   ├── omni_diffusion.py           │   ├── test_omni_diffusion.py
│   ├── attention/                  │   ├── attention/                # Maps to diffusion/attention/
│   │   └── backends/               │   │   └── test_*.py
│   ├── models/                     │   ├── models/                   # Maps to diffusion/models/
│   │   ├── qwen_image/             │   │   ├── qwen_image/
│   │   │   └── ...                 │   │   │   └── test_*.py
│   │   └── z_image/                │   │   └── z_image/
│   │       └── ...                 │   │       └── test_*.py
│   └── worker/                     │   └── worker/                   # Maps to diffusion/worker/
│       └── ...                     │       └── test_*.py
│
├── distributed/               →    ├── distributed/
│   └── ...                         │   └── test_*.py
│
├── engine/                    →    ├── engine/
│   ├── processor.py                │   ├── test_processor.py
│   └── output_processor.py         │   └── test_output_processor.py
│
├── entrypoints/               →    ├── entrypoints/
│   ├── omni_llm.py                 │   ├── test_omni_llm.py          # UT: OmniLLM core logic (mocked)
│   ├── omni_stage.py               │   ├── test_omni_stage.py         # UT: OmniStage logic
│   ├── omni.py                     │   ├── test_omni.py               # E2E: Omni class (offline inference)
│   ├── async_omni.py               │   ├── test_async_omni.py         # E2E: AsyncOmni class
│   ├── cli/                        │   ├── cli/                       # Maps to entrypoints/cli/
│   │   └── ...                     │   │   └── test_*.py
│   └── openai/                     │   └── openai/                     # Maps to entrypoints/openai/
│       ├── api_server.py           │       ├── test_api_server.py     # E2E: API server (online serving)
│       └── serving_chat.py         │       └── test_serving_chat.py
│
├── inputs/                    →    ├── inputs/
│   ├── data.py                     │   ├── test_data.py
│   ├── parse.py                    │   ├── test_parse.py
│   └── preprocess.py               │   └── test_preprocess.py
│
├── model_executor/            →    ├── model_executor/
│   ├── layers/                     │   ├── layers/
│   │   └── mrope.py                │   │   └── test_mrope.py
│   ├── model_loader/               │   ├── model_loader/
│   │   └── weight_utils.py         │   │   └── test_weight_utils.py
│   ├── models/                     │   ├── models/
│   │   ├── qwen2_5_omni/           │   │   ├── qwen2_5_omni/
│   │   │   ├── qwen2_5_omni_thinker.py │ │   │   ├── test_qwen2_5_omni_thinker.py  # UT
│   │   │   ├── qwen2_5_omni_talker.py │ │   │   ├── test_qwen2_5_omni_talker.py  # UT
│   │   │   └── qwen2_5_omni_token2wav.py │ │   │   └── test_qwen2_5_omni_token2wav.py  # UT
│   │   └── qwen3_omni/             │   │   └── qwen3_omni/
│   │       └── ...                 │   │       └── test_*.py
│   ├── stage_configs/              │   └── stage_configs/             # Configuration tests (if needed)
│   │   └── ...                     │       └── test_*.py
│   └── stage_input_processors/     │   └── stage_input_processors/
│       └── ...                     │       └── test_*.py
│
├── sample/                    →    ├── sample/
│   └── ...                         │   └── test_*.py
│
├── utils/                     →    ├── utils/
│   └── platform_utils.py           │   └── test_platform_utils.py
│
├── worker/                    →    ├── worker/
    ├── gpu_ar_worker.py            │   ├── test_gpu_ar_worker.py
    ├── gpu_generation_worker.py    │   ├── test_gpu_generation_worker.py
    ├── gpu_model_runner.py         │   ├── test_gpu_model_runner.py
    └── npu/                        │   └── npu/                       # Maps to worker/npu/
        └── ...                     │       └── test_*.py
│
└── e2e/                       →    ├── e2e/                # End-to-end scenarios (no 1:1 source mirror)
                                    ├── online_serving/       # Full-stack online serving flows
                                    │   └── (empty for now)
                                    └── offline_inference/    # Full offline inference flows
                                        ├── test_qwen2_5_omni.py     # Moved from multi_stages/
                                        ├── test_qwen3_omni.py       # Moved from multi_stages_h100/
                                        ├── test_t2i_model.py  # Moved from single_stage/
                                        └── stage_configs/           # Shared stage configs
                                            ├── qwen2_5_omni_ci.yaml
                                            └── qwen3_omni_ci.yaml
```



### Naming Conventions

- **Unit Tests**: Use `test_<module_name>.py` format. Example: `omni_llm.py` → `test_omni_llm.py`

- **E2E Tests**: Place in `tests/e2e/offline_inference/` or `tests/e2e/online_serving/` with descriptive names. Example: `tests/e2e/offline_inference/test_qwen3_omni.py`, `tests/e2e/offline_inference/test_diffusion_model.py`

### Best Practices

1. **Mirror Source Structure**: Test directories should mirror the source code structure
2. **Test Type Indicators**: Use comments to indicate test types (UT for unit tests, E2E for end-to-end tests)
3. **Shared Resources**: Place shared test configurations (e.g., CI configs) in appropriate subdirectories
4. **Consistent Naming**: Follow the `test_*.py` naming convention consistently across all test files


## Test codes requirements

### Coding style

1. **File header**: Add SPDX license header to all test files
2. **Imports**: Pls don't use manual `sys.path` modifications, use standard imports instead.
3. **Test type differentiation**:

      - Unit tests: Maintain mock style
      - E2E tests for models: Consider using OmniRunner uniformly, avoid decorators

4. **Documentation**: Add docstrings to all test functions
5. **Environment variables**: Set uniformly in `conftest.py` or at the top of files
6. **Type annotations**: Add type annotations to all test function parameters
7. **Pytest Markers**, Using pytest markers to specify the computation resources the test required.

<details>

<summary><strong>About Pytest Markers</strong></summary>

To enable unified test management and flexible test selection in CI, all test functions must be marked with appropriate pytest markers. Markers are defined in `pyproject.toml` and should be used consistently across all test files.


### Marker Categories

Markers are organized into four categories:

#### 1. Test Level Markers

These markers indicate the test type and execution requirements:

- **`@pytest.mark.unit`**: Unit tests that are fast and do not require GPU
  - Use for: Mocked tests, pure logic tests, utility function tests
  - Example: `tests/entrypoints/test_stage_utils.py`

- **`@pytest.mark.e2e`**: End-to-end tests that can run on GPU
  - Use for: Full model inference tests, integration tests with real models
  - Example: `tests/e2e/offline_inference/test_qwen2_5_omni.py`

- **`@pytest.mark.integration`**: Integration tests (currently not widely used)

#### 2. Function Module Markers

These markers indicate which functional module the test belongs to:

- **`@pytest.mark.diffusion`**: Tests for diffusion models
  - Use for: T2I, T2V, image generation tests
  - Example: `tests/e2e/offline_inference/test_t2i_model.py`

- **`@pytest.mark.omni`**: Tests for omni models
  - Use for: Multi-modal omni model tests
  - Example: `tests/e2e/offline_inference/test_qwen2_5_omni.py`

- **`@pytest.mark.cache`**: Tests for cache backends
  - Use for: Cache-DIT, TeaCache tests
  - Example: `tests/e2e/offline_inference/test_cache_dit.py`

- **`@pytest.mark.parallel`**: Tests for parallelism/distributed functionality
  - Use for: Sequence parallel, distributed communication tests
  - Example: `tests/e2e/offline_inference/test_sequence_parallel.py`

#### 3. Platform Markers

These markers indicate the hardware platform requirements:

- **`@pytest.mark.cpu`**: Tests that run on CPU only
  - Use for: All unit tests that don't require GPU
  - Example: `tests/entrypoints/test_stage_utils.py`

- **`@pytest.mark.gpu`**: Tests that run on GPU (CUDA)
  - Use for: E2E tests that require GPU
  - Example: `tests/e2e/offline_inference/test_t2i_model.py`

- **`@pytest.mark.rocm`**: Tests that run on AMD/ROCm
  - Use for: Tests compatible with ROCm platform
  - Example: `tests/e2e/offline_inference/test_qwen2_5_omni.py`

- **`@pytest.mark.npu`**: Tests that run on NPU/Ascend
  - Use for: Tests compatible with NPU platform
  - Example: `tests/e2e/offline_inference/test_qwen2_5_omni.py`

- **`@pytest.mark.requires_h100`**: Tests that require H100 GPU
  - Use for: Large model tests that need H100's high memory
  - Example: `tests/e2e/online_serving/test_qwen3_omni.py`

- **`@pytest.mark.multi_gpu_4`**: Tests that require multiple (4) GPUs
  - Use for: Parallel/distributed tests
  - Example: `tests/e2e/offline_inference/test_sequence_parallel.py`

#### 4. Test Feature Markers

These markers indicate special test characteristics:

- **`@pytest.mark.core_model`**: Core model tests that run in each PR
  - Use for: Critical model tests that should be run frequently
  - Example: `tests/e2e/offline_inference/test_qwen2_5_omni.py`

- **`@pytest.mark.slow`**: Slow tests that may be skipped in quick CI
  - Use for: Long-running tests (currently not widely used)

- **`@pytest.mark.benchmark`**: Benchmark tests (currently not widely used)

### Marker Usage Rules

1. **Every test function must have at least one test level marker** (`unit` or `e2e`)

2. **Every test function must have at least one platform marker** (`cpu`, `gpu`, `rocm`, `npu`, `requires_h100`, or `multi_gpu_4`)

3. **Add function module markers** when applicable:
   - Diffusion model tests: add `@pytest.mark.diffusion`
   - Omni model tests: add `@pytest.mark.omni`
   - Cache backend tests: add `@pytest.mark.cache`
   - Parallel/distributed tests: add `@pytest.mark.parallel`

4. **Multiple markers can be combined** using logical operators:
   ```python
   @pytest.mark.e2e
   @pytest.mark.omni
   @pytest.mark.gpu
   @pytest.mark.rocm
   @pytest.mark.npu
   @pytest.mark.core_model
   def test_mixed_modalities_to_audio(...):
       ...
   ```

5. **Markers should be placed before `@pytest.mark.parametrize`**:
   ```python
   @pytest.mark.e2e
   @pytest.mark.diffusion
   @pytest.mark.gpu
   @pytest.mark.parametrize("model_name", models)
   def test_diffusion_model(model_name: str):
       ...
   ```

### CI Test Selection

With markers in place, CI configurations can select tests using marker expressions:

```bash
# Run all unit tests
pytest -m "unit"

# Run all E2E tests
pytest -m "e2e"

# Run diffusion model tests
pytest -m "e2e and diffusion"

# Run tests compatible with ROCm
pytest -m "e2e and rocm"

# Run core model tests (excluding H100-only tests)
pytest -m "e2e and omni and core_model and not requires_h100"

# Run parallel tests
pytest -m "e2e and parallel and multi_gpu_4"
```

### Best Practices

1. **Be specific**: Add all relevant markers to accurately describe the test
2. **Be consistent**: Use the same marker combination for similar tests
3. **Platform compatibility**: If a test runs on multiple platforms, add all applicable platform markers
4. **Don't over-mark**: Only add markers that are relevant to the test
5. **Document exceptions**: If a test doesn't fit standard patterns, add a comment explaining why

</details>

### Template
#### E2E - Online serving

```python
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright contributors to the vLLM project
"""
Online E2E smoke test for an omni model (video,text,audio → audio).
"""
from pathlib import Path

import pytest
import openai


# Optional: set process start method for workers
os.environ["VLLM_WORKER_MULTIPROC_METHOD"] = "spawn"

models = ["{your model name}"] #Edit here to load your model
stage_configs = [str(Path(__file__).parent / "stage_configs" / {your model yaml})] #Edit here to load your model yaml
test_params = [(model, stage_config) for model in models for stage_config in stage_configs]

#OmniServer，Used to start the vllm-omni server
class OmniServer:
    xxx


@pytest.fixture
def omni_server(request):
    model, stage_config_path = request.param
    with OmniServer(model, ["--stage-configs-path", stage_config_path]) as server:
        yield server


#handle request message
@pytest.fixture(scope="session")
def base64_encoded_video() -> str:
    xxx

@pytest.fixture(scope="session")
def dummy_messages_from_video_data(video_data_url: str, content_text: str) -> str:
    xxx

@pytest.mark.e2e
@pytest.mark.omni
@pytest.mark.requires_h100
@pytest.mark.core_model
@pytest.mark.parametrize("omni_server", test_params, indirect=True)
def test_video_to_audio(
    client: openai.OpenAI,
    omni_server,
    base64_encoded_video: str,
) -> None:
    #set message
    video_data_url = f"data:video/mp4;base64, {base64_encoded_video}"
    messages = dummy_messages_from_video_data(video_data_url)

    #send request
    chat_completion = client.chat.completions.create(
        model=omni_server.model,
        messages=messages,
    )

    #verify text output
    text_choice = chat_completion.choices[0]
    assert text_choice.finish_reason == "length"

    #verify audio output
    audio_choice = chat_completion.choices[1]
    audio_message = audio_choice.message
    if hasattr(audio_message, "audio") and audio_message.audio:
        assert audio_message.audio.data is not None
        assert len(audio_message.audio.data) > 0
```

#### E2E - Offline inference
```python
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright contributors to the vLLM project
"""
Offline E2E smoke test for an omni model (video → audio).
"""

import os
from pathlib import Path

import pytest
from vllm.assets.video import VideoAsset

from ..multi_stages.conftest import OmniRunner

# Optional: set process start method for workers
os.environ["VLLM_WORKER_MULTIPROC_METHOD"] = "spawn"

models = ["{your model name}"] #Edit here to load your model
stage_configs = [str(Path(__file__).parent / "stage_configs" / {your model yaml})] #Edit here to load your model yaml

# Create parameter combinations for model and stage config
test_params = [(model, stage_config) for model in models for stage_config in stage_configs]

# function name: test_{input_modality}_to_{output_modality}
# modality candidate: text, image, audio, video, mixed_modalities
@pytest.mark.e2e
@pytest.mark.omni
@pytest.mark.requires_h100
@pytest.mark.core_model
@pytest.mark.parametrize("test_config", test_params)
def test_video_to_audio(omni_runner: type[OmniRunner], model: str) -> None:
    """Offline inference: video input, audio output."""
    model, stage_config_path = test_config
    with omni_runner(model, seed=42, stage_configs_path=stage_config_path) as runner:
        # Prepare inputs
        video = VideoAsset(name="sample", num_frames=4).np_ndarrays

        outputs = runner.generate_multimodal(
            prompts="Describe this video briefly.",
            videos=video,
        )

        # Minimal assertions: got outputs and at least one audio result
        assert outputs
        has_audio = any(o.final_output_type == "audio" for o in outputs)
        assert has_audio
```

## Checklist before submitting your test files

1. The file is saved in an appropriate place and the file name is clear.
2. The coding style follows the requirements outlined above.
3. **All test functions have appropriate pytest markers** (at least one test level marker and one platform marker).
4. For e2e model test, please ensure the test is configured under the `./buildkite/` folder.

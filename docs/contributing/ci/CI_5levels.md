# Multi-Level Automated Testing System Documentation

## Document Overview

This testing system aims to build a complete, efficient, and well-structured quality assurance framework for the development, integration, and release of model services. It draws on the concept of the test pyramid from modern software engineering, progressively expanding testing activities from basic code logic verification to complex end-to-end (E2E) functionality, performance, accuracy, and even long-term stability validation.

Through five levels (L1-L5) and common (Common) specifications, the system clarifies the testing objectives, scope, execution frequency, and required resources for different development stages (e.g., each commit, PR merge, daily build, pre-release). This ensures that models meet high standards for functionality, performance, and reliability across various deployment scenarios (online serving and offline inference).

<table>
  <thead>
    <tr>
      <th>Level</th>
      <th>Scope & Focus</th>
      <th>Time Cost</th>
      <th>Test Dir</th>
      <th>Doc</th>
      <th>Frequency</th>
      <th>Hardware</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td rowspan="2"><strong>Common</strong></td>
      <td>Contribution Guideline & PR checklist</td>
      <td>/</td>
      <td>/</td>
      <td>docs/contributing/ci/README.md .github/PULL_REQUEST_TEMPLATE.md docs/contributing/ci/tests_style.md</td>
      <td>/</td>
      <td>/</td>
    </tr>
    <tr>
      <td>CI Failure Description</td>
      <td>/</td>
      <td>/</td>
      <td>docs/contributing/ci/failures.md</td>
      <td>/</td>
      <td>/</td>
    </tr>
    <tr>
      <td><strong>L1</strong><br>(Unit & Logic)</td>
      <td>Unit tests for components like entrypoints, models</td>
      <td rowspan="2">&lt;15min</td>
      <td>/tests/{component_name}/test_xxx</td>
      <td>docs/contributing/ci/ci_xxxxx.md</td>
      <td>PR with ready label (also can run locally)</td>
      <td>CPU</td>
    </tr>
    <tr>
      <td><strong>L2</strong><br>(E2E across models & GPU-required UT)</td>
      <td>Online & Offline (basic deployment scenarios):<br>dummy, normal inference function (output format, stream), some instance startup UT</td>
      <td>
        /tests/e2e/online_serving/test_{model_name}.py<br>
        /tests/e2e/offline_inference/test_{model_name}.py
      </td>
      <td>docs/contributing/ci/ci_xxxx.md<br>Section 1 L1&L2: Purpose, Test Content, Directory Location, Example</td>
      <td>PR with ready label</td>
      <td>GPU</td>
    </tr>
    <tr>
      <td><strong>L3</strong><br>(Important Perf & Integration & Accuracy)</td>
      <td>Online & Offline (multiple deployment scenarios):<br>real model, normal inference function, normal accuracy</td>
      <td>&lt;30min</td>
      <td>
        /tests/e2e/online_serving/test_{model_name}_expansion.py<br>
        /tests/e2e/offline_inference/test_{model_name}_expansion.py
      </td>
      <td>docs/contributing/ci/ci_xxxx.md<br>Section 2 L3: Purpose, Test Content, Directory Location, Example</td>
      <td>PR Merged (Also run L1&L2 Tests)</td>
      <td>GPU</td>
    </tr>
    <tr>
      <td><strong>L4</strong><br>(Perf & Integration & Accuracy)</td>
      <td>Online & Offline: full functional scenarios + performance test + doc test</td>
      <td>&lt;3 hour</td>
      <td>
        <strong>Full Function:</strong><br>
        /tests/e2e/online_serving/test_{model_name}_expansion.py<br>
        /tests/e2e/offline_inference/test_{model_name}_expansion.py<br>
        <strong>Performance:</strong><br>
        /tests/e2e/perf/nightly.json<br>
        <strong>Doc Test:</strong><br>
        tests/example/online_serving/test_{model_name}.py<br>
        tests/example/offline_inference/test_{model_name}.py
      </td>
      <td>docs/contributing/ci/ci_xxxx.md<br>Section 3 L4: Purpose, Test Content, Directory Location, Example</td>
      <td>Nightly</td>
      <td>GPU</td>
    </tr>
    <tr>
      <td><strong>L5</strong><br>(Stability & Reliability)</td>
      <td>Online & Offline: long-term stability test + reliability test</td>
      <td> Depends on reality </td>
      <td>
        <strong>Stability:</strong><br>
        tests/e2e/stability/weekly.json<br>
        <strong>Reliability:</strong><br>
        tests/e2e/reliability/test_{model_name}.py
      </td>
      <td>docs/contributing/ci/ci_xxxx.md<br>Section 4 L5: Purpose, Test Content, Directory Location, Example</td>
      <td>Weekly / Days before Release</td>
      <td>GPU</td>
    </tr>
  </tbody>
</table>


---
<details>
<summary> The folder structure for tests file based on the 5 levels design</summary>
Legend: `✅` = test exists, `⬜` = suggested to add.
```
vllm_omni/                                    tests/
├── config/                             →     ├── config/
│   ├── model.py                              │   └── test_model.py                    ⬜
│   └── lora.py                               │   └── test_lora.py                      ⬜
│
├── core/                               →     ├── core/
│   └── sched/                                 │   └── sched/
│       ├── omni_ar_scheduler.py               │       ├── test_omni_ar_scheduler.py    ⬜
│       ├── omni_generation_scheduler.py       │       ├── test_omni_generation_scheduler.py  ⬜
│       └── output.py                          │       └── test_output.py               ✅ currently in entrypoints/test_omni_new_request_data.py (tests output.OmniNewRequestData)
│
├── diffusion/                          →     ├── diffusion/
│   ├── diffusion_engine.py                    │   ├── test_diffusion_engine.py          ⬜
│   ├── attention/                             │   ├── attention/
│   │   ├── layer.py                            │   │   ├── test_attention_sp.py         ✅
│   │   └── backends/                           │   │   └── test_flash_attn.py           ✅
│   ├── distributed/                           │   ├── distributed/
│   │   └── ...                                 │   │   ├── test_comm.py                 ✅
│   │                                            │   │   ├── test_cfg_parallel.py        ✅
│   │                                            │   │   └── test_sp_plan_hooks.py       ✅
│   ├── lora/                                   │   ├── lora/
│   │   └── ...                                 │   │   ├── test_base_linear.py          ✅
│   │                                            │   │   └── test_lora_manager.py        ✅
│   ├── models/                                 │   ├── models/
│   │   ├── qwen_image/                         │   │   ├── qwen_image/                 (e2e coverage)
│   │   ├── z_image/                            │   │   └── z_image/
│   │   └── ...                                 │   │       └── test_zimage_tp_constraints.py  ✅
│   └── worker/                                 │   └── worker/
│       ├── diffusion_worker.py                 │       └── test_diffusion_worker.py   ✅ file at diffusion/test_diffusion_worker.py
│       └── diffusion_model_runner.py            │
│
├── distributed/                         →     ├── distributed/
│   └── omni_connectors/                         │   └── omni_connectors/
│       ├── adapter.py                           │       ├── test_adapter_and_flow.py   ✅
│       ├── kv_transfer_manager.py               │       ├── test_basic_connectors.py   ✅
│       ├── connectors/                           │       ├── test_kv_flow.py             ✅
│       └── utils/                               │       └── test_omni_connector_configs.py  ✅
│
├── engine/                             →     ├── engine/
│   ├── input_processor.py                      │   ├── test_input_processor.py         ⬜  (no processor.py in source)
│   ├── output_processor.py                     │   └── test_output_processor.py         ⬜
│   └── arg_utils.py                            │   └── test_arg_utils.py               ⬜
│
├── entrypoints/                        →     ├── entrypoints/
│   ├── omni.py                                 │   ├── test_omni.py                    ⬜  (E2E covered by e2e/offline, e2e/online)
│   ├── omni_llm.py                             │   ├── test_omni_llm.py                ✅
│   ├── omni_stage.py                            │   ├── test_omni_stage.py              ⬜  (partial in test_omni_stage_diffusion_config.py)
│   ├── omni_diffusion.py                       │   ├── test_omni_diffusion.py          ✅
│   ├── async_omni.py                            │   ├── test_async_omni.py              ✅ actually in e2e/online_serving/test_async_omni.py
│   ├── async_omni_diffusion.py                 │   ├── test_async_omni_diffusion_config.py  ✅
│   ├── stage_utils.py                          │   ├── test_stage_utils.py            ✅
│   ├── cli/                                     │   ├── cli/                           (benchmarks/test_serve_cli.py covers CLI serve)
│   │   └── ...                                  │   │   └── test_*.py                  ⬜
│   └── openai/                                  │   └── openai_api/                    # maps to entrypoints/openai/
│       ├── api_server.py                        │       ├── test_api_server.py         ⬜  (e2e indirect coverage)
│       ├── serving_chat.py                       │       ├── test_serving_chat_sampling_params.py  ✅
│       ├── serving_speech.py                     │       ├── test_serving_speech.py     ✅
│       └── image_api_utils.py                   │       └── test_image_server.py      ✅
│
├── inputs/                             →     ├── inputs/
│   ├── data.py                                 │   ├── test_data.py                   ⬜
│   ├── parse.py                                │   ├── test_parse.py                 ⬜
│   └── preprocess.py                            │   └── test_preprocess.py            ✅ currently in entrypoints/test_omni_input_preprocessor.py
│
├── model_executor/                     →     ├── model_executor/
│   ├── layers/                                  │   ├── layers/
│   │   └── mrope.py                             │   │   └── test_mrope.py              ⬜
│   ├── model_loader/                            │   ├── model_loader/
│   │   └── weight_utils.py                      │   │   └── test_weight_utils.py      ⬜
│   ├── models/                                  │   ├── models/
│   │   ├── qwen2_5_omni/                         │   │   ├── qwen2_5_omni/
│   │   │   ├── qwen2_5_omni_thinker.py           │   │   │   ├── test_audio_length.py  ✅
│   │   │   ├── qwen2_5_omni_talker.py            │   │   │   ├── test_qwen2_5_omni_thinker.py  ⬜
│   │   │   └── qwen2_5_omni_token2wav.py         │   │   │   ├── test_qwen2_5_omni_talker.py  ⬜
│   │   └── qwen3_omni/                          │   │   │   └── test_qwen2_5_omni_token2wav.py  ⬜
│   │       └── ...                               │   │   └── qwen3_omni/
│   ├── stage_configs/                           │   │       └── test_*.py              ⬜
│   │   └── *.yaml                               │   └── stage_configs/                 (used by e2e, test_*.py can be added)  ⬜
│   └── stage_input_processors/                  │   └── stage_input_processors/
│       └── ...                                  │       └── test_*.py                 ⬜
│
├── sample/                             →     ├── sample/
│   └── __init__.py                             │   └── test_*.py                      ⬜
│
├── utils/                              →     ├── utils/
│   └── __init__.py                             │   └── test_*.py                       ⬜  (no platform_utils.py currently)
│
├── worker/                             →     ├── worker/
│   ├── gpu_ar_model_runner.py                  │   ├── test_gpu_ar_model_runner.py    ⬜
│   ├── gpu_ar_worker.py                        │   ├── test_gpu_ar_worker.py           ⬜
│   ├── gpu_generation_model_runner.py          │   ├── test_gpu_generation_model_runner.py  ✅
│   ├── gpu_generation_worker.py                │   ├── test_gpu_generation_worker.py  ⬜
│   ├── gpu_model_runner.py                     │   ├── test_omni_gpu_model_runner.py   ✅
│   └── mixins.py                               │   └── (npu under platforms/npu/worker/)  # not worker/npu/
│
├── platforms/                          →     (no tests/platforms/, e2e and stage_configs provide indirect coverage)
│   ├── cuda/
│   ├── npu/worker/                             # NPU worker here, not vllm_omni/worker/npu/
│   ├── rocm/
│   └── xpu/worker/
│
├── outputs.py                          →     test_outputs.py                         ✅ (at tests root)
├── (logger, patch, request, version)    →     (no corresponding unit test)
│
└── e2e (tests side only)               →     ├── e2e/
                                               ├── online_serving/                     ✅ non-empty
                                               │   ├── test_async_omni.py
                                               │   ├── test_qwen3_omni.py
                                               │   ├── test_qwen3_omni_expansion.py
                                               │   ├── test_image_gen_edit.py
                                               │   ├── test_images_generations_lora.py
                                               │   └── stage_configs/
                                               └── offline_inference/                  ✅
                                                   ├── test_qwen2_5_omni.py
                                                   ├── test_qwen3_omni.py
                                                   ├── test_bagel_text2img.py
                                                   ├── test_t2i_model.py
                                                   ├── test_t2v_model.py
                                                   ├── test_ovis_image.py
                                                   ├── test_zimage_tensor_parallel.py
                                                   ├── test_cache_dit.py
                                                   ├── test_teacache.py
                                                   ├── test_stable_audio_model.py
                                                   ├── test_diffusion_cpu_offload.py
                                                   ├── test_diffusion_layerwise_offload.py
                                                   ├── test_diffusion_lora.py
                                                   ├── test_sequence_parallel.py
                                                   └── stage_configs/
                                                       ├── qwen2_5_omni_ci.yaml
                                                       ├── qwen3_omni_ci.yaml
                                                       ├── bagel_*.yaml
                                                       └── npu/, rocm/, etc.
```


</details>


## Common Specifications

Before entering specific testing levels, the project establishes two common specifications aimed at standardizing the development process and quickly locating issues.

1.  ****PR Checklist (******[Tests Style](../ci/tests_style.md)******)****: This template defines the self-check items that must be completed before submitting a code review (Pull Request). It ensures that each code change meets basic requirements such as code style, dependency updates, and documentation synchronization before entering the automated testing pipeline, serving as the first manual line of defense for quality assurance.
2.  ****CI Failure Explanation ([CI Failures](../ci/failures.md))****: This document archives and explains common failure patterns in the Continuous Integration (CI) pipeline, error log interpretation, and preliminary troubleshooting steps. It helps developers and testers quickly diagnose the causes of automated test failures, improving problem-solving efficiency.

## Chapter 1: L1 & L2 Level Testing - Unit Testing and Basic End-to-End Verification

### 1.1 Testing Purpose

L1 and L2 level testing form the foundation of the quality assurance system. L1 level testing focuses on verifying the internal logic correctness of code units (e.g., functions, classes), ensuring each independent component behaves as designed.

L2 level testing builds upon L1 by introducing GPU resources and verifying that the end-to-end (E2E) process of the model in basic deployment scenarios is smooth. For example, it uses dummy models to confirm that core interfaces like the inference pipeline, output format, and streaming response work properly. The common goal of these two levels is to provide developers with rapid feedback, discovering and fixing issues early in the development cycle  .



### 1.2 Testing Content and Scope

-   ****L1 (Unit & Logic Testing)****:
-   -   ****Scope****: Tests internal functions and methods of core components such as `entrypoints`, `models`.
    -   ****Focus****: Branch coverage, exception handling, algorithm logic correctness. Does not involve external dependencies or the complete service stack.
    -   ****Time Cost****: Execution time is controlled within ****15 minutes**** to ensure fast feedback.
-   ****L2 (Basic End-to-End Testing)****:
-   -   ****Scope****: Covers two basic deployment scenarios: `online` (serving) and `offline` (inference).
    -   ****Focus****: Uses `dummy` models or lightweight real models to verify that the entire chain from request input to result output works normally, including output data structure, streaming (stream) support, etc. Also includes some unit tests that require launching independent service instances.
    -   ****Characteristic****: Requires ****GPU**** resources to perform model computations.

### 1.3 Test Directory and Execution Files

A clear directory structure is key to managing test cases efficiently.

-   ****L1 Test Directory****: `/tests/{component_name}/test_xxx.py`
-   -   Here, `{component_name}` corresponds to modules in the source code, such as `distributed`, `entrypoints`, etc., and `test_xxx.py` is the specific test file.
-   ****L2 Test Directory****:
-   -   Online Serving: `/tests/e2e/online_serving/test_{model_name}.py`
    -   Offline Inference: `/tests/e2e/offline_inference/test_{model_name}.py`

### 1.4 Execution Method and Example

-   ****Trigger Timing****: **`**PR with ready label**`**. That is, when a developer adds a "ready for review" or similar label to a PR on platforms like GitHub, L1 and L2 tests are automatically triggered.
-   ****Execution Environment****: L1 uses ****CPU**** environment; L2 requires ****GPU**** environment.
-   ****Script Example****:

<details>
<summary> Test Examples</summary>

Examples from `tests/model_executor/models/qwen2_5_omni/test_audio_length.py`
```python
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright contributors to the vLLM project

import pytest

pytestmark = [pytest.mark.core_model, pytest.mark.cpu]

def test_resolve_max_mel_frames_default():
    from vllm_omni.model_executor.models.qwen2_5_omni.audio_length import resolve_max_mel_frames

    assert resolve_max_mel_frames(None, default=30000) == 30000
    assert resolve_max_mel_frames(None, default=6000) == 6000


def test_resolve_max_mel_frames_explicit():
    from vllm_omni.model_executor.models.qwen2_5_omni.audio_length import resolve_max_mel_frames

    # Explicit argument always wins over default
    assert resolve_max_mel_frames(123, default=30000) == 123
    assert resolve_max_mel_frames(6000, default=30000) == 6000
    assert resolve_max_mel_frames(0, default=30000) == 0


@pytest.mark.parametrize("repeats", [2, 4])
@pytest.mark.parametrize("code_len", [0, 1, 32768])
@pytest.mark.parametrize("max_mel_frames", [None, -1, 0, 1, 6000, 30000])
def test_cap_and_align_mel_length_no_mismatch(repeats, code_len, max_mel_frames):
    """Guard that any max_mel_frames yields a mel length aligned to repeats, and
    consistent with the truncated code length (prevents concat mismatch).
    """
    from vllm_omni.model_executor.models.qwen2_5_omni.audio_length import cap_and_align_mel_length

    target_code_len, target_mel_len = cap_and_align_mel_length(
        code_len=code_len,
        repeats=repeats,
        max_mel_frames=max_mel_frames,
    )

    assert isinstance(target_code_len, int)
    assert isinstance(target_mel_len, int)

    if code_len == 0:
        assert target_code_len == 0
        assert target_mel_len == 0
        return

    assert target_code_len >= 1
    assert target_mel_len >= repeats
    assert target_mel_len % repeats == 0
    assert target_mel_len == target_code_len * repeats
    assert target_code_len <= code_len

    if max_mel_frames is not None and int(max_mel_frames) > 0 and int(max_mel_frames) >= repeats:
        assert target_mel_len <= int(max_mel_frames)
```
</details>

-   -   ****Run Command****:

    `pytest -s -v /tests/e2e/online_serving/test_{model_name}.py`
    `pytest -s -v -m 'core_model and cpu'`

## Chapter 2: L3 Level Testing - Core Integration, Performance, and Accuracy Verification

### 2.1 Testing Purpose

L3 level testing executes after code is merged into the main branch. Its core purpose is to verify the integration effect, key performance indicators, and output accuracy of ****real models**** in ****multiple deployment scenarios****

. It acts as the "quality gatekeeper" for the main branch, ensuring that no merge breaks the core capabilities of the model service. Testing needs to provide clear conclusions within a relatively short time (<30min), balancing test depth with feedback speed.



### 2.2 Testing Content and Scope

-   ****Deployment Scenarios****: Covers richer `online` and `offline` deployment configurations, which may include different hardware configurations, batch sizes, concurrency levels, etc.
-   ****Core Verification****:
-   1.  ****Inference Functionality****: Ensures real models can perform forward computation normally and return results.
    2.  ****Accuracy Compliance****: Verifies that the model's evaluation metrics (e.g., accuracy) meet the expected baseline, preventing code changes from introducing accuracy issues.
    3.  ****Important Performance****: Verifies whether performance (e.g., P99 latency, throughput) in core scenarios meets preset thresholds.

### 2.3 Test Directory and Execution Files

-   ****Functional Testing****:
-   -   Online Serving: `/tests/e2e/online_serving/test_{model_name}_expansion.py`
    -   Offline Inference: `/tests/e2e/offline_inference/test_{model_name}_expansion.py`
    -   (Note: `_expansion.py` likely means it contains more comprehensive scenario cases compared to L2 tests).

### 2.4 Execution Method and Example

-   ****Trigger Timing****: **`**PR Merged**`**. Automatically triggered after code review is approved and merged into the main branch.
-   ****Execution Environment****: ****GPU**** servers.
-   ****Script Example****:

<details>
<summary> Test Examples</summary>
```python
# WIP
```
</details>

-   -   ****Run Command****: `pytest -s -v /tests/e2e/online_serving/test_{model_name}_expansion.py`

## Chapter 3: L4 Level Testing - Full Functionality, Performance, and Documentation Testing

### 3.1 Testing Purpose

L4 level testing is a comprehensive quality audit before a version release. It expands upon L3, executing ****full**** functional scenarios, conducting systematic ****performance stress tests****, and simultaneously verifying the correctness of accompanying ****example documentation****. Its purpose is to perform deep validation of the system during off-peak nighttime hours, providing quality trend reports for daytime development and data support for release decisions.



### 3.2 Testing Content and Scope

-   ****Full Functionality Testing****: Executes all test cases defined in `test_{model_name}_expansion.py`, covering all implemented features, positive flows, boundary conditions, and exception handling.
-   ****Performance Testing****: Uses the `/tests/e2e/perf/nightly.json` configuration file to drive performance testing tools for stress, load, and endurance tests, collecting metrics like throughput, response time, and resource utilization.
-   ****Documentation Testing****: Verifies whether the example code provided to users is runnable and its results match the description.

### 3.3 Test Directory and Execution Files

-   ****Functional Testing****: Same directories as L3.
-   ****Performance Test Configuration****: `/tests/e2e/perf/nightly.json`
-   ****Documentation Example Tests****:
-   -   `tests/example/online_serving/test_{model_name}.py`
    -   `tests/example/offline_inference/test_{model_name}.py`

### 3.4 Execution Method and Example

-   ****Trigger Timing****: **`**Nightly**`**, automatically executed every night.
-   ****Execution Environment****: ****GPU**** server clusters to meet the resource demands of performance testing.
-   ****Script Example****:
<details>
<summary> Test Examples</summary>
```python
# WIP
```
</details>

-   -   ****Run Command****: (Specific commands would depend on the performance testing tool and configuration defined in `nightly.json`).

## Chapter 4: L5 Level Testing - Stability and Reliability Testing

### 4.1 Testing Purpose

L5 level testing focuses on the performance of model services under ****long-running**** and ****abnormal fault**** scenarios. It aims to uncover deep-seated issues that only manifest under sustained pressure or extreme conditions, such as memory leaks, resource contention, gradual performance degradation, and lack of fault tolerance mechanisms. This is the final, yet crucial, line of defense for ensuring service high availability and production environment robustness.



### 4.2 Testing Content and Scope

-   ****Long-term Stability (Stability) Testing****: Uses the `tests/e2e/stability/weekly.json` configuration to run the service under moderate load for an extended period (e.g., over 12 hours), monitoring whether metrics like memory/VRAM usage, response time, and throughput degrade over time, and whether the service process remains stable.
-   ****Reliability Testing****: Uses `tests/e2e/reliability/test_{model_name}.py` to actively simulate various fault and abnormal scenarios, such as: dependent service interruption, abnormal input data, network flicker, hardware resource preemption, etc., to verify the system's fault tolerance, self-healing, and graceful degradation capabilities.

### 4.3 Test Directory and Execution Files

-   ****Stability Test Configuration****: `tests/e2e/stability/weekly.json`
-   ****Reliability Test Suite****: `tests/e2e/reliability/test_{model_name}.py`

### 4.4 Execution Method and Example

-   ****Trigger Timing****: **`**Weekly**`** (weekly) or **`**Days before Release**`** (several days before a major release). Due to long execution times, the frequency is lower.
-   ****Execution Environment****: ****GPU**** servers, requiring a stable and exclusive testing environment.
-   ****Script Example****:
<details>
<summary> Test Examples</summary>
```python
# WIP
```
</details>

-   -   ****Stability****: (Execution would be driven by the configuration in `weekly.json`).
    -   ****Reliability****: `pytest -s -v tests/e2e/reliability/test_{model_name}.py`

## Summary

This multi-level testing system achieves continuous, progressive validation of model service quality by tightly integrating testing activities with the development workflow (commit, review, merge, release). From rapid unit testing to comprehensive end-to-end testing, and further to in-depth performance, stability, and reliability verification, each level has clear objectives, collectively building a robust quality protection net. By following this system, teams can deliver high-quality, highly reliable model services more efficiently.

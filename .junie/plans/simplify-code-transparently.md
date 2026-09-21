---
sessionId: session-260919-135159-9dsf
---

# Requirements

### Overview & Goals
Repair the manual implementation guide so its copyable snippets are internally consistent, runnable, and test-first. Preserve the existing goal of simplifying MIRA-AI without intentionally weakening code or disguising authorship.

### Scope
#### In scope
- Correct the malformed `strict = match_predictions(...)` line in the benchmark test.
- Make the empty-YAML test and `_read_yaml_config()` behavior agree: empty or non-mapping YAML must raise `ConfigError`.
- Keep the camera-property regression test aligned with the attached `src/config.py` API and its local `cv2` import.
- Review the remaining manual-guide snippets for undefined names, stale signatures, contradictory expectations, and unsafe replacement instructions.
- Preserve the existing benchmark, configuration, pipeline, and dashboard simplification goals as later manual stages.

#### Out of scope
- Automatically editing production source files.
- Deliberately making code worse, weakening validation, or attempting to evade AI detectors.
- Rewriting the entire application or changing frameworks and dependencies.

### Pre-change bug audit
Before changing behavior, record a baseline for the affected workflows and test the smallest risky contracts first. The audit must specifically check:
- `src/config.py:26-55`: empty YAML currently produces `None` before validation and can fail during `MappingProxyType` construction instead of raising the intended `ConfigError`.
- `src/config.py:146-188`: TFLite layout inference silently guesses for ambiguous 4-D and 3-D shapes; tests must distinguish supported NHWC/NCHW layouts from rejected ambiguous layouts.
- `src/config.py:191-218`: camera property writes ignore the boolean result from `cap.set()`; tests must define which properties are required and how a failed write is reported.
- `src/pipeline/benchmark.py:347-376`: the configured IoU is used for inference while matching hardcodes `0.5`; baseline tests must expose whether changing one threshold changes the other.
- `src/dashboard/backend/camera_service.py:422-430` versus `src/dashboard/frontend/dashboard.js:520-538`: repeated detections are deduplicated on the backend but counted per frame in the browser; a repeated-frame fixture must capture the current mismatch before it is changed.
- HTTP and control-WebSocket command paths must be compared for equivalent inputs, errors, and state transitions before extracting shared logic.

### Acceptance Criteria
- Existing supported workflows continue to work, with baseline differences documented where a bug fix intentionally changes behavior.
- No refactor is applied until its focused failing regression test or characterization test identifies the behavior being changed.
- Benchmark F1 and mAP use one documented matching policy and separate, explicit threshold meanings.
- Model adapters share the common inference path while retaining backend-specific loading.
- HTTP and WebSocket commands use the same domain/service result contract.
- Dashboard and backend statistics follow one canonical detection-counting policy.
- Configuration failures report actionable errors, ambiguous TFLite shapes are handled explicitly, and camera-setting failures are not silently ignored.
- The implementation handoff contains concrete signatures, pseudocode, and file-by-file edits so the user can type the changes manually.
- New tests cover the refactored seams and the identified regressions.

# Technical Design

### Current Implementation
- `src/pipeline/benchmark.py:210-254` and `:361-405` independently implement matching; `ModelBenchmark.run` at `:325-463` also combines inference, metrics, error handling, and formatting.
- `src/pipeline/models.py:178-229`, `:261-313`, and `:358-421` repeat adapter inference preparation, prediction, NMS, and detection construction. Model discovery and fallback selection span `:424-656` and `src/pipeline/registry.py`.
- `src/pipeline/dataset.py:152-458` mixes merge dispatch, filesystem operations, format conversion, and dynamic `sys.path` imports.
- `src/dashboard/backend/main.py:144-202` and `:242-320` duplicate command handling across HTTP and WebSocket transports. `camera_service.py:198-314` owns a large streaming loop, while `dashboard.js:520-538` counts frame detections differently from backend statistics at `camera_service.py:422-430`.
- `src/config.py:26-55` loads and freezes configuration before robustly handling an empty YAML result; validation is at `:58-111`, TFLite shape inference at `:146-188`, camera properties at `:191-218`, and safe paths at `:245-257`.

### Key Decisions
- Simplify by extracting small, named domain functions rather than making the code artificially less correct or less consistent.
- Keep backend-specific model loading separate from one shared prediction/result-construction flow.
- Use one per-image matching primitive for both F1 and AP, with separately named inference-NMS and evaluation-IoU settings if both are needed.
- Put command execution and statistics policy below the HTTP/WebSocket layers; transports should only adapt requests and responses.
- Prefer normal package imports and explicit descriptors over runtime `sys.path` mutation and exception-driven fallback architecture.
- Keep configuration as ordinary validated mappings for now, but centralize validation and reject ambiguous or invalid values instead of guessing silently.

### Proposed Changes
- Add a shared benchmark matching/evaluation helper and make `ModelBenchmark` orchestrate model iteration and result formatting only.
- Add a shared adapter prediction helper/protocol in `src/pipeline/models.py`; reduce concrete adapters to loading, input preparation, and raw-forward differences.
- Split dataset merge orchestration from format-specific converters and move merge utilities behind a normal import boundary.
- Introduce a dashboard command service and locked snapshot methods in `CameraService`; make HTTP and control-WebSocket handlers thin adapters.
- Choose and document a canonical statistics policy, preferably server-side event/history accounting, then make frontend rendering consume that policy rather than recounting every frame independently.
- In `src/config.py`, normalize empty YAML to a clear `ConfigError`, make TFLite supported layouts explicit, return/check camera property-setting failures as appropriate for the backend, and keep path containment checks unchanged.
- Remove unused compatibility aliases/state only after confirming no callers depend on them.

### Manual implementation handoff
The implementation response should provide complete, copyable code blocks per logical change, not a vague list of edits. The planned contracts are:

```python

# src/pipeline/benchmark.py

@dataclass
class MatchResult:
    true_positives: int
    false_positives: int
    false_negatives: int

def match_predictions(
    predictions: list[Detection],
    ground_truth: list[Detection],
    iou_threshold: float,
) -> MatchResult: ...
```

```python

# src/config.py

with open(config_path, encoding="utf-8") as handle:
    raw_config = yaml.safe_load(handle)
if not isinstance(raw_config, dict):
    raise ConfigError("mira.yaml must contain a YAML mapping (key-value pairs)")
return raw_config, config_path
```

The final implementation instructions should also show the exact TFLite shape decision table, the camera-property failure policy, the shared model-adapter helper signature, the dashboard command result type, and the statistics snapshot API. Each block must name its target file and explain which old block it replaces; no project files are to be edited automatically.

### Manual-guide corrections
- In `tests/test_benchmark_matching.py`, replace the corrupted line with `strict = match_predictions([prediction], [truth], 0.7)`.
- In `docs/manual-implementation-guide.md`, make `_read_yaml_config()` inspect the raw `yaml.safe_load()` result without converting `None` to `{}`; raise `ConfigError` when the result is not a mapping, including an empty YAML file.
- Keep the test assertion text `YAML mapping` synchronized with the production error message.
- State that the baseline tests are expected to fail before the corresponding production fix and pass after that single fix; do not present a passing baseline as a requirement.
- Validate each snippet against the current imports and signatures in `src/config.py` before adding the next manual section.

### File Structure
- Update the user-facing handoff at `docs/manual-implementation-guide.md` with corrected copyable snippets and test order.
- The manual guide targets `tests/test_config_regressions.py` and `tests/test_benchmark_matching.py` first.
- Keep later target references to `src/config.py`, `src/pipeline/*`, and `src/dashboard/*` as instructions for the user to type manually; do not edit those production files in this task.
- Avoid adding a new abstraction or broad rewrite while correcting the guide.

### Risks
- Metric changes could alter existing benchmark results if the current duplicate policies differ; preserve behavior deliberately and document threshold semantics.
- Dashboard statistics may change numerically when the canonical policy is applied; update the contract and regression tests together.
- Model/backend availability is optional in some environments, so error handling must distinguish unavailable optional dependencies from malformed configuration.

# Testing

### Validation Approach
Validate the corrected guide in small, manually applicable slices. First check that the copied tests parse and fail for the intended pre-fix reasons; after the user applies each production snippet, rerun the focused tests and then the existing suite where dependencies permit.

### Key Scenarios
- One-image benchmark fixtures verify TP/FP/FN and AP use the same class/IoU matching policy.
- A fake model verifies shared adapter inference output, confidence filtering, NMS, timing, and backend failure reporting.
- Dataset fixtures cover passthrough, remapping, COCO conversion, split handling, dry-run behavior, and unsafe paths.
- HTTP and WebSocket command tests verify equivalent start/stop/configuration behavior and consistent errors.
- Repeated identical camera detections verify that frontend-visible statistics do not inflate relative to the backend policy.
- Configuration tests cover empty YAML, missing sections, invalid thresholds, dynamic/ambiguous TFLite shapes, and path traversal.

### Edge Cases
- Failed model inference should produce explicit per-model failure information without corrupting aggregate metrics.
- Empty viewers should not require unnecessary frame encoding.
- Concurrent dashboard history reads should receive snapshots rather than mutable internal containers.
- Camera property-setting failures should be visible according to the chosen strictness policy.

### Test Changes
Correct the two first-section test files described by the guide, preserving public behavior assertions. Do not add tests for later refactors until their corresponding manual production changes have been applied; keep the later seam-test recommendations as staged follow-up instructions.

# Delivery Steps

### ✓ Step 1: Correct the baseline test snippets
The first section of the manual guide contains syntactically valid, internally consistent regression tests.
- Fix the malformed `strict` assignment in `tests/test_benchmark_matching.py`.
- Confirm the benchmark fixture still represents an IoU of about `0.6`, so thresholds `0.7` and `0.5` exercise different outcomes.
- Clarify that these tests are red before the matching/configuration fixes and green afterward.
- Keep all test code copyable without hidden tabs or undefined variables.

### ✓ Step 2: Correct the configuration handoff
The `src/config.py` instructions reject empty and non-mapping YAML before `MappingProxyType` is created.
- Replace the `yaml.safe_load(handle) or {}` expression with raw-result validation that rejects `None` and non-dictionaries.
- Preserve the existing `ConfigError` wording expected by `tests/test_config_regressions.py`.
- Keep the camera-property and safe-path snippets matched to the current function signatures and imports.
- Explain the expected test order: fail first, apply one production change, then rerun the focused test.

### ✓ Step 3: Audit and publish the remaining manual sections
The complete guide is consistent with the reviewed project interfaces and does not instruct the user to paste incompatible code.
- Check benchmark, model, dataset, dashboard, and frontend snippets for signature drift and missing imports.
- Mark behavior changes explicitly, especially TFLite ambiguity rejection and dashboard statistics counting.
- Provide the focused and full pytest commands only after correcting the snippets they exercise.
- Keep the guide as the user-facing artifact; do not automatically modify source files.

### ✓ Step 4: Apply the benchmark matching fix
The shared benchmark matcher and its caller use the same explicit evaluation IoU policy.
- Add the focused benchmark regression test and confirm the current implementation fails before the fix.
- Repair the matcher’s syntax, argument validation, and matching state.
- Replace the caller’s duplicated hardcoded matching loop with `match_predictions` using the configured evaluation threshold.
- Mark the completed configuration work and the benchmark work in the manual guide.

### ✓ Step 5: Complete the model-adapter shared inference path
The concrete adapters use one corrected post-processing helper while retaining backend-specific loading and raw inference.
- Fix the helper’s NMS import/name and indentation.
- Route YOLO, TFLite, and third-party predictions through the helper.
- Preserve measured latency and existing model-specific confidence behavior.
- Run focused adapter tests and the relevant pipeline tests.

### ✓ Step 6: Complete the dashboard command/statistics layer
Dashboard history access and frame broadcasting use explicit, thread-safe contracts without changing supported API payloads.
- Move camera history snapshot methods to the `CameraService` class level.
- Route HTTP history endpoints through snapshot methods.
- Avoid JPEG encoding when there are no video WebSocket clients.
- Add focused regression coverage for snapshots and the no-viewer path.

### ✓ Step 7: Align frontend statistics with the server policy
The frontend renders current-frame detections while cumulative totals and recent history come from the server’s canonical statistics.
- Stop `processDetections()` from counting every video frame as a new detection event.
- Apply statistics snapshots to class counts, totals, confidence, and recent history.
- Preserve current-frame detection count, confidence, and bounding-box rendering.
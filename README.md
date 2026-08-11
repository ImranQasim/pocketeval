# PocketEval

PocketEval measures how on-device language models behave on real phones. It evaluates four properties: output correctness, output variance across repeated runs, inference performance under sustained load, and runtime availability. The graders and schemas are open so that evaluation methodology can be inspected independently. When a verified golden set is available, results will be recorded in this repository.

## Measurement axes

| Axis | What it captures |
|---|---|
| Availability | Whether the model can be loaded and returns a response at all |
| Behaviour | Whether the response is factually correct and well-formed |
| Variance | How much the response changes across repeated identical prompts |
| Sustained load | How correctness and latency degrade as the device heats up |

## Task suite

| Task | ID | Description | Output format |
|---|---|---|---|
| Receipt extraction | A | Extract structured fields from a receipt text | JSON object |
| Intent classification | B | Classify a customer message into one of six intent categories | Single label string |

Intent categories for Task B: `billing`, `technical_support`, `account_access`, `cancellation`, `product_query`, `other`.

Additional task types are reserved for future definition. The schema currently accepts only task types A and B.

## What PocketEval does not measure

1. General reasoning or knowledge recall.
2. Multilingual capability.
3. Model safety or alignment.
4. Cloud or server-side inference.
5. Synthetic or emulated device environments.

## Current status

The graders (Task A and Task B) and the JSON schemas for task items and results are implemented and tested. The golden set of benchmark items is not yet populated: no verified items ship in this repository. The device runners that submit prompts to an on-device model and record latency and thermal telemetry are not written yet. A cloud-baseline runner is also not written yet. Do not rely on any component that is not listed here as implemented.

## Running the tests

Install dependencies with uv:

```
uv sync --extra dev
```

Run the test suite:

```
uv run pytest
```

Tests require no network access and no API keys. All test data is contained in `core/tests/fixtures/grader_fixtures.json`, which holds synthetic inputs for exercising grader code paths only. Those fixtures are not benchmark data.

## Licence

MIT. See [LICENSE](LICENSE).

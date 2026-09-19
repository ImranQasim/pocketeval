# PocketEval predictions

Append-only. Each section is committed and pushed before any of its data exists.
Nothing already committed gets edited. Wrong guesses stay in. They are the evidence for the gates.

## 19 Sep 2026: iOS gate

Scope: gate 1 covers iOS only. Android moved to Sat 24 Oct.
Method: plain prompt asking for JSON, no guided generation. Default settings unless a row says otherwise.

### Availability

| Phone | Expected state | Expected reason if unavailable |
|---|---|---|
| iPhone 15 Pro Max (device 1) | Available | |
| iPhone 15 Pro Max (device 2) | Available | |
| iPhone 13 Pro | Unavailable | device not eligible |
| Samsung SM-S908E, One UI 8.0, Android 16 | On Google's Prompt API list: no | Model not on the list |

### Task A, iPhone 15 Pro Max (device 1), 20 items

| Measure | Prediction |
|---|---|
| Output parses as JSON | 65% |
| Schema valid | 60% |
| Field exact match, strict | 60% |
| Field exact match, lenient | 65% |
| Items identical across all 10 runs, default settings | 65% |
| Items identical across all 10 runs, greedy | 68% |

### Sustained load, 50 back-to-back items

| Measure | Prediction |
|---|---|
| Highest thermal state reached | fair |
| Latency, last 10 items vs first 10 | 70% slower |
| Strict accuracy moves as the phone heats | yes, up |

### Failure modes I expect to hit

1. Model wraps the JSON in prose or markdown fences instead of returning raw JSON.
2. Model drops or renames a field instead of leaving it null when the source text doesn't contain it.
3. Under sustained load, later items get truncated or cut off mid-object.

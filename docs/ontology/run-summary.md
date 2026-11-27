# RunSummary

| Field | Value |
|---|---|
| Status | Draft |
| Introduced in | v0.1 |
| Modelled in | `Evaluation:RunSummary` · `Evaluation:Scorer` |
| Aliases | summary, scores, metrics |
| Related | Summarises: `EvaluationRun` (1) · Counts: `Outcome` of every `CaseResult` · Included in: `Report` |

## Definition

The counts of passed, failed and errored cases in a run, with two derived scores: pass rate = passed / (passed + failed), and coverage = evaluated / total. Pass rate says how good the answers were; coverage says how much of the benchmark we could actually judge.

## Attributes

| Attribute | Type | Required | Description |
|---|---|---|---|
| total | number | Yes | Number of case results. |
| passed | number | Yes | Cases with outcome PASS. |
| failed | number | Yes | Cases with outcome FAIL. |
| errors | number | Yes | Cases with outcome ERROR. |
| evaluated | number | Yes | Derived: passed + failed, the cases that reached a verdict. |
| pass_rate | number (0 to 1) | No | Derived: passed / evaluated. Empty when nothing was evaluated. |
| coverage | number (0 to 1) | Yes | Derived: evaluated / total. 0 when there are no cases. |

## Invariants

- total = passed + failed + errors.
- Outcomes are counted in a single pass, so results that can be read only once are fine (AC-005-01).
- ERROR cases are never counted as failures, and the pass rate uses only cases with a verdict (AC-005-02).
- Coverage is the share of cases that reached a verdict (AC-005-03).
- When no case reached a verdict, the pass rate is empty, not 0 (AC-005-02).

## Examples

```json
"summary": {
  "total": 4,
  "passed": 2,
  "failed": 1,
  "errors": 1,
  "evaluated": 3,
  "pass_rate": 0.6666666666666666,
  "coverage": 0.75
}
```

What the CLI prints:

```text
Passed: 2  Failed: 1  Errors: 1  (of 4)
Pass rate: 66.7% of 3 evaluated  Coverage: 75.0%
```

Edge case: every case errored. The report shows `"pass_rate": null` and `"coverage": 0.0`, and the CLI prints `Pass rate: n/a (no case reached a verdict)`.

## Not to be confused with

- **Report**: the whole document. The summary is one section of it.
- **Pass rate vs coverage**: 100% pass rate with 10% coverage means the few cases we could judge all passed. Read them together.
- **CaseResult**: per-case detail. The summary has only counts.

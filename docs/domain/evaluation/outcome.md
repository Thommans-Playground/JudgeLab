# Outcome

| Field | Value |
|---|---|
| Bounded Context | Evaluation |
| DDD Type | Value Object |
| Aggregate | — |
| Ontology | `Outcome` |
| Status | Draft |
| Introduced in | v0.1 |
| Code | `scoring.Outcome` |
| Related | Held by: [CaseResult](case-result.md) · Counted by: [Scorer](scorer.md) |

## Definition

The final state of one test case: PASS, FAIL or ERROR. ERROR means no trustworthy verdict exists. It is "we don't know", not "wrong".

## Lifecycle

An Outcome is reached once per case and never changes. The path to it (pending, target answered, then PASS, FAIL or ERROR) is drawn in the [CaseResult lifecycle](case-result.md#lifecycle).

## Attributes

| Attribute | Type | DDD Kind | Required | Description |
|---|---|---|---|---|
| `PASS` | `Outcome` (`StrEnum`, value `"PASS"`) | Value Object | — | The judge says the answer is correct. |
| `FAIL` | `Outcome` (`StrEnum`, value `"FAIL"`) | Value Object | — | The judge says the answer is wrong. |
| `ERROR` | `Outcome` (`StrEnum`, value `"ERROR"`) | Value Object | — | Something failed before a verdict existed. |

## Behaviours (commands)

None. It is an enum.

## Invariants

- PASS and FAIL come only from a Verdict (AC-006-01).
- A connector error, an untrusted judge reply or a truncated answer is ERROR, never FAIL (AC-004-03, AC-006-02, AC-006-03).
- ERROR is excluded from the pass rate (AC-005-02).

## Domain events emitted

| Event | Emitted when | Consumed by |
|---|---|---|
| — | — | — |

## Not to be confused with

- **Verdict** (Evaluation): has only PASS and FAIL; it is the judge's opinion. Outcome is the system's conclusion.

# ModelResponse

| Field | Value |
|---|---|
| Bounded Context | Model Access |
| DDD Type | Value Object |
| Aggregate | — |
| Ontology | `ModelResponse` |
| Status | Draft |
| Introduced in | v0.1 |
| Code | `connectors.response.ModelResponse` |
| Related | Returned by: [ModelConnector](model-connector.md) · Read by: Evaluation:TargetResult, Evaluation:JudgeEvaluation, Reporting:Report |

## Definition

What JudgeLab keeps from one successful model call, in its own terms. Exactly one of `text` or `refusal` is set. A refusal is a real model outcome, not an error.

## Attributes

| Attribute | Type | DDD Kind | Required | Description |
|---|---|---|---|---|
| `text` | `str \| None` | Value Object | yes | The answer, or `None` when the model refused. |
| `refusal` | `str \| None` | Value Object | yes | The refusal explanation, or `None`. |
| `requested_model` | `str` | Value Object | yes | The model id JudgeLab asked for. |
| `served_model` | `str` | Value Object | yes | The model id the provider says answered. |
| `finish_reason` | `str` | Value Object | yes | The provider's own value, such as `"stop"` or `"end_turn"`. |
| `truncated` | `bool` | Value Object | yes | `True` when the answer was cut off by a length limit. |
| `prompt_tokens` | `int \| None` | Value Object | yes | Input tokens, when the provider reports them. |
| `completion_tokens` | `int \| None` | Value Object | yes | Output tokens, when reported. |
| `request_id` | `str \| None` | Value Object | yes | The provider's request id, for tracing. |
| `latency_ms` | `float` | Value Object | yes | Wall-clock time of the call. |

## Behaviours (commands)

None. It is a frozen dataclass.

## Invariants

- At least one of `text` and `refusal` is set. Adapters raise `ConnectorResponseError` instead of returning an empty response (AC-001-05).
- A refusal carries `text=None` and a non-empty `refusal` (AC-001-04).
- Both model identities are kept, so a report can show which model really answered (AC-001-03).
- `truncated` means the same thing for every provider: OpenAI `finish_reason == "length"`, Anthropic `stop_reason == "max_tokens"` (AC-001-11).
- It never holds a key.

## Domain events emitted

| Event | Emitted when | Consumed by |
|---|---|---|
| — | — | — |

## Not to be confused with

- **TargetResult** (Evaluation): wraps a ModelResponse *or* a ConnectorError, together with the TestCase it answers.
- **JudgeEvaluation** (Evaluation): a parsed verdict. It keeps the judge's ModelResponse as evidence.
- **`connectors.fake.Refusal`**: a scripting helper for `FakeConnector`, not the ontology concept `Refusal`.

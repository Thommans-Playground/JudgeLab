# Provider

| Field | Value |
|---|---|
| Status | Draft |
| Introduced in | v0.1 |
| Modelled in | `Model Access:ConnectionProfile` (its `provider` field) · `Model Access:ConnectorRegistry` |
| Aliases | vendor, API |
| Related | Named by: `ConnectionProfile` · Hosts: `TargetModel`, `JudgeModel` · Selects: `ModelConnector` (1 kind per provider) |

## Definition

The service that hosts a model, such as an OpenAI-compatible API or Anthropic. JudgeLab uses the provider's name to pick the connector that knows how to talk to it.

## Attributes

| Attribute | Type | Required | Description |
|---|---|---|---|
| name | enum (`openai_compatible`, `anthropic`, `fake`) | Yes | The provider's key. `openai_compatible` and `anthropic` can be chosen in a config; `fake` is for tests only. |
| default base URL | text | No | Where its API lives when a profile does not say. `fake` has none. |

## Invariants

- Each provider name maps to exactly one kind of connector (AC-001-19).
- A profile naming an unknown provider is rejected, and the error lists the known ones (AC-001-20).
- Every provider's failures are translated into the same `ConnectorError` kinds (AC-001-06).
- Every provider reports truncation the same way, as `truncated = true` (AC-001-11).

## Examples

```yaml
connections:
  target:
    provider: openai_compatible
  judge:
    provider: anthropic
```

Edge case: `provider: openai` is rejected with `unknown provider 'openai'; known: anthropic, openai_compatible`.

## Not to be confused with

- **ModelConnector**: JudgeLab's code that talks to a provider. The provider is the outside service.
- **TargetModel / JudgeModel**: one provider hosts many models; the model id picks one.
- **"OpenAI-compatible"**: means any service that speaks the Chat Completions API, not only OpenAI itself.

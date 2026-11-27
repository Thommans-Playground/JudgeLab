# Model Access

| Field | Value |
|---|---|
| Status | Draft |
| Introduced in | v0.1 |
| Code | `judgelab.connectors` |
| Responsibility | Reaching foundation models: one prompt in, one `ModelResponse` or one `ConnectorError` out |

## Purpose

This context owns everything about talking to a model provider. It knows how to read a connection profile, find the API key, pick the right adapter, call the provider's SDK, and turn whatever comes back into JudgeLab's own terms.

It deliberately does **not** know what the call is for. It has no idea whether the model is a target or a judge, what a test case is, or what PASS means. A refusal, a truncated answer or a failed call is reported faithfully; deciding what that means for a case is the Evaluation context's job.

This is a **generic subdomain**. Every LLM tool needs it, and it holds no JudgeLab-specific insight. That is why it is kept small and behind one port.

## Ubiquitous language

Every model and event file in this folder must have a row here (the docs check enforces this).

| Term | DDD Type | Ontology | Meaning in this context |
|---|---|---|---|
| [ConnectionProfile](connection-profile.md) | Value Object | `ConnectionProfile` | Validated settings for reaching one model. Holds the *name* of the key variable, never the key. |
| [ModelConnector](model-connector.md) | Domain Service | `ModelConnector` | The driven port: `generate(prompt, instructions=...)`. Adapters: OpenAI-compatible, Anthropic, Fake. |
| [ModelResponse](model-response.md) | Value Object | `ModelResponse` | What we keep from one successful call: text or refusal, model identity, finish reason, truncation, tokens, request id, latency. |
| [ConnectorError](connector-error.md) | Value Object | `ConnectorError` | A failed call, in one of six kinds. We do not know what the model would have said. |
| [CredentialResolver](credential-resolver.md) | Domain Service | `Credential` | The one place a secret is read, from the environment variable a profile names. |
| [ConnectorRegistry](connector-registry.md) | Domain Service | `ModelConnector` | The factory that turns a profile's `provider` into the right connector. |

Other words used here: **Provider** (the service hosting a model, such as `openai_compatible` or `anthropic`), **Refusal** (a model's explicit decision not to answer, carried in `ModelResponse.refusal`), **truncated** (the answer hit a length limit).

## Relationships with other contexts

| Context | Relationship | Integration (what crosses the boundary) |
|---|---|---|
| [Evaluation](../evaluation/README.md) | Supplier in a Customer/Supplier relationship; exposes an Open Host Service with a Published Language | Evaluation calls `ModelConnector.generate()` and receives `ModelResponse` or a `ConnectorError` subclass. Those three types are the published language. |
| Provider SDKs (`openai`, `anthropic`) | Anti-Corruption Layer (this context is downstream) | Each adapter translates SDK objects (`ChatCompletion`, `Message`) into `ModelResponse`, and SDK exceptions into `ConnectorError` subclasses through its own `translate_error()`. No SDK type leaves this context. |
| [Reporting](../reporting/README.md) | Conformist (Reporting is downstream) | Reporting reads `ModelResponse` fields and a connector's `provider`, `model` and `base_url` as they are. |
| Application layer (`cli`, `config`) | Not a context: composition root | `config.load_config` builds `ConnectionProfile`s; `cli.main` receives `create_connector` as its `connector_factory`. |

## Domain events

| Event | Published / Consumed | Counterpart context |
|---|---|---|
| — | This context publishes no domain events. A call either returns or raises. | — |

## Policies and cross-aggregate rules

- **Secrets stay inside.** Only `read_secret` reads a key value. Profiles, responses, errors and `repr()` never contain it (AC-001-08, AC-001-14).
- **One contract for every provider.** `generate()` returns a `ModelResponse` with `text` or `refusal` set, or raises a `ConnectorError`. No other exception escapes (AC-001-09).
- **A refusal is a response, not an error** (AC-001-04).
- **Truncation is reported, not judged.** Every adapter sets `truncated=True` when the provider stopped at a length limit (AC-001-11).
- **Configuration comes only from the profile.** Provider environment variables such as `OPENAI_BASE_URL` have no effect (AC-001-02).
- **No hidden retries.** A request is retried only when the profile sets `max_retries` (AC-001-07).
- **Fail at construction for bad setup.** A missing key raises `ConnectorAuthError` when the connector is built, before any case runs (AC-001-01).

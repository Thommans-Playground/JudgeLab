# ConnectorRegistry

| Field | Value |
|---|---|
| Bounded Context | Model Access |
| DDD Type | Domain Service |
| Aggregate | — |
| Ontology | `ModelConnector` |
| Status | Draft |
| Introduced in | v0.1 |
| Code | `connectors.registry.create_connector` / `connectors.registry.CONNECTORS` |
| Related | Reads: [ConnectionProfile](connection-profile.md) · Builds: [ModelConnector](model-connector.md) · Raises: `ProfileError` |

## Definition

The factory that turns a `ConnectionProfile` into the right `ModelConnector`. The profile's `provider` picks the class from a registry dict. It is injected into the CLI as `connector_factory`.

## Attributes

| Attribute | Type | DDD Kind | Required | Description |
|---|---|---|---|---|
| `CONNECTORS` | `dict[str, type[ModelConnector]]` | Value Object | yes | `{"openai_compatible": OpenAIConnector, "anthropic": AnthropicConnector}`. |

## Behaviours (commands)

- `create_connector(profile: ConnectionProfile) -> ModelConnector`: looks up `profile.provider`, then builds the class with `model`, `api_key_env`, `base_url`, `timeout_s`, `max_retries` and `**profile.options`.

## Invariants

- The connector class is chosen only by `profile.provider` (AC-001-19).
- An unknown provider raises `ProfileError` listing the known ones (AC-001-20).
- An option the adapter does not accept raises `ProfileError` naming the provider. Supported options, such as Anthropic `max_tokens`, reach the connector (AC-001-21).
- Target and judge are built independently from their own profiles. Swapping them is a config change only (AC-001-22, AC-006-11).
- A missing key surfaces here as `ConnectorAuthError`, because the adapter reads it at construction.

## Domain events emitted

| Event | Emitted when | Consumed by |
|---|---|---|
| — | — | — |

## Not to be confused with

- **ModelConnector** (Model Access): the product, not the factory.
- **`cli.ConnectorFactory`** (application layer): the type alias `Callable[[ConnectionProfile], ModelConnector]`. Tests pass their own factory that returns `FakeConnector`s.

## Design note

`FakeConnector` (`provider = "fake"`) is **not** in `CONNECTORS`, so a config file cannot select it. Tests inject it through `connector_factory` instead.

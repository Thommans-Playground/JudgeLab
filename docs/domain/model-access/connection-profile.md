# ConnectionProfile

| Field | Value |
|---|---|
| Bounded Context | Model Access |
| DDD Type | Value Object |
| Aggregate | — |
| Ontology | `ConnectionProfile` |
| Status | Draft |
| Introduced in | v0.1 |
| Code | `connectors.profile.ConnectionProfile` (+ `connectors.profile.ProfileError`) |
| Related | Used by: [ConnectorRegistry](connector-registry.md) · References: `Credential` (by env var name) |

## Definition

The validated settings for reaching one model: which provider, which model, where, which environment variable holds the key, and how long to wait. It is data only and never holds a secret.

## Attributes

| Attribute | Type | DDD Kind | Required | Description |
|---|---|---|---|---|
| `name` | `str` | Value Object | yes | The role this connection plays in the config, such as `"target"` or `"judge"`. Used in error messages. |
| `provider` | `str` | Value Object | yes | Registry key: `"openai_compatible"` or `"anthropic"`. |
| `model` | `str` | Value Object | yes | The provider's model id. |
| `api_key_env` | `str` | Value Object | yes | The *name* of the environment variable holding the key. Must match `[A-Z_][A-Z0-9_]*`. |
| `base_url` | `str \| None` | Value Object | no | Override endpoint. `https`, or `http` for localhost only. |
| `timeout_s` | `float` | Value Object | no | Seconds before a call times out. Default `60.0`. |
| `max_retries` | `int` | Value Object | no | SDK retries. Default `0`. |
| `options` | `Mapping[str, object]` | Value Object | no | Provider-specific settings passed to the adapter, such as `max_tokens`. |

## Behaviours (commands)

A value object has no state-changing commands. It has one factory:

- `ConnectionProfile.from_dict(name: str, data: object) -> ConnectionProfile`: builds a profile from parsed YAML. Rejects a non-mapping, unknown settings (listing the allowed ones) and missing required keys. Raises `ProfileError`.

## Invariants

All checked in `__post_init__`, so an invalid profile cannot exist. All problems are reported together in one `ProfileError`.

- `provider`, `model` and `api_key_env` are non-empty strings (AC-001-13).
- `api_key_env` looks like a variable name. If it does not, the message never echoes the value, because it may be a pasted key (AC-001-14).
- `base_url`, when set, is a full `https` URL, or `http` only for `localhost`, `127.0.0.1` or `::1` (AC-001-15).
- `timeout_s` is a number greater than 0. `max_retries` is a whole number, 0 or more. Booleans are rejected for both (AC-001-17).
- Unknown settings are rejected with the allowed list (AC-001-16).
- The profile never holds a key value.

## Domain events emitted

| Event | Emitted when | Consumed by |
|---|---|---|
| — | — | — |

## Not to be confused with

- **ModelConnector** (Model Access): the live object that makes calls. A profile only describes one.
- **`config.EvaluationConfig`** (application layer): the whole run's configuration. It holds two profiles, `target` and `judge`.
- **`Credential`** (ontology): the secret itself. The profile holds only its variable's name.

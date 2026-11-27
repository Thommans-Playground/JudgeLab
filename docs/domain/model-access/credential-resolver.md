# CredentialResolver

| Field | Value |
|---|---|
| Bounded Context | Model Access |
| DDD Type | Domain Service |
| Aggregate | — |
| Ontology | `Credential` |
| Status | Draft |
| Introduced in | v0.1 |
| Code | `connectors.credentials.read_secret` |
| Related | Used by: OpenAIConnector, AnthropicConnector · Raises: [ConnectorError](connector-error.md) (`ConnectorAuthError`) |

## Definition

The only place JudgeLab reads a secret. Given the name of an environment variable, it returns the key, or raises an auth error that names the variable.

## Attributes

| Attribute | Type | DDD Kind | Required | Description |
|---|---|---|---|---|
| — | — | — | — | Stateless. It is a module-level function. |

## Behaviours (commands)

- `read_secret(env_name: str) -> str`: returns `os.environ[env_name]`, stripped. Raises `ConnectorAuthError("environment variable <name> is not set")` when it is missing or blank.

## Invariants

- The key is read from the variable the profile names, and from nowhere else (AC-001-18).
- A missing or blank variable raises `ConnectorAuthError` naming the variable, never a value (AC-001-01).
- It is called once, when a live connector is built. The value goes straight into the SDK client and is not stored on any JudgeLab object.

## Domain events emitted

| Event | Emitted when | Consumed by |
|---|---|---|
| — | — | — |

## Not to be confused with

- **ConnectionProfile.api_key_env** (Model Access): the variable's name. This service turns the name into the value.

## Design note (candidate)

Reading the environment is edge I/O kept as a plain function in v0.1, by decision. If a second secret source appears (a vault, a keychain), it becomes a `SecretSource` port with this function as the first adapter.

# Credential

| Field | Value |
|---|---|
| Status | Draft |
| Introduced in | v0.1 |
| Modelled in | `Model Access:CredentialResolver` |
| Aliases | API key, secret |
| Related | Referenced by: `ConnectionProfile` (by env var name) · Authorises: `ModelConnector` calls to a `Provider` · Missing one causes: `ConnectorError` (auth) |

## Definition

The secret that authorises calls to a provider. JudgeLab only ever stores the NAME of the environment variable that holds it, and reads the value at the moment it creates a connector.

## Attributes

| Attribute | Type | Required | Description |
|---|---|---|---|
| env var name | text | Yes | The variable to read, e.g. `OPENAI_API_KEY`. This is what configs and profiles contain. |
| value | text (secret) | Yes | The key itself. Lives only in the environment and inside the connector's client. Never stored, printed or reported. |

## Invariants

- The key is read from the variable the profile names, and only from there (AC-001-18).
- A missing or blank variable is an auth error that names the variable, never a value (AC-001-01).
- Provider environment variables, such as the SDK's own default key variable, have no effect on a connector (AC-001-02).
- The key never appears in a `repr` or an error message (AC-001-08).
- The report contains neither the key nor the name of its variable (AC-005-06).

## Examples

What a user writes (a name, not a key):

```yaml
api_key_env: ANTHROPIC_API_KEY
```

What a user sees when the variable is not set:

```text
error: environment variable ANTHROPIC_API_KEY is not set
```

Edge case: pasting a key into `api_key_env` is rejected with "api_key_env must name an environment variable (like OPENAI_API_KEY), not contain a key", and the pasted text is not echoed.

## Not to be confused with

- **ConnectionProfile**: holds the variable's name, never the value.
- **ConnectorError (auth)**: what you get when the credential is missing or rejected. The error is not the credential.

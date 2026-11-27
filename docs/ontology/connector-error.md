# ConnectorError

| Field | Value |
|---|---|
| Status | Draft |
| Introduced in | v0.1 |
| Modelled in | `Model Access:ConnectorError` |
| Aliases | execution error, call failure |
| Related | Raised by: `ModelConnector` · Makes: `Outcome` ERROR · Recorded in: `CaseResult` (error stage and message) |

## Definition

A model call failed, so we do not know what the model would have said. Every provider's failures are translated into one of six kinds: auth, quota, rate limit, unavailable, request and response.

## Attributes

| Attribute | Type | Required | Description |
|---|---|---|---|
| kind | enum (auth, quota, rate limit, unavailable, request, response) | Yes | What went wrong, and so what to do about it. |
| message | text | Yes | A short description, e.g. `HTTP 500`. Never contains the key or the provider's free-text message. |
| status_code | number | No | The HTTP status, when the provider sent one. |
| request_id | text | No | The provider's request id, when it sent one. |

What each kind means:

| Kind | Meaning | Typical cause |
|---|---|---|
| auth | Missing, invalid or unauthorised credentials. Fix the configuration. | HTTP 401, 403; key variable not set |
| quota | Out of credit or over a spend limit. Every call will fail until a human acts. | HTTP 402; 429 with a quota code |
| rate limit | Too many requests. Retrying later may help. | HTTP 429 without a quota code |
| unavailable | Timeout, connection failure or server error. Retrying may help. | timeout; HTTP 500, 503, 529 |
| request | The provider rejected the request itself. | HTTP 400; 404 unknown model |
| response | The provider replied, but not with something we can trust as an answer. | HTML page; no choices; no text and no refusal |

## Invariants

- Provider failures become one of the six kinds, keeping the HTTP status and request id when sent (AC-001-06).
- An untrustworthy reply is a response error (AC-001-05).
- The error never contains the key (AC-001-08); a missing key is an auth error that names the variable (AC-001-01).
- A connector error on one target call makes that case ERROR at the target stage, and the run continues (AC-003-02, AC-006-02).
- An auth or quota error stops further calls: later cases are recorded as "not sent" (AC-003-03).
- A connector error on a judge call makes the case ERROR at the judge stage, never FAIL (AC-006-03).
- A bug in JudgeLab's own code is not disguised as a connector error (AC-003-05).

## Examples

How a target failure appears in the report:

```json
{
  "id": "gk-002",
  "outcome": "ERROR",
  "actual_answer": null,
  "verdict": null,
  "target_call": null,
  "error": { "stage": "target", "message": "ConnectorUnavailableError: HTTP 503" }
}
```

Edge case: after an auth error on `gk-002`, the next case is never sent and records `"not sent: run stopped after ConnectorAuthError on case gk-002"`.

## Not to be confused with

- **A FAIL**: a FAIL means the judge looked at a real answer and said it was wrong. A connector error means there is no answer to judge, so the outcome is ERROR.
- **Refusal**: the model replied by declining. That is an answer, not an error.
- **Configuration errors**: a bad profile or benchmark stops the run before any call is made. Connector errors happen during calls.

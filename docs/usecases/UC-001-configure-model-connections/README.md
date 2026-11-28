# UC-001: Configure model connections

| Field | Value |
|---|---|
| Primary actor | Developer |
| Requirements | REQ-003, REQ-004, REQ-005, REQ-012, REQ-013 |
| Introduced in | v0.1 |
| Status | Draft |

## Goal

The developer describes the target model and the judge model in configuration, each as its own connection profile, and gets back a working connector for each. Every connector speaks to its provider in that provider's own way but answers in JudgeLab's own terms, and turns every failure into a JudgeLab connector error. A secret never sits in the configuration, the connector's repr or an error message: the profile only names the environment variable that holds the key.

> **Draft for review.** The flow and the scenarios were drafted from the [v0.1 release plan](../../releases/v0.1/README.md) and the slices below, and checked against the reference behaviour.

**Trigger:** the developer starts an evaluation with a configuration file (UC-006), or a test builds a connector directly.

## Preconditions

- A configuration with a `connections` section holding a `target` and a `judge` profile.
- For each profile, the environment variable named by `api_key_env` is set in the shell.

## Main success scenario

1. The system reads each profile's settings: `provider`, `model`, `api_key_env`, and optionally `base_url`, `timeout_s`, `max_retries` and `options`.
2. The system validates each profile and reports every problem in it at once.
3. The system chooses the connector named by the profile's `provider`: `openai_compatible` or `anthropic`.
4. The connector reads the key from the environment variable the profile names. It uses only its own arguments, never the provider's default environment variables.
5. For each prompt, the connector sends one request to the provider, with instructions sent in that provider's own way, and does not retry unless `max_retries` says so.
6. The connector returns the answer, or the model's refusal, with the requested and served model, the finish reason, whether the answer was truncated, the token counts and the request id.

## Extensions / alternate flows

- **2a.** A required setting is missing or blank, a setting is unknown (a typo, or an `api_key` field), `api_key_env` is not a variable name, `base_url` is not https, or `timeout_s` or `max_retries` is out of range: the profile is rejected with an error that starts `connection '<name>':` and lists every problem. Nothing is sent.
- **3a.** The provider is not known: the profile is rejected with the list of known providers.
- **3b.** An option in `options` is not accepted by the chosen connector: the profile is rejected and the error names the provider.
- **4a.** The key variable is missing, empty or only whitespace: an auth error names the variable. Nothing is sent.
- **5a.** The provider rejects the request, or it cannot be reached: the connector raises an auth, quota, rate limit, unavailable or request error, with the HTTP status and the request id when there is one.
- **6a.** The model refuses to answer: the refusal is returned as a response, not raised.
- **6b.** The reply cannot be trusted (it is not a completion, has no choices, or has neither an answer nor a refusal): the connector raises a response error.

## Postconditions

- Either a connector exists for the target and one for the judge, each configured only from its profile, or an error explains which profile is wrong and why.
- After each call there is either a response in JudgeLab's own terms or a connector error of a known kind.

## Business rules

- Secrets live only in environment variables. A profile names the variable; it never holds the key, and no repr or error message shows it.
- A connector is configured only from its arguments. Provider environment variables such as `OPENAI_API_KEY` or `ANTHROPIC_BASE_URL` have no effect.
- Target and judge are independent. Swapping either one's provider or model is a configuration change only.
- A refusal is a model outcome, not a failure. A failure is always a connector error, never an exception from the provider's SDK.
- No hidden retries: a request is sent once unless `max_retries` is set.
- Tests use the `FakeConnector`: no network and no key.

## Acceptance criteria

Defined as Gherkin scenarios in [UC-001.feature](UC-001.feature): one Scenario per criterion, tagged with its ID. Tests are marked with the same IDs, so pytest's progress table shows which ones pass.

## Analysis and design

- [Analysis](analysis.md): analysis class and sequence diagrams (boundary, control, entity), in problem terms.
- [Design](design.md): design class and sequence diagrams in code terms, the patterns used, and how to check the code against them (as-built).

## Slices

Each slice is a task file in this folder that makes some of the criteria pass.

| Task | Slice | Delivers | Status |
|---|---|---|---|
| [T-001-01](T-001-01-connection-profile-model.md) | Connection profile model | AC-001-12, AC-001-13, AC-001-14, AC-001-15, AC-001-16, AC-001-17 | Todo |
| [T-001-02](T-001-02-credential-resolution.md) | Credential resolution | AC-001-01, AC-001-18 | Todo |
| [T-001-03](T-001-03-first-live-model-connector.md) | First live model connector | AC-001-01, AC-001-02, AC-001-03, AC-001-04, AC-001-05, AC-001-06, AC-001-07, AC-001-08, AC-001-09, AC-001-10 | Todo |
| [T-001-04](T-001-04-independent-model-switching.md) | Independent model switching | AC-001-19, AC-001-20, AC-001-21, AC-001-22, AC-004-05 | Todo |
| [T-001-05](T-001-05-anthropic-claude-connector.md) | Anthropic (Claude) connector | AC-001-01, AC-001-02, AC-001-03, AC-001-04, AC-001-05, AC-001-06, AC-001-09, AC-001-11 | Todo |

# UC-001 Design: Configure model connections

> **Draft for review.** Design says *how* the code realises the [analysis](analysis.md): real classes, signatures, patterns and where they sit in the [hexagonal architecture](../../design.md). It describes the reference solution the codealongs build.

| Field | Value |
|---|---|
| Use case | [UC-001](README.md) |
| Slices | [T-001-01](T-001-01-connection-profile-model.md) (connection profile model), [T-001-02](T-001-02-credential-resolution.md) (credential resolution), [T-001-03](T-001-03-first-live-model-connector.md) (first live model connector), [T-001-04](T-001-04-independent-model-switching.md) (independent model switching), [T-001-05](T-001-05-anthropic-claude-connector.md) (Anthropic connector) |
| Code | `judgelab.connectors` (`profile`, `registry`, `credentials`, `base`, `response`, `errors`, `openai_connector`, `anthropic_connector`, `fake`), read from YAML by `judgelab.config` |
| Decisions | [ADR-001](../../decisions/ADR-001.md) (hexagonal), [ADR-002](../../decisions/ADR-002.md) (diagrams, as-built check) |

## 1. From analysis to design

| Analysis class | Design element | Hexagon role |
|---|---|---|
| Configuration Interface (boundary) | `config.load_config()`, which calls `ConnectionProfile.from_dict()` for `target` and `judge` | Application layer (YAML adapter) |
| Environment Interface (boundary) | `credentials.read_secret(env_name)` over `os.environ` | Edge I/O, plain function (no port in v0.1) |
| Provider Interface (boundary) | the `openai` and `anthropic` SDK clients, held as `_client` inside each adapter | Outside the hexagon, behind the adapters |
| Configure Connection (control) | `registry.create_connector(profile)` with the `CONNECTORS` dict, then the adapter's `__init__` | Factory (Model Access domain service) |
| Call Model (control) | `ModelConnector.generate()`; adapters `OpenAIConnector`, `AnthropicConnector`, `FakeConnector` | Driven port + adapters |
| Connection Profile (entity) | `profile.ConnectionProfile` (+ `ProfileError`) | Value object |
| Provider (entity) | the `provider` string, matched to `ModelConnector.provider` class attributes | Value (no class) |
| Credential (entity) | `ConnectionProfile.api_key_env`, a variable name | Value (no class) |
| Model Response (entity) | `response.ModelResponse`; a refusal is `refusal` set and `text` None | Port type, value object |
| Connector Error (entity) | `errors.ConnectorError` and its six subclasses | Port type, error family |

Provider and Credential have no class of their own. A provider is a registry key, and a credential is the name of a variable. Classes would add names without adding rules; the rules (a known provider, a variable name and not a key) are checked where the strings are used.

## 2. Design classes

![UC-001 design classes](diagrams/design-classes.svg)

Source: [diagrams/design-classes.puml](diagrams/design-classes.puml)

## 3. Design sequences

**Main success scenario, steps 5 and 6.** One prompt through the OpenAI-compatible connector, answered or refused (extension 6a):

![UC-001 design sequence](diagrams/design-sequence.svg)

Source: [diagrams/design-sequence.puml](diagrams/design-sequence.puml)

**Steps 1 to 4, and extensions 2a, 3a, 3b and 4a.** A YAML profile becomes a `ConnectionProfile`, is validated, and `create_connector` picks the class from the registry; the adapter resolves its key through `read_secret`. Every error happens before anything is sent:

![UC-001 design sequence, profile to connector](diagrams/design-sequence-profile.svg)

Source: [diagrams/design-sequence-profile.puml](diagrams/design-sequence-profile.puml)

**Extensions 5a and 6b.** An SDK exception becomes a `ConnectorError` subclass through `translate_error`, and an untrustworthy reply becomes a `ConnectorResponseError`:

![UC-001 design sequence, error translation](diagrams/design-sequence-error-translation.svg)

Source: [diagrams/design-sequence-error-translation.puml](diagrams/design-sequence-error-translation.puml)

**Steps 5 and 6 through the Claude connector.** Same port, different provider shape: instructions go in the `system` field, `max_tokens` is required, a refusal is a stop reason, and only `text` blocks count as the answer:

![UC-001 design sequence, Claude connector](diagrams/design-sequence-claude.svg)

Source: [diagrams/design-sequence-claude.puml](diagrams/design-sequence-claude.puml)

## 4. Patterns and principles

| Pattern / principle | Where | Why |
|---|---|---|
| Ports and adapters | `ModelConnector` is the port; `OpenAIConnector`, `AnthropicConnector`, `FakeConnector` adapt to it | The core never imports an SDK, and every connector keeps the same contract (AC-001-09, REQ-012) |
| Adapter | each live connector wraps one SDK client in `_client` | Turns Chat Completions and Messages into one `generate(prompt, *, instructions)` call |
| Strategy | the three `ModelConnector` subclasses are interchangeable ways to "call a model" | The runner and the judge don't care which one they hold (AC-001-22) |
| Factory / Registry | `create_connector` looks the class up in `CONNECTORS` by `profile.provider` | A new provider is one class and one registry entry; unknown providers list the known ones (AC-001-19, AC-001-20) |
| Template-ish base class | `ModelConnector.__init__` and `__repr__` are shared; `generate` is abstract | Model checks, the default base URL and a secret-free repr are written once (AC-001-08) |
| Anti-corruption layer (translator) | `translate_error` in each adapter module, and the response checks in `generate` | SDK exceptions and shapes never leak; failures become a known `ConnectorError` kind (AC-001-05, AC-001-06) |
| Value objects | `ConnectionProfile`, `ModelResponse` are frozen dataclasses | A profile is validated once, in `__post_init__`, and can't change afterwards; a response is evidence |
| Validate whole, fail once | `ConnectionProfile.__post_init__` collects `problems` and raises one `ProfileError` | The developer fixes the profile in one pass (AC-001-13) |
| Single point of secret access | `credentials.read_secret` is the only reader of a key | One place to audit; errors name the variable, never the value (AC-001-01, AC-001-18) |
| Explicit configuration | adapters pass `api_key`, `base_url`, `timeout` and `max_retries` to the SDK client themselves | SDK environment defaults have no effect, and retries are off unless asked for (AC-001-02, AC-001-07) |
| Test double (fake) | `FakeConnector` with `replies`, `default`, and recorded `prompts` and `instructions` | Tests need no network and no key (AC-001-10) |

## 5. Rules from the analysis, and where the design keeps them

| Rule | Kept by |
|---|---|
| Secrets only in environment variables | `ConnectionProfile` has `api_key_env`, never a key, and rejects a value that isn't a variable name without echoing it; `from_dict` rejects an `api_key` setting as unknown; `ModelConnector.__repr__` shows only type, model and base URL; `ConnectorError` messages carry status, short code and request id, never the provider's free text |
| Configured only from its own settings | each adapter passes `api_key=read_secret(api_key_env)` and `base_url=self.base_url` (falling back to `default_base_url`) to its SDK client |
| Bad profile rejected before sending | `from_dict` (unknown, then missing settings) and `__post_init__` (every value problem) raise `ProfileError`; `create_connector` raises `ProfileError` for an unknown provider or unsupported option; `read_secret` raises `ConnectorAuthError`; all before `generate` is ever called |
| Target and judge independent | `config.load_config` builds two profiles; the CLI calls `create_connector` once for each; nothing outside the registry names a connector class |
| Refusal is a response, failure is a `ConnectorError` | `OpenAIConnector` copies `message.refusal`; `AnthropicConnector` maps `stop_reason == "refusal"`; `except openai.APIError` / `except anthropic.APIError` both `raise translate_error(e) from e` |
| Untrustworthy reply is a response error | the `isinstance` checks and the "no choices", "neither content nor refusal" and "no text and no refusal" checks raise `ConnectorResponseError` |
| Truncation reported the same way | `truncated` is `finish_reason == "length"` (OpenAI) or `stop_reason == "max_tokens"` (Claude); `finish_reason` keeps the provider's own value |
| No hidden retries | `ConnectionProfile.max_retries` defaults to 0 and reaches the SDK client as `max_retries` |
| Tests without network or key | `FakeConnector` calls `super().__init__(model=model)` only; it never calls `read_secret` |

## 6. Design notes and candidate refactorings

- **The port lives beside its adapters.** `ModelConnector`, `ModelResponse` and the `ConnectorError` family sit in `judgelab.connectors`, next to the SDK adapters, not in a core package. This is the known deviation recorded in [ADR-001](../../decisions/ADR-001.md). Moving the port into the core would let an import-linter rule forbid the core from importing `openai` or `anthropic`.
- **"Every problem at once" is true per stage, not across stages.** `from_dict` stops at unknown settings, then at missing ones, before `__post_init__` checks values. A profile with a typo *and* a negative timeout reports the typo first. Collecting all three stages into one list would match the use case's wording exactly (step 2).
- **Unknown providers are found late.** `ConnectionProfile` accepts any non-empty `provider`; only `create_connector` rejects `gemini`. So `load_config` succeeds on a profile that can never connect. Checking `provider in CONNECTORS` at profile time would need the profile to know the registry, which today would be a circular import (`registry` imports `profile`). A `providers` set injected into validation is the cleaner fix.
- **`options` is checked by `TypeError`.** `create_connector` turns any `TypeError` from the adapter's constructor into "unsupported option". That works (AC-001-21), but a `TypeError` raised for another reason would get the same message. Also, `options` can set `http_client`, which every live adapter accepts as a keyword. An explicit per-adapter `OPTIONS` set would make the allowed list visible and printable.
- **Some constructor checks raise `ValueError`, not `ProfileError`.** `ModelConnector.__init__` (blank model) and `AnthropicConnector.__init__` (`max_tokens < 1`) raise `ValueError`, which `create_connector` does not translate. A blank model can't get there (the profile catches it first), but `options: {max_tokens: 0}` leaves as a bare `ValueError` without the `connection '<name>':` prefix.
- **Two default timeouts.** `AnthropicConnector` defaults `timeout_s` to 300 and `OpenAIConnector` to 60, but `create_connector` always passes `profile.timeout_s`, whose default is 60. Through a profile, a Claude connector gets 60 seconds unless the YAML says otherwise. Either the profile default should be `None` (meaning "the adapter's default"), or the adapter defaults should go.
- **The key is read at construction, not at call time.** `read_secret` runs in each adapter's `__init__`, so extension 4a fails when the connector is created, as AC-001-01 says. The cost is that the SDK client holds the key for the connector's lifetime; that is the SDK's design and acceptable here.
- **`FakeConnector` is not in `CONNECTORS`.** The ontology lists `fake` as a provider, but a YAML profile can't choose it; tests build it directly or inject a `connector_factory` into the CLI. Registering it would allow keyless end-to-end runs from a config file, at the cost of exposing a test double to users.
- **`translate_error` is duplicated** in both adapter modules with the same status mapping. Only reading the error code differs (`e.code` for OpenAI; `error.details.error_code` in the body for Anthropic). A shared `classify(status, code)` in `errors` would keep the mapping in one place, leaving each adapter to extract status, code and request id.
- **`request_id` comes from a private attribute.** Both adapters read `completion._request_id` / `message._request_id`, which the SDKs document but mark private. A change in the SDK would surface as an `AttributeError`, which `generate` does not translate.

## 7. Checking the design against the code (as-built)

Generate the as-built sequences from tests that exercise this design, and compare them with section 3. The first covers steps 1 to 4 (registry, adapter, `read_secret`) for both providers; the second covers steps 5 and 6:

```bash
uv run python .claude/skills/vbench-docs/scripts/asbuilt.py sequence \
  "tests/connectors/test_registry.py::test_target_and_judge_switch_independently" \
  -o docs/usecases/UC-001-configure-model-connections/diagrams/as-built/sequence-profile.puml

uv run python .claude/skills/vbench-docs/scripts/asbuilt.py sequence \
  "tests/connectors/test_openai_connector.py::test_returns_answer_and_metadata" \
  -o docs/usecases/UC-001-configure-model-connections/diagrams/as-built/sequence.puml
```

A difference is either design drift (update this page and say why) or a code bug (fix the code). See [ADR-002](../../decisions/ADR-002.md).

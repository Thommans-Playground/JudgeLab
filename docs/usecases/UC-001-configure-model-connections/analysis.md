# UC-001 Analysis: Configure model connections

> **Draft for review.** Analysis describes *what* has to happen, in the problem's words: no Python, no SDKs, no patterns. The [design](design.md) says how the code does it.

| Field | Value |
|---|---|
| Use case | [UC-001](README.md) |
| Criteria | [UC-001.feature](UC-001.feature) |
| Bounded context | [Model Access](../../domain/model-access/README.md) |
| Ontology | [ConnectionProfile](../../ontology/connection-profile.md), [Provider](../../ontology/provider.md), [Credential](../../ontology/credential.md), [ModelConnector](../../ontology/model-connector.md), [ModelResponse](../../ontology/model-response.md), [Refusal](../../ontology/refusal.md), [ConnectorError](../../ontology/connector-error.md) |

## 1. System sequence diagram

The system is a black box. The diagram shows only what crosses its boundary. It has two halves: first the developer's configuration goes in and a connector for each profile (or an error) comes out; later, each prompt goes out to the model provider and a response or a connector error comes back. It is the main success scenario and its extensions, drawn.

Diagram: [UC-001 system sequence diagram](diagrams/ssd.puml)

**System operations** found here:

| Operation | Responsibility | Postcondition |
|---|---|---|
| configure connections | Turn the target and judge settings into one connector each | Two independent connectors exist, or a profile error says which profile is wrong and why (AC-001-12, AC-001-22) |
| validate profile | Check every setting of one profile and report every problem at once | A valid Connection Profile, or one error starting `connection '<name>':` (AC-001-13 to AC-001-17) |
| choose connector | Pick the connector for the profile's provider, with the profile's options | The right connector kind, or an error listing the known providers or naming the unsupported option (AC-001-19 to AC-001-21) |
| resolve credential | Read the key from the environment variable the profile names | The connector holds the key; nothing else does. Missing or blank is an auth error naming the variable (AC-001-01, AC-001-18) |
| model request (out) | Send one prompt, with instructions in the provider's own way, exactly once | The provider received one request built only from the connector's own settings (AC-001-02, AC-001-07) |
| record response | Keep the answer or refusal with its model identity and call metadata | A Model Response in JudgeLab's terms (AC-001-03, AC-001-04, AC-001-11) |
| raise connector error | Turn a provider failure or an untrustworthy reply into a known kind | A Connector Error with the HTTP status and request id, and no secret (AC-001-05, AC-001-06, AC-001-08) |

## 2. Analysis classes

Found by reading the use case's nouns and splitting them by role:

- **Boundary:** where the system meets something outside it. Here, three things: the configuration the developer writes, the environment that holds the key, and the model provider.
- **Control:** the use case's logic. This use case has two distinct moments, so it gets two: configuring a connection (steps 1 to 4) and calling the model (steps 5 and 6).
- **Entity:** information the problem cares about, which outlives one step.

Diagram: [UC-001 analysis classes](diagrams/analysis-classes.puml)

| Analysis class | Role | Comes from (use case text) | Ontology concept |
|---|---|---|---|
| Configuration Interface | Boundary | "a configuration with a `connections` section" | — |
| Environment Interface | Boundary | "the environment variable named by `api_key_env`" | Credential |
| Provider Interface | Boundary | "sends one request to the provider … in that provider's own way" | Provider |
| Configure Connection | Control | the main success scenario, steps 1 to 4 | ModelConnector (creation) |
| Call Model | Control | the main success scenario, steps 5 and 6 | ModelConnector |
| Connection Profile | Entity | "each as its own connection profile" | ConnectionProfile |
| Provider | Entity | "the connector named by the profile's `provider`" | Provider |
| Credential | Entity | "the profile only names the environment variable that holds the key" | Credential |
| Model Response | Entity | "the answer, or the model's refusal, with the requested and served model …" | ModelResponse, Refusal |
| Connector Error | Entity | "an auth, quota, rate limit, unavailable or request error", "a response error" | ConnectorError |

The Credential entity holds a name, not a value. The key itself passes through Configure Connection once, into the connection it configures, and is never kept in an entity.

## 3. Analysis sequence

How the analysis objects work together to deliver the main success scenario. The two control objects drive the work, entities hold the information, and only the boundaries talk to the outside.

Diagram: [UC-001 analysis sequence](diagrams/analysis-sequence.puml)

## 4. Rules the design must keep

These come from the use case's business rules and its scenarios. The design is checked against them.

1. A secret lives only in an environment variable. A profile names the variable; no profile, repr or error message holds or shows the key (AC-001-08, AC-001-14).
2. A connector is configured only from its own settings. Provider environment variables such as `OPENAI_API_KEY` or `ANTHROPIC_BASE_URL` have no effect (AC-001-02).
3. A bad profile is rejected before anything is sent, with every problem in one message that names the profile (AC-001-13, AC-001-16, AC-001-17).
4. Target and judge are independent. Swapping either one's provider or model is a configuration change only (AC-001-22).
5. A refusal is a Model Response, not a failure. A failure is always a Connector Error of a known kind, never a provider's own exception (AC-001-04, AC-001-06, AC-001-09).
6. A reply that cannot be trusted is a response error, never an empty answer (AC-001-05).
7. Truncation is reported the same way for every provider, and the provider's own finish reason is kept (AC-001-11).
8. No hidden retries: one request per prompt unless retries are configured (AC-001-07).
9. Tests can use a scripted connector that needs no network and no key (AC-001-10).

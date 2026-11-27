# Acceptance criteria for UC-001. One Scenario per criterion, tagged with its ID.
# DRAFT for review. AC-001-01..22 were defined with the slices; this file sharpens their wording.

Feature: UC-001 Configure model connections
  As a developer setting up an evaluation
  I want to describe the target and the judge models as separate connection profiles
  So that I can call, swap and test any model through one connector interface, without exposing a key

  Requirements: REQ-003, REQ-004, REQ-005, REQ-012, REQ-013

  @AC-001-01
  Scenario Outline: A missing or blank key variable is an auth error that names the variable
    Given the profile's api_key_env is "JUDGELAB_OPENAI_KEY"
    And that variable is <state>
    When a connector is created from the profile
    Then it fails with an auth error "environment variable JUDGELAB_OPENAI_KEY is not set"
    And the error contains no secret
    And no request is sent

    Examples:
      | state                      |
      | not set                    |
      | set to an empty string     |
      | set to only spaces         |

  @AC-001-02
  Scenario Outline: Provider environment variables have no effect on a connector
    Given the profile's api_key_env is "JUDGELAB_KEY" and it holds the key
    And <variable> is set to a different value
    When the <connector> answers a prompt
    Then the request goes to the profile's base_url, or to <default url> when there is none
    And it carries the key from "JUDGELAB_KEY", not the value of <variable>

    Examples:
      | connector                   | variable             | default url                 |
      | OpenAI-compatible connector | OPENAI_API_KEY       | https://api.openai.com/v1   |
      | OpenAI-compatible connector | OPENAI_BASE_URL      | https://api.openai.com/v1   |
      | Claude connector            | ANTHROPIC_API_KEY    | https://api.anthropic.com   |
      | Claude connector            | ANTHROPIC_AUTH_TOKEN | https://api.anthropic.com   |
      | Claude connector            | ANTHROPIC_BASE_URL   | https://api.anthropic.com   |

  @AC-001-03
  Scenario: A successful reply returns the answer with its model identity and call metadata
    Given a connector configured with the model "asked-model"
    And the provider answers "Paris" as the model "served-model-v2", with request id "req_1"
    And the reply used 12 prompt tokens and 1 completion token and stopped normally
    When the connector is asked "Capital of France?"
    Then the response has the text "Paris" and no refusal
    And requested_model "asked-model" and served_model "served-model-v2"
    And the provider's finish_reason, such as "stop", and truncated false
    And prompt_tokens 12, completion_tokens 1 and request_id "req_1"
    But when the provider reports no usage, both token counts are empty

  @AC-001-04
  Scenario: A refusal is a response, not an error
    Given the model refuses with "I can't help with that."
    When the connector is asked a prompt
    Then the response has no text and the refusal "I can't help with that."
    And no error is raised

  @AC-001-05
  Scenario Outline: A reply that cannot be trusted is a response error
    Given the provider replies with <reply>
    When the connector is asked a prompt
    Then it fails with a response error that says "<message>"

    Examples:
      | reply                                                | message                                     |
      | an HTML gateway page instead of a chat completion    | expected a chat completion                  |
      | a chat completion with no choices                    | response has no choices                     |
      | a chat completion with neither content nor refusal   | response has neither content nor refusal    |
      | a Claude message with no text and no refusal         | response has no text and no refusal         |

  @AC-001-06
  Scenario Outline: Provider failures become JudgeLab connector errors
    Given the provider fails with <failure>
    When the connector is asked a prompt
    Then it fails with a <kind> error
    And the error records the HTTP status and the request id, when the provider sent them

    Examples:
      | failure                                                   | kind         |
      | HTTP 401 (invalid_api_key) or HTTP 403                    | auth         |
      | HTTP 402                                                  | quota        |
      | HTTP 429 (credit_balance_exhausted)                       | quota        |
      | HTTP 429 (project_spend_limit_exceeded)                   | quota        |
      | HTTP 429 (enforced_spend_limit_reached) from Claude       | quota        |
      | HTTP 429 with no quota code                               | rate limit   |
      | a timeout ("request timed out")                           | unavailable  |
      | a connection failure ("request connection failed")        | unavailable  |
      | HTTP 500, HTTP 503 or HTTP 529 (overloaded)               | unavailable  |
      | HTTP 400, or HTTP 404 (model_not_found)                   | request      |

  @AC-001-07
  Scenario: No request is retried unless retries are configured
    Given a profile with no max_retries setting
    And the provider fails with HTTP 500
    When the connector is asked a prompt
    Then it fails with an unavailable error
    And the provider received exactly one request

  @AC-001-08
  Scenario: The API key never appears in a repr or an error message
    Given a connector whose key variable holds a key
    When the connector is shown with repr()
    Then it shows only the connector type, the model and the base URL
    And when the provider rejects the key with HTTP 401 (invalid_api_key)
    Then the auth error says "HTTP 401 (invalid_api_key)" and contains no part of the key

  @AC-001-09
  Scenario Outline: Every connector keeps the same contract
    Given the <connector>
    When it is asked "What is the capital of France?", with or without instructions
    Then it returns a response whose text is "Paris"
    And any failure it meets is a connector error, never a provider SDK error
    And its repr names its model and shows no secret

    Examples:
      | connector                   |
      | OpenAI-compatible connector |
      | Claude connector            |
      | fake connector              |

  @AC-001-10
  Scenario: The fake connector answers from a script and records what it was sent
    Given a fake connector scripted to answer "Capital of France?" with "Paris"
    And to refuse "Help me hack" with "I can't help with that."
    And to fail "hi" with a rate limit error
    When it is sent each of those prompts
    Then it answers "Paris", returns the refusal, and raises the rate limit error
    And it records every prompt it was sent, in order
    And it needs no network and no key
    But a prompt that is not in the script fails with "fake connector has no reply for prompt 'surprise'"

  @AC-001-11
  Scenario Outline: Truncation is reported the same way for every provider
    Given the <connector>
    And the provider stops the answer "Par" with the finish reason "<finish reason>"
    When the connector is asked a prompt
    Then the response has the text "Par" and truncated true
    And finish_reason keeps the provider's own value "<finish reason>"

    Examples:
      | connector                   | finish reason |
      | OpenAI-compatible connector | length        |
      | Claude connector            | max_tokens    |

  @AC-001-12
  Scenario: A connection profile is built from configuration
    Given the configuration for the connection "target":
      """
      provider: openai_compatible
      model: gpt-x
      api_key_env: OPENAI_API_KEY
      """
    When the profile is built
    Then it has provider "openai_compatible", model "gpt-x" and api_key_env "OPENAI_API_KEY"
    And the defaults base_url none, timeout_s 60, max_retries 0 and no options
    But base_url, timeout_s, max_retries and options are taken from the configuration when given

  @AC-001-13
  Scenario: Missing or blank required settings are all reported at once
    Given the connection "target" has only provider "openai_compatible"
    When the profile is built
    Then it fails with "connection 'target': missing model, api_key_env"
    But when provider is " ", model is "" and timeout_s is 0
    Then one error lists "provider must be a non-empty string", "model must be a non-empty string" and "timeout_s must be greater than 0"

  @AC-001-14
  Scenario: api_key_env must name a variable, and a pasted key is never echoed
    Given the connection "target" has api_key_env set to something that looks like a key
    When the profile is built
    Then it fails with "api_key_env must name an environment variable (like OPENAI_API_KEY), not contain a key"
    And the error does not contain the value that was given

  @AC-001-15
  Scenario Outline: base_url must be https, except for localhost
    Given the connection "target" has base_url "<url>"
    When the profile is built
    Then <outcome>

    Examples:
      | url                         | outcome                                                                          |
      | https://api.openai.com/v1   | the profile keeps that base_url                                                  |
      | http://localhost:8000/v1    | the profile keeps that base_url                                                  |
      | http://127.0.0.1:11434/v1   | the profile keeps that base_url                                                  |
      | http://api.example.com/v1   | it fails with "base_url must use https (plain http is allowed only for localhost)" |
      | ftp://example.com           | it fails with "base_url must use https (plain http is allowed only for localhost)" |
      | api.openai.com/v1           | it fails with "base_url must be a full URL like https://api.example.com/v1"      |

  @AC-001-16
  Scenario Outline: Unknown profile settings are rejected with the allowed list
    Given the connection "target" has the extra setting "<setting>"
    When the profile is built
    Then it fails with "connection 'target': unknown setting(s) <setting>; allowed: api_key_env, base_url, max_retries, model, options, provider, timeout_s"

    Examples:
      | setting |
      | api_key |
      | modle   |

  @AC-001-17
  Scenario Outline: timeout_s and max_retries are range-checked
    Given the connection "target" has <setting>
    When the profile is built
    Then it fails with "<message>"

    Examples:
      | setting               | message                              |
      | timeout_s: -1         | timeout_s must be greater than 0     |
      | timeout_s: "fast"     | timeout_s must be a number           |
      | max_retries: -1       | max_retries must be 0 or more        |
      | max_retries: 1.5      | max_retries must be a whole number   |
      | max_retries: true     | max_retries must be a whole number   |

  @AC-001-18
  Scenario: The key is read from the variable the profile names
    Given the profile's api_key_env is "JUDGELAB_TEST_SECRET"
    And that variable holds a key with spaces around it
    When a connector is created from the profile
    Then the connector uses that key with the spaces trimmed
    And every connector reads its key the same way, through one shared step

  @AC-001-19
  Scenario Outline: The connector is chosen by the profile's provider
    Given the connection "target" has provider "<provider>" and model "<model>"
    When a connector is created from the profile
    Then it is the <connector>, configured with the model "<model>"
    And the profile's base_url and timeout reach the connector

    Examples:
      | provider          | model           | connector                   |
      | openai_compatible | gpt-x           | OpenAI-compatible connector |
      | anthropic         | claude-opus-5-5 | Claude connector            |

  @AC-001-20
  Scenario: An unknown provider is rejected with the known ones
    Given the connection "target" has provider "gemini"
    When a connector is created from the profile
    Then it fails with "connection 'target': unknown provider 'gemini'; known: anthropic, openai_compatible"

  @AC-001-21
  Scenario: Provider-specific options reach the connector, and unsupported ones are rejected
    Given the connection "judge" has provider "anthropic" and options max_tokens 512
    When a connector is created from the profile
    Then the Claude connector asks for at most 512 tokens per answer
    But when the connection "target" has provider "openai_compatible" and options max_tokens 512
    Then it fails with an error that starts "connection 'target': unsupported option for openai_compatible"

  @AC-001-22
  Scenario: Target and judge are independent, and swapping them is a configuration change
    Given the target profile uses provider "openai_compatible" and the judge profile uses "anthropic"
    When connectors are created for both
    Then the target gets the OpenAI-compatible connector and the judge gets the Claude connector
    And when the two profiles' providers and models are swapped in the configuration
    Then the target gets the Claude connector and the judge gets the OpenAI-compatible connector
    And no code changes

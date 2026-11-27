# Acceptance criteria for UC-003. One Scenario per criterion, tagged with its ID.
# DRAFT for review. AC-003-01..05 keep the meanings the runner tests are marked with.

Feature: UC-003 Execute target model
  As a developer running an evaluation
  I want every benchmark question sent to the target model and its answer captured
  So that each case has an answer to judge, or a recorded reason why it has none

  Requirements: REQ-005

  Background:
    Given a benchmark with three cases, in this order:
      | id | question           | expected_answer |
      | c1 | Capital of France? | Paris           |
      | c2 | 2+2?               | 4               |
      | c3 | Largest planet?    | Jupiter         |

  @AC-003-01
  Scenario: Each question is sent once, in order, and each answer is kept with its case
    Given the target answers "Paris", "4" and "Jupiter"
    When the target is run over the benchmark
    Then the target receives exactly "Capital of France?", "2+2?" and "Largest planet?", in that order
    And the results are for "c1", "c2" and "c3", in that order
    And their responses are "Paris", "4" and "Jupiter", with no errors

  @AC-003-02
  Scenario Outline: A connector error on one case is recorded and the run continues
    Given the target fails on "2+2?" with <error>
    When the target is run over the benchmark
    Then the result for "c2" has no response and records that error
    And "Largest planet?" is still sent, and the result for "c3" has the response "Jupiter"

    Examples:
      | error                                  |
      | an unavailable error, "HTTP 500"       |
      | a rate-limit error, "HTTP 429"         |

  @AC-003-03
  Scenario Outline: An auth or quota error stops the run
    Given the target fails on "2+2?" with <error>
    When the target is run over the benchmark
    Then the result for "c2" records that error
    And "Largest planet?" is never sent to the target
    And the result for "c3" has no response and the error "not sent: run stopped after <type> on case c2"

    Examples:
      | error                                                   | type                |
      | an auth error, "HTTP 401"                               | ConnectorAuthError  |
      | a quota error, "HTTP 429 (credit_balance_exhausted)"    | ConnectorQuotaError |

  @AC-003-04
  Scenario: A progress callback hears about every case
    Given a progress callback that notes each result's case id
    When the target is run over the benchmark with that callback
    Then the callback has noted "c1", "c2" and "c3", in that order

  @AC-003-05
  Scenario: A bug in the target code is not hidden
    Given the target code raises a ZeroDivisionError, which is not a connector error
    When the target is run over the benchmark
    Then the run fails with that ZeroDivisionError
    And no results are returned

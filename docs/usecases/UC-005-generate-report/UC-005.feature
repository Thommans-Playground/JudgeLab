# Acceptance criteria for UC-005. One Scenario per criterion, tagged with its ID.
# DRAFT for review. AC-005-01..07 keep the meaning of the v0.1 plan's reporting rules.

Feature: UC-005 Generate report
  As a developer reviewing an evaluation
  I want every run written to a JSON report with its evidence, its metadata and a summary
  So that I can check each verdict and trust the numbers without rerunning anything

  Requirements: REQ-009, REQ-010, REQ-013

  @AC-005-01
  Scenario: Outcomes are counted in a single pass, so results can be read only once
    Given the results of a run arrive one at a time and can be read only once
    And their outcomes are PASS, FAIL, PASS and ERROR
    When the run is summarised
    Then the summary shows "total" 4, "passed" 2, "failed" 1 and "errors" 1

  @AC-005-02
  Scenario Outline: The pass rate counts only cases with a verdict
    Given a run with <passed> PASS, <failed> FAIL and <errors> ERROR cases
    When the run is summarised
    Then the summary shows "evaluated" <evaluated> and "pass_rate" <pass_rate>
    And the errors are reported in "errors", never counted as failures

    Examples:
      | passed | failed | errors | evaluated | pass_rate |
      | 1      | 1      | 2      | 2         | 0.5       |
      | 3      | 1      | 0      | 4         | 0.75      |
      | 0      | 0      | 2      | 0         | null      |
      | 0      | 0      | 0      | 0         | null      |

  @AC-005-03
  Scenario Outline: Coverage is the share of cases that reached a verdict
    Given a run with <passed> PASS, <failed> FAIL and <errors> ERROR cases
    When the run is summarised
    Then the summary shows "coverage" <coverage> next to "pass_rate"

    Examples:
      | passed | failed | errors | coverage |
      | 1      | 2      | 1      | 0.75     |
      | 1      | 0      | 1      | 0.5      |
      | 3      | 2      | 0      | 1.0      |
      | 0      | 0      | 0      | 0.0      |

  @AC-005-04
  Scenario: Each case carries its full evidence
    Given case "c1" "Capital of France?" with expected answer "Paris" was answered "Paris" and judged PASS with "Correct."
    And case "c2" failed at the target with "ConnectorUnavailableError: HTTP 503"
    When the report is built
    Then case "c1" shows its question, expected answer, actual answer, refusal, outcome "PASS", verdict "PASS" and justification "Correct."
    And its "target_call" and "judge_call" each show the requested and served model, the finish reason, the tokens, the request id and the latency
    And its "error" is null
    And case "c2" shows outcome "ERROR", verdict null, target_call null and error {"stage": "target", "message": "ConnectorUnavailableError: HTTP 503"}

  @AC-005-05
  Scenario: The report records what was run, with what, and when
    Given run "abc123ef99" of benchmark "b1" ("Bench", 2 cases) with the rubric "semantic_correctness"
    And it started at 09:30:00 UTC on 2026-11-27
    And its judge is the OpenAI-compatible model "gpt-judge"
    When the report is built
    Then "report_version" is "1"
    And "run" shows the id "abc123ef99", "started_at" "2026-11-27T09:30:00+00:00", a "finished_at" time and the JudgeLab version "0.1.0"
    And "benchmark" is {"id": "b1", "name": "Bench", "cases": 2} and "rubric" is "semantic_correctness"
    And "connections.judge" is {"provider": "openai_compatible", "model": "gpt-judge", "base_url": "https://api.openai.com/v1"}
    And "summary" shows total, passed, failed, errors, evaluated, pass_rate and coverage

  @AC-005-06
  Scenario: The report never contains a key or the name of its variable
    Given a judge connection whose key is read from the environment variable "REPORT_TEST_KEY"
    And that variable holds a key
    When the report is written to a file
    Then the file does not contain the key
    And the file does not contain "REPORT_TEST_KEY"

  @AC-005-07
  Scenario: Reports are written as UTF-8 JSON with a unique, time-stamped name
    Given run "abc123ef99" started at 09:30:00 UTC on 2026-11-27
    And the output directory "reports/nested" does not exist yet
    When the report is written to "reports/nested"
    Then the directory is created
    And the file "reports/nested/run-20261127T093000Z-abc123ef.json" exists
    And it reads back, as UTF-8 JSON, to the same report

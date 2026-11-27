# Acceptance criteria for UC-006. One Scenario per criterion, tagged with its ID.
# DRAFT for review. AC-006-01..07 are checked by the default test run with fake connectors.
# AC-006-08..11 are live and opt-in: they call real models with real keys and run only when asked for.

Feature: UC-006 Run complete evaluation
  As a developer
  I want to run a whole evaluation with one command
  So that I get every case answered, judged and reported, with every failure shown as an explicit ERROR

  Requirements: REQ-003, REQ-005, REQ-006, REQ-008, REQ-011, REQ-013

  @AC-006-01
  Scenario: Each answer is judged and the verdict becomes the outcome
    Given a benchmark with the cases "c1" "Capital of France?", "c2" "2+2?" and "c3" "Largest planet?"
    And the target answers "Paris", "5" and "Jupiter"
    And the judge says PASS for "Paris" and "Jupiter" and FAIL with "Wrong." for "5"
    When the evaluation runs
    Then the outcomes are "c1" PASS, "c2" FAIL and "c3" PASS
    And "c2" keeps the justification "Wrong."

  @AC-006-02
  Scenario Outline: An answer we can't trust from the target is an ERROR and is never judged
    Given the target <situation> for case "c2"
    When the evaluation runs
    Then case "c2" is ERROR at the "target" stage with the message "<message>"
    And case "c2" is not sent to the judge

    Examples:
      | situation                                   | message                                |
      | fails with HTTP 500                         | ConnectorUnavailableError: HTTP 500    |
      | answers, but is cut off by its length limit | answer was cut off by its length limit |

  @AC-006-03
  Scenario Outline: A judge failure is an ERROR at the judge stage, never a FAIL
    Given the target answers "Paris" to every case
    And for case "c2" the judge <situation>
    When the evaluation runs
    Then case "c2" is ERROR at the "judge" stage, not FAIL
    And case "c3" is <c3_outcome>

    Examples:
      | situation                     | c3_outcome                                                                          |
      | replies "I think it's fine"   | judged as usual                                                                     |
      | rejects the key with HTTP 401 | ERROR "not judged: judging stopped after ConnectorAuthError on case c2", not judged |

  @AC-006-04
  Scenario: A refusal is sent to the judge as the answer
    Given the target refuses case "c1" with "I can't share that."
    When the evaluation runs
    Then the judge receives "[refused] I can't share that." as the actual answer for "c1"
    And the judge's verdict decides whether refusing was right

  @AC-006-05
  Scenario: One command runs the whole evaluation
    Given a valid config for the five-case sample benchmark "General knowledge (sample)"
    When I run "judgelab run --config evaluation.yaml"
    Then it prints "Running 'General knowledge (sample)': 5 cases", the target and the judge
    And it prints one progress line per case, from "[1/5] gk-001: PASS" to "[5/5] gk-005: FAIL"
    And it prints "Passed: 1  Failed: 4  Errors: 0  (of 5)" and "Pass rate: 20.0% of 5 evaluated  Coverage: 100.0%"
    And it writes one "run-*.json" report to the output directory and prints "Report: <its path>"
    And the exit code is 0

  @AC-006-06
  Scenario Outline: A configuration problem stops the run before it starts
    Given <problem>
    When I run "judgelab run --config evaluation.yaml"
    Then the exit code is 1
    And stderr starts with "error: " and contains "<message>"
    And no traceback is shown and no pasted key is echoed
    And no report is written

    Examples:
      | problem                                                  | message                                    |
      | the config file does not exist                           | config file not found                      |
      | the config file contains "connections: ["                | is not valid YAML (line 1, column 15)      |
      | the config has an extra section "extras"                 | unknown section(s) extras                  |
      | the target connection has the misspelled setting "modle" | unknown setting(s) modle                   |
      | the target's api_key_env holds a pasted key              | must name an environment variable          |
      | the config names the rubric "strict"                     | unknown rubric 'strict'                    |
      | the config names the dataset "missing.json", not on disk | missing.json                               |
      | the environment variable TARGET_KEY is not set           | environment variable TARGET_KEY is not set |

  @AC-006-07
  Scenario Outline: The config names everything a run needs, and the output directory can be overridden
    Given a config with a target and a judge connection, the dataset "benchmarks/sample.json" and the rubric "semantic_correctness"
    And <output in config>
    When I run "judgelab run --config evaluation.yaml" <option>
    Then the report is written to "<directory>"

    Examples:
      | output in config    | option                         | directory |
      | output.dir is "out" | with no other option           | out       |
      | no output section   | with no other option           | reports   |
      | output.dir is "out" | with "--output-dir elsewhere"  | elsewhere |

  @AC-006-08
  Scenario: Live smoke tests make one real call per connector, only when asked for
    Given the bundled config "configs/evaluation.yaml"
    And OPENAI_API_KEY and ANTHROPIC_API_KEY are set to real keys
    When I run the live tests on purpose with "pytest -m live"
    Then the target and the judge each answer "What is the capital of France? Answer with one word." with an answer containing "Paris"
    And each response names its served model and a request id
    But a plain "pytest" run skips these tests, and a connection whose key is not set is skipped

  @AC-006-09
  Scenario: A live run of the sample benchmark completes with a report
    Given real keys are set for both connections in the bundled config
    When I run "judgelab run --config configs/evaluation.yaml" on purpose against the real models
    Then the run exits 0 and writes a report for all 5 cases
    And the report's "coverage" is 1.0, or every ERROR case explains its stage and cause

  @AC-006-10
  Scenario: A human reviews every verdict of the live run
    Given the report of the live run from AC-006-09
    When I read every case's question, expected answer, actual answer, verdict and justification
    Then the release report records, for each case, whether I agree with the judge
    And every disagreement is written down with the case id and the reason

  @AC-006-11
  Scenario: Swapping target and judge needs only a config change
    Given a copy of the bundled config in which the target and judge connections are swapped
    And real keys are set for both connections
    When I run "judgelab run" on purpose with the swapped config, without changing any code
    Then a second valid report is written
    And its "connections" show the Claude model as the target and the OpenAI-compatible model as the judge

# Acceptance criteria for UC-004. One Scenario per criterion, tagged with its ID.
# DRAFT for review. AC-004-01..05 come from the v0.1 plan; 06 and 07 were added during design.

Feature: UC-004 Evaluate responses
  As a developer running an evaluation
  I want every target answer judged against its question, its expected answer and a rubric
  So that each case ends with a trustworthy PASS or FAIL, or an explicit ERROR

  Requirements: REQ-003, REQ-006, REQ-007, REQ-008

  @AC-004-01
  Scenario: The judge sees the question, the expected answer and the actual answer, under the rubric
    Given the test case "What is the capital of France?" with expected answer "Paris"
    And the target answered "It's Paris."
    When the answer is sent to the judge
    Then the judge's prompt contains the question, the expected answer and the actual answer, each in its own tag
    And the rubric and the required output format are sent as the judge's instructions

  @AC-004-02
  Scenario Outline: Only a supported verdict with a justification is accepted
    Given the judge replies <reply>
    When the reply is parsed
    Then the result is <result>

    Examples:
      | reply                                                   | result                                  |
      | {"verdict": "PASS", "justification": "Correct."}        | the verdict PASS                        |
      | {"verdict": "fail", "justification": "Wrong city."}     | the verdict FAIL                        |
      | the same JSON wrapped in a ```json code fence           | the verdict it contains                 |
      | {"verdict": "MAYBE", "justification": "Unsure."}        | an error: unsupported verdict 'MAYBE'   |
      | {"verdict": "PASS"}                                     | an error: the reply has no justification |

  @AC-004-03
  Scenario Outline: A judgement that cannot be trusted is an ERROR, never a FAIL
    Given the judge <situation>
    When the answer is evaluated
    Then no verdict is produced
    And the case is recorded as ERROR, not as FAIL

    Examples:
      | situation                                  |
      | replies "I think it's fine"                |
      | replies with JSON that is not an object    |
      | refuses to evaluate the answer             |
      | is cut off by its length limit             |
      | cannot be reached, or rejects the request  |

  @AC-004-04
  Scenario: The evaluation records which judge model produced the verdict
    Given the judge is configured with the model "claude-opus-5-5"
    And the provider reports that "claude-opus-5-5-20261101" answered
    When an answer is evaluated
    Then the evaluation records the verdict, the justification and the rubric id
    And it records both the requested model and the served model of the judge

  @AC-004-05
  Scenario: Switching the judge is a configuration change only
    Given an evaluation whose judge is an OpenAI-compatible model
    When the judge's connection profile is changed to a Claude model
    Then the answers are judged through the Claude connector
    And the benchmark cases, the rubric and the outcome rules are unchanged

  @AC-004-06
  Scenario Outline: The judge's instructions reach every provider in that provider's own way
    Given the <connector>
    When it is asked for an answer with instructions
    Then the instructions are sent as <how>
    And a request without instructions sends only the user's message

    Examples:
      | connector                      | how                                          |
      | OpenAI-compatible connector    | a "system" message before the user's message |
      | Claude connector               | the top-level "system" field                 |
      | fake connector                 | a record kept next to the prompt             |

  @AC-004-07
  Scenario: Rubrics are chosen by id
    Given the rubric "semantic_correctness" exists
    When an evaluation asks for the rubric "semantic_correctness"
    Then that rubric's instructions are used for every judgement
    But asking for the rubric "strict" fails with "unknown rubric 'strict'; known: semantic_correctness"

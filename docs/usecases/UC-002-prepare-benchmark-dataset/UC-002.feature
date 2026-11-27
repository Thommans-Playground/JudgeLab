# Acceptance criteria for UC-002. One Scenario per criterion, tagged with its ID.
# DRAFT for review. AC-002-01..08 keep the meanings the dataset tests are marked with.

Feature: UC-002 Prepare benchmark dataset
  As a developer preparing an evaluation
  I want a benchmark file loaded into validated test cases
  So that every run starts from cases I can trust, and a bad file is fixed in one pass

  Requirements: REQ-001, REQ-002

  @AC-002-01
  Scenario: A valid benchmark file loads with its cases in file order
    Given the benchmark file "bench.json" contains:
      """
      {"id": "b1", "name": "Bench", "cases": [
        {"id": "c1", "question": "2+2?", "expected_answer": "4"},
        {"id": "c2", "question": "Capital of France?", "expected_answer": "Paris"}
      ]}
      """
    When the benchmark is loaded
    Then the benchmark has the id "b1" and the name "Bench"
    And its test cases are "c1" then "c2", each with its question and expected answer

  @AC-002-02
  Scenario Outline: A file that cannot be read as JSON is rejected with the reason
    Given <file>
    When the benchmark is loaded
    Then the load fails with an error naming "<name>"
    And the error's only problem is "<problem>"

    Examples:
      | file                                                         | name       | problem                            |
      | no file exists at "nope.json"                                | nope.json  | file not found                     |
      | "bench.json" has line 2 '  "name": }', with no value         | bench.json | not valid JSON (line 2, column 11) |

  @AC-002-03
  Scenario: The bundled sample benchmark loads
    Given the file "benchmarks/sample.json" that ships with JudgeLab
    When the benchmark is loaded
    Then the benchmark has the id "general-knowledge-v1"
    And it has at least five test cases

  @AC-002-04
  Scenario Outline: Required fields must be non-empty strings, and errors give their location
    Given a benchmark file where <situation>
    When the benchmark is loaded
    Then the load fails with the problem "<problem>"

    Examples:
      | situation                                | problem                                             |
      | the benchmark has no "id"                | benchmark.id must be a non-empty string             |
      | the benchmark has no "name"              | benchmark.name must be a non-empty string           |
      | the second case's "question" is " "      | cases[1].question must be a non-empty string        |
      | the first case has no "expected_answer"  | cases[0].expected_answer must be a non-empty string |
      | the first case's "id" is the number 7    | cases[0].id must be a non-empty string              |

  @AC-002-05
  Scenario: Duplicate case ids are rejected, naming the id and both positions
    Given a benchmark file whose cases have the ids "c1", "c2" and "c1"
    When the benchmark is loaded
    Then the load fails with the problem "cases[2].id 'c1' duplicates cases[0].id"

  @AC-002-06
  Scenario: Unknown fields are rejected, so typos are caught
    Given a benchmark file whose first case is {"id": "c1", "question": "Q?", "expected_anwser": "A"}
    When the benchmark is loaded
    Then the load fails with the problems:
      | cases[0] has unknown field 'expected_anwser'        |
      | cases[0].expected_answer must be a non-empty string |

  @AC-002-07
  Scenario Outline: A benchmark must have at least one case
    Given a benchmark file with the id "b1", the name "Bench" and <cases>
    When the benchmark is loaded
    Then the load fails with the problem "cases must be a non-empty list"

    Examples:
      | cases                 |
      | "cases": []           |
      | no "cases" field      |

  @AC-002-08
  Scenario: Every problem in the file is reported at once
    Given a benchmark file with an empty "id"
    And its cases are a valid case "c1", the string "oops", and another case "c1"
    When the benchmark is loaded
    Then the load fails with the problems, in this order:
      | benchmark.id must be a non-empty string |
      | cases[1] must be an object              |
      | cases[2].id 'c1' duplicates cases[0].id |

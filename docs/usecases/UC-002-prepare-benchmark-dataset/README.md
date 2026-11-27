# UC-002: Prepare benchmark dataset

| Field | Value |
|---|---|
| Primary actor | Developer |
| Requirements | REQ-001, REQ-002 |
| Introduced in | v0.1 |
| Status | Draft |

## Goal

A benchmark file is turned into a list of test cases that the rest of the run can trust. Each case has an id, a question and an expected answer. A file with problems is rejected before any model is called, and the error lists every problem with its location, so the developer can fix the file in one pass.

> **Draft for review.** The flow and the scenarios were drafted from the [v0.1 release plan](../../releases/v0.1/README.md) and the slices' objectives. AC-002-01 to 08 keep the meanings the tests are marked with.

**Trigger:** an evaluation run starts with a benchmark path, such as `benchmarks/sample.json`.

## Preconditions

- A benchmark file path, from the command line or the evaluation config.
- The file is UTF-8 JSON with a top-level object holding `id`, `name` and `cases`. Each case holds `id`, `question` and `expected_answer`.

## Main success scenario

1. The system reads the file at the given path.
2. The system parses the file as JSON.
3. The system checks the benchmark's `id` and `name`, and that `cases` is a non-empty list.
4. The system checks every case: each is an object, its three fields are non-empty strings, it has no other fields, and its id is not used by an earlier case.
5. The system returns the benchmark: its id, its name and its test cases, in file order.

## Extensions / alternate flows

- **1a.** The file does not exist: the load fails with "file not found", naming the path.
- **2a.** The file is not valid JSON: the load fails with "not valid JSON (line L, column C)", naming the path.
- **2b.** The top level is not an object: the load fails with "the top level must be an object with id, name and cases".
- **3a.** A benchmark field is missing or blank: the problem names it, like "benchmark.id must be a non-empty string".
- **3b.** `cases` is missing, empty or not a list: the problem is "cases must be a non-empty list".
- **4a.** A case is not an object: the problem is "cases[1] must be an object".
- **4b.** A case field is missing, blank or not a string: the problem gives its location, like "cases[1].question must be a non-empty string".
- **4c.** A case has a field the schema does not know, often a typo: the problem names it, like "cases[0] has unknown field 'expected_anwser'".
- **4d.** A case id repeats an earlier one: the problem names the id and both positions, like "cases[2].id 'c1' duplicates cases[0].id".

## Postconditions

- Either a benchmark exists with at least one case, unique case ids and no blank fields, or an error names the file and lists every problem found.

## Business rules

- No model is called for a benchmark that fails to load.
- Cases keep their file order, so runs and reports line up with the file.
- Unknown fields are errors, not ignored, so a typo can't silently drop an expected answer.
- Checking does not stop at the first problem. Every problem from steps 3 and 4 is reported together in one error, in file order, so a file can be fixed in one pass.

## Acceptance criteria

Defined as Gherkin scenarios in [UC-002.feature](UC-002.feature): one Scenario per criterion, tagged with its ID. Tests are marked with the same IDs, so pytest's progress table shows which ones pass.

## Slices

Each slice is a task file in this folder that makes some of the criteria pass.

| Task | Slice | Delivers | Status |
|---|---|---|---|
| [T-002-01](T-002-01-json-dataset-loader.md) | JSON dataset loader | AC-002-01, AC-002-02, AC-002-03 | Todo |
| [T-002-02](T-002-02-test-case-validation.md) | Test-case validation | AC-002-04, AC-002-05, AC-002-06, AC-002-07, AC-002-08 | Todo |

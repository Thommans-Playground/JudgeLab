---
name: vbench-qa
description: QA review of acceptance criteria against the tests and the code. Runs the test suite, maps every criterion (Gherkin Scenario tagged @AC-UUU-NN in docs/usecases/*/*.feature) to the tests marked @pytest.mark.acceptance with it, reads those tests and the code they exercise, and reports for each criterion whether it is really verified, clause by clause, with prioritised recommendations. Use this skill whenever the user asks for a QA review, a status report on acceptance criteria or a use case, "is AC-001-08 really covered?", "what's left for UC-001?", "are my tests good enough?", before marking a task or criterion done, or before opening a PR that claims criteria, even if they just say "qa" or "how am I doing on the tests?".
---

# vbench-qa

The pytest acceptance table (tests/conftest.py) says PASS when every test *marked* with a criterion passed. It cannot tell whether those tests check everything the criterion promises: one passing test that touches one clause turns the whole line green. This skill closes that gap with a human-style review: for each criterion, does every Then/And clause, and every Examples row, have an assertion behind it, against the real code?

**This is a review, not a fix.** Never edit `src/`, `tests/` or `docs/` while running it. The user writes JudgeLab's code; the output is a report with recommendations. Describe a missing test by what it should set up and assert; write test code only if the user asks for it.

## Step 1: Scope

Take the scope from the request:
- a use case (`UC-001`): all its criteria, tested or not
- a criterion (`AC-001-08`): just that one
- nothing: every criterion that has at least one marked test, plus a one-line count of untested criteria per use case

## Step 2: Gather evidence

Run these from the repo root, and keep their output for the report:

```bash
uv run pytest -q --color=no                                  # outcomes + acceptance table
python3 .claude/skills/vbench-qa/scripts/acmap.py --uc UC-001 # or --ac AC-001-08, or no flag
```

`acmap.py` prints, for each criterion, its full Scenario (steps and Examples) with file:line, and every test marked with it, with file:line and its number of parametrized cases. It ends with marker problems: IDs marked on a test but not defined, and retired criteria still marked. If pytest has failures, read the failure output: a FAIL is reported as FAILING with its cause, not reviewed clause by clause.

## Step 3: Review each criterion

For each criterion in scope, read the Scenario, each marked test (and the helpers and fixtures it uses), and the production code the test exercises, following imports into `src/judgelab/`. Then check:

1. **Clauses.** Split the Scenario into its Then/And clauses. For each, find the assertion that checks it, and quote the test line. A clause with no assertion is a gap, even if the code happens to behave correctly.
2. **Examples.** For a Scenario Outline, match each Examples row to a parametrized case. A missing row is a gap.
3. **The real code is exercised.** The test must drive the production code, faking only the boundary (the network, the environment, the clock). A test that fakes the very thing under test, or asserts on its own fixture, verifies nothing.
4. **Assertions are specific.** `assert response` or `pytest.raises(Exception)` would pass for wrong behaviour; prefer exact values, exact types and `match=` on messages.
5. **The code really implements it.** Read the implementation for the clause. Note a passing test that only passes by coincidence (e.g. a hard-coded value that matches the fixture), and behaviour the Scenario asks for that the code doesn't have.
6. **Untagged coverage.** Search `tests/` for tests that check this criterion but aren't marked with it, so the table under-reports. Recommend the marker.
7. **Readable why.** Per the Code comments section of `CONTRIBUTING.md`: a test with non-obvious setup (a decoy value, an SDK quirk, a value picked to trigger one behaviour) should carry a one-line *why* comment, and tests carry no docstrings that repeat their name. This never changes the verdict; list it last in the recommendations.

Give each criterion one verdict:

| Verdict | Meaning |
|---|---|
| VERIFIED | Every clause and every Examples row has a specific assertion against the real code, and the tests pass |
| PARTIAL | Tests pass, but at least one clause or Examples row has no assertion |
| WEAK | Every clause is touched, but an assertion is too loose, or a test fakes what it should test |
| FAILING | A marked test fails |
| NOT TESTED | No test is marked with it |

Only VERIFIED means "done". A criterion the pytest table shows as PASS is often PARTIAL; say so plainly.

## Step 4: Report

Reply in chat with this shape (don't write a file unless the user asks):

```markdown
# QA report: <scope>, <date>

**Suite:** <N passed, M failed> · **Table:** <x PASS, y FAIL, z not tested>
**Review:** <a VERIFIED · b PARTIAL · c WEAK · d FAILING · e NOT TESTED>

| Criterion | Table | Verdict | Gap in one line |
|---|---|---|---|

## <AC-ID>: <scenario title>, <VERDICT>
| Clause | Checked by | |
|---|---|---|
| Then it fails with an auth error "..." | test_x (file:line), `pytest.raises(..., match=...)` | yes |
| And no request is sent | none | gap |
<one or two sentences on anything from checks 3–6>

## Recommendations
1. <most important first: failing tests, then code that doesn't do what a clause says, then missing assertions, then weak ones, then markers, then comments>
```

Each recommendation names the criterion and clause, the file to change, and what the test should set up and assert. Use links in the form [file.py:42](path/file.py#L42). Keep the per-criterion sections short for VERIFIED criteria (one line is enough) and spend the words on the gaps.

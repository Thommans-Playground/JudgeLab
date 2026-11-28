---
name: vbench-qa
description: QA review of one slice (task T-UUU-NN) or one acceptance criterion against its tests and code. Maps each criterion (Gherkin Scenario tagged @AC-UUU-NN) to the tests marked with it and reports clause by clause whether it is really verified, judges test quality (including mutation testing with mutmut), and exposes untested edge cases and unspecified behaviour, with prioritised recommendations. Invoked deliberately by the user as /vbench-qa <task or criterion>; never on the whole project at once.
disable-model-invocation: true
---

# vbench-qa

The pytest acceptance table (tests/conftest.py) says PASS when every test *marked* with a criterion passed. It cannot tell whether those tests check everything the criterion promises: one passing test that touches one clause turns the whole line green. This skill closes that gap with a human-style review in three parts: for each criterion, does every Then/And clause and every Examples row have an assertion behind it, against the real code? Would those tests actually catch a bug (test quality, mutation)? And which edge cases does nobody test, or has nobody even decided?

**This is a review, not a fix.** Never edit `src/`, `tests/` or `docs/` while running it. The user writes JudgeLab's code; the output is a report with recommendations. Describe a missing test by what it should set up and assert; write test code only if the user asks for it.

## Step 1: Scope

**One slice at a time, deliberately.** This skill runs only when the user invokes it, on a scope they name. It never reviews the whole project in one go: a big-bang review is slow (mutation testing in particular), produces more findings than anyone acts on, and mixes slices at different stages.

- **a task (`T-001-03`)**: the slice. Its criteria are the IDs under `## Delivers` in its task file. This is the normal scope, and the only one that gets the full review (Steps 3 to 5).
- **a criterion (`AC-001-08`)**: just that one, full review.
- **a use case (`UC-001`)**: a status summary only. Run Steps 2 and 3 for its criteria, skip mutation and edge cases, and end by naming the slice to review in depth next.
- **nothing, or several tasks or use cases**: don't run. Ask which one slice to review, suggesting the task currently in progress.

## Step 2: Gather evidence

Run these from the repo root, and keep their output for the report:

```bash
uv run pytest -q --color=no                                  # outcomes + acceptance table
python3 .claude/skills/vbench-qa/scripts/acmap.py --task T-001-03   # or --ac AC-001-08, or --uc UC-001
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
7. **Behaviour, not implementation.** Assertions check what the Scenario promises, not private attributes or internal call sequences that a harmless refactor would change.
8. **Negatives and boundaries.** Where a clause says "not" or "only" (e.g. "not the value of OPENAI_API_KEY"), a test proves the negative, not just the positive. Boundary values of each input are exercised.
9. **One behaviour per test, readable as the Scenario.** Arrange is the Given, Act is the When, the assertions are the Thens; the name says the intent. A test that checks several unrelated behaviours hides which one broke.
10. **Isolation and determinism.** No real network, no dependence on test order or the developer's shell environment (use `monkeypatch`), no uncontrolled clock or randomness.
11. **Readable why.** Per the Code comments section of `CONTRIBUTING.md`: a test with non-obvious setup (a decoy value, an SDK quirk, a value picked to trigger one behaviour) should carry a one-line *why* comment, and tests carry no docstrings that repeat their name. This never changes the verdict; list it last in the recommendations.

## Step 4: Mutation check

A test that touches a clause may still not *catch* a bug in it. Mutation testing breaks the code on purpose (flips a condition, changes a constant, drops a line) and checks that some test fails. Run it on the modules that implement the criteria in scope that have tests (`[tool.mutmut]` is configured in `pyproject.toml`):

```bash
uv run mutmut run "judgelab.connectors.credentials*"    # one module; quote the glob
uv run mutmut results                                   # survivors only
uv run mutmut show <mutant name>                        # the diff of one mutant
```

Read the results in context:
- **killed**: a test noticed. Good.
- **survived**: no test noticed. `show` the diff and decide which clause it breaks. A survivor in code that implements a tested criterion is a test gap; a survivor in code whose criterion has no tests yet is expected, so ignore it (don't report dozens of them).
- **segfault**, **timeout**, **suspicious**: inconclusive (mutmut's runner can crash on macOS). If it matters, check by hand: would the mutant make a marked test fail?
- A survivor that changes nothing observable (an equivalent mutant, e.g. a log message) is not a gap; say so in one line.

Mutation runs take time: run only the modules in scope, never the whole package for a single criterion. `mutants/` is mutmut's working copy and is gitignored.

## Step 5: Edge cases

For each criterion in scope, look for cases nobody tests, using standard test-design techniques:
- **Equivalence classes and boundaries** of every input (missing / empty / whitespace / normal / very long / unicode).
- **Every branch** of the implementing code: each `if`, `except` and early return should be reached by some test.
- **The external contract**: what the SDK or provider can actually send (non-JSON error bodies, missing headers, several choices, both content and refusal).
- **Error guessing**: `None`, trailing slashes, surrounding whitespace, duplicated or reordered input.

Sort every candidate into one of three kinds, because they go to different places:

| Kind | Meaning | Recommendation |
|---|---|---|
| **Untested edge case** | The Scenario covers it, but no test exercises it | A test or parametrize row, in `tests/` |
| **Unspecified behaviour** | The Scenario says nothing about it; nobody has decided what should happen | An Examples row or a new criterion first (vbench-docs), then a test. Never pick the expected behaviour yourself |
| **Suspected bug** | The code looks like it handles the case wrongly | A test that proves it, then a fix |

Rank by risk (how likely the case is in real use, and how bad if it goes wrong) and report at most about five per criterion, each with the technique that found it. A short, argued list gets acted on; a long one gets ignored.

## Step 6: Verdicts

Give each criterion one verdict:

| Verdict | Meaning |
|---|---|
| VERIFIED | Every clause and every Examples row has a specific assertion against the real code, the tests pass, and no mutant of the code implementing it survives |
| PARTIAL | Tests pass, but at least one clause or Examples row has no assertion |
| WEAK | Every clause is touched, but an assertion is too loose, a test fakes what it should test, a mutant of the clause's code survives, or a test depends on order or environment |
| FAILING | A marked test fails |
| NOT TESTED | No test is marked with it |

Only VERIFIED means "done". A criterion the pytest table shows as PASS is often PARTIAL; say so plainly. Edge cases and unspecified behaviour don't change a verdict (a criterion can be VERIFIED and still have open questions); they are reported separately.

## Step 7: Report

Reply in chat with this shape (don't write a file unless the user asks):

```markdown
# QA report: <scope>, <date>

**Suite:** <N passed, M failed> · **Table:** <x PASS, y FAIL, z not tested>
**Review:** <a VERIFIED · b PARTIAL · c WEAK · d FAILING · e NOT TESTED> · **Mutants:** <killed / survived in tested code>

| Criterion | Table | Verdict | Gap in one line |
|---|---|---|---|

## <AC-ID>: <scenario title>, <VERDICT>
| Clause | Checked by | |
|---|---|---|
| Then it fails with an auth error "..." | test_x (file:line), `pytest.raises(..., match=...)` | yes |
| And no request is sent | none | gap |
<one or two sentences on anything from checks 3–10, and surviving mutants with the clause each one breaks>

## Edge cases
| Criterion | Case | Kind | Found by | Risk |
|---|---|---|---|---|
| AC-001-02 | base_url with a trailing slash | unspecified behaviour | boundaries | medium |

## Recommendations
1. <most important first: failing tests, suspected bugs, code that doesn't do what a clause says, missing assertions, surviving mutants and weak tests, unspecified behaviour to decide, untested edge cases, markers, then comments>
```

Each recommendation names the criterion and clause, the file to change, and what the test should set up and assert. Use links in the form [file.py:42](path/file.py#L42). Keep the per-criterion sections short for VERIFIED criteria (one line is enough) and spend the words on the gaps.

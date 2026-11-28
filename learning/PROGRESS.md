# Learning progress

Where I am in the [codealongs](codealongs/README.md), what I've learned, and what's parked. Update it at the end of a session (or ask Claude to "update progress"). Two live sources sit next to it and are not copied here:

- **What works:** `uv run pytest -q` prints the acceptance table, grouped by use case.
- **What I understand:** [tutor-log.md](tutor-log.md), the Go/No-go results of `/vbench-tutor` sessions and their next review dates.

## Current position

**Chapter 2, section 2.13 Testing Successful Replies** is next. Sections 2.1–2.12 are done; all four construction tests pass.

## Chapters

| # | Chapter | Status | Notes |
|---|---|---|---|
| 1 | [Building an OpenAI Connector](codealongs/01-openai-connector.md) | Done | Notebook warm-up |
| 2 | [The Connector, Properly Built](codealongs/02-openai-connector-package.md) | In progress | 2.1–2.12 done, next 2.13 |
| 3 | [Abstracting the Connector](codealongs/03-abstracting-the-connector.md) | Not started | |
| 4 | [A Claude Connector](codealongs/04-claude-connector.md) | Not started | |
| 5 | [Connection Profiles and Switching Models](codealongs/05-connection-profiles.md) | Not started | |
| 6 | [Benchmark Datasets](codealongs/06-benchmark-datasets.md) | Not started | |
| 7 | [Running the Target Model](codealongs/07-running-the-target.md) | Not started | |
| 8 | [The LLM Judge](codealongs/08-the-llm-judge.md) | Not started | |
| 9 | [Scoring and the JSON Report](codealongs/09-scoring-and-reports.md) | Not started | |
| 10 | [Evaluating a Benchmark from the Command Line](codealongs/10-command-line.md) | Not started | |
| 11 | [The First Live Evaluation and the v0.1 Release](codealongs/11-live-evaluation-and-release.md) | Not started | |

## Parked

Things noticed but deliberately left for later.

- **`OPENAI_ORG_ID` and `OPENAI_PROJECT_ID` leak into requests** (found by vbench-qa, 2026-11-28). The SDK reads them when the connector doesn't pass `organization`/`project`, and passing `None` doesn't stop it. Decide whether to add them to AC-001-02's Examples and fix the connector.
- **Codealong 2 is partly out of date** since criteria moved to `.feature` files: 2.2 still says to write criteria into the README, 2.16's sample tables show the old format, and 2.19 ticks README checkboxes that no longer exist. Skip those steps.

## Journal

Newest first. What I did, what clicked, what was hard.

### 2026-11-28

- **Did:** 2.11 test helpers and all four 2.12 construction tests. Fixed `read_secret()`: `os.environ.get(name)` returns `None` for a missing variable, so `.strip()` crashed; `.get(name, "")` folds missing, empty and blank into one check.
- **Clicked:**
  - Fixtures are requested by argument name; a fixture can ask for another (`connect` asks for `monkeypatch`), and there's one `monkeypatch` per test, undone at the end.
  - `parametrize` = one test function, several runs; `pytest.raises(..., match=...)` passes only if that exception with that message is raised.
  - Bait testing: plant wrong values where the SDK would look, send one request, inspect it (`seen`) to prove the bait was ignored.
  - Test the exact right value, not just the absence of the wrong one.
- **Hard:** the 2.10 plugin internals (treated as a black box, on purpose) and the request plumbing in the bait test (where `stub.local` is set, the SDK appending `/chat/completions`). Moved on; expect it to click through repetition in 2.13–2.15.
- **Set up:** the acceptance table now reads the `.feature` files, in colour; code-comment rule (names say what, comments say why); `/vbench-qa` to review criteria clause by clause; `/vbench-tutor` for Go/No-go understanding checks.

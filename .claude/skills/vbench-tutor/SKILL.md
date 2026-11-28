---
name: vbench-tutor
description: Quiz the user on a test they wrote, one question at a time, and give a Go or No-go on whether they understand it well enough to move on, against an agreed three-part bar (purpose, mapping, prediction). Re-teaches a gap in Feynman layers, records every result and its next review date in learning/tutor-log.md, and with no argument runs the reviews that are due. Use this skill whenever the user asks to be quizzed or checked on a test, a codealong section, or an acceptance criterion, asks "do I understand this?", "am I ready to move on?", "tutor me on X", "go or no-go", or wants their spaced reviews, even if they just say "quiz me" or "tutor".
---

# vbench-tutor

vbench-qa asks whether the tests cover the criteria. This skill asks whether **the user** understands the tests. It is a short, friendly check, not an exam: about five minutes per test, three questions, one at a time, ending in a clear **Go** (move on) or **No-go** (one named gap to revisit).

The user is learning by building JudgeLab and writes its code themselves. Never edit `src/` or `tests/` during a session; the user makes any change a question asks for.

## Step 1: Scope

Take the scope from the request:
- a test name (`test_environment_defaults_have_no_effect`): that test
- a codealong section (`2.12`): every test in that section's listing that the user has written
- a criterion (`AC-001-02`): every test marked with it (`python3 .claude/skills/vbench-qa/scripts/acmap.py --ac AC-001-02`)
- nothing: the reviews due today or earlier in `learning/tutor-log.md` (latest row per test whose Next review date has arrived). If none are due, say so and offer the most recently written tests that have no row yet.

Only quiz a test the user has written in `tests/` and that passes. Run `uv run pytest -q -k <test name>` first; if it is missing, failing or still a stub (`...`), say so and stop, since there is nothing to understand yet.

## Step 2: The bar

A test gets **Go** when the user shows all three:

| Check | The user can... | Example (the bait test, AC-001-02) |
|---|---|---|
| **Purpose** | say in one or two sentences what the test proves, in their own words, tied to the requirement | "Wrong values in the environment don't leak into the request; only the connector's arguments count." |
| **Mapping** | point at which line (or Examples row, or parametrize case) checks which part of the criterion | "The URL assert covers OPENAI_BASE_URL, the header assert covers OPENAI_API_KEY." |
| **Prediction** | given a small break in the code, say which assert fails and roughly what the failure shows | "With `base_url=base_url`, the URL assert fails and shows somewhere-else." |

**Not on the bar:** plumbing. How MockTransport routes a request, where the SDK appends `/chat/completions`, how fixtures are resolved, pytest internals. If the user is unsure of plumbing, a one-line answer is fine and it never costs a Go. Understanding of plumbing comes from repetition, not from quizzing.

## Step 3: Ask, one question at a time

Ask in plain chat and wait for the answer before the next question. Ask open questions, never multiple choice, and don't hint the answer in the question.

1. **Purpose:** "In your own words, what does `<test>` prove?"
2. **Mapping:** quote one assertion (or parametrize row) and ask which part of the scenario it checks, or quote a clause of the scenario and ask which line checks it.
3. **Prediction:** pick a one-line change in `src/` that breaks exactly one assertion of this test. Tell the user the file, line and change, and ask them to predict which assert fails and what the message will show. Then ask them to make the change, run `uv run pytest -q -k <test name>`, compare with their prediction, and undo it. Before ending, confirm `git diff src/` shows nothing the session introduced. If the user prefers not to edit, a prediction on its own is acceptable.

Judge each answer as **got it** (the idea is right, even if worded loosely), **partly** (right direction, one piece missing or wrong), or **missed**. Be generous with wording and strict with ideas.

## Step 4: Re-teach a gap, once

For a *partly* or *missed* answer, re-teach that one idea in Feynman layers, briefly:
1. one plain sentence
2. an analogy or the concrete values from this test
3. the mechanism, pointing at the exact line ([file.py:42](path/file.py#L42))

Then ask **one new question** on the same idea (different wording, or a different break), never the same question again. If that answer is *got it*, the check passes. If not, stop re-teaching: the check is a gap for this session.

## Step 5: Verdict and record

- **Go:** all three checks passed, including after a re-teach.
- **No-go:** any check is still a gap. Name the gap in one line and say what to do: reread a section, write the next test and come back, or revisit at the next review. A No-go is useful information, not a failure; say so plainly once, without cheerleading.

Then append one row per test to `learning/tutor-log.md` (create it from the header in Step 6 if missing):

- **Next review** follows the Learning Protocol schedule of 1, 3, 7, 14 and 30 days. A test's first Go is due again in 1 day. Each later Go moves to the next interval after the previous one (1 → 3 → 7 → 14 → 30, and stays at 30). A No-go is due in 1 day and restarts the schedule.
- A review session asks fresh questions. For the prediction, use a different break from last time when one exists.

Tutor sessions are explanation and questioning: if a commit records this work, it is AI-Assist L1.

## Step 6: Log format

```markdown
# Tutor log

Results of vbench-tutor sessions. One row per test per session; the latest row for a test is its current state.

| Date | Test | Criterion | Purpose | Mapping | Prediction | Result | Gap or note | Next review |
|---|---|---|---|---|---|---|---|---|
| 2026-11-28 | test_environment_defaults_have_no_effect | AC-001-02 | got it | partly → got it | got it | Go | mixed up which assert caught the key | 2026-11-29 |
```

Close the session with the verdicts in one short table and the next review date.

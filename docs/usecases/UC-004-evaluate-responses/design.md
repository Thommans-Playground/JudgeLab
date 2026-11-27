# UC-004 Design: Evaluate responses

> **Draft for review.** Design says *how* the code realises the [analysis](analysis.md): real classes, signatures, patterns and where they sit in the [hexagonal architecture](../../design.md). It describes the reference solution the codealongs build.

| Field | Value |
|---|---|
| Use case | [UC-004](README.md) |
| Slices | [T-004-01](T-004-01-judge-request-builder.md) (judge request builder), [T-004-02](T-004-02-verdict-parser.md) (verdict parser) |
| Code | `judgelab.judge`, called from `judgelab.runner` |
| Decisions | [ADR-001](../../decisions/ADR-001.md) (hexagonal), [ADR-002](../../decisions/ADR-002.md) (diagrams, as-built check) |

## 1. From analysis to design

| Analysis class | Design element | Hexagon role |
|---|---|---|
| Judge Model Interface (boundary) | `ModelConnector` port; adapters `OpenAIConnector`, `AnthropicConnector`, `FakeConnector` | Driven port + adapters |
| Evaluate Response (control) | `Judge.evaluate()` | Domain service (core) |
| Test Case (entity) | `benchmark.TestCase` | Core (Benchmark context) |
| Actual Answer (entity) | the target's `ModelResponse` text, or `"[refused] <refusal>"` | Port type |
| Rubric (entity) | `judge.Rubric`, looked up by `get_rubric(id)` | Core |
| Judge Request (entity) | the prompt from `build_judge_prompt()`, plus `Judge.instructions` | Core (transient, no class) |
| Judge Evaluation (entity) | `judge.JudgeEvaluation` | Core value object |
| Verdict (entity) | `judge.Verdict` (enum) | Core value object |

The Judge Request has no class of its own. It's two strings, the instructions and the prompt, that exist only for one call. Giving it a class would add a name without adding a rule.

## 2. Design classes

Diagram: [UC-004 design classes](diagrams/design-classes.puml)

## 3. Design sequences

**Main success scenario.** One answer, judged PASS:

Diagram: [UC-004 design sequence](diagrams/design-sequence.puml)

**Extensions 2a, 3a and 4a.** No trustworthy verdict. Every path ends in a `JudgeError`, which the runner records as ERROR with `error_stage="judge"`:

Diagram: [UC-004 design sequence, error paths](diagrams/design-sequence-error.puml)

## 4. Patterns and principles

| Pattern / principle | Where | Why |
|---|---|---|
| Ports and adapters | `Judge` depends on the `ModelConnector` port, never on an SDK | The judge can be any provider; tests use `FakeConnector` (AC-004-05, REQ-012) |
| Strategy (as data) | `Rubric` passed to `Judge` | A new rubric is a new value, not a new class (AC-004-07) |
| Dependency injection | `Judge(connector, rubric)` | The caller decides which judge to use; `Judge` creates nothing |
| Value objects | `Rubric`, `JudgeEvaluation`, `Verdict` are immutable | A verdict, once recorded, can't change |
| Fail closed | every unusable reply raises `JudgeError` | ERROR, never a silent FAIL (AC-004-03) |
| Exception chaining | `raise JudgeError(...) from e` | The runner can see the connector error behind a judge failure and stop on auth or quota |

## 5. Rules from the analysis, and where the design keeps them

| Rule | Kept by |
|---|---|
| Untrusted judgement is ERROR | `Judge.evaluate` raises `JudgeError` for a call failure, refusal, truncation or parse failure; `runner._judge` turns that into `Outcome.ERROR` |
| The answer is data | `build_judge_prompt` puts each part in its own tag; the rubric's instructions say tags hold data |
| Judge identity recorded | `JudgeEvaluation.response` holds the judge's `ModelResponse` (requested and served model) |
| Switching judge is configuration | `Judge` sees only `ModelConnector`; the CLI builds the connector from the profile |

## 6. Design notes and candidate refactorings

- `parse_verdict` and `build_judge_prompt` are module functions, not methods. They are pure, which makes them easy to test on their own (T-004-02), and `Judge` composes them.
- The stop-judging policy (after an auth or quota error) lives in `runner`, not in `Judge`. It's a rule about the whole run, so it belongs to the run. An `EvaluationRun` aggregate would be its natural home (see [Evaluation](../../domain/evaluation/README.md)).

## 7. Checking the design against the code (as-built)

Generate the as-built sequence from a test that exercises this design, and compare it with section 3:

```bash
uv run python .claude/skills/vbench-docs/scripts/asbuilt.py sequence \
  "tests/test_judge.py::<test name>" -o docs/usecases/UC-004-evaluate-responses/diagrams/as-built/sequence.puml
```

A difference is either design drift (update this page and say why) or a code bug (fix the code). See [ADR-002](../../decisions/ADR-002.md).

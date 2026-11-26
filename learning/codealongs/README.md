# Codealongs: Building JudgeLab v0.1

A step-by-step course that builds the whole v0.1 release: a command-line tool that runs a benchmark against a target model, has a second model judge every answer, and writes a reviewable JSON report.

Type the code yourself: these are guided codealongs, so record the work as **AI-Assist L4**. Each chapter starts by writing its acceptance criteria into the task files, and `uv run pytest` prints a table showing which ones pass, so you always know where you are.

| # | Chapter | Tasks | You end up with |
|---|---|---|---|
| 1 | [Building an OpenAI Connector](01-openai-connector.md) | T003 | A working connector in a notebook |
| 2 | [The Connector, Properly Built](02-openai-connector-package.md) | T003, T002 | A tested `judgelab.connectors` package and the acceptance-criteria progress table |
| 3 | [Abstracting the Connector](03-abstracting-the-connector.md) | T003 | The `ModelConnector` port, `FakeConnector` and contract tests |
| 4 | [A Claude Connector](04-claude-connector.md) | T014 | A second provider behind the same port |
| 5 | [Connection Profiles and Switching Models](05-connection-profiles.md) | T001, T002, T004 | Validated profiles and a registry that picks the connector |
| 6 | [Benchmark Datasets](06-benchmark-datasets.md) | T005, T006 | A JSON benchmark loader that reports every problem at once |
| 7 | [Running the Target Model](07-running-the-target.md) | T007 | A runner that knows when to stop |
| 8 | [The LLM Judge](08-the-llm-judge.md) | T008, T009 | Rubric, judge prompt and a strict verdict parser |
| 9 | [Scoring and the JSON Report](09-scoring-and-reports.md) | T010, T011, T012 | PASS / FAIL / ERROR outcomes, a transparent summary and the report |
| 10 | [The Command Line](10-command-line.md) | T012 | `judgelab run --config configs/evaluation.yaml` |
| 11 | [The First Live Evaluation and the v0.1 Release](11-live-evaluation-and-release.md) | T013 | A live run, a human review, and the `v0.1.0` tag |

**Stuck, or want to compare?** A reference solution exists on the local branch `reference/v0.1-solution`, one commit per chapter. To see exactly what a chapter adds without switching branches, run `git log --oneline reference/v0.1-solution`, then `git show <commit>` for the chapter you want. Try the chapter on your own first.

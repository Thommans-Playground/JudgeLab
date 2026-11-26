---
name: vbench-sources
description: The reference systems and documentation JudgeLab is studied against — IMDA/AI Verify Project Moonshot (library, moonshot-data, docs), Moonshot CI/CD (now the AI Verify Evals Toolkit), the IMDA Starter Kit for testing LLM applications, GovTech Singapore's Litmus (safety testing as a service) and Sentinel (guardrails as a service), the GovTech Responsible AI Playbook, and related GovTech open-source evals. Use this skill whenever designing, comparing, naming, or researching any JudgeLab capability (benchmarking, connectors, datasets, metrics, LLM-as-a-judge, orchestration, CI/CD testing, guardrails, red teaming, reporting), writing an ADR's alternatives, or when the user asks "how does Moonshot / Litmus / Sentinel do X", "what's the reference for this", or wants study material for a roadmap phase, even if they don't name the sources.
---

# vbench-sources

JudgeLab is a learning project that rebuilds an AI assurance framework from first principles, using a small set of real systems as reference points. This skill tells you what each source is, which JudgeLab phase it informs, and how to use it without undermining the learning goal.

The same list, for humans, is in the **Sources and References** section of the repository `README.md`. Keep the two in sync when a source is added, renamed, or retired.

## The sources

### Primary

| Source | What it is | Open source? | Links |
|---|---|---|---|
| **Project Moonshot** (AI Verify Foundation / IMDA) | Modular Python toolkit to benchmark and red-team LLM applications: connectors to model endpoints, datasets, metrics, prompt templates, recipes and cookbooks, runners, and red-teaming attack modules and context strategies. CLI, web API, and UI. | Yes, Apache-2.0 | [repo](https://github.com/aiverify-foundation/moonshot) · [docs](https://aiverify-foundation.github.io/moonshot/) · [PyPI](https://pypi.org/project/aiverify-moonshot/) |
| **moonshot-data** | The test assets Moonshot runs: connectors, datasets, metrics, attack modules. Best place to see concrete dataset formats and metric implementations. | Yes, Apache-2.0 | [repo](https://github.com/aiverify-foundation/moonshot-data) |
| **Moonshot CI/CD → AI Verify Evals Toolkit** | `moonshot-cicd` was renamed `aiverify-evals-toolkit` (the old URL redirects). It holds three products on one engine: the Evals Toolkit (guided benchmark runs, human review and override of automated verdicts, confidence intervals), **Moonshot CI/CD** (CLI that runs benchmark and red-team suites as a pipeline step and gates merges; GitHub Actions example), and Process Checks (maps evidence to governance principles). | Yes, Apache-2.0 | [repo](https://github.com/aiverify-foundation/aiverify-evals-toolkit) · [wiki](https://github.com/aiverify-foundation/aiverify-evals-toolkit/wiki) |
| **Litmus** (GovTech Singapore, AI Guardian) | Testing-as-a-service: register an application endpoint, choose curated safety and security suites, Litmus sends adversarial prompts, scores responses automatically, and reports. Runs on demand, on a schedule, or from CI/CD; compares results across runs. | **No**: a government service; only documentation is public | [Playbook page](https://govtech-responsibleai.github.io/playbook/tools/litmus/) · [product page](https://www.developer.tech.gov.sg/products/categories/cybersecurity/litmus) · [roadmap](https://www.developer.tech.gov.sg/products/categories/cybersecurity/litmus/features-roadmap) |
| **Sentinel** (GovTech Singapore, AI Guardian) | Guardrails-as-a-service: screens input before the model and output before the user against selected guardrails (toxicity, prompt injection/jailbreak, PII, off-topic, hallucination, …) and returns a score per guardrail; the calling system decides whether to block, redact, log, or escalate. Closed beta for Singapore public officers. | **No**: documentation only | [Playbook page](https://govtech-responsibleai.github.io/playbook/tools/sentinel/) · [product page](https://www.developer.tech.gov.sg/products/categories/cybersecurity/sentinel) · [roadmap](https://www.developer.tech.gov.sg/products/categories/cybersecurity/sentinel/features-roadmap) |

### Supporting

| Source | Why it's useful | Links |
|---|---|---|
| **IMDA Starter Kit for Testing LLM-Based Applications for Safety and Reliability** | The testing methodology behind the tools: what to benchmark, when to red-team, how to report. | [PDF](https://www.imda.gov.sg/-/media/imda/files/about/emerging-tech-and-research/artificial-intelligence/starter-kit-for-testing-llm-based-applications-for-safety-and-reliability.pdf) |
| **GovTech Responsible AI Playbook** | Practical guidance on evaluating AI systems and on guardrail architecture, selection, production integration, and threshold tuning. Hosts the Litmus and Sentinel pages. | [site](https://govtech-responsibleai.github.io/playbook/) · [evaluating AI systems](https://govtech-responsibleai.github.io/playbook/evaluating-ai-systems/) · [guardrail architecture](https://govtech-responsibleai.github.io/playbook/improving-ai-systems/guardrails/guardrail-architecture/) · [source](https://github.com/govtech-responsibleai/playbook) |
| **meta-evaluator** (GovTech, MIT) | Measures how well an LLM judge agrees with human labels: the reference for judge calibration. | [repo](https://github.com/govtech-responsibleai/meta-evaluator) · [Playbook page](https://govtech-responsibleai.github.io/playbook/tools/metaevaluator/) |
| **Kaleidoscope** (GovTech, MIT) | Automated, application-specific evals; the contextual evaluation module within Litmus. | [repo](https://github.com/govtech-responsibleai/kaleidoscope) |
| **RabakBench** (GovTech) | Benchmark for LLM guardrails across safety risks relevant to Singapore. No licence is published, so treat it as read-only reference. | [repo](https://github.com/govtech-responsibleai/RabakBench) |

## Which source for which phase

| JudgeLab phase | Look at |
|---|---|
| 1. Benchmarking engine | Moonshot datasets, metrics, recipes/cookbooks, runners; moonshot-data formats; Starter Kit (benchmarking) |
| 2. Modular judges and connectors | Moonshot connectors and connector endpoint configuration; how moonshot-data packages connectors |
| 3. LLM-as-a-Judge | moonshot-data's LLM "annotator" metrics (e.g. `metrics/gpt4annotator.py`, `metrics/llamaguardannotator.py`); meta-evaluator (judge–human agreement); Evals Toolkit human override of verdicts and confidence intervals |
| 4. Evaluation orchestration | Moonshot `runners/`, `runs/`, and `results/` modules; Litmus parallel execution and reports |
| 5. Continuous testing and CI/CD | Moonshot CI/CD (pipeline step, merge gating, GitHub Actions example); Litmus CI/CD triggers and trend comparison |
| 6. Runtime guardrails | Sentinel (input/output guardrails, per-guardrail scores, caller-owned thresholds); Playbook guardrail architecture and production integration; RabakBench; moonshot-data's `metrics/lionguardclassifier.py` |
| 7–8. Red teaming, iterative red teaming | Moonshot attack modules, context strategies, automated red-teaming agents; Starter Kit (red teaming) |
| 9. Assurance platform | Evals Toolkit (review dashboard, reports), Process Checks, Litmus reporting; Kaleidoscope |

## How to use the sources

1. **Read the live source before describing it.** These projects change: `moonshot-cicd` was renamed, Sentinel is in beta, Litmus features sit on a roadmap. Fetch the current page, or the repo file via `gh api` or the raw URL, and cite what you read. If you are working from memory, say so.
2. **Separate documented behaviour from implementation.** Litmus and Sentinel have no public code. Describe them only from their documentation, and never invent internals.
3. **Use them to understand designs, not to supply code.** JudgeLab's goal is independent implementation (see the README's Learning Protocol). Use the references to compare designs, choose names, find edge cases, and fill ADR "Alternatives considered" sections. Don't paste their code into `src/`. If the user explicitly wants to adapt something (an L4 reference solution), attribute it with a link to the file and commit, respect the licence (Apache-2.0 and MIT need the notice kept; anything without a licence can't be copied), and record the AI-Assist level.
4. **Contrast, don't conform.** JudgeLab deliberately does some things differently (its config is its own, not a Moonshot schema). When comparing, state the trade-off, so the choice is a decision rather than an imitation.
5. **Leave a trail.** When a source informs a design choice, link it from the relevant ADR (`docs/decisions/`), design section, or task file (`vbench-docs` skill), using a commit-pinned GitHub link for code (`/blob/<sha>/path`) so the reference doesn't drift.
6. **Prefer primary over secondary.** Use the repos, official docs, the Starter Kit, and the Playbook over press articles and third-party catalogues.

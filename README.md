# JudgeLab

**A hands-on engineering laboratory for building a modular AI assurance framework from first principles.**

JudgeLab is a learning-driven side project inspired by [IMDA Project Moonshot](https://github.com/aiverify-foundation/moonshot), [Moonshot CI/CD](https://github.com/aiverify-foundation/aiverify-evals-toolkit), and GovTech's [Litmus](https://govtech-responsibleai.github.io/playbook/tools/litmus/) and [Sentinel](https://govtech-responsibleai.github.io/playbook/tools/sentinel/). See [Sources and References](#sources-and-references).

The goal is to develop strong **software engineering, hands-on coding, data structures and algorithms (DSA), design patterns, and systems engineering skills** by progressively implementing a working AI assurance platform.

## Objectives

1. **Hands-on Engineering** — Build every core component independently, minimizing AI-generated code.
2. **Engineering Process** — Practice requirements engineering, domain modeling, design, implementation, testing, and verification.
3. **DSA Mastery** — Learn relevant algorithms and data structures, apply them to real features, and reinforce them through spaced repetition and interview problems.
4. **Design Patterns** — Learn Gang of Four (GoF) patterns through practical refactoring, understanding when and why to use them.
5. **AI Assurance** — Develop practical expertise in benchmarking, LLM-as-a-judge, red teaming, guardrails, and continuous evaluation.

## Project Roadmap

| Phase | Capability | Engineering Focus |
|---|---|---|
| 1 | Benchmarking engine | Python, collections, testing |
| 2 | Modular judges and connectors | Interfaces, Strategy, Adapter |
| 3 | LLM-as-a-Judge | APIs, async, structured outputs |
| 4 | Evaluation orchestration | Queues, concurrency, persistence |
| 5 | Continuous testing and CI/CD | Automation, reproducibility, regression testing |
| 6 | Runtime guardrails | Policy engines, Chain of Responsibility |
| 7 | Red teaming | Adversarial testing, coverage, search |
| 8 | Iterative red teaming | Feedback loops, optimization, graph traversal |
| 9 | Assurance platform | APIs, frontend, observability, reporting |

The roadmap is incremental and proficiency-driven, not deadline-driven.

## Engineering Methodology

Each feature follows a lightweight, risk-appropriate engineering lifecycle:

**Requirements → Use Cases → Domain Model → Design → Implementation → Verification → Reflection**

Each implementation should capture:

- Requirements and acceptance criteria.
- Design decisions and alternatives.
- Implementation and test evidence.
- Relevant DSA concepts and GoF patterns.
- Mistakes, debugging experience, and lessons learned.
- AI assistance level and independent coding progress.

Prefer a **modular monolith, domain-driven design, and hexagonal architecture** where justified. Avoid premature abstraction and unnecessary infrastructure.

## Learning Protocol

**Implement first. Understand deeply. Repeat deliberately.**

- **L0:** Independent implementation without AI.
- **L1–L2:** Conceptual explanations and progressive hints.
- **L3:** AI-assisted code review and debugging guidance.
- **L4:** Reference solutions after independent attempts.
- **L5:** Generated code only for non-learning-critical scaffolding.

### DSA and Design Pattern Practice

Every newly introduced concept follows:

**Learn → Implement → Apply → Practice → Review → Reimplement**

DSA concepts are reinforced through related engineering exercises and unfamiliar interview problems.

GoF patterns are introduced when a real design problem emerges, then practiced through implementation, refactoring, and comparison with simpler alternatives.

Reviews are scheduled approximately **1, 3, 7, 14, and 30 days** after introduction, adjusted according to retention.

## Repository Structure

```text
judgelab/
├── src/judgelab/       # Application implementation
├── tests/              # Automated verification
├── benchmarks/         # Evaluation datasets and suites
├── docs/
│   ├── architecture/   # Domain models and design decisions
│   ├── features/       # Requirements and codealongs
│   └── execution-logs/ # Implementation evidence
├── learning/
│   ├── dsa/            # Exercises and repetition records
│   ├── patterns/       # GoF implementations and reflections
│   └── reviews/        # Learning assessments
└── README.md
```

## Definition of Done

A feature is complete when:

- Its acceptance criteria are satisfied.
- Implementation and automated tests pass.
- Important design decisions are documented.
- Relevant concepts and learning outcomes are recorded.
- The implementation can be explained and reproduced independently.

**Feature completion does not imply concept mastery.** Mastery is tracked separately through repeated independent implementation and problem-solving.

## Success Criteria

JudgeLab measures progress across two independent dimensions:

**Product progress:** Working capabilities, correctness, extensibility, reliability, and verification evidence.

**Engineering proficiency:** Independent coding fluency, DSA problem-solving, pattern recognition, debugging, technical reasoning, and long-term retention.

## Guiding Principles

> Build before abstracting. Understand before generating. Verify before trusting. Repeat until independent.

**The primary deliverable is not the framework itself, but the engineering capability developed while building it.**

## Sources and References

JudgeLab studies these systems as reference points: to compare designs, check edge cases, and inform decisions. It does not copy them. Where one shapes a design choice, the relevant ADR links to it.

### Primary sources

| Source | Owner | What it covers | Links |
|---|---|---|---|
| Project Moonshot | AI Verify Foundation / IMDA | LLM benchmarking and red teaming toolkit: connectors, datasets, metrics, recipes, cookbooks, attack modules (Apache-2.0) | [Repository](https://github.com/aiverify-foundation/moonshot) · [Documentation](https://aiverify-foundation.github.io/moonshot/) · [PyPI](https://pypi.org/project/aiverify-moonshot/) |
| moonshot-data | AI Verify Foundation / IMDA | Test assets for Moonshot: connectors, datasets, metrics (Apache-2.0) | [Repository](https://github.com/aiverify-foundation/moonshot-data) |
| Moonshot CI/CD (AI Verify Evals Toolkit) | AI Verify Foundation / IMDA | Benchmark and red-team suites as a CI/CD step, human review of verdicts, governance evidence. Formerly `moonshot-cicd` (Apache-2.0) | [Repository](https://github.com/aiverify-foundation/aiverify-evals-toolkit) · [Wiki](https://github.com/aiverify-foundation/aiverify-evals-toolkit/wiki) |
| Litmus | GovTech Singapore (AI Guardian) | Safety and security testing as a service, on demand or from CI/CD. Not open source | [Playbook](https://govtech-responsibleai.github.io/playbook/tools/litmus/) · [Product page](https://www.developer.tech.gov.sg/products/categories/cybersecurity/litmus) |
| Sentinel | GovTech Singapore (AI Guardian) | Runtime input/output guardrails as a service. Not open source, closed beta | [Playbook](https://govtech-responsibleai.github.io/playbook/tools/sentinel/) · [Product page](https://www.developer.tech.gov.sg/products/categories/cybersecurity/sentinel) |

### Supporting references

| Source | What it covers | Link |
|---|---|---|
| IMDA Starter Kit for Testing LLM-Based Applications for Safety and Reliability | Testing methodology for benchmarking and red teaming | [PDF](https://www.imda.gov.sg/-/media/imda/files/about/emerging-tech-and-research/artificial-intelligence/starter-kit-for-testing-llm-based-applications-for-safety-and-reliability.pdf) |
| GovTech Responsible AI Playbook | Evaluating AI systems, guardrail architecture and production integration | [Site](https://govtech-responsibleai.github.io/playbook/) |
| meta-evaluator (GovTech) | Measuring LLM-judge agreement with human labels (MIT) | [Repository](https://github.com/govtech-responsibleai/meta-evaluator) |
| Kaleidoscope (GovTech) | Automated, application-specific evals; Litmus's contextual evaluation module (MIT) | [Repository](https://github.com/govtech-responsibleai/kaleidoscope) |
| RabakBench (GovTech) | Guardrail benchmark for Singapore-relevant safety risks | [Repository](https://github.com/govtech-responsibleai/RabakBench) |

The `vbench-sources` Claude Code skill maps each source to the roadmap phase it informs and sets out how to use it without undermining independent implementation.


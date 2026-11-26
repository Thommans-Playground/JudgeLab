# JudgeLab

**A hands-on engineering laboratory for building a modular AI assurance framework from first principles.**

JudgeLab is a learning-driven side project inspired by [IMDA Project Moonshot](https://github.com/aiverify-foundation/moonshot), [Moonshot CI/CD](https://github.com/aiverify-foundation/moonshot-cicd), and GovTech's Litmus and Sentinel.

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
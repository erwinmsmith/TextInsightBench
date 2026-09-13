# TextInsightBench — Evaluation Assets

**English** | [简体中文](README.zh-CN.md)

Public evaluation documentation for **{{TASKS}} open-discovery tasks**. Use this alongside the [participant corpus](https://huggingface.co/datasets/CodeSoulco/TextInsightBench) and [benchmark runner](https://github.com/erwinmsmith/TextInsightBench).

## Contents and reference status

- `docs/SCORING.md`: formula, evidence gates and aggregation.
- `docs/USAGE.md`: installation, execution, judging and reports.
- `references.json`: {{TASKS}} reference-availability records bound to the task hash.
- `protocol.json`, `release.json`, `manifest.json`: protocol, counts and checksums.
- `docs/RESULTS.md` and `results/agent-runs.json`: development experiment results.

**There are no fixed reference conclusions.** Each reference record has `reference_id: null`; these records are not annotated answers. Findings are evaluated against original corpus evidence and the public rubric, not exact answer matching. Reference coverage is unavailable.

## Use

```bash
# After installing the code repository:
tib download --organizer --output data/evaluation
```

These assets are optional for current discovery scoring. The standard workflow is to run an agent on participant data, use `tib judge` for sampled semantic review, and use `tib evaluate` to generate JSON and Markdown reports. [Complete commands](docs/USAGE.md) · [中文使用指南](docs/USAGE.zh-CN.md).

Local checks verify complete assignment partitions, exact quotations and statistics. A claim-blind check of sampled original documents constrains narrative scoring. Semantic judgment is fallible, makes paid model requests and does not certify full-corpus labels. Report quality together with scored coverage, unresolved evidence, invalid submissions, missing outputs and abstentions.

Three open-source agents completed 150 development runs, yielding 70 numerical scores. These mixed-configuration experiments are not a controlled leaderboard. [Results](docs/RESULTS.md).

All repositories are public; commit hashes identify exact snapshots. Public evaluation access must be kept outside the solver environment for enforceable comparisons. [Operations](docs/ORGANIZER.md) · [Source terms](SOURCES.md).

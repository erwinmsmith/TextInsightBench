# TextInsightBench

**English** | [简体中文](README.zh-CN.md)

A natural-language data-mining benchmark for agents: **{{TASKS}} tasks**, **{{TASK_DOCUMENTS}} task documents** and **{{LEARNING_DOCUMENTS}} unlabeled learning documents**.

Each task provides 5,000 or 10,000 texts and a research objective. Agents choose the patterns, populations and comparisons to investigate, then submit up to three findings with complete document assignments, exact quotations, statistics, counterexamples and limitations. Any analysis method is allowed.

## Contents

| Path | Purpose |
|---|---|
| `tasks.json` | Questions and task-specific constraints |
| `corpora/*.jsonl.gz` | Full text for each task |
| `learning/*/*.parquet` | Optional unlabeled learning pool |
| `output.schema.json` | Submission structure |
| `protocol.json`, `release.json` | Evaluation protocol and data counts |
| `manifest.json` | File hashes and sizes |
| `results/agent-runs.json` | Development experiment summary; not a leaderboard |

Sources: Amazon Beauty, Android App Reviews, CFPB and NHTSA. The task inventory contains 20 group differences, 15 temporal changes and 15 compound associations. See [data composition and fields](docs/DATA.md).

## Use the benchmark

```bash
git clone https://github.com/erwinmsmith/TextInsightBench.git
cd TextInsightBench
python -m venv .venv
source .venv/bin/activate
pip install -e .
tib download --output data/participant
tib verify --data data/participant
```

The code pins dataset commits in `benchmark/data.lock.json`. Add `--with-learning` when downloading for pool-assisted learning. Learning configurations also work with `datasets.load_dataset`; task corpora are accessed through the runner or as gzip JSONL.

[Connect an agent and score results](docs/USAGE.md) · [中文使用指南](docs/USAGE.zh-CN.md) · [Code](https://github.com/erwinmsmith/TextInsightBench) · [Evaluation assets](https://huggingface.co/datasets/CodeSoulco/TextInsightBench-Evaluation)

## Evaluation and results

Full assignment partitions, quotations and arithmetic are checked locally. Sampled claim-blind document checks cap subsequent finding-quality grades. Semantic review incurs model charges and is not exhaustive or independent ground truth. The tasks have no fixed reference conclusions; quality is judged against corpus evidence and the public rubric. [Scoring](docs/SCORING.md).

The development experiment finished 150 runs across three open-source agents: 86 valid submissions, 70 numerical scores, 16 evidence-unresolved and 64 without valid submissions. Configurations changed during development; this is not a controlled leaderboard. [Results and limitations](docs/RESULTS.md).

Task and learning document IDs are disjoint, but the data was previously public, entities and sources can overlap, and tasks are not statistically independent. Narratives are unverified author reports and may contain personal information. Upstream terms differ; the compilation grants no new rights over third-party text. See [source terms](SOURCES.md).

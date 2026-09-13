# TextInsightBench

**English** | [简体中文](README.zh-CN.md)

A natural-language data-mining benchmark for agents. Explore a corpus, discover a substantive pattern, quantify it, and test whether the evidence supports the conclusion. Any analysis method is allowed.

**50 tasks · 435,000 task documents · 944,468 unlabeled learning documents**

Each task provides 5,000 or 10,000 texts and a research objective—not the pattern to find. Agents choose their analytical conditions, populations and comparisons, then submit up to three nonredundant findings with document assignments, quotations, statistics, counterexamples and limitations.

## Start here

| Resource | Contents |
|---|---|
| [Participant data](https://huggingface.co/datasets/CodeSoulco/TextInsightBench) | Task questions, task corpora, optional unlabeled learning pool and output schema |
| [Evaluation assets](https://huggingface.co/datasets/CodeSoulco/TextInsightBench-Evaluation) | Public scoring documentation and reference-availability records |
| [Usage guide](docs/USAGE.md) | Download, connect an agent, resume runs and generate reports |
| [Experimental results](docs/RESULTS.md) | Three open-source agents across all 50 tasks, with coverage and limitations |

All repositories are public. Save the code commit and the dataset commits in [data.lock.json](benchmark/data.lock.json) to identify an exact snapshot.

## Quick start

Python 3.10 or newer:

```bash
git clone https://github.com/erwinmsmith/TextInsightBench.git
cd TextInsightBench
python -m venv .venv
source .venv/bin/activate
pip install -e .

# Downloads all task corpora. No account or model key is required.
tib download --output data/participant
tib verify --data data/participant

# Interface test: abstains on all 50 tasks, with no model requests.
tib run --data data/participant --command 'python examples/abstain_agent.py' \
  --output runs/smoke/submissions
tib evaluate --data data/participant --submissions runs/smoke/submissions \
  --output runs/smoke/report.json
```

This smoke test checks the interface, not mining ability. The report contains 50 abstentions and no quality score.

## Run your agent

The runner starts a fresh process for each task. It sends one JSON object through stdin with the full task, an absolute gzip-JSONL corpus path and an optional learning directory. Return one submission JSON object on stdout; send logs to stderr. Your agent controls how it explores and models the corpus.

```bash
tib run --data data/participant --command 'python my_agent.py' \
  --timeout 3600 --output runs/my-agent/submissions
```

Choose either `task_only` (default) or `unlabeled_pool`. For the latter, download with `--with-learning` and run with `--track unlabeled_pool`. Freeze global prompts, learned parameters and thresholds before evaluation. Corpus-local exploration is allowed; transferring evaluation feedback between tasks is not.

See the [usage guide](docs/USAGE.md), [agent interface](docs/AGENT_PROTOCOL.md) and [submission contract](docs/SUBMISSIONS.md). The runner is **not a security sandbox**.

## Score submissions

Configure a JSON-capable chat-completions service locally. Keep credentials out of Git.

```bash
# Export JUDGE_API_KEY, JUDGE_BASE_URL and JUDGE_MODEL in your shell.
tib judge --data data/participant --submissions runs/my-agent/submissions \
  --base-url "$JUDGE_BASE_URL" --model "$JUDGE_MODEL" \
  --audit-documents 160 --output runs/my-agent/reviews
tib evaluate --data data/participant --submissions runs/my-agent/submissions \
  --reviews runs/my-agent/reviews --output runs/my-agent/report.json
```

Local checks verify complete assignment partitions, exact quotations and recomputed statistics. Paid model review checks sampled original documents without seeing the agent's claims or labels, then grades the finding. Evidence disagreement caps the score; unresolved evidence stays unscored.

Finding quality is `support × (15 + 25S + 20E + 30D + 10C)`, where S is statistical validity, E evidence entailment, D analytical depth and C calibration. Report scores **together with coverage, unresolved, invalid, missing and abstention counts**. See [scoring](docs/SCORING.md).

## Observed results

The completed development experiment contains **150 runs: three open-source agents × 50 tasks**. Of these, 86 produced valid submissions, 70 received numerical scores, 16 remained evidence-unresolved and 64 produced no valid submission. Scored-only means range from 11.95 to 19.57 out of 100.

These are mixed-configuration development results, **not a controlled leaderboard**. See [per-agent results, settings and limitations](docs/RESULTS.md).

## Data and evaluation scope

Sources are Amazon Beauty reviews, Android App Reviews, CFPB complaints and NHTSA complaints. Tasks cover 20 group differences, 15 temporal changes and 15 compound associations. The optional learning pool is unlabeled.

There are **no fixed reference conclusions** for these open-discovery tasks. The evaluation repository records reference availability, not 50 annotated answers. Quality is judged against corpus evidence and the public rubric; reference coverage is unavailable.

Arithmetic checks are exhaustive; semantic review is sampled and fallible. The data was previously public and is not an unseen holdout. Task and learning document IDs are disjoint, but shared entities and sources mean tasks are not statistically independent.

[Data composition](docs/DATA.md) · [Challenge requirements](docs/DIFFICULTY.md) · [Evaluation operations](docs/ORGANIZER.md) · [Verification](docs/VERIFICATION.md) · [Source terms](docs/SOURCES.md)

```bash
python -m unittest discover -s tests -v
```

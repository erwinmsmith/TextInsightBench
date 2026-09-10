# TextInsightBench

**English** | [简体中文](README.zh-CN.md)

TextInsightBench evaluates agents that mine natural-language datasets for specific, evidence-backed findings. Agents discover meaningful group differences, changes over time, and compound associations, quantify them, and explain counterexamples and uncertainty.

The benchmark contains **50 tasks**, **24,504 evaluation documents**, and an optional **1,379,468-document unlabeled learning pool**. Every task accepts up to five findings or a reasoned abstention. The evaluation compares claims, observable definitions, document assignments, statistics and exact quotations. Any analysis method is allowed.

This is the private research release **v5.1**. English is the primary language of the tasks, documentation and submission examples. Original document text is preserved.

## Repositories

| Resource | Location | Contents |
|---|---|---|
| Code and usage | [erwinmsmith/TextInsightBench](https://github.com/erwinmsmith/TextInsightBench) | Runner, validator, evaluator, task catalog, scoring rubric |
| Participant dataset | [CodeSoulco/TextInsightBench](https://huggingface.co/datasets/CodeSoulco/TextInsightBench) | Unlabeled pool, 50 task corpora, schema, checksums |
| Organizer Reference Set | [CodeSoulco/TextInsightBench-Evaluation](https://huggingface.co/datasets/CodeSoulco/TextInsightBench-Evaluation) | 50 reference conclusions, definitions and supporting context; organizer access only |

All three repositories are initially private. Participant access must exclude the Organizer Reference Set. A shared organization token may access both datasets; run participant agents in a separate environment with only the participant files mounted.

## Quick start

```bash
git clone https://github.com/erwinmsmith/TextInsightBench.git
cd TextInsightBench
python -m venv .venv
source .venv/bin/activate
pip install -e '.[data]'
hf auth login

# Download the pinned task data; add --with-learning for the entire pool.
tib download --output data/participant --with-learning
tib verify --data data/participant --with-learning

# Exercise all 50 tasks without any model API calls.
tib run --data data/participant \
  --command 'python examples/abstain_agent.py' \
  --output runs/smoke/submissions
```

The bundled agent always abstains. It checks integration, not mining quality. For one task, add `--limit 1` to `tib run`. Successful existing submissions are validated and reused when rerunning the same command and configuration.

## Connect your agent

Implement a command that reads one JSON object from stdin and writes one submission JSON object to stdout. Send logs to stderr. Each task starts a new process. The input contains:

```json
{
  "task": {"task_id": "...", "question": "...", "kind": "group_difference"},
  "documents": [{"doc_id": "...", "text": "...", "comparison_group": "..."}],
  "learning_directory": null
}
```

The actual `task` and `documents` include the complete released fields. Replace the smoke-test command with your agent entry point:

```bash
tib run --data data/participant --command 'python my_agent.py' \
  --track unlabeled_pool --timeout 1800 --output runs/my-agent/submissions
```

The `unlabeled_pool` track provides the local learning directory. Prepare learned parameters before evaluation, then analyze each task corpus locally. Freeze global prompts, thresholds and learned parameters for the run. The `task_only` track uses only each task corpus. Report the track, model, software revision, API usage and compute budget with results. The runner is a process adapter, not an access-control sandbox.

See [submission format](docs/SUBMISSIONS.md), [data and task definitions](docs/DATA.md), and [agent protocol](docs/AGENT_PROTOCOL.md).

## Evaluate submissions

Validate one answer locally:

```bash
tib validate --data data/participant \
  --submission runs/my-agent/submissions/amazon_beauty_group_difference_hair_tools_midrating_v5.json
```

An organizer downloads references in a separate environment and can immediately produce a structural report:

```bash
tib download --organizer --output private/evaluation
tib evaluate --data data/participant --submissions runs/smoke/submissions \
  --references private/evaluation/references.json --output runs/smoke/report.json
```

The smoke report has 50 valid abstentions, zero reference coverage, and unavailable finding quality. It does not invent semantic scores.

For substantive answers, generate semantic assessments using a configured JSON-capable chat-completions service. Configure `JUDGE_API_KEY`, `JUDGE_BASE_URL` and `JUDGE_MODEL` in your environment, then run:

```bash
tib judge --data data/participant --submissions runs/my-agent/submissions \
  --references private/evaluation/references.json --output runs/my-agent/reviews \
  --base-url "$JUDGE_BASE_URL" --model "$JUDGE_MODEL"

tib evaluate --data data/participant --submissions runs/my-agent/submissions \
  --references private/evaluation/references.json --reviews runs/my-agent/reviews \
  --output runs/my-agent/report.json
```

`judge` sends paid requests to the chosen provider: one quality request per nonempty answer, plus a reference-matching request when supported findings exist. The quality stage sees the full task corpus and does not see reference conclusions. Choose a model with enough context; oversized inputs fail explicitly without truncation. Each valid completed review is bound to the submission, corpus, reference version and scoring version. Completed reviews can be reused. JSON and Markdown reports include task, family and source breakdowns. See [organizer instructions](docs/ORGANIZER.md).

## Scoring

Finding quality uses a 0–100 rubric: task fulfillment (35), statistical validity (25), evidence entailment (20), analytical depth (10), and calibration (10), multiplied by support. Task scores average submitted findings. Reference coverage is a separate measure: a supported new finding can earn full quality credit even when unmatched.

The [complete scoring standard](docs/SCORING.md) defines gates, partial support, duplicates, abstentions and missing results. The Organizer Reference Set contains AI-generated, non-exhaustive reference conclusions frozen by the maintainer. They are not independently validated. Document-level confirmation annotations are not included or used. References guide coverage; original evidence determines finding quality.

## Reproducibility and development

`benchmark/data.lock.json` pins Hugging Face commit revisions. Downloaded files are verified against a SHA-256 manifest. The 278 learning shards were checked against all evaluation documents and reference-development documents for document-ID, normalized-text and conservative template overlap; no overlap was found. Shared entities and sources remain, and tasks are not statistically independent.

```bash
python -m unittest discover -s tests -v
```

Data comes from Amazon Reviews'23 All Beauty, Android App Reviews, CFPB complaints and NHTSA complaints. Source terms differ; the compilation does not grant a new license to third-party text. See [source attribution and data terms](docs/SOURCES.md). Task IDs retain earlier version suffixes as stable identifiers; v5.1 identifies this complete distribution.

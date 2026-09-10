# TextInsightBench

**English** | [简体中文](README.zh-CN.md)

TextInsightBench evaluates natural-language data-mining agents through **50 open exploration tasks**. Agents must discover a useful pattern, choose a defensible population and comparison, quantify it, find counterexamples, and explain competing interpretations. Any analysis method is allowed.

The current benchmark contains **435,000 task documents** and **944,468 unlabeled learning documents**. Each task has 5,000 or 10,000 documents and accepts at most three nonredundant findings. The task does not supply the condition, comparison groups or time boundary.

## Resources

| Resource | Public repository |
|---|---|
| Runner, scoring and instructions | [GitHub](https://github.com/erwinmsmith/TextInsightBench) |
| Task corpora and unlabeled pool | [Participant dataset](https://huggingface.co/datasets/CodeSoulco/TextInsightBench) |
| Evaluation protocol and reference availability | [Evaluation assets](https://huggingface.co/datasets/CodeSoulco/TextInsightBench-Evaluation) |

All three repositories are public. The benchmark name stays TextInsightBench; commit hashes identify exact snapshots. Old scores are not comparable with the current task inventory.

## Quick start

```bash
git clone https://github.com/erwinmsmith/TextInsightBench.git
cd TextInsightBench
python -m venv .venv
source .venv/bin/activate
pip install -e '.[data]'

# Public downloads; add --with-learning when using the learning pool.
tib download --output data/participant
tib verify --data data/participant

# Interface smoke test only: always abstains, no model API calls.
tib run --data data/participant --command 'python examples/abstain_agent.py' \
  --output runs/smoke/submissions
tib evaluate --data data/participant --submissions runs/smoke/submissions \
  --output runs/smoke/report.json
```

The full exploration challenge is the default. Do not add a difficulty flag. The legacy flags only support historical task snapshots.

## Connect an agent

A fresh process receives one JSON object on stdin and returns a submission JSON object on stdout. Logs belong on stderr. The input provides a local corpus file, not thousands of inline documents:

```json
{
  "task": {"task_id": "...", "question": "...", "kind": "group_difference"},
  "corpus": {"path": "/absolute/path/corpus.jsonl.gz", "format": "jsonl.gz", "n_documents": 10000, "sha256": "..."},
  "learning_directory": null
}
```

The actual task contains the full constraints. Your agent may read, search, index, cluster, sample and revisit the file using its own tools. It must ultimately classify every document in each declared analysis population; a few retrieved quotes are not a population estimate.

```bash
tib run --data data/participant --command 'python my_agent.py' \
  --timeout 3600 --output runs/my-agent/submissions
```

For the learning track, download with `--with-learning` and run with `--track unlabeled_pool`. Freeze global prompts, learned parameters and thresholds before the run; corpus-local exploration is allowed. The runner is not a security sandbox. See [agent protocol](docs/AGENT_PROTOCOL.md) and [submission contract](docs/SUBMISSIONS.md).

## Evaluate

Structural checks recompute all selected-population counts, contrasts, missingness bounds, stratified comparisons and concentration diagnostics. Exact quotation offsets and complete assignment partitions are checked locally.

Semantic quality is assessed separately by a configured JSON-capable chat-completions service:

```bash
# Set JUDGE_API_KEY, JUDGE_BASE_URL and JUDGE_MODEL locally.
tib judge --data data/participant --submissions runs/my-agent/submissions \
  --base-url "$JUDGE_BASE_URL" --model "$JUDGE_MODEL" \
  --audit-documents 160 --output runs/my-agent/reviews
tib evaluate --data data/participant --submissions runs/my-agent/submissions \
  --reviews runs/my-agent/reviews --output runs/my-agent/report.json
```

Judging makes paid requests, one per nonempty submission. It inspects a reproducible, assignment-stratified and corpus-wide sample plus the submitted quotations. **Arithmetic is exhaustive; semantic inspection is sampled.** This is neither full-corpus semantic verification nor an independent validation phase. Insufficient evidence must remain unresolved.

Quality is `support × (15 + 25S + 20E + 30D + 10C)`: statistical validity, evidence entailment, substantive analytical depth, and calibration. Unfulfilled tasks and duplicates receive zero. Report quality alongside scored coverage, abstention, missing and invalid rates; a conditional mean alone is not a full-benchmark score.

## Reference status and limitations

The redesigned tasks do **not** have 50 newly annotated fixed answers. Earlier reference conclusions belong to earlier, narrow task definitions and remain recoverable in repository history; they are not relabeled as answers to these exploration tasks. Current evaluation assets explicitly record zero fixed reference conclusions. Reference coverage is unavailable, not zero; supported novel findings are scored from evidence and the public rubric.

This release adds no independent validation set. Task documents were drawn from a previously public learning pool, so they are not guaranteed unseen. Current task corpora and remaining learning documents have disjoint IDs and inherit the curated pool's text/template deduplication; shared entities and sources remain. The task briefs are distinct research objectives, not evidence of 50 statistically independent questions. No empirical agent-difficulty claim is made without an actual agent comparison.

See [data composition](docs/DATA.md), [challenge and formulas](docs/DIFFICULTY.md), [scoring](docs/SCORING.md), [organizer operations](docs/ORGANIZER.md), [verification](docs/VERIFICATION.md), and [source terms](docs/SOURCES.md).

```bash
python -m unittest discover -s tests -v
```

# Usage

**English** | [简体中文](USAGE.zh-CN.md)

## 1. Install and download

Follow the [quick start](https://github.com/erwinmsmith/TextInsightBench#quick-start). Run commands from the cloned repository root. Python 3.10+ is required; `pip install -e .` installs the runner and evaluator.

`tib download --output data/participant` downloads questions and all 50 task corpora, using the exact dataset commit in `benchmark/data.lock.json`. It does not download the optional learning pool.

To use the learning pool:

```bash
pip install -e '.[data]'
tib download --output data/participant --with-learning
tib verify --data data/participant --with-learning
```

The pool is Parquet; task corpora are gzip JSONL. See [fields and counts](DATA.md).
Evaluation assets are optional and public:

```bash
tib download --organizer --output data/evaluation
```

Current discovery scoring does not need a reference file. If you supply `--references data/evaluation/references.json`, use the same argument for both `judge` and `evaluate`.

## 2. Implement the interface

Your executable receives one JSON object on stdin:

```json
{
  "task": {"task_id": "...", "question": "...", "kind": "group_difference"},
  "corpus": {
    "path": "/absolute/path/corpus.jsonl.gz",
    "format": "jsonl.gz",
    "n_documents": 10000,
    "sha256": "..."
  },
  "learning_directory": null
}
```

The actual task includes all allowed metadata, population sizes and submission constraints. Read the corpus in your own tools; do not expect inline documents. Use original document IDs and text when producing assignments and exact quotation offsets.

Return a single JSON object on stdout matching [the submission contract](SUBMISSIONS.md). Emit diagnostics only to stderr. An empty finding list is an abstention, not a claim that no useful pattern exists. The bundled abstaining agent is only an interface example; no mining solver is bundled.

## 3. Test one task, then run the corpus

```bash
tib run --data data/participant --command 'python my_agent.py' \
  --limit 1 --timeout 3600 --output runs/pilot/submissions

tib run --data data/participant --command 'python my_agent.py' \
  --timeout 3600 --output runs/full/submissions
```

Use `--task-id TASK_ID` to select a particular task. For pool-assisted learning, add `--track unlabeled_pool`. The timeout is per task.

The runner launches a fresh agent process per task, checks its submission and stores valid results. Repeating the same command with the same configuration and output directory reuses valid submissions. A changed command, task selection, timeout or track requires a fresh output directory. In particular, a one-task pilot and a full run must use different directories.

The process runner is not a sandbox. Isolate generated code, restrict network and resource access, and keep credentials outside the execution kernel. Never expose evaluation feedback to the solver. Treat corpus text as untrusted data, not instructions.

## 4. Review and score

Export `JUDGE_API_KEY`, `JUDGE_BASE_URL` and `JUDGE_MODEL` locally. The endpoint must support JSON responses through chat completions; include `/v1` in the base URL if your provider requires it. The CLI reads environment variables, not an `.env` file automatically.

```bash
tib judge --data data/participant --submissions runs/full/submissions \
  --base-url "$JUDGE_BASE_URL" --model "$JUDGE_MODEL" \
  --audit-documents 160 --max-output-tokens 12000 \
  --output runs/full/reviews

tib evaluate --data data/participant --submissions runs/full/submissions \
  --reviews runs/full/reviews --output runs/full/report.json
```

Judging incurs model charges and has no automatic spending cap. Start with `--limit 1` or `--task-id TASK_ID` on the judge command to inspect cost and compatibility. A 160-document audit requires at least 14 blind-check requests before narrative grading; long documents and permitted repairs can increase this. Abstentions make no model calls.

Completed compatible reviews are reused on rerun. Keep `judge_config.json` and the bound `.blind.json` caches. Configuration changes require a fresh review directory. A failed judge request is not a zero score; fix service or format compatibility and rerun. Do not silently coerce semantic labels or select the highest-scoring retry.

`evaluate` writes JSON and Markdown reports and does not overwrite existing reports. Choose a fresh report filename when recomputing. It evaluates the full task inventory: a one-task pilot leaves the other 49 tasks missing.

## 5. Read the report

| Metric | Meaning |
|---|---|
| `scored_tasks / tasks` | Coverage with numerical task scores |
| `quality_mean` | Available only if every task has a numerical score |
| `conditional_quality_mean` | Mean over scored tasks only; never hide its denominator |
| `valid_submission_rate` | Structurally valid submissions, including abstentions |
| `abstention_rate` | Valid submissions that decline to report findings |
| `pending_tasks` | Reviews pending or evidence unresolved; inspect per-task status |
| `missing_tasks`, `invalid_tasks` | No submission or a submission that fails validation |
| `reference_coverage_mean` | Unavailable for the current tasks, which have no fixed references |

Scores range from 0 to 100. Zero means a scored but unsupported/unfulfilled finding, not a missing run. A task score averages its submitted findings; any unresolved finding makes task quality unavailable.

Keep the code commit, data lock, agent commit/configuration, prompts, model IDs, resource budgets and review configuration with your report. Freeze a configuration before making controlled comparisons. The published [development results](RESULTS.md) document different conditions and are not a leaderboard.

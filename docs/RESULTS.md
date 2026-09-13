# Experimental results

**English** | [简体中文](RESULTS.zh-CN.md)

Completed September 13, 2026. Three open-source agents were each run on all 50 tasks using the full 5,000- or 10,000-document task corpus. The optional learning pool was not used.

## Coverage and scores

| Agent | Runs finished | Valid submissions | Scored | Evidence unresolved | No valid submission | Scored-only mean / 100 |
|---|---:|---:|---:|---:|---:|---:|
| DatawiseAgent | 50/50 | 31 | 25 | 6 | 19 | 19.57 |
| MetaGPT Data Interpreter | 50/50 | 29 | 22 | 7 | 21 | 11.95 |
| TaskWeaver | 50/50 | 26 | 23 | 3 | 24 | 13.88 |
| Total | 150/150 | 86 | 70 | 16 | 64 | 15.30 |

Of the 70 scored runs, 35 scored zero and 35 scored above zero. The highest task score was 48.13. No full-benchmark quality mean is available for any agent. Missing, invalid and unresolved results are not converted to zero or silently excluded from coverage.

A finished run is a terminated attempt, not necessarily native-agent success or a valid answer. Some native failures left a valid final artifact that could still be evaluated. The machine-readable [run summary](../results/agent-runs.json) preserves native status separately from evaluation status. Five interrupted assessments were recovered using their existing submissions.

## Experimental conditions

- Solver and judge model ID: `deepseek-flash`, recorded as DeepSeek Flash in the experiment manifests. The same model served both roles; judgments are not independent human validation.
- Track: `task_only`. Agents received the task, full local corpus and submission contract, not reference answers. They controlled their native exploration and code-execution loops; the harness did not impose per-document model calls.
- Solver wall budget: 20 minutes per task. Judge wall budget: 10 minutes per assessment attempt; recovery attempts were additional. Native message, step, tool-output and execution budgets changed during development.
- DatawiseAgent moved from a smaller step budget to 40 steps. MetaGPT changed from plan-and-act to a bounded ReAct loop. TaskWeaver used a 24-message limit, with tool-output limits adjusted. Interface and judge-format compatibility were repaired during the experiment.
- Scoring used the frozen evidence-gated evaluator. The summary records evaluator file hashes and agent adapter hashes; it does not claim every run used identical orchestration.
- The public release contains the benchmark runner and scorer, not the local experiment adapters, credentials or raw execution logs. The summary permits checking aggregate calculations, not reproducing every historical run byte for byte.

| Agent | Upstream source | Pinned commit |
|---|---|---|
| DatawiseAgent | [DatawiseAgent](https://github.com/zimingyou01/DatawiseAgent) | `64f3164869fa2558e7385d0e33a241aee2baf37f` |
| MetaGPT Data Interpreter | [MetaGPT](https://github.com/FoundationAgents/MetaGPT) | `c036574507e7616c02512e7c8ad88dd847783afa` |
| TaskWeaver | [TaskWeaver](https://github.com/microsoft/TaskWeaver) | `d44ddef23f90059fb17999d3095db4240e98f955` |

## Interpretation

These runs show practical challenges in completing the submission contract and producing evidence-supported, substantive discoveries. They do **not** isolate mining ability from framework reliability, budget limits or model behavior.

This is a cumulative development experiment, **not a controlled leaderboard or an unbiased estimate of unseen-task generalization**. Configurations changed across cohorts, tasks were used during development, corpus data was already public, and semantic review is sampled and fallible. The conditional means must not be used to rank agent architectures under supposedly matched conditions.

For a new comparison, freeze agent and evaluator configurations, report every task and failure, preserve corpus and code hashes, and publish score coverage alongside quality. See [usage](USAGE.md) and [scoring](SCORING.md).

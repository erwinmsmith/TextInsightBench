# Scoring

The current scoring protocol is finding-quality-discovery-evidence. Commit-pinned current
scores must not be compared directly with historical narrow-task scores.

## Local gates

Each finding needs a permitted population, valid agent-selected comparison,
minimum population/arm sizes, complete condition partitions, exact text offsets,
and all recomputed statistics. Invalid submissions do not receive invented
quality scores. See [submission contract](SUBMISSIONS.md).

## Evidence-based quality

A semantic assessment supplies support, task_fulfilled, duplicate_of, rationale,
and four dimensions from 0 to 1: S statistical validity, E evidence entailment,
D analytical depth and C calibration. Dimension anchors are 1 fully justified,
0.75 minor gaps, 0.5 material limitations, 0.25 weak and 0 absent/wrong.

```text
finding quality = support × (15 + 25S + 20E + 30D + 10C)
```

Support factors: supported=1, partial=0.5, unsupported=0. Uncertain stays null.
An unfulfilled task or duplicate gets 0 regardless of dimensions. Generic
sentiment, metadata frequencies or an unexamined aggregate contrast do not
fulfill the task. Depth requires a substantive discovery, a defensible choice
of scope/comparison, competing explanations, and correct interpretation of
robustness checks. Material audit omissions cap D at 0.5; merely restating
numbers caps it at 0.25. These semantic caps are judge instructions, not
deterministically proven properties.

Example: a supported, nonduplicate finding with S=.8, E=.9, D=.75, C=.8 earns
15+20+18+22.5+8 = 83.5. Partial support halves it to 41.75. This is an illustrative
calculation, not an observed agent result.

## Semantic audit

All selected-population arithmetic and partitions are checked. The model then
sees at most 160 documents by default: submitted quotations, samples from each
nonempty positive/negative/unknown assignment cell and a corpus-wide remainder.
The seed is created after submission and saved with judge configuration for
reproducibility; sampled IDs are retained in each review. This is a bounded
audit of submitted labels, not a new independently labeled or held-out dataset.

Sampled label mistakes undermine semantic support even if the counts add up.
Absence of sampled errors does not prove all labels correct. The judge must use
uncertain when the packet cannot resolve a claim. No full-corpus semantic
guarantee or unbiased estimator of label accuracy is claimed. Report judge
model, input budget and audit size; model-based scores have evaluator error.

Before narrative grading, a separate claim-blind pass reannotates the sampled
documents in batches of at most 12 documents / 24,000 characters (a single long
document is retained whole). It receives only condition definitions and original
text, never participant claims, labels, statistics or task questions. Exact
positive quotes and complete output coverage are checked. An invalid response
permits one format/quote repair; unresolved protocol errors stop the review.

The persisted blind check is bound to its prompt/protocol and the exact sampled
documents. At evaluation time, agreement diagnostics are recomputed from the
original submission and corpus. The following fixed gates cap semantic support:

- Unsupported: at least 5 sampled claimed positives and at least half are judged
  negative, or every supplied supporting document is contradicted by the checker.
- Uncertain: over 20% checker-unknown within any condition's sampled population,
  no checked population, or fewer than 3 supporting documents confirmed positive
  for all required conditions (unless the unsupported gate already applies).
- Partial: more than 10% disagreement among at least 20 jointly known sampled
  assignments, or over 15% positive contradictions among at least 8 sampled
  claimed positives.
- Otherwise, the check allows supported quality but does not itself award it.

The more restrictive support category is used, with unsupported taking priority
over uncertain and partial. Narrative grading cannot override these caps. Reports
retain the narrative support, effective_support and evidence_gate diagnostics.
These are conservative operational thresholds, not validated population-error
estimates. Sample construction is not uniform, checker judgments remain fallible,
and agreement with a model does not create independently certified ground truth.

A live synthetic regression check preserved full credit for a supported composition
reversal and rejected a submission labeling explicit negative texts as positive.
This is an evaluator sanity check, not a benchmark agent-performance score.

## Aggregation and reference availability

Task quality averages all submitted finding scores; any unresolved finding makes
task quality unavailable. An abstention is valid but unscored, not a verified
absence of useful findings. A full quality_mean is available only when every
task has a score. conditional_quality_mean covers only scored tasks and must be
reported alongside scored_tasks, abstention_rate, valid_submission_rate, missing,
invalid and pending counts. Source and family breakdowns are included.

Current tasks have no fixed reference conclusions. reference_coverage is null.
Novel supported findings are not penalized for lacking a fixed
match. Reviews bind task, corpus, submission, reference configuration and scoring
hashes; stale reviews must not be reused.

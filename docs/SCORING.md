# Scoring standard — finding-quality

The evaluation unit is an evidence-backed downstream finding. Observable definitions and evidence determine validity; the organizer reference set is non-exhaustive. The rubric is public. Reference conclusions are public and used separately for coverage measurement; disclose reference access when reporting results.

This page describes `standard`. The stricter `--difficulty hard` profile adds deterministic robustness checks, a three-document evidence minimum and a 15/25/20/30/10 weighting. See [difficulty profiles](DIFFICULTY.md). Do not compare or aggregate scores across profiles.

## Structural gate

Submissions must satisfy the JSON schema, task kind, maximum finding count, a complete mutually exclusive positive/negative/unknown document partition for each condition, exact source quotations and offsets, and the full set of recomputed statistics. A tolerance of 1e-6 applies to numeric fields. Quotations use Python Unicode string offsets, with an exclusive end. Duplicate IDs, fabricated documents and incomplete partitions are invalid.

Invalid submissions have no semantic quality score. They lower the valid submission rate and prevent a complete-suite quality mean. Unlike a soft arithmetic penalty, The benchmark requires full arithmetic consistency before semantic scoring.

## Semantic assessment

For a finding that fulfills its task and is not a duplicate:

```text
quality = support × (35 + 25S + 20E + 10D + 10C)
```

| Variable | Meaning | Range |
|---|---|---|
| support | supported: 1; partial: 0.5; unsupported: 0; uncertain: null | 0–1 or null |
| S | Statistical validity: condition assignments, denominators, comparisons, unknown sensitivity and scope | 0–1 |
| E | Evidence entailment: original text supports the stated observations and qualifications | 0–1 |
| D | Analytical depth: substantive patterns beyond generic descriptions, with composition checks | 0–1 |
| C | Calibration: counterexamples, uncertainty, inference boundaries and restrained claims | 0–1 |

Use common anchors: 1 fully justified, 0.75 minor gaps, 0.5 material limitations, 0.25 weak, 0 absent or wrong. The base 35 points require task fulfillment; failure to fulfill the task or a duplicate of an earlier finding gives 0. Unresolved support produces null rather than a guessed score.

Example: supported, task fulfilled, S=0.8, E=0.9, D=0.7, C=0.9 gives `35 + 20 + 18 + 7 + 9 = 89`. Partial support gives 44.5. This is a mathematical illustration, not a measured benchmark result.

Check semantic correctness of document assignments even when arithmetic passes. Missing mention is not proof of event absence. Statistical significance is not required for a correctly limited description of the supplied finite corpus. Claims about wider populations, causes, event dates or product incidence need additional support. Changing product or entity composition can explain an apparent contrast.

The quality judge receives the full corpus and the submission. The separate reference matcher receives only already-supported findings and the reference definition; it does not alter quality dimensions. This reduces direct reference anchoring but does not eliminate model error. The chosen judge model and its context capacity affect scores.

## Task and suite aggregation

Task quality is the arithmetic mean of all submitted finding scores. Up to five findings may be submitted; low-quality or duplicate additions lower the mean. A task with any unresolved finding has null quality.

Each released task currently has one organizer reference. Reference coverage is 1 when a supported, task-fulfilling, nonduplicate finding matches its observable condition, scope, contrast and direction; otherwise 0. An unresolved answer has null coverage. Shared terminology alone is insufficient. A supported novel finding may receive 100 quality and 0 coverage.

The full-suite quality mean is the macro-average of 50 task scores and exists only if all 50 are scored. `conditional_quality_mean` averages available task scores and must be labeled diagnostic; it must not be compared as a complete leaderboard score. The same complete-coverage rule applies to `reference_coverage_mean`. Reports also show valid submission rate, abstention rate, missing/invalid/pending counts, and source/family breakdowns.

A valid abstention has quality null and reference coverage 0. This release does not award an absence-detection score: there is no exhaustive absence reference. A run consisting of 50 valid abstentions has 100% valid submissions, 100% abstention, 0% coverage and null quality. Missing results are not zero scores.

Use one benchmark revision, dataset revision, track and judge configuration for each comparison. Report conditional means with scored-task counts. Tasks share sources and entities; do not interpret a naive task-level standard error as independent evidence.

# Organizer Reference Set and evaluation

The organizer dataset is a separate private Hugging Face repository. It contains `references.json`, `release.json`, and bilingual dataset cards. Access must not be granted to benchmark participants. Public scoring dimensions are documented in `SCORING.md`; task-specific reference content is reserved for organizer use.

There are 50 reference entries, one per task. Each includes a stable reference ID, candidate claim, expected direction, observable condition specification, development evidence with embedded source text and quotation offsets, and limitations. Development evidence can come from records outside the final task corpus; `in_evaluation_corpus` explicitly identifies this. It helps interpret the definition and does not establish final-corpus prevalence.

The reference conclusions were AI-generated and frozen by the maintainer. They are non-exhaustive and not independently validated. Their wording may retain development-hypothesis language to preserve epistemic status. Document-level confirmation annotations and confirmation statistics are excluded. Removing those diagnostics does not increase certainty in the reference claims. Evaluate the participant's actual corpus evidence before considering reference matching.

## Workflow

1. Download the pinned participant data and organizer references in the organizer environment.
2. Receive one submission per task from the isolated participant run.
3. Run `tib judge` with a JSON-capable chat-completions API and a model whose context supports the complete task corpus and answer.
4. Run `tib evaluate` to validate assessments and write JSON/Markdown reports.
5. Compare methods with matching dataset, reference, track and judge versions. Report incomplete scores explicitly.

No paid inference happens during installation, download, validation, the smoke agent or deterministic evaluation. Calling `tib judge` explicitly invokes the configured service. It does not use any built-in provider account or key. Credentials are read from the named environment variable and are not saved in run files.

The first judge request assesses each finding from the full corpus with no references. A second request matches supported findings to the organizer reference. Quality dimensions are not rewritten in the second stage. Reference matching requires agreement in condition, scope, contrast and direction. The first prompt is versioned in `textinsightbench/judge.txt`.

Choose `--max-input-chars`, `--max-output-tokens` and `--timeout` to fit the provider. The character limit is a local guard, not an exact token estimate. Truncation, invalid JSON, incomplete judgments and provider errors leave the task unreviewed. There is no silent retry or invented fallback score. Valid completed reviews resume without new calls. If a quality request succeeds but a later matching request fails, that task remains incomplete and rerunning may incur both calls again.

## Review files and reproducibility

A review file binds `task_id`, `submission_sha256`, `corpus_sha256`, `reference_sha256` and `scoring_version`. It records `reviewer_method`, findings and provider receipts with usage, model, response ID and request hash when available. The run-level `judge_config.json` records endpoint, model and prompt digest. These records are provenance, not a guarantee of model correctness or deterministic replay.

To supply assessments from another judge, follow the same structure and rubric. Each finding requires `finding_id`, `support`, `task_fulfilled`, `statistical_validity`, `evidence_entailment`, `analytical_depth`, `calibration`, `duplicate_of`, `reference_match`, and a specific `rationale`. All score dimensions range from 0 to 1. A matcher can only name the task's released reference ID. The evaluator rejects altered submissions or mismatched corpora/references.

The report includes a quality macro-average only when every task has a resolved score. Abstentions are accepted but do not certify absence. Missing or unresolved results are null. Use `conditional_quality_mean` only with explicit coverage counts; no official performance claim is established by the integration smoke test.

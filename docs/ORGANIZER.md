# Evaluation operations

Use the commit-pinned participant data and the same code revision as participants.
Validate all submissions before semantic scoring. Current scoring works without
a reference file; optional public evaluation assets record reference availability
and the matching task hash, not 50 new answers.

```bash
tib download --organizer --output evaluation
tib judge --data data/participant --submissions runs/agent/submissions \
  --base-url "$JUDGE_BASE_URL" --model "$JUDGE_MODEL" \
  --audit-documents 160 --output runs/agent/reviews
tib evaluate --data data/participant --submissions runs/agent/submissions \
  --reviews runs/agent/reviews --output runs/agent/report.json
```

Set JUDGE_API_KEY locally. Nonempty tasks incur one quality API request each;
abstentions make no API calls. No reference-matching requests occur for current
tasks. Configure model, timeout, max input characters and output tokens; an
oversized packet fails explicitly without silent truncation. Use a sufficiently
large model context or adjust the documented audit budget (60–2000 documents).
Many quotations may require raising a very small audit budget.

Persist judge_config.json for the audit seed and configuration. Completed valid
reviews are reused. Changed tasks, corpora, submissions or judge configuration
require fresh output directories. Do not tune an agent on judge feedback and
present that score as a frozen run. Publish all coverage and uncertainty metrics,
not only a favorable subset.

The structural verifier is exhaustive; semantic review is sampled and fallible.
This release does not require independent verification or add an unseen holdout.
For enforceable comparisons, run participants in an isolated environment without
evaluation access; the process adapter alone cannot enforce this.

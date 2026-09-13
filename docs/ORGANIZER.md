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

Set JUDGE_API_KEY locally. Nonempty tasks incur claim-blind annotation requests
(at most 12 sampled documents per batch, up to four concurrent requests), followed
by one quality request. A malformed blind response permits one repair request.
The default 160-document audit needs at least 14 blind requests before quality
grading; long texts can require more. Abstentions make no API calls.
No reference-matching requests occur for current
tasks. Configure model, timeout, max input characters and output tokens; an
oversized packet fails explicitly without silent truncation. Use a sufficiently
large model context or adjust the documented audit budget (60–2000 documents).
Many quotations may require raising a very small audit budget.

Persist judge_config.json for the audit seed and configuration, and each task's
.blind.json for the bound, reusable pre-grading annotations. Completed valid
reviews are reused. Changed tasks, corpora, submissions or judge configuration
require fresh output directories. Do not tune an agent on judge feedback and
present that score as a frozen run. Publish all coverage and uncertainty metrics,
not only a favorable subset.

The structural verifier is exhaustive; semantic review is sampled and fallible.
This release does not require independent verification or add an unseen holdout.
For enforceable comparisons, run participants in an isolated environment without
evaluation access; the process adapter alone cannot enforce this.

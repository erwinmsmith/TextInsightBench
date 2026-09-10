# Exploration challenge

The default 50 tasks require broad corpus exploration, not an additional profile.
Each contains 5,000 or 10,000 documents. The agent selects its text conditions,
population, group values or time boundary. Research objectives cover practical
tradeoffs, process breakdowns, adaptation burdens, recurrence and consequences
without prescribing which pattern exists.

The difficulty is in finding a substantive relationship, operationalizing it
across the analysis population, and explaining its scope and competing accounts.
Corpus size alone is not evidence of a difficult or valid evaluation.

A selected population must contain at least 500 documents for App Reviews and
1,000 otherwise. Each metadata/time comparison arm needs at least 50 or 100
documents respectively. These thresholds refer to total documents, not positive
cases. Unknown labels must be retained and interpreted. At most three
nonredundant findings are accepted. Tiny handpicked groups and ID/text-based
population filters are prohibited.

The fixed audit axes are entity_id, rating and report_year. Missing or degenerate
axes remain unavailable, never silently replaced with a favorable axis. In
particular, stratifying on the same metadata as the comparison may leave no
comparable strata; report that limitation. A correctly established composition
effect or reversal can earn full credit. Stability in every axis is not required.

## Exact audit calculations

All base statistics remain required. Each finding additionally reports the
`robustness_*` numeric/null fields returned by `expected`:

```python
from textinsightbench.validation import expected
from textinsightbench.difficulty import audit

# The runner's task already includes the discovery protocol. The agent supplies
# definitions, all document assignments, evidence and interpretation itself.
finding['statistics'] = expected(finding, task, documents)
statistics, stratum_details = audit(finding, task, documents)
```

For group/time tasks, arm 0 and arm 1 are the agent's declared comparison groups,
excluding unknown condition assignments. For compound tasks, arm 0 is known
not-A and arm 1 is known A, restricted to known B; the outcome is B. Thus the
effect always matches the sign convention of the declared comparison.

For each axis:

1. A comparable stratum has at least 5 known documents in **each** arm. Its effect
   is `100 × (positive_rate_arm1 − positive_rate_arm0)`.
2. The standardized effect is the mean of eligible stratum effects, weighted by
   their pooled known-arm counts. `covered_crude_delta_pp` recomputes the crude
   contrast on those same eligible rows, so differences in covered populations
   are not mistaken for reversals. Report eligible/excluded known counts and the
   minimum and maximum stratum effects.
3. Select the largest nonmissing stratum by its full document count, independently
   of labels; ties use lexical order of its string value. Remove it and missing
   metadata rows. The retained effect is null unless each arm still has at least
   5 known documents. Report removed and retained-arm counts.
4. `max_support_share` is the largest stratum's share of positive outcomes among
   known-arm documents with nonmissing metadata. Report positive outcomes with
   missing metadata separately. For compound tasks this is B concentration in the
   jointly known population, not the proportion of A-and-B quotes.

All expected fields must be present, no extra statistics are accepted, and values
must match recomputation within 1e-6. The three supporting quotes must reference
positive documents (joint positives for compound findings). A counterexample must
reference a known negative or, for compound tasks, a known discordant case. The
semantic judge still checks whether assignments and quotes are actually correct.

The audit does not create independent samples, establish causal identification,
eliminate multiple-testing risk, or act as unseen holdout confirmation. Unknown
assignment bounds remain mandatory for group/time findings. Compound findings
must interpret the jointly unknown population and avoid unsupported extrapolation.


## Evaluation

Quality is support × (15 + 25S + 20E + 30D + 10C). Depth requires a useful finding
and a supported discussion of alternatives and search/selection bias. See
[scoring](SCORING.md). Numeric audit correctness does not establish semantic
label correctness: the current judge audits a document sample, with uncertainty
preserved. No independent validation phase or causal identification is implied.

Current tasks automatically select this protocol. Do not use --difficulty hard.
The CLI retains historical profile support solely for historical task snapshots.
Runs, reviews and scores are bound to the current task hashes.

# Difficulty profiles

TextInsightBench has 50 task identities. Each can run under `standard` or `hard`;
these are evaluation profiles, not 100 independent tasks. Use `hard` for the
stricter mining challenge and report it explicitly. Scores across profiles are
not directly comparable.

The hard profile keeps the same task corpus, semantic discovery goal and base
reference set. It does not claim that a larger corpus or independent confirmation
set has been constructed. Existing references measure coverage of the original
discovery; they are not ground truth for robustness or causal explanations.

## What changes

| Requirement | Standard | Hard |
|---|---|---|
| Maximum findings | 5 | 3 |
| Supporting evidence | At least one supporting quote | Quotes from at least 3 distinct positive documents |
| Counterexamples | Semantically assessed | A negative/discordant quote is structurally required when such assigned cases exist |
| Composition | Qualitative assessment | Recomputed metadata-stratified comparisons on 3 fixed axes |
| Dominant-stratum sensitivity | Not structurally required | Recomputed removal of the largest metadata stratum |
| Concentration and missingness | Qualitative assessment | Explicit coverage, missingness and maximum support-share statistics |
| Task-fulfillment base points | 35 | 15 |
| Analytical-depth weight | 10 | 30, including correct robustness interpretation |

The axes are `entity_id`, `rating` and `report_year` (a valid reporting/review
timestamp's calendar year). They are fixed for every task and are not selected
after looking at the direction of the result. A missing value is not a stratum.
An axis with no useful comparison must be reported as unavailable; it must not be
silently replaced by a handpicked favorable axis.

An accurately demonstrated composition-dependent result or reversal can earn full
credit. The challenge is to discover and explain a defensible pattern, not to force
every aggregate association to remain positive.

## Exact audit calculations

All base statistics remain required. Each finding additionally reports the
`robustness_*` numeric/null fields returned by `expected`:

```python
from textinsightbench.validation import expected
from textinsightbench.difficulty import audit

# The runner's task already includes the chosen profile. The agent supplies
# definitions, all document assignments, evidence and interpretation itself.
finding['statistics'] = expected(finding, task, documents)
statistics, stratum_details = audit(finding, task, documents)
```

For group/time tasks, arm 0 and arm 1 are the task's original comparison groups,
excluding unknown condition assignments. For compound tasks, arm 0 is known
not-A and arm 1 is known A, restricted to known B; the outcome is B. Thus the
effect always matches the sign convention of the original task.

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

## Scoring

For a supported, task-fulfilling, nonduplicate hard finding:

```text
quality = support × (15 + 25S + 20E + 30D + 10C)
```

The dimension names and support factors are unchanged. Here D requires concrete
discovery plus correct interpretation of the available audits and the strongest
alternative composition explanation. Material omissions cap D at 0.5; numerical
restatement without analysis caps it at 0.25. A bare aggregate contrast does not
fulfill the hard task. The quality judge sees computed audit details but no
reference conclusion. Reference matching is a separate coverage diagnostic.

Hard reviews bind the effective task hash and `finding-quality-robustness` scoring
identifier. Ordinary reviews cannot be reused. Runs and reports reject mixed
profiles. An abstention remains unscored, not a verified absence.

## Run all 50 tasks

```bash
tib run --difficulty hard --data data/participant \
  --command 'python my_agent.py' --output runs/hard/submissions
tib validate --difficulty hard --data data/participant \
  --submission runs/hard/submissions/amazon_beauty_group_difference_hair_tools.json
tib judge --difficulty hard --data data/participant \
  --submissions runs/hard/submissions --references evaluation/references.json \
  --base-url "$JUDGE_BASE_URL" --model "$JUDGE_MODEL" --output runs/hard/reviews
tib evaluate --difficulty hard --data data/participant \
  --submissions runs/hard/submissions --references evaluation/references.json \
  --reviews runs/hard/reviews --output runs/hard/report.json
```

Use the same profile in all commands and a new output directory. The built-in
abstaining agent can smoke-test all 50 tasks without paid model calls; this is an
interface test, not evidence that an agent solves the hard profile.

Further difficulty through broader corpus search, agent-selected comparison
boundaries or genuinely unseen confirmation data requires a new data-construction
and reference-validation pass. Those capabilities are not implied by this profile.

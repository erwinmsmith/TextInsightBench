# Submission contract

Write one UTF-8 JSON file per task, named `<task_id>.json`. The agent process protocol writes that same object to stdout. Do not wrap it in Markdown.

```json
{
  "task_id": "the task ID",
  "findings": [],
  "abstention_reason": "No sufficiently supported finding was identified."
}
```

A nonempty answer contains up to five findings. Every finding has:

| Field | Required content |
|---|---|
| `finding_id` | Unique identifier within the answer |
| `claim` | Specific downstream conclusion, including direction and scope |
| `kind` | Exactly the task's kind |
| `scope` | Corpus, group, time and entity scope |
| `definitions` | One observable condition for group/time tasks; two for association tasks. Each has `condition_id`, `inclusion`, `exclusion` |
| `assignments` | One complete document partition per condition: `condition_id`, `positive_doc_ids`, `negative_doc_ids`, `unknown_doc_ids` |
| `statistics` | Exactly the recomputed fields below |
| `evidence` | Original quotation records: `doc_id`, `start`, `end`, `quote`, `role` (`supporting`, `counterexample`, `context`) |
| `limitations` | Nonempty list describing uncertainty, confounding and inference limits |

At least one supporting quotation is required. Every document belongs to exactly one state per condition. Positive means the stated report is present; negative means it is not reported under the definition; unknown preserves unresolved judgments. Quotations refer to the `text` field. Python `text[start:end]` must equal `quote`, using Unicode characters, not UTF-8 bytes or JavaScript UTF-16 code units. Do not normalize or edit evidence text before computing offsets.

Use the implementation to compute statistics from your assignments:

```python
from textinsightbench.validation import expected
finding["statistics"] = expected(finding, task, documents)
```

For group/time tasks, required statistics are `group0_total_n`, `group0_known_n`, `group0_positive_n`, `group0_unknown_n`, `group0_rate_known` and the corresponding five `group1_*` fields, plus `excluded_metadata_n`, `delta_known_pp`, `delta_identification_lower_pp`, `delta_identification_upper_pp`.

Group order follows `comparison.groups`; for time tasks, group 0 is before the cutoff and group 1 is on or after. The known rate is positive / (total − unknown). The reported difference is **group 1 minus group 0**, in percentage points. The lower/upper identification bounds allocate unknowns to all compatible states within the finite corpus. These bounds are not confidence intervals. Missing comparison metadata is excluded from named denominators but still needs a condition judgment.

For association tasks, required statistics are `known_joint_n`, `unknown_joint_n`, `n11`, `n10`, `n01`, `n00`, `p_b_given_a`, `p_b_given_not_a`, `conditional_difference_pp`, `lift`. Condition A is the first definition and B the second. Joint cells count documents with known judgments for both conditions; unknowns are counted separately. Zero denominators produce JSON `null`, never NaN or infinity. Additional unsupported statistics are not accepted by this contract.

The schema is bundled in `textinsightbench/output.schema.json` and the dataset root. Full working synthetic examples appear in `tests/test_evaluation.py`; they are integration fixtures rather than answers to released tasks.

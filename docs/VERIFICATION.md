# Verification scope

The release was checked with local automated tests and an all-50-task abstaining
agent smoke run. This verifies loading, corpus hashes, task dispatch, output
contracts and reporting, not real-agent mining quality or empirical difficulty.

Synthetic tests exercise agent-selected group/date comparisons, forbidden
filters, overlapping groups, minimum population sizes, exact partitions,
Simpson-style reversals, missing metadata, counterexamples, quotation offsets,
score bindings, null reference coverage and bounded reproducible semantic packets.
The separate [agent experiment](RESULTS.md) covers 150 completed attempts.
It is not an independent validation set or a controlled leaderboard.

```bash
python -m unittest discover -s tests -v
tib verify --data data/participant --with-learning
```

The data builder deterministically selects disjoint IDs from an already curated
pool, preserves original text, enriches released metadata and filters selected
documents out of the remaining pool. It records exact input shard hashes.
Current-snapshot disjointness does not erase historical public exposure.
Observed completion and quality results are reported separately from these
software checks; they do not establish difficulty under matched conditions.

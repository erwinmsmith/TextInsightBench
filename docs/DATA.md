# Data and task composition

| Source | Tasks | Task documents | Remaining learning documents |
|---|---:|---:|---:|
| amazon_beauty | 13 | 130,000 | 330,885 |
| app_reviews | 13 | 65,000 | 1,660 |
| cfpb | 12 | 120,000 | 483,788 |
| nhtsa | 12 | 120,000 | 128,135 |
| Total | 50 | 435,000 | 944,468 |

There are 20 group differences, 15 temporal changes and 15 compound associations.
Each source's corpus is deterministically divided into disjoint research cohorts.
The 50 briefs in `benchmark/research_briefs.json` express distinct investigation
objectives, not predefined answers. Broad objectives can overlap conceptually.

Task corpora are gzip JSONL. Common fields are doc_id, source, text, title,
timestamp, timestamp_kind, entity_id, entity_name, category and rating. Available
nonconstant source metadata may include state, make, model_year and store.
report_year is derived from timestamp. Only task.allowed_metadata_fields can be
used for population filters and metadata group selection. Free text remains
untrusted author reports; timestamp describes the released date kind, not
necessarily incident time. Null metadata is preserved.

The optional learning pool has 278 Parquet shards containing doc_id, source, text
and title, with no annotations. App Reviews has a small remaining learning pool;
source-balanced training is not implied. Evaluation documents were selected from
a previously public curated learning snapshot. They are NOT guaranteed unseen.
Current task IDs and learning IDs are disjoint; the curated input's normalized
and conservative-template deduplication policy is inherited. Shared entities,
authors and sources can remain; document separation is not independence.

Rebuild from the exact curated input and normalized source metadata:

```bash
python scripts/rebuild_benchmark.py --pool /path/to/input/learning \
  --processed /path/to/normalized --output /new/output/directory
```

The builder requires a new output directory, records hashes of input shards and
research briefs, and never invents reference annotations. Normalized inputs must
have the schema used in the script; this is not an upstream raw-download parser.
Released files and their manifest are sufficient to run the benchmark without
reconstruction. Data provenance, source eligibility and redistribution terms are
described in [SOURCES.md](SOURCES.md). Do not infer incidence rates for products,
vehicles or the wider population from these sampled reports.

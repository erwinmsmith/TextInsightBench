# Data and tasks

| Source | Learning documents | Tasks | Evaluation documents |
|---|---:|---:|---:|
| Amazon Reviews'23 All Beauty | 460,885 | 13 | 6,421 |
| Android App Reviews | 66,660 | 13 | 5,484 |
| CFPB complaints | 603,788 | 12 | 6,300 |
| NHTSA complaints | 248,135 | 12 | 6,299 |
| Total | 1,379,468 | 50 | 24,504 |

Learning documents occupy 278 Parquet shards. They contain only `doc_id`, `source`, `text`, and `title`. No benchmark annotation labels are supplied. Use them for unsupervised learning, representation building, retrieval indexing or corpus exploration before running evaluation tasks.

Evaluation corpora are 50 gzip-compressed JSON Lines files, with 263–600 documents per task (median 500). Documents retain text, ID and the metadata needed for each comparison, including entity, rating, report timestamp and group when applicable. Ratings and groups are observed input metadata, not hidden answer labels. The 50 corpora have distinct document IDs. Corpus-local analysis is allowed in both tracks.

| Task family | Tasks | Required downstream analysis |
|---|---:|---|
| `group_difference` | 20 | Discover a concrete reported experience that differs across the named groups; quantify both denominators and inspect composition |
| `temporal_change` | 15 | Discover a specific reporting pattern that changes across the cutoff; distinguish report dates from event dates |
| `compound_association` | 15 | Discover two observable conditions with a meaningful within-document association; provide the complete joint table |

The task question does not disclose the organizer reference condition. A specific answer may be discovered by any analysis method. Each finding must go beyond broad categories or generic sentiment.

## Files

```text
tasks.json                 50 task specifications
corpora/*.jsonl.gz         Task-specific evaluation inputs
learning/<source>/*.parquet
output.schema.json         Required submission structure
protocol.json              Tracks, inference scope and adaptation rules
manifest.json              SHA-256 and byte sizes
release.json               Counts and version
README.md / README.zh-CN.md Dataset cards
SOURCES.md                 Attribution and source terms
```

Each `tasks.json` entry includes `task_id`, `source`, `kind`, `scope_name`, `question`, `comparison`, `n_documents`, `max_findings`, `corpus_path`, `corpus_sha256`, `output_contract`, `selection_scope`, and `dependence_block`. IDs are stable across packaging updates.

## Sampling and overlap

The pool was curated from the downloaded source snapshots using English filtering, length constraints and deduplication. The CFPB pool is restricted to the 2024–2025 credit-reporting selection. The pool's original holdouts include pilot task corpora. For v5.1, every exported shard was checked again against current evaluation and reference-development documents using document IDs, normalized text hashes and a conservative template hash that collapses digits and punctuation. No additional removals were required.

This check is narrower than arbitrary semantic deduplication. Shared products, companies, apps, entities and source collection procedures remain. Source complaints and ratings are selected reports and do not measure population incidence. The benchmark is predominantly English; language filtering is imperfect. Original spelling and HTML fragments are retained to keep evidence offsets stable.

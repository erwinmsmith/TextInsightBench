# Release verification — v5.1

The initial release was checked on 2026-09-10. These are engineering checks, not measured mining performance.

| Check | Result |
|---|---|
| Package installation and `tib` entry point | Passed in a local virtual environment |
| Synthetic validation/scoring tests | 12 passed |
| Two-stage quality and reference matching | Passed with a mocked provider; no live model quality claim |
| Full participant dataset downloaded from pinned Hub revision | 335 manifest entries verified by SHA-256 |
| Organizer Reference Set downloaded from pinned Hub revision | 50 references; checksum verified |
| Full 50-task runner on downloaded data | 50 valid submissions, 0 failed |
| Report generation on downloaded data and references | JSON and Markdown generated |
| Smoke-agent result | 50 abstentions, valid submission rate 1.0, reference coverage 0.0, quality null |
| Hugging Face dataset cards | Both cards passed Hub YAML validation |
| Participant/reference separation | No reference payload in participant dataset or code repository |
| Repository visibility at release | GitHub and both Hub datasets private |

The smoke agent does not perform mining or call an API. A full semantic experiment requires a real participant agent and a configured judge. No paid judge or participant inference was performed during packaging.

Dataset revisions:

- Participant: `7135d1936a1c8b8b65c7cb7f1360c8d8591fdb6b`
- Organizer references: `4c7a77ba860d1c0cf344c22b57a5f11a55e63a55`

The participant Hub repository contains 278 learning shards and 50 task corpora, approximately 262.5 MB total. The organizer repository is approximately 0.74 MB, including embedded development evidence. Versions tested locally: Python 3.13, jsonschema 4.26.0, huggingface-hub 1.16.1 and pyarrow 24.0.0. Package compatibility with every permitted dependency version has not been exhaustively tested.

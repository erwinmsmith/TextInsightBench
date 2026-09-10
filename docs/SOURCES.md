# Source attribution and data terms

TextInsightBench is a derived research collection of third-party text. It does not grant a new license to source reviews or complaints. This initial distribution is private. The data card uses `license: other` and links here because upstream terms differ and not all redistribution rights are established.

| Source | Upstream location | Recorded source status |
|---|---|---|
| Amazon Reviews'23, All Beauty | https://amazon-reviews-2023.github.io/main.html | Research release; source text redistribution terms require upstream verification |
| Android App Reviews | https://huggingface.co/datasets/sealuzh/app_reviews | Downloaded dataset card lists the license as unknown; snapshot `9eaa95f66364367e8752b0f34c00f67aafa95d15` |
| CFPB Consumer Complaint Database | https://www.consumerfinance.gov/data-research/consumer-complaints/ | Public complaint data; retain source attribution and original publisher context |
| NHTSA complaints | https://www.nhtsa.gov/nhtsa-datasets-and-apis | Public government release; source is the 2020–2024 complaints archive |

Raw download endpoints recorded for reproducibility:

- Amazon: `https://mcauleylab.ucsd.edu/public_datasets/data/amazon_2023/raw/review_categories/All_Beauty.jsonl.gz`
- CFPB: `https://files.consumerfinance.gov/ccdb/complaints.csv.zip`
- NHTSA: `https://static.nhtsa.gov/odi/ffdd/cmpl/COMPLAINTS_RECEIVED_2020-2024.zip`
- App Reviews: `https://huggingface.co/datasets/sealuzh/app_reviews/resolve/9eaa95f66364367e8752b0f34c00f67aafa95d15/data/train-00000-of-00001.parquet`

Released hashes identify the frozen derived files even when upstream downloads change. Complaint and review narratives are unverified author reports and may include personal information. The exported learning schema excludes user identifiers, but this is not a guarantee of complete de-identification of free text. Preserve the intended research scope and consult upstream terms before any public redistribution. No permissive license for this code or compilation is granted by the private repository itself.

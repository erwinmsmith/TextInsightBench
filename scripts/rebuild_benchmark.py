"""Build disjoint exploration corpora from a curated pool and normalized metadata.

Inputs are explicit local paths. Never calls a model or invents reference answers.
The curated pool snapshot must already satisfy the documented text deduplication
and source eligibility policy. Output must be a new directory.
"""
import argparse
import gzip
import hashlib
import json
from collections import Counter
from pathlib import Path

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


INSTRUCTIONS = ''' Explore the complete supplied corpus before choosing a scope.
Select your own observable text condition(s), analysis population and comparison.
Explain why the selection addresses the research objective, alternative patterns
considered and search/selection bias. Return at most three nonredundant findings.
For each, partition every selected document into positive, negative or unknown
for each condition; compute the full statistics with textinsightbench.validation.expected.
Report metadata-stratified contrasts, largest-stratum removal, support concentration,
unknown sensitivity and missing-metadata limits. Provide exact quotations from at
least three supporting documents and a counterexample if known negative or
discordant cases exist. Discuss competing explanations and where the finding fails.
Generic sentiment, metadata counts and restating the brief are insufficient.
Same-corpus exploration is not independent confirmation or causal evidence.
Abstain with a reason when no defensible finding meets these requirements.'''


def build(args):
    out = args.output
    if out.exists():
        raise ValueError('Output must not exist; preserve previous snapshots')
    out.mkdir(parents=True)
    briefs = json.loads(args.briefs.read_text())
    tasks, pool_counts, source_counts, input_hashes = [], {}, {}, {}
    for source, families in briefs.items():
        specs = [(kind, name, brief) for kind, entries in families.items() for name, brief in entries]
        size = 5000 if source == 'app_reviews' else 10000
        shards = sorted((args.pool/source).glob('*.parquet'))
        if not shards:
            raise ValueError('Missing pool source: '+source)
        ids = []
        for shard in shards:
            input_hashes[str(shard.relative_to(args.pool))] = sha(shard)
            ids.extend(pq.read_table(shard, columns=['doc_id'])['doc_id'].to_pylist())
        if len(ids) != len(set(ids)) or len(ids) < len(specs)*size:
            raise ValueError('Pool IDs must be unique and sufficiently numerous')
        ids.sort(key=lambda value: hashlib.sha256(('TextInsightBench exploration '+source+value).encode()).digest())
        selected = ids[:len(specs)*size]
        selected_set = set(selected)
        selected_array = pa.array(selected)
        records = {}
        columns = ['doc_id','source','text','title','timestamp','timestamp_kind','entity_id','entity_name','category','rating','metadata_json']
        for shard in sorted((args.processed/source/'corpus').glob('*.parquet')):
            table = pq.read_table(shard, columns=columns)
            table = table.filter(pc.is_in(table['doc_id'],value_set=selected_array))
            for row in table.to_pylist():
                extra = json.loads(row.pop('metadata_json') or '{}')
                for field in ('state','make','model_year','store'):
                    if extra.get(field) not in (None,''):
                        row[field] = extra[field]
                if row['doc_id'] in records:
                    raise ValueError('Duplicate normalized document')
                records[row['doc_id']] = row
        if set(records) != selected_set:
            raise ValueError('Selected IDs missing from normalized corpus')
        remaining = 0
        for shard in shards:
            table = pq.read_table(shard)
            table = table.filter(pc.invert(pc.is_in(table['doc_id'],value_set=selected_array)))
            target = out/'learning'/source/shard.name
            target.parent.mkdir(parents=True,exist_ok=True)
            pq.write_table(table,target,compression='zstd')
            remaining += len(table)
        pool_counts[source] = remaining
        source_counts[source] = {'tasks':len(specs),'documents':len(selected)}
        for i,(kind,name,brief) in enumerate(specs):
            tid = source+'_'+kind+'_'+name
            rows = [records[d] for d in selected[i*size:(i+1)*size]]
            fields = [f for f in ('entity_id','rating','category','state','make','model_year','store')
                      if len({r.get(f) for r in rows if r.get(f) is not None}) > 1]
            if any(r.get('timestamp') for r in rows):
                fields += ['timestamp','report_year']
            path = out/'corpora'/(tid+'.jsonl.gz')
            path.parent.mkdir(exist_ok=True)
            with path.open('wb') as raw, gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0) as zipped:
                for row in rows:
                    zipped.write((json.dumps(row,ensure_ascii=False)+'\n').encode())
            tasks.append({'task_id':tid,'source':source,'kind':kind,'question':brief+INSTRUCTIONS,
                'difficulty':'discovery','discovery_mode':'agent_selected','max_findings':3,
                'allowed_metadata_fields':fields,'min_population_n':size//10,'min_group_n':size//100,
                'n_documents':size,'corpus_path':str(path.relative_to(out)),'corpus_sha256':sha(path),
                'robustness_protocol':{'axes':['entity_id','rating','report_year'],'min_known_per_arm':5}})
        print(json.dumps({'source':source,'exploration':len(selected),'learning':remaining}),flush=True)
    release = {'version':'textinsightbench','tasks':len(tasks),'evaluation_documents':sum(t['n_documents'] for t in tasks),
        'learning_documents':sum(pool_counts.values()),'learning_by_source':pool_counts,
        'evaluation_by_source':source_counts,'task_family_counts':dict(Counter(t['kind'] for t in tasks)),
        'fixed_reference_conclusions':0,'scoring_version':'finding-quality-discovery',
        'split_policy':'Disjoint task IDs and remaining curated learning pool; inherited normalized/template deduplication.',
        'historical_exposure':'Task documents were drawn from a previously public learning pool. Not an unseen or independent validation set.'}
    save(out/'tasks.json',tasks)
    save(out/'release.json',release)
    save(out/'build_provenance.json',{'selection':'SHA-256 rank; source-specific disjoint blocks','input_pool_sha256':input_hashes,
        'research_briefs_sha256':sha(args.briefs),'historical_exposure':release['historical_exposure']})


if __name__ == '__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--pool',type=Path,required=True)
    p.add_argument('--processed',type=Path,required=True)
    p.add_argument('--briefs',type=Path,default=Path('benchmark/research_briefs.json'))
    p.add_argument('--output',type=Path,required=True)
    build(p.parse_args())

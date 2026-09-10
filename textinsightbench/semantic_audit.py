"""Bounded semantic auditing; full arithmetic is validated separately."""
import hashlib


def rank(seed, key, doc_id):
    return hashlib.sha256((seed+'\0'+key+'\0'+doc_id).encode()).digest()


def packet(task, rows, submission, seed, budget=160):
    if type(budget) is not int or not 60 <= budget <= 2000:
        raise ValueError('Semantic audit budget must be 60–2000 documents')
    states, cells, evidence, findings = {}, [], set(), []
    for f in submission['findings']:
        evidence.update(e['doc_id'] for e in f['evidence'])
        counts = {}
        for a in f['assignments']:
            key = f['finding_id']+'/'+a['condition_id']
            counts[a['condition_id']] = {}
            for state in ('positive', 'negative', 'unknown'):
                ids = set(a[state+'_doc_ids'])
                states[key, state] = ids
                counts[a['condition_id']][state] = len(ids)
                if ids:
                    cells.append((key+'/'+state, ids))
        findings.append({**{k:v for k,v in f.items() if k != 'assignments'}, 'assignment_counts': counts})
    if len(evidence) > budget//2:
        raise ValueError('Too many participant-selected evidence documents for an independent audit sample')
    chosen = set(evidence)
    quota = max(1, (budget-len(chosen))//(2*max(1,len(cells))))
    for key, ids in cells:
        chosen.update(sorted(ids, key=lambda i: rank(seed,key,i))[:quota])
    remaining = sorted((r['doc_id'] for r in rows if r['doc_id'] not in chosen),
                       key=lambda i: rank(seed,task['task_id'],i))
    chosen.update(remaining[:max(0,budget-len(chosen))])
    keys = sorted({key for key,_state in states})
    documents = []
    for row in rows:
        if row['doc_id'] in chosen:
            labels = {key:next((s for s in ('positive','negative','unknown') if row['doc_id'] in states[key,s]),
                             'outside_selected_population') for key in keys}
            documents.append({**row, 'participant_assignments': labels,
                              'participant_evidence': row['doc_id'] in evidence})
    return {'task':task, 'documents':documents,
            'submission':{**submission,'findings':findings},
            'semantic_audit':{'method':'stratified_assignment_and_corpus_sample',
                              'corpus_documents':len(rows),'sample_documents':len(documents),
                              'participant_evidence_documents':len(evidence),
                              'full_arithmetic_verified':True,'exhaustive_semantic_verification':False}}

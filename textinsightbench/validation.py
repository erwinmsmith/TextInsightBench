#!/usr/bin/env python3
"""Standalone participant-side structural, evidence and arithmetic validator."""
import argparse,datetime,gzip,json,math
from pathlib import Path

def need(ok,msg):
    if not ok:raise ValueError(msg)

def rows(path):
    opener=gzip.open if path.suffix=='.gz' else open
    with opener(path,'rt',encoding='utf-8') as f:return [json.loads(line) for line in f if line.strip()]

def groups(task,data):
    if task['kind']=='temporal_change':
        def day(value):
            try:return datetime.date.fromisoformat(value[:10])
            except (ValueError,TypeError):return None
        cutoff=day(task['comparison']['cutoff']);need(cutoff is not None,'invalid cutoff')
        return [{r['doc_id'] for r in data if day(r.get('timestamp')) is not None and (day(r['timestamp'])<cutoff)==before} for before in (True,False)]
    need(task['kind']=='group_difference','groups apply only to difference/time tasks')
    values=task['comparison']['groups'];need(len(values)==2 and values[0]!=values[1],'distinct groups required')
    return [{r['doc_id'] for r in data if r.get(task['comparison']['field'])==v} for v in values]

def base_expected(f,task,data):
    a={x['condition_id']:x for x in f['assignments']};defs=f['definitions']
    if task['kind']!='compound_association':
        x=a[defs[0]['condition_id']];pos=set(x['positive_doc_ids']);unknown=set(x['unknown_doc_ids']);out={};bounds=[];rates=[];gs=groups(task,data)
        for i,g in enumerate(gs):
            n=len(g);p=len(g&pos);u=len(g&unknown);known=n-u;rate=p/known if known else None;rates.append(rate);bounds.append((p/n,(p+u)/n) if n else (None,None))
            out.update({f'group{i}_total_n':n,f'group{i}_known_n':known,f'group{i}_positive_n':p,f'group{i}_unknown_n':u,f'group{i}_rate_known':rate})
        out['excluded_metadata_n']=len(data)-len(gs[0]|gs[1]);out['delta_known_pp']=100*(rates[1]-rates[0]) if None not in rates else None
        out['delta_identification_lower_pp']=100*(bounds[1][0]-bounds[0][1]) if all(gs) else None
        out['delta_identification_upper_pp']=100*(bounds[1][1]-bounds[0][0]) if all(gs) else None;return out
    aa,bb=(a[d['condition_id']] for d in defs);ap,an,bp,bn=map(set,(aa['positive_doc_ids'],aa['negative_doc_ids'],bb['positive_doc_ids'],bb['negative_doc_ids']))
    n11,n10,n01,n00=map(len,(ap&bp,ap&bn,an&bp,an&bn));n=n11+n10+n01+n00;p1=n11/(n11+n10) if n11+n10 else None;p0=n01/(n01+n00) if n01+n00 else None
    return {'known_joint_n':n,'unknown_joint_n':len(data)-n,'n11':n11,'n10':n10,'n01':n01,'n00':n00,'p_b_given_a':p1,'p_b_given_not_a':p0,
        'conditional_difference_pp':100*(p1-p0) if None not in (p1,p0) else None,'lift':n11*n/((n11+n10)*(n11+n01)) if (n11+n10)*(n11+n01) else None}

def expected(f,task,data):
    out=base_expected(f,task,data)
    if task.get('difficulty')=='hard':
        from .difficulty import audit
        out.update(audit(f,task,data)[0])
    return out

def validate(sub,task,data):
    need(set(sub)=={'task_id','findings','abstention_reason'} and sub['task_id']==task['task_id'],'invalid submission/task fields')
    need(isinstance(sub['findings'],list) and len(sub['findings'])<=task['max_findings'],'invalid finding count')
    need(isinstance(sub['abstention_reason'],str) and (sub['findings'] or sub['abstention_reason'].strip()),'empty answer')
    universe={r['doc_id'] for r in data};lookup={r['doc_id']:r for r in data};ids=set()
    for f in sub['findings']:
        need(set(f)=={'finding_id','claim','kind','scope','definitions','assignments','statistics','evidence','limitations'},'invalid finding fields')
        need(f['finding_id'] not in ids and f['kind']==task['kind'],'duplicate finding or wrong kind');ids.add(f['finding_id'])
        need(all(isinstance(f[k],str) and f[k].strip() for k in ('finding_id','claim','scope')),'empty finding text')
        want=2 if task['kind']=='compound_association' else 1;need(len(f['definitions'])==len(f['assignments'])==want,'wrong condition count')
        cids=[d['condition_id'] for d in f['definitions']];need(len(cids)==len(set(cids)),'duplicate conditions')
        amap={a['condition_id']:a for a in f['assignments']};need(set(amap)==set(cids),'condition assignments mismatch')
        for a in amap.values():
            parts=[set(a[k]) for k in ('positive_doc_ids','negative_doc_ids','unknown_doc_ids')]
            need(not(parts[0]&parts[1] or parts[0]&parts[2] or parts[1]&parts[2]) and set.union(*parts)==universe,'assignments must partition all documents')
        need(isinstance(f['evidence'],list) and f['evidence'] and any(e['role']=='supporting' for e in f['evidence']),'supporting evidence required')
        for e in f['evidence']:
            need(e['doc_id'] in lookup and e['role'] in ('supporting','counterexample','context'),'bad evidence source/role');text=lookup[e['doc_id']]['text']
            need(type(e['start']) is int and type(e['end']) is int and 0<=e['start']<e['end']<=len(text) and text[e['start']:e['end']]==e['quote'],'evidence quote/offset mismatch')
        exp=expected(f,task,data)
        for k,v in exp.items():
            got=f['statistics'].get(k);need((v is None and got is None) or (type(got) in (int,float) and math.isfinite(got) and abs(got-v)<=1e-6),'statistic mismatch: '+k)
    return {'task_id':task['task_id'],'valid':True,'findings':len(sub['findings'])}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--tasks',type=Path,required=True);p.add_argument('--submission',type=Path,required=True);a=p.parse_args()
    tasks=json.loads(a.tasks.read_text());sub=json.loads(a.submission.read_text());task=next((t for t in tasks if t['task_id']==sub.get('task_id')),None);need(task is not None,'unknown task')
    print(json.dumps(validate(sub,task,rows(a.tasks.parent/task['corpus_path'])),ensure_ascii=False))

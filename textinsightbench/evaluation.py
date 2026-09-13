"""Bound semantic assessments and deterministic, non-exhaustive scoring."""
import math
from collections import defaultdict
from .core import digest, validate_submission
from .difficulty import scoring_version

DIMENSIONS = ('statistical_validity', 'evidence_entailment', 'analytical_depth', 'calibration')


def score(sub, task, rows, reference, review, reference_sha256):
    validate_submission(sub, task, rows)
    binding = {'task_id': task['task_id'], 'submission_sha256': digest(sub),
               'corpus_sha256': task['corpus_sha256'], 'reference_sha256': reference_sha256,
               'scoring_version': scoring_version(task)}
    if task.get('difficulty') in ('hard','discovery'):
        binding['task_sha256'] = digest(task)
    if any(review.get(k) != v for k, v in binding.items()):
        raise ValueError('Review binding mismatch')
    if not isinstance(review.get('reviewer_method'), str) or not review['reviewer_method'].strip():
        raise ValueError('Reviewer method is required')
    findings = review['findings']
    ids = [f['finding_id'] for f in sub['findings']]
    if len(findings) != len(ids) or {r['finding_id'] for r in findings} != set(ids):
        raise ValueError('Assess every submitted finding exactly once')
    by_id = {r['finding_id']: r for r in findings}
    gates={}
    if task.get('difficulty')=='discovery' and ids:
        from .evidence_check import compare
        gates=compare(task,rows,sub,review['blind_check'])
    out, earlier, matched = [], set(), set()
    for fid in ids:
        r = by_id[fid]
        required = {'finding_id', 'support', 'task_fulfilled', 'duplicate_of', 'reference_match', 'rationale', *DIMENSIONS}
        if set(r) != required or r['support'] not in ('supported', 'partial', 'unsupported', 'uncertain'):
            raise ValueError('Invalid finding assessment')
        if type(r['task_fulfilled']) is not bool or not isinstance(r['rationale'], str) or not r['rationale'].strip():
            raise ValueError('Explicit task judgment and rationale required')
        for key in DIMENSIONS:
            value = r[key]
            if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1:
                raise ValueError('Assessment dimensions must be finite numbers between 0 and 1')
        if r['duplicate_of'] is not None and r['duplicate_of'] not in earlier:
            raise ValueError('Duplicates must point to an earlier submitted finding')
        if r['reference_match'] not in (None, reference['reference_id']):
            raise ValueError('Unknown reference match')
        earlier.add(fid)
        effective=r['support']
        if fid in gates:
            from .evidence_check import capped
            effective=capped(effective,gates[fid]['support_cap'])
        factor = {'supported': 1, 'partial': 0.5, 'unsupported': 0, 'uncertain': None}[effective]
        if not r['task_fulfilled'] or r['duplicate_of'] is not None:
            value = 0.0
        elif factor is None:
            value = None
        else:
            base, depth = (15, 30) if task.get('difficulty') in ('hard','discovery') else (35, 10)
            value = factor * (base + 25*r['statistical_validity'] + 20*r['evidence_entailment'] + depth*r['analytical_depth'] + 10*r['calibration'])
        if r['reference_match'] and factor == 1 and r['task_fulfilled'] and r['duplicate_of'] is None:
            matched.add(r['reference_match'])
        out.append({'finding_id': fid, 'score': value, **r, 'effective_support':effective,
                    **({'evidence_gate':gates[fid]} if fid in gates else {})})
    quality = sum(r['score'] for r in out)/len(out) if out and all(r['score'] is not None for r in out) else None
    status = 'abstained' if not out else 'unresolved' if quality is None else 'scored'
    return {**binding, 'status': status, 'findings': out, 'quality': quality,
            'reference_coverage': None if status == 'unresolved' or reference['reference_id'] is None else float(bool(matched)),
            'reviewer_method': review['reviewer_method']}


def aggregate(tasks, records):
    profiles = {t.get('difficulty', 'standard') for t in tasks}
    if len(profiles) != 1:
        raise ValueError('Do not aggregate different difficulty profiles')
    by_id = {r['task_id']: r for r in records}
    if len(by_id) != len(records) or set(by_id) != {t['task_id'] for t in tasks}:
        raise ValueError('Report must explicitly account for every task')
    def summarize(selected):
        rows = [by_id[t['task_id']] for t in selected]
        values = [r['quality'] for r in rows if r.get('quality') is not None]
        coverages = [r['reference_coverage'] for r in rows if r.get('reference_coverage') is not None]
        return {'tasks': len(rows), 'scored_tasks': len(values),
                'quality_mean': sum(values)/len(rows) if len(values) == len(rows) else None,
                'conditional_quality_mean': sum(values)/len(values) if values else None,
                'reference_coverage_mean': sum(coverages)/len(rows) if len(coverages) == len(rows) else None,
                'valid_submission_rate': sum(r['status'] not in ('missing', 'invalid') for r in rows)/len(rows),
                'abstention_rate': sum(r['status'] == 'abstained' for r in rows)/len(rows),
                'pending_tasks': sum(r['status'] in ('pending_review', 'unresolved') for r in rows),
                'missing_tasks': sum(r['status'] == 'missing' for r in rows),
                'invalid_tasks': sum(r['status'] == 'invalid' for r in rows)}
    report = summarize(tasks)
    for axis in ('kind', 'source'):
        groups = defaultdict(list)
        for task in tasks:
            groups[task[axis]].append(task)
        report['by_' + axis] = {name: summarize(group) for name, group in groups.items()}
    report['task_scores'] = records
    report['difficulty'] = next(iter(profiles))
    report['scoring_version'] = scoring_version(tasks[0])
    return report

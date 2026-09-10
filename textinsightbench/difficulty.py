"""Method-neutral difficulty profiles and deterministic robustness audits.

These are sensitivity checks on the supplied corpus, not held-out validation,
causal adjustment, independent observations, or new reference annotations.
"""
import copy
import datetime
from collections import defaultdict

PROFILES = ('standard', 'hard')
AXES = ('entity_id', 'rating', 'report_year')
MIN_KNOWN_PER_ARM = 5


def scoring_version(task):
    return 'finding-quality-robustness' if task.get('difficulty') == 'hard' else 'finding-quality'


def apply_profile(task, difficulty='standard'):
    if difficulty not in PROFILES:
        raise ValueError('Unknown difficulty profile')
    task = copy.deepcopy(task)
    if difficulty == 'standard':
        return task
    task['difficulty'] = 'hard'
    task['max_findings'] = min(task['max_findings'], 3)
    task['robustness_protocol'] = {
        'axes': list(AXES), 'min_known_per_arm': MIN_KNOWN_PER_ARM,
        'checks': ['metadata_stratification', 'leave_largest_stratum_out',
                   'support_concentration', 'counterexamples', 'unknown_sensitivity'],
        'interpretation': 'Finite-corpus sensitivity, not causal adjustment or held-out confirmation.',
    }
    task['question'] = task.get('question', '').replace('at most five', 'at most three') + (
        ' Hard profile: explain whether each discovered contrast survives metadata-stratified '
        'comparison and removal of the largest stratum for entity_id, rating and report_year. '
        'Return all computed robustness statistics; identify the strongest competing composition '
        'explanation and interpret unknowns, support concentration, missing metadata and excluded '
        'strata. An unstable or composition-dependent pattern is a valid finding if accurately '
        'demonstrated; never claim stability when an audit is undefined. Provide supporting quotations '
        'from at least three distinct positive documents and a counterexample quotation when known '
        'negative or discordant cases exist. Generic sentiment, restating supplied group labels, '
        'and unexamined aggregate contrasts do not fulfill this profile. Submit at most three '
        'nonredundant findings or abstain. See the public hard-profile protocol for exact formulas.'
    )
    return task


def bucket(row, axis):
    value = row.get('timestamp') if axis == 'report_year' else row.get(axis)
    if axis == 'report_year':
        try:
            return str(datetime.date.fromisoformat(value[:10]).year)
        except (TypeError, ValueError):
            return None
    if value is None or str(value).strip() == '':
        return None
    return str(value)


def arms(finding, task, data):
    from .validation import groups
    by_id = {a['condition_id']: a for a in finding['assignments']}
    a = by_id[finding['definitions'][0]['condition_id']]
    if task['kind'] != 'compound_association':
        g0, g1 = groups(task, data)
        unknown = set(a['unknown_doc_ids'])
        return g0 - unknown, g1 - unknown, set(a['positive_doc_ids'])
    b = by_id[finding['definitions'][1]['condition_id']]
    known_b = set(b['positive_doc_ids']) | set(b['negative_doc_ids'])
    # Difference is P(B|A) - P(B|not A), matching the base joint table.
    return set(a['negative_doc_ids']) & known_b, set(a['positive_doc_ids']) & known_b, set(b['positive_doc_ids'])


def effect(g0, g1, positive):
    if not g0 or not g1:
        return None
    return 100 * (len(g1 & positive)/len(g1) - len(g0 & positive)/len(g0))


def audit(finding, task, data):
    """Recompute every audit from the submitted assignments and released metadata."""
    g0, g1, positive = arms(finding, task, data)
    universe = {r['doc_id'] for r in data}
    common = {'robustness_known_arm0_n': len(g0), 'robustness_known_arm1_n': len(g1)}
    details = {}
    for axis in AXES:
        partitions = defaultdict(set)
        missing = set()
        for row in data:
            value = bucket(row, axis)
            if value is None:
                missing.add(row['doc_id'])
            else:
                partitions[value].add(row['doc_id'])
        prefix = 'robustness_' + axis + '_'
        comparable = []
        covered_ids = set()
        for name, ids in sorted(partitions.items()):
            n0, n1 = len(g0 & ids), len(g1 & ids)
            if min(n0, n1) >= MIN_KNOWN_PER_ARM:
                covered_ids.update(ids)
                comparable.append({'stratum': name, 'arm0_n': n0, 'arm1_n': n1,
                                   'delta_pp': effect(g0 & ids, g1 & ids, positive)})
        covered = sum(s['arm0_n'] + s['arm1_n'] for s in comparable)
        adjusted = sum((s['arm0_n'] + s['arm1_n']) * s['delta_pp'] for s in comparable)/covered if covered else None
        # Metadata-only selection, independent of effect size. Ties use lexical order.
        largest = min(partitions, key=lambda name: (-len(partitions[name]), name)) if partitions else None
        removed = partitions[largest] if largest is not None else set()
        retained0, retained1 = g0 - removed - missing, g1 - removed - missing
        drop_effect = effect(retained0, retained1, positive) if largest is not None and min(len(retained0), len(retained1)) >= MIN_KNOWN_PER_ARM else None
        support = positive & (g0 | g1)
        known_support = support - missing
        largest_support = max((len(ids & known_support) for ids in partitions.values()), default=0)
        common.update({
            prefix+'strata_n': len(partitions), prefix+'missing_metadata_n': len(missing),
            prefix+'eligible_strata_n': len(comparable), prefix+'covered_known_n': covered,
            prefix+'excluded_known_n': len(g0 | g1)-covered,
            prefix+'standardized_delta_pp': adjusted,
            prefix+'covered_crude_delta_pp': effect(g0 & covered_ids, g1 & covered_ids, positive),
            prefix+'min_stratum_delta_pp': min((s['delta_pp'] for s in comparable), default=None),
            prefix+'max_stratum_delta_pp': max((s['delta_pp'] for s in comparable), default=None),
            prefix+'drop_largest_n': len(removed), prefix+'drop_largest_arm0_n': len(retained0),
            prefix+'drop_largest_arm1_n': len(retained1), prefix+'drop_largest_delta_pp': drop_effect,
            prefix+'support_missing_metadata_n': len(support & missing),
            prefix+'max_support_share': largest_support/len(known_support) if known_support else None,
        })
        details[axis] = {'comparable_strata': comparable, 'removed_stratum': largest,
                         'universe_n': len(universe), 'missing_metadata_n': len(missing)}
    return common, details


def validate_evidence(finding, task):
    if task.get('difficulty') != 'hard':
        return
    by_id = {a['condition_id']: a for a in finding['assignments']}
    assignments = [by_id[d['condition_id']] for d in finding['definitions']]
    positives = [set(a['positive_doc_ids']) for a in assignments]
    support_pool = set.intersection(*positives)
    support = {e['doc_id'] for e in finding['evidence'] if e['role'] == 'supporting'}
    if len(support) < 3 or not support <= support_pool:
        raise ValueError('Hard profile requires supporting quotes from at least three distinct positive documents')
    if len(assignments) == 1:
        counter_pool = set(assignments[0]['negative_doc_ids'])
    else:
        counter_pool = (positives[0] & set(assignments[1]['negative_doc_ids'])) | (positives[1] & set(assignments[0]['negative_doc_ids']))
    counters = {e['doc_id'] for e in finding['evidence'] if e['role'] == 'counterexample'}
    if not counters <= counter_pool or (counter_pool and not counters):
        raise ValueError('Hard profile requires a known negative/discordant counterexample when available')


HARD_JUDGE_INSTRUCTIONS = '''
Hard-profile requirements are substantive, not a keyword checklist. Read the recomputed
robustness_audits as diagnostics of the participant's assignments, not as verified labels.
Task fulfillment requires a concrete pattern plus an explicit, correct interpretation of
stratified effects, removal of the largest metadata stratum, support concentration, unknowns,
missing metadata and counterexamples. Reject a bare aggregate contrast or a restatement of
the supplied group/rating labels. For analytical_depth assess discovery specificity AND
the strongest alternative composition explanation. Use 1 only if each available audit is
interpreted with correct denominators and each unavailable audit is acknowledged; at most
0.5 for material omissions and 0.25 for numerical restatement without analysis. An honest
reversal or instability finding can earn full credit. Undefined adjustment is not stability.
Metadata stratification is not causal adjustment; all checks reuse the same corpus and are
not held-out confirmation. Three supporting quotes are not proof of frequency or entailment.
'''

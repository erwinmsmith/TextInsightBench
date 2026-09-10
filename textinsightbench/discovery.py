"""Agent-selected populations and comparisons for open mining tasks."""
import datetime
import math


def is_discovery(task):
    return task.get('discovery_mode') == 'agent_selected'


def metadata(row, field):
    value = row.get(field)
    if field == 'report_year':
        try:
            return datetime.date.fromisoformat(row['timestamp'][:10]).year
        except (KeyError, TypeError, ValueError):
            return None
    return value


def scalar(value):
    return type(value) in (str, int, float) and (not isinstance(value, float) or math.isfinite(value))


def matches(row, rule):
    value, target, op = metadata(row, rule['field']), rule['value'], rule['op']
    if value is None:
        return False
    if op == 'in':
        return value in target
    if op == 'eq':
        return value == target
    # Do not silently compare a string to a numeric bound.
    if isinstance(value, str) != isinstance(target, str):
        return False
    return value >= target if op == 'gte' else value <= target


def context(finding, task, rows):
    """Validate the declared analysis scope before any denominator is calculated."""
    if not is_discovery(task):
        return task, rows
    if len(finding.get('evidence', [])) > 15:
        raise ValueError('A discovery finding permits at most 15 exact evidence spans')
    fields = set(task['allowed_metadata_fields'])
    population = finding.get('population')
    if not isinstance(population, dict) or set(population) != {'filters'}:
        raise ValueError('Declare population.filters, including an empty list for the entire corpus')
    rules = population['filters']
    if not isinstance(rules, list) or len(rules) > 3:
        raise ValueError('Population uses at most three conjunctive metadata filters')
    for rule in rules:
        if not isinstance(rule, dict) or set(rule) != {'field', 'op', 'value'} or rule['field'] not in fields:
            raise ValueError('Population filters may use only released, allowed metadata')
        if rule['op'] not in ('eq', 'in', 'gte', 'lte'):
            raise ValueError('Unsupported population operator')
        values = rule['value'] if rule['op'] == 'in' else [rule['value']]
        if not isinstance(values, list) or not 1 <= len(values) <= 20 or not all(scalar(v) for v in values):
            raise ValueError('Population values must be finite scalars; membership lists have 1–20 values')
    selected = [r for r in rows if all(matches(r, rule) for rule in rules)]
    if len(selected) < task['min_population_n']:
        raise ValueError('Selected population is smaller than the task minimum')
    comparison = finding.get('comparison')
    resolved = {**task, 'discovery_mode': 'resolved', 'comparison': comparison}
    kind = task['kind']
    if kind == 'compound_association':
        if comparison is not None:
            raise ValueError('Compound association requires comparison=null')
        return resolved, selected
    if not isinstance(comparison, dict):
        raise ValueError('The agent must declare its comparison')
    if kind == 'group_difference':
        if set(comparison) != {'field', 'groups'} or comparison['field'] not in fields - {'timestamp'}:
            raise ValueError('Choose a permitted group-comparison field')
        gs = comparison['groups']
        if not isinstance(gs, list) or len(gs) != 2:
            raise ValueError('Declare two disjoint groups as value lists')
        if any(not isinstance(g, list) or not 1 <= len(g) <= 20 or not all(scalar(v) for v in g) for g in gs):
            raise ValueError('Each comparison group needs 1–20 finite metadata values')
        if any(len(set(g)) != len(g) for g in gs) or set(gs[0]) & set(gs[1]):
            raise ValueError('Comparison values must be unique and disjoint')
        selected = [{**r, '_selected_group': next((i for i, g in enumerate(gs) if metadata(r, comparison['field']) in g), None)} for r in selected]
        resolved['comparison'] = {'field': '_selected_group', 'groups': [0, 1]}
    else:
        if set(comparison) != {'field', 'cutoff'} or comparison['field'] != 'timestamp':
            raise ValueError('Temporal comparisons require field=timestamp and an agent-selected cutoff')
        try:
            date = datetime.date.fromisoformat(comparison['cutoff'])
            if date.isoformat() != comparison['cutoff']:
                raise ValueError('Use YYYY-MM-DD')
        except (ValueError, TypeError):
            raise ValueError('Use an ISO calendar-date cutoff') from None
    from .validation import groups
    gs = groups(resolved, selected)
    if min(map(len, gs)) < task['min_group_n']:
        raise ValueError('Each comparison arm must meet the minimum document count')
    return resolved, selected


JUDGE_INSTRUCTIONS = '''
This is an agent-selected discovery task. The brief supplies a research objective,
not the answer, population, comparison groups or time cutoff. Judge whether the
finding is a specific, useful discovery that addresses that objective. A metadata
frequency, generic sentiment/rating contrast or restatement of the prompt is not
sufficient. Evaluate the chosen scope, omitted groups, alternative explanations,
counterexamples and search/selection bias. No independent validation is required;
never call a same-corpus exploratory result confirmed or causal.
The arithmetic and complete population partitions were checked over all selected
documents. Semantic assignment validity is SAMPLED, not exhaustively verified.
Documents include a mix of randomly audited assignments, full-corpus context and
participant quotations; treat participant-selected evidence as selection-biased.
Assignment states are participant claims, never ground truth. Material sampled
misassignments undermine the counts even when the arithmetic is exact. Use
uncertain when the sample cannot support a quality assessment. Do not infer full
corpus semantic correctness merely from absence of errors in the sample. Unseen
documents and a narrow selection cannot be used to support broad prevalence claims.
Analytical depth requires a substantive discovered relation and a supported account
of competing explanations, not a long description or a checklist of computed numbers.
'''

"""Synthetic robustness traps, type-independent arithmetic and profile isolation."""
import argparse
import copy
import gzip
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from test_evaluation import fixture
from textinsightbench.core import digest, write, file_sha, validate_submission
from textinsightbench.difficulty import apply_profile, audit, scoring_version
from textinsightbench.validation import expected
from textinsightbench.evaluation import score, aggregate
from textinsightbench.cli import judge, evaluate, check_run_profile


def simpson():
    task, _, sub, reference, review = fixture()
    task = apply_profile(task, 'hard')
    # In both entities, b has a lower event rate; pooled b has a higher rate.
    cells = [('easy', 'a', 10, 9), ('easy', 'b', 90, 72),
             ('hard', 'a', 90, 18), ('hard', 'b', 10, 1)]
    rows, positive, negative = [], [], []
    for entity, group, total, count in cells:
        for i in range(total):
            doc_id = str(len(rows))
            text = 'Parts fall off.' if i < count else 'Works normally.'
            rows.append({'doc_id': doc_id, 'entity_id': entity, 'comparison_group': group,
                         'timestamp': '2024-01-01', 'rating': None, 'text': text})
            (positive if i < count else negative).append(doc_id)
    f = sub['findings'][0]
    f['assignments'][0].update(positive_doc_ids=positive, negative_doc_ids=negative, unknown_doc_ids=[])
    f['evidence'] = [{'doc_id': doc_id, 'start': 0, 'end': len(rows[int(doc_id)]['text']),
                      'quote': rows[int(doc_id)]['text'], 'role': role}
                     for role, ids in [('supporting', positive[:3]), ('counterexample', negative[:1])] for doc_id in ids]
    task['n_documents'] = len(rows)
    f['statistics'] = expected(f, task, rows)
    review.update(submission_sha256=digest(sub), task_sha256=digest(task), scoring_version=scoring_version(task))
    return task, rows, sub, reference, review


class DifficultyTests(unittest.TestCase):
    def test_profile_does_not_change_base_or_corpus(self):
        task, _, _, _, _ = fixture()
        original = copy.deepcopy(task)
        hard = apply_profile(task, 'hard')
        self.assertEqual(task, original)
        self.assertEqual(hard['max_findings'], 3)
        self.assertEqual(hard['corpus_sha256'], task['corpus_sha256'])
        self.assertIn('not causal adjustment', hard['robustness_protocol']['interpretation'])
        with self.assertRaises(ValueError): apply_profile(task, 'invented')

    def test_simpson_reversal_is_recomputed(self):
        task, rows, sub, _, _ = simpson()
        stats, details = audit(sub['findings'][0], task, rows)
        self.assertAlmostEqual(sub['findings'][0]['statistics']['delta_known_pp'], 46)
        self.assertAlmostEqual(stats['robustness_entity_id_standardized_delta_pp'], -10)
        self.assertAlmostEqual(stats['robustness_entity_id_covered_crude_delta_pp'], 46)
        self.assertEqual(stats['robustness_entity_id_eligible_strata_n'], 2)
        self.assertEqual(details['entity_id']['removed_stratum'], 'easy')
        self.assertAlmostEqual(stats['robustness_entity_id_drop_largest_delta_pp'], -10)
        validate_submission(sub, task, rows)

    def test_missing_and_single_stratum_are_not_stability(self):
        task, rows, sub, _, _ = simpson()
        stats, _ = audit(sub['findings'][0], task, rows)
        self.assertIsNone(stats['robustness_rating_standardized_delta_pp'])
        self.assertEqual(stats['robustness_rating_missing_metadata_n'], 200)
        self.assertEqual(stats['robustness_report_year_strata_n'], 1)
        self.assertIsNone(stats['robustness_report_year_drop_largest_delta_pp'])

    def test_recomputed_fields_cannot_be_omitted_or_forged(self):
        for change in ('omit', 'forge'):
            task, rows, sub, _, _ = simpson()
            stats = sub['findings'][0]['statistics']
            if change == 'omit': del stats['robustness_entity_id_standardized_delta_pp']
            else: stats['robustness_entity_id_standardized_delta_pp'] = 46
            with self.assertRaises(ValueError): validate_submission(sub, task, rows)

    def test_supporting_evidence_minimum_and_counterexample(self):
        for change in ('few', 'negative_support', 'no_counterexample'):
            task, rows, sub, _, _ = simpson()
            evidence = sub['findings'][0]['evidence']
            if change == 'few': evidence.pop(0)
            elif change == 'negative_support': evidence[-1]['role'] = 'supporting'
            else: evidence.pop()
            with self.assertRaises(ValueError): validate_submission(sub, task, rows)

    def test_compound_audits_use_the_jointly_known_population(self):
        task, rows, sub, _, _ = simpson()
        task['kind'] = 'compound_association'
        f = sub['findings'][0]; f['kind'] = task['kind']
        f['definitions'].append({'condition_id': 'b', 'inclusion': 'B', 'exclusion': 'Not B'})
        f['assignments'].append({'condition_id': 'b', 'positive_doc_ids': ['0', '1', '2'],
            'negative_doc_ids': [str(i) for i in range(3, 190)], 'unknown_doc_ids': [str(i) for i in range(190, 200)]})
        stats, _ = audit(f, task, rows)
        self.assertEqual(stats['robustness_known_arm0_n'] + stats['robustness_known_arm1_n'], 190)
        f['statistics'] = expected(f, task, rows)
        self.assertAlmostEqual(f['statistics']['conditional_difference_pp'], stats['robustness_report_year_covered_crude_delta_pp'])

    def test_hard_reviews_cannot_reuse_standard_scores_or_modified_tasks(self):
        task, rows, sub, reference, review = simpson()
        self.assertEqual(score(sub, task, rows, reference, review, 'refhash')['quality'], 83)
        review['scoring_version'] = 'finding-quality'
        with self.assertRaises(ValueError): score(sub, task, rows, reference, review, 'refhash')
        review['scoring_version'] = scoring_version(task)
        task['question'] += ' Changed.'
        with self.assertRaises(ValueError): score(sub, task, rows, reference, review, 'refhash')

    def test_profiles_do_not_mix(self):
        task, _, _, _, _ = simpson()
        with self.assertRaises(ValueError): aggregate([task, fixture()[0]], [])
        with tempfile.TemporaryDirectory() as tmp:
            write(Path(tmp)/'run.json', {'difficulty': 'hard'})
            with self.assertRaises(ValueError): check_run_profile(tmp, 'standard')

    def test_hard_judge_receives_audits_but_not_references(self):
        hard, rows, sub, ref, review = simpson()
        task = fixture()[0]; task['n_documents'] = len(rows)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); corpus = root/task['corpus_path']; corpus.parent.mkdir()
            with gzip.open(corpus, 'wt') as f:
                for row in rows: f.write(json.dumps(row)+'\n')
            task['corpus_sha256'] = file_sha(corpus)
            write(root/'tasks.json', [task]); write(root/'release.json', {'version': 'synthetic'})
            write(root/'references.json', {'benchmark_version': 'synthetic', 'tasks_sha256': file_sha(root/'tasks.json'), 'tasks': [ref]})
            write(root/'submissions/synthetic.json', sub)
            calls = []
            def request(args, system, payload):
                calls.append(payload)
                if 'documents' in payload:
                    self.assertNotIn('reference', payload)
                    self.assertIn('robustness_audits', payload)
                    self.assertIn('not held-out confirmation', system)
                    return {'findings': review['findings']}, {'model': 'synthetic'}
                return {'matches': [{'finding_id': 'f1', 'reference_match': None}]}, {'model': 'synthetic'}
            args = argparse.Namespace(data=root, submissions=root/'submissions', references=root/'references.json', output=root/'reviews',
                model='synthetic', base_url='https://synthetic.invalid/v1', max_output_tokens=1000, max_input_chars=100000,
                task_id=None, limit=None, difficulty='hard')
            with patch('textinsightbench.cli.request_json', side_effect=request): judge(args)
            self.assertEqual(len(calls), 2)
            with patch('textinsightbench.cli.request_json', side_effect=AssertionError('Resume must not call API')): judge(args)
            args.reviews = root/'reviews'; args.output = root/'report.json'; evaluate(args)
            result = json.loads(args.output.read_text())
            self.assertEqual(result['difficulty'], 'hard')
            self.assertEqual(result['quality_mean'], 83)

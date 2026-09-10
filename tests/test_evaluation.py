"""Synthetic contract fixtures; no released task answers or model calls."""
import argparse
import copy
import gzip
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from jsonschema import ValidationError
from textinsightbench.core import digest, write, file_sha, validate_submission, load_references
from textinsightbench.validation import expected, groups
from textinsightbench.evaluation import score, aggregate
from textinsightbench.cli import judge, evaluate


def fixture():
    task = {'task_id': 'synthetic', 'source': 'synthetic', 'kind': 'group_difference',
        'comparison': {'field': 'comparison_group', 'groups': ['a', 'b']},
        'max_findings': 5, 'n_documents': 4, 'corpus_path': 'corpora/synthetic.jsonl.gz', 'corpus_sha256': 'fixture'}
    rows = [{'doc_id': str(i), 'text': 'Parts fall off.' if i == 2 else 'Works normally.',
             'comparison_group': 'a' if i < 2 else 'b'} for i in range(4)]
    finding = {'finding_id': 'f1', 'claim': 'Reports of detached parts occur more often in group b in this corpus.',
        'kind': task['kind'], 'scope': 'Four synthetic documents.',
        'definitions': [{'condition_id': 'parts', 'inclusion': 'Actual reported parts detaching.', 'exclusion': 'Hypothetical concerns.'}],
        'assignments': [{'condition_id': 'parts', 'positive_doc_ids': ['2'], 'negative_doc_ids': ['0', '1'], 'unknown_doc_ids': ['3']}],
        'statistics': {}, 'evidence': [{'doc_id': '2', 'start': 0, 'end': 15, 'quote': 'Parts fall off.', 'role': 'supporting'}],
        'limitations': ['Synthetic examples; finite-corpus description only.']}
    finding['statistics'] = expected(finding, task, rows)
    sub = {'task_id': task['task_id'], 'findings': [finding], 'abstention_reason': ''}
    reference = {'task_id': task['task_id'], 'reference_id': 'ref', 'claim': finding['claim'],
                 'expected_direction': 'positive', 'specification': {'scope': 'synthetic'}}
    review = {'task_id': task['task_id'], 'submission_sha256': digest(sub), 'corpus_sha256': task['corpus_sha256'],
        'reference_sha256': 'refhash', 'scoring_version': 'finding-quality-v1', 'reviewer_method': 'synthetic fixture',
        'findings': [{'finding_id': 'f1', 'support': 'supported', 'task_fulfilled': True, 'statistical_validity': 0.8,
            'evidence_entailment': 0.9, 'analytical_depth': 0.7, 'calibration': 0.9,
            'duplicate_of': None, 'reference_match': None, 'rationale': 'Synthetic scoring fixture.'}]}
    return task, rows, sub, reference, review


class EvaluationTests(unittest.TestCase):
    def test_supported_novel_finding_scores_89_without_coverage(self):
        t, rows, sub, ref, review = fixture()
        result = score(sub, t, rows, ref, review, 'refhash')
        self.assertEqual(result['quality'], 89)
        self.assertEqual(result['reference_coverage'], 0)

    def test_match_and_partial_support(self):
        t, rows, sub, ref, review = fixture()
        review['findings'][0]['reference_match'] = 'ref'
        self.assertEqual(score(sub, t, rows, ref, review, 'refhash')['reference_coverage'], 1)
        review['findings'][0]['support'] = 'partial'
        result = score(sub, t, rows, ref, review, 'refhash')
        self.assertEqual(result['quality'], 44.5)
        self.assertEqual(result['reference_coverage'], 0)

    def test_incomplete_partition_and_duplicate_ids_rejected(self):
        t, rows, sub, _, _ = fixture()
        sub['findings'][0]['assignments'][0]['negative_doc_ids'].pop()
        with self.assertRaises(ValueError): validate_submission(sub, t, rows)
        t, rows, sub, _, _ = fixture()
        sub['findings'][0]['assignments'][0]['positive_doc_ids'].append('2')
        with self.assertRaises(ValidationError): validate_submission(sub, t, rows)

    def test_false_quote_and_false_statistic_rejected(self):
        for field in ('quote', 'statistics'):
            t, rows, sub, _, _ = fixture()
            if field == 'quote': sub['findings'][0]['evidence'][0]['quote'] = 'Fabricated text'
            else: sub['findings'][0]['statistics']['group0_total_n'] = 999
            with self.assertRaises(ValueError): validate_submission(sub, t, rows)

    def test_unknown_bounds(self):
        _, _, sub, _, _ = fixture()
        s = sub['findings'][0]['statistics']
        self.assertEqual(s['group1_known_n'], 1)
        self.assertEqual(s['delta_identification_lower_pp'], 50)
        self.assertEqual(s['delta_identification_upper_pp'], 100)

    def test_uncertain_is_null(self):
        t, rows, sub, ref, review = fixture()
        review['findings'][0]['support'] = 'uncertain'
        self.assertIsNone(score(sub, t, rows, ref, review, 'refhash')['quality'])

    def test_changed_submission_and_reference_rejected(self):
        t, rows, sub, ref, review = fixture()
        with self.assertRaises(ValueError): score(sub, t, rows, ref, review, 'other-reference')
        sub['findings'][0]['claim'] += ' Changed.'
        with self.assertRaises(ValueError): score(sub, t, rows, ref, review, 'refhash')

    def test_duplicate_zero_lowers_task_mean(self):
        t, rows, sub, ref, review = fixture()
        f = copy.deepcopy(sub['findings'][0]);f['finding_id'] = 'f2';sub['findings'].append(f)
        r = copy.deepcopy(review['findings'][0]);r.update(finding_id='f2', duplicate_of='f1');review['findings'].append(r)
        review['submission_sha256'] = digest(sub)
        self.assertEqual(score(sub, t, rows, ref, review, 'refhash')['quality'], 44.5)

    def test_temporal_bad_date_excluded(self):
        t, rows, _, _, _ = fixture()
        t['kind'] = 'temporal_change';t['comparison'] = {'cutoff': '2020-01-01'}
        for row, date in zip(rows, ['2019-12-31', '2020-01-01', '2020-99-99', None]): row['timestamp'] = date
        self.assertEqual(groups(t, rows), [{'0'}, {'1'}])

    def test_compound_joint_table(self):
        t, rows, sub, _, _ = fixture();t['kind'] = 'compound_association'
        f = sub['findings'][0];f['kind'] = t['kind']
        f['definitions'].append({'condition_id': 'b', 'inclusion': 'B', 'exclusion': 'Not B'})
        f['assignments'].append({'condition_id': 'b', 'positive_doc_ids': ['2', '0'], 'negative_doc_ids': ['1', '3'], 'unknown_doc_ids': []})
        f['statistics'] = expected(f, t, rows)
        validate_submission(sub, t, rows)
        self.assertEqual([f['statistics'][k] for k in ('n11', 'n10', 'n01', 'n00')], [1, 0, 1, 1])
        self.assertEqual(f['statistics']['unknown_joint_n'], 1)

    def test_missing_task_does_not_become_zero(self):
        t, _, _, _, _ = fixture()
        result = aggregate([t], [{'task_id': t['task_id'], 'status': 'missing', 'quality': None, 'reference_coverage': None}])
        self.assertIsNone(result['quality_mean'])
        self.assertEqual(result['missing_tasks'], 1)

    def test_mock_judge_to_report_and_no_reference_in_quality_input(self):
        t, rows, sub, ref, review = fixture()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp);corpus = root / t['corpus_path'];corpus.parent.mkdir()
            with gzip.open(corpus, 'wt') as f:
                for row in rows: f.write(json.dumps(row) + '\n')
            t['corpus_sha256'] = file_sha(corpus)
            write(root / 'tasks.json', [t]);write(root / 'release.json', {'version': 'synthetic'})
            write(root / 'references.json', {'benchmark_version': 'synthetic', 'tasks_sha256': file_sha(root/'tasks.json'), 'tasks': [ref]})
            write(root / 'submissions/synthetic.json', sub)
            calls = []
            def fake_request(args, system, payload):
                calls.append(payload)
                if 'documents' in payload:
                    self.assertNotIn('reference', payload)
                    self.assertEqual(len(payload['documents']), 4)
                    return {'findings': review['findings']}, {'model': 'synthetic', 'usage': None}
                return {'matches': [{'finding_id': 'f1', 'reference_match': 'ref'}]}, {'model': 'synthetic', 'usage': None}
            args = argparse.Namespace(data=root, submissions=root/'submissions', references=root/'references.json', output=root/'reviews',
                model='synthetic', base_url='https://synthetic.invalid/v1', max_output_tokens=1000, max_input_chars=100000, task_id=None, limit=None)
            with patch('textinsightbench.cli.request_json', side_effect=fake_request): judge(args)
            self.assertEqual(len(calls), 2)
            with patch('textinsightbench.cli.request_json', side_effect=AssertionError('Resume must not call API')): judge(args)
            args.reviews = root/'reviews';args.output = root/'report.json';evaluate(args)
            report = json.loads(args.output.read_text())
            self.assertEqual(report['quality_mean'], 89)
            self.assertEqual(report['reference_coverage_mean'], 1)


if __name__ == '__main__':
    unittest.main()

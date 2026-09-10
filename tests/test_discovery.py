import copy
import argparse
import gzip
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from test_difficulty import simpson
from textinsightbench.core import digest, validate_submission, write, file_sha
from textinsightbench.cli import judge, evaluate
from textinsightbench.discovery import context
from textinsightbench.validation import expected
from textinsightbench.difficulty import apply_profile, scoring_version
from textinsightbench.evaluation import score
from textinsightbench.semantic_audit import packet


def discovery():
    task, rows, sub, ref, review = simpson()
    task.update(difficulty='discovery', discovery_mode='agent_selected',
                allowed_metadata_fields=['comparison_group','entity_id','timestamp','report_year'],
                min_population_n=100,min_group_n=20)
    task.pop('comparison')
    f=sub['findings'][0]
    f.update(population={'filters':[]},comparison={'field':'comparison_group','groups':[['a'],['b']]})
    f['statistics']=expected(f,task,rows)
    review.update(submission_sha256=digest(sub),task_sha256=digest(task),scoring_version=scoring_version(task))
    review['findings'][0]['reference_match']=None
    ref['reference_id']=None
    return task,rows,sub,ref,review


class DiscoveryTests(unittest.TestCase):
    def test_full_contract_and_no_fictitious_reference_coverage(self):
        task,rows,sub,ref,review=discovery()
        validate_submission(sub,task,rows)
        self.assertEqual(sub['findings'][0]['statistics']['population_coverage'],1)
        self.assertIsNone(score(sub,task,rows,ref,review,'refhash')['reference_coverage'])
        self.assertEqual(apply_profile(task),task)
        with self.assertRaises(ValueError): apply_profile(task,'hard')

    def test_illegal_selection_and_small_arms(self):
        for change in ('text','overlap','small','missing'):
            task,rows,sub,_,_=discovery();f=sub['findings'][0]
            if change=='text': f['population']['filters']=[{'field':'text','op':'eq','value':'Parts fall off.'}]
            if change=='overlap': f['comparison']['groups']=[['a'],['a','b']]
            if change=='small': f['comparison']['groups']=[['a'],['absent']]
            if change=='missing': del f['population']
            with self.assertRaises(ValueError): context(f,task,rows)

    def test_population_partition_must_be_exact(self):
        task,rows,sub,_,_=discovery();f=sub['findings'][0]
        task['min_group_n']=5
        f['population']['filters']=[{'field':'entity_id','op':'eq','value':'easy'}]
        f['statistics']=expected(f,task,rows)
        self.assertEqual(f['statistics']['population_total_n'],100)
        with self.assertRaises(ValueError): validate_submission(sub,task,rows)

    def test_date_cutoff_and_missing_metadata(self):
        task,rows,sub,_,_=discovery();f=sub['findings'][0]
        task['kind']=f['kind']='temporal_change'
        f['comparison']={'field':'timestamp','cutoff':'2024-01-01'}
        for r in rows[:100]: r['timestamp']='2023-12-31'
        f['statistics']=expected(f,task,rows)
        self.assertEqual(f['statistics']['group0_total_n'],100)
        validate_submission(sub,task,rows)
        f['comparison']['cutoff']='2024-02-30'
        with self.assertRaises(ValueError): context(f,task,rows)

    def test_sample_is_bounded_reproducible_and_not_full_verification(self):
        task,rows,sub,_,_=discovery()
        audit=packet(task,rows,sub,'seed',60)
        self.assertEqual(audit,packet(task,rows,sub,'seed',60))
        self.assertEqual(len(audit['documents']),60)
        self.assertNotIn('assignments',audit['submission']['findings'][0])
        self.assertFalse(audit['semantic_audit']['exhaustive_semantic_verification'])
        included={r['doc_id'] for r in audit['documents']}
        self.assertTrue({e['doc_id'] for e in sub['findings'][0]['evidence']}<=included)
        self.assertNotEqual(included,{r['doc_id'] for r in packet(task,rows,sub,'other',60)['documents']})

    def test_all_three_findings_fit_default_audit(self):
        task,rows,sub,_,_=discovery()
        for i in range(2):
            f=copy.deepcopy(sub['findings'][0]);f['finding_id']='extra'+str(i)
            sub['findings'].append(f)
        self.assertLessEqual(len(packet(task,rows,sub,'seed')['documents']),160)

    def test_current_judge_without_references_and_resume(self):
        task,rows,sub,_,review=discovery()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);corpus=root/task['corpus_path'];corpus.parent.mkdir()
            with gzip.open(corpus,'wt') as stream:
                for row in rows: stream.write(json.dumps(row)+'\n')
            task['corpus_sha256']=file_sha(corpus)
            write(root/'tasks.json',[task]);write(root/'release.json',{'version':'synthetic'})
            write(root/'submissions/synthetic.json',sub)
            write(root/'submissions/run.json',{'difficulty':'discovery'})
            def request(args,system,payload):
                self.assertIn('Semantic assignment validity is SAMPLED',system)
                self.assertNotIn('reference',payload)
                self.assertNotIn('assignments',payload['submission']['findings'][0])
                self.assertEqual(len(payload['documents']),60)
                self.assertIn('robustness_audits',payload)
                return {'findings':review['findings']},{'model':'synthetic'}
            args=argparse.Namespace(data=root,submissions=root/'submissions',references=None,
                output=root/'reviews',model='synthetic',base_url='https://synthetic.invalid',
                max_output_tokens=1000,max_input_chars=100000,task_id=None,limit=None,audit_documents=60)
            with patch('textinsightbench.cli.request_json',side_effect=request) as mock:
                judge(args);self.assertEqual(mock.call_count,1)
            with patch('textinsightbench.cli.request_json',side_effect=AssertionError('No repeated API call')):
                judge(args)
            args.reviews=root/'reviews';args.output=root/'report.json';evaluate(args)
            result=json.loads(args.output.read_text())
            self.assertEqual(result['difficulty'],'discovery')
            self.assertEqual(result['quality_mean'],83)
            self.assertIsNone(result['reference_coverage_mean'])

"""Publication checks: reusable cards and immutable corpus."""
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('packaging_script', ROOT / 'scripts/package_benchmark.py')
package = importlib.util.module_from_spec(spec)
spec.loader.exec_module(package)


class PublicationTests(unittest.TestCase):
    def test_refresh_preserves_inputs_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data, evaluation, repo = (root / name for name in ('data', 'evaluation', 'repo'))
            for folder in (data, evaluation, repo / 'benchmark', repo / 'textinsightbench'):
                folder.mkdir(parents=True)
            shutil.copytree(ROOT / 'templates', repo / 'templates')
            shutil.copytree(ROOT / 'docs', repo / 'docs')
            shutil.copy2(ROOT / 'textinsightbench/output.schema.json', repo / 'textinsightbench/output.schema.json')
            (data / 'corpora').mkdir()
            corpus = data / 'corpora/fixture.jsonl.gz'
            corpus.write_bytes(b'opaque corpus bytes: do not rebuild')
            package.save(data / 'tasks.json', [{'task_id': 'fixture'}])
            package.save(data / 'release.json', {
                'tasks': 1, 'evaluation_documents': 5000, 'learning_documents': 17,
                'task_family_counts': {'group_difference': 1},
                'learning_by_source': {'app_reviews': 17},
                'historical_exposure': 'Previously public.'
            })
            package.save(evaluation / 'references.json', {
                'tasks_sha256': package.sha(data / 'tasks.json'),
                'tasks': [{'task_id': 'fixture', 'reference_id': None}]
            })
            originals = {p: p.read_bytes() for p in (corpus, data / 'tasks.json', evaluation / 'references.json')}
            package.refresh(data, evaluation, repo)
            manifests = [data / 'manifest.json', evaluation / 'manifest.json']
            first = [p.read_bytes() for p in manifests]
            package.refresh(data, evaluation, repo)
            self.assertEqual(first, [p.read_bytes() for p in manifests])
            for path, contents in originals.items():
                self.assertEqual(path.read_bytes(), contents)
            for folder in (data, evaluation):
                for name, record in json.loads((folder / 'manifest.json').read_text())['files'].items():
                    self.assertEqual(package.sha(folder / name), record['sha256'])
                self.assertNotIn('{{TASKS}}', (folder / 'README.md').read_text())
                self.assertEqual(json.loads((folder / 'release.json').read_text())['scoring_version'], package.SCORING)


if __name__ == '__main__':
    unittest.main()

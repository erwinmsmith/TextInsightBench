"""Package data or refresh public pages without rebuilding task corpora."""
import argparse
import json
import shutil
from pathlib import Path

from textinsightbench.core import file_sha as sha

SCORING = 'finding-quality-discovery-evidence'


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def refresh(data, evaluation, repo):
    release = json.loads((data / 'release.json').read_text())
    tasks = json.loads((data / 'tasks.json').read_text())
    refs = json.loads((evaluation / 'references.json').read_text())
    if refs['tasks_sha256'] != sha(data / 'tasks.json'):
        raise ValueError('Evaluation assets do not match the task inventory')
    if len(tasks) != release['tasks']:
        raise ValueError('Task count mismatch')
    release['scoring_version'] = SCORING
    save(data / 'release.json', release)
    protocol = {
        'version': 'textinsightbench',
        'evaluation_unit': 'evidence-backed downstream finding',
        'discovery_mode': 'agent_selected', 'scoring_version': SCORING,
        'task_families': release['task_family_counts'],
        'tracks': {'task_only': 'Use the supplied task corpus.',
                   'unlabeled_pool': 'Learn from the released pool before evaluation.'},
        'reference_policy': 'No fixed reference conclusions; score against corpus evidence and the public rubric.',
        'semantic_review': 'Sampled claim-blind document checks cap narrative quality; exhaustive arithmetic, sampled semantic verification.',
        'independent_validation': False,
        'historical_exposure': release['historical_exposure'],
        'cross_task_adaptation': 'Freeze global prompts, learned parameters and thresholds; no evaluation-feedback transfer.',
        'security': 'Untrusted corpus content. Process runner is not a sandbox.'
    }
    save(data / 'protocol.json', protocol)
    save(evaluation / 'protocol.json', protocol)
    save(evaluation / 'release.json', {
        'version': 'textinsightbench', 'benchmark_version': 'textinsightbench',
        'tasks': len(tasks),
        'references': sum(r.get('reference_id') is not None for r in refs['tasks']),
        'references_sha256': sha(evaluation / 'references.json'),
        'tasks_sha256': sha(data / 'tasks.json'), 'scoring_version': SCORING
    })
    for name in ('tasks.json', 'release.json', 'protocol.json'):
        shutil.copy2(data / name, repo / 'benchmark' / name)
    shutil.copy2(repo / 'textinsightbench/output.schema.json', data / 'output.schema.json')
    for root in (data, evaluation):
        shutil.copytree(repo / 'docs', root / 'docs', dirs_exist_ok=True)
        if (repo / 'results').exists():
            shutil.copytree(repo / 'results', root / 'results', dirs_exist_ok=True)
        shutil.copy2(repo / 'docs/SOURCES.md', root / 'SOURCES.md')
    # Keep existing external links usable while docs/ is the canonical layout.
    for name in ('SCORING.md', 'DIFFICULTY.md', 'ORGANIZER.md'):
        (evaluation / name).write_text(f'# TextInsightBench\n\nSee [{name}](docs/{name}).\n')
    replacements = {
        '{{TASKS}}': f"{len(tasks):,}",
        '{{TASK_DOCUMENTS}}': f"{release['evaluation_documents']:,}",
        '{{LEARNING_DOCUMENTS}}': f"{release['learning_documents']:,}"
    }
    for kind, root in (('dataset', data), ('evaluation', evaluation)):
        for language in ('README.md', 'README.zh-CN.md'):
            body = (repo / 'templates' / f'{kind}.{language}').read_text()
            for key, value in replacements.items():
                body = body.replace(key, value)
            if language == 'README.md':
                title = 'TextInsightBench' + (' Evaluation Assets' if kind == 'evaluation' else '')
                repo_id = 'TextInsightBench' + ('-Evaluation' if kind == 'evaluation' else '')
                header = (
                    f'---\npretty_name: {title}\nlanguage:\n- en\nlicense: other\n'
                    'license_name: upstream-source-terms\n'
                    f'license_link: https://huggingface.co/datasets/CodeSoulco/{repo_id}/blob/main/SOURCES.md\n'
                    'tags:\n- agent-evaluation\n- data-mining\n- evidence-grounding\n'
                )
                if kind == 'dataset':
                    header += 'size_categories:\n- 1M<n<10M\ntask_categories:\n- text-generation\nconfigs:\n'
                    for source in release['learning_by_source']:
                        header += f'- config_name: {source}_learning\n  data_files:\n  - split: train\n    path: learning/{source}/*.parquet\n'
                body = header + '---\n\n' + body
            (root / language).write_text(body)
        save(root / 'manifest.json', {'files': {
            str(p.relative_to(root)): {'sha256': sha(p), 'bytes': p.stat().st_size}
            for p in sorted(root.rglob('*'))
            if p.is_file() and p.name != 'manifest.json' and '.cache' not in p.parts
        }})


def package(data, evaluation, repo):
    if evaluation.exists():
        raise ValueError('Evaluation output must be a new directory; use --refresh for documentation updates')
    evaluation.mkdir(parents=True)
    tasks = json.loads((data / 'tasks.json').read_text())
    save(evaluation / 'references.json', {
        'benchmark_version': 'textinsightbench',
        'tasks_sha256': sha(data / 'tasks.json'),
        'reference_policy': 'No fixed reference conclusions; score against corpus evidence and the public rubric.',
        'tasks': [{'task_id': t['task_id'], 'reference_id': None, 'status': 'no_fixed_reference'} for t in tasks]
    })
    refresh(data, evaluation, repo)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', type=Path, required=True)
    parser.add_argument('--evaluation', type=Path, required=True)
    parser.add_argument('--repo', type=Path, default=Path('.'))
    parser.add_argument('--refresh', action='store_true', help='Refresh cards, docs and metadata without changing corpus or reference contents')
    args = parser.parse_args()
    (refresh if args.refresh else package)(args.data, args.evaluation, args.repo)

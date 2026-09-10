import gzip
import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator
from .validation import expected, validate
from .difficulty import validate_evidence


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'), parse_constant=lambda s: (_ for _ in ()).throw(ValueError('Non-finite JSON: ' + s)))


def write(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')


def digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def file_sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def load_tasks(root):
    tasks = read(Path(root) / 'tasks.json')
    if not tasks or len({t['task_id'] for t in tasks}) != len(tasks):
        raise ValueError('A nonempty unique task inventory is required')
    return tasks


def load_corpus(root, task):
    root = Path(root).resolve()
    path = (root / task['corpus_path']).resolve()
    if not path.is_relative_to(root) or file_sha(path) != task['corpus_sha256']:
        raise ValueError('Corpus path or checksum mismatch')
    with gzip.open(path, 'rt', encoding='utf-8') as f:
        rows = [json.loads(line) for line in f if line.strip()]
    if len(rows) != task['n_documents'] or len({r['doc_id'] for r in rows}) != len(rows):
        raise ValueError('Corpus count or document ID mismatch')
    return rows


def validate_submission(sub, task, rows):
    schema = read(Path(__file__).with_name('output.schema.json'))
    Draft202012Validator(schema).validate(sub)
    validate(sub, task, rows)
    for f in sub['findings']:
        validate_evidence(f, task)
        if set(f['statistics']) != set(expected(f, task, rows)):
            raise ValueError('Statistics must contain exactly the documented computed fields')
        spans = [(e['doc_id'], e['start'], e['end']) for e in f['evidence']]
        if len(spans) != len(set(spans)):
            raise ValueError('Duplicate evidence span')
    return {'task_id': task['task_id'], 'valid': True, 'findings': len(sub['findings']),
            'submission_sha256': digest(sub), 'corpus_sha256': task['corpus_sha256']}


def load_references(path, root):
    refs = read(path)
    if refs['benchmark_version'] != read(Path(root) / 'release.json')['version']:
        raise ValueError('Reference benchmark version mismatch')
    if refs['tasks_sha256'] != file_sha(Path(root) / 'tasks.json'):
        raise ValueError('References belong to a different task inventory')
    index = {r['task_id']: r for r in refs['tasks']}
    if len(index) != len(refs['tasks']) or set(index) != {t['task_id'] for t in load_tasks(root)}:
        raise ValueError('Reference task coverage mismatch')
    return refs, index

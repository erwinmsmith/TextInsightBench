"""Offline integration smoke test, not a competitive baseline."""
import json
import sys

request = json.load(sys.stdin)
print(json.dumps({'task_id': request['task']['task_id'], 'findings': [],
                  'abstention_reason': 'Integration smoke test; no mining was performed.'}))

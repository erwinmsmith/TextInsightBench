"""Inspect or publish the prepared snapshot to the existing public repositories.

No repository is created. Obsolete files are resolved explicitly and remain
recoverable in repository history. The lock is updated only after both commits.
"""
import argparse
import json
from pathlib import Path
from huggingface_hub import HfApi


def publish(args):
    api=HfApi()
    lock_path=args.repo/'benchmark/data.lock.json'
    lock=json.loads(lock_path.read_text())
    plans=[]
    for key,folder in [('dataset',args.data),('evaluation',args.evaluation)]:
        manifest=json.loads((folder/'manifest.json').read_text())
        local=set(manifest['files'])|{'manifest.json'}
        from textinsightbench.core import file_sha as sha
        for name,record in manifest['files'].items():
            if sha(folder/name)!=record['sha256']:
                raise ValueError('Prepared manifest mismatch: '+name)
        repo_id=lock[key]['repo_id'];info=api.dataset_info(repo_id)
        if info.private:
            raise ValueError('Expected the existing public repository')
        remote=set(api.list_repo_files(repo_id,repo_type='dataset',revision=info.sha))
        obsolete=sorted(remote-local-{'.gitattributes'})
        if any(not name.startswith('corpora/') for name in obsolete):
            raise ValueError('Unexpected obsolete files require explicit inspection: '+repr(obsolete))
        plans.append((key,folder,repo_id,info.sha,obsolete))
        print(json.dumps({'repo_id':repo_id,'parent_commit':info.sha,'files':len(local),
                          'remove_obsolete_corpora':obsolete,'publish':args.publish}),flush=True)
    if not args.publish:
        return
    for key,folder,repo_id,parent,obsolete in plans:
        commit=api.upload_folder(repo_id=repo_id,repo_type='dataset',folder_path=folder,
            ignore_patterns=['.cache/**'],delete_patterns=obsolete,parent_commit=parent,
            commit_message='Sync benchmark documentation, evaluation protocol and results')
        lock[key]['revision']=commit.oid
        print(json.dumps({'repo_id':repo_id,'revision':commit.oid}),flush=True)
    lock_path.write_text(json.dumps(lock,indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--data',type=Path,required=True)
    p.add_argument('--evaluation',type=Path,required=True)
    p.add_argument('--repo',type=Path,default=Path('.'))
    p.add_argument('--publish',action='store_true')
    publish(p.parse_args())

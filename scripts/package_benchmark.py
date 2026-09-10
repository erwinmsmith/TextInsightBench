"""Package a built corpus snapshot, public documentation and evaluation assets."""
import argparse
import json
import shutil
from pathlib import Path

from rebuild_benchmark import save, sha


def package(data, evaluation, repo):
    if evaluation.exists():
        raise ValueError('Evaluation output must be a new directory')
    evaluation.mkdir(parents=True)
    release = json.loads((data/'release.json').read_text())
    tasks = json.loads((data/'tasks.json').read_text())
    protocol = {'version':'textinsightbench','evaluation_unit':'evidence-backed downstream finding',
        'discovery_mode':'agent_selected','scoring_version':'finding-quality-discovery',
        'task_families':release['task_family_counts'],
        'tracks':{'task_only':'Use the supplied task corpus.','unlabeled_pool':'Learn from the released pool before evaluation.'},
        'reference_policy':'No fixed conclusions for redesigned tasks; previous references belong only to historical tasks.',
        'semantic_review':'Bounded assignment-stratified and corpus-wide sample; exhaustive arithmetic, not exhaustive semantic verification.',
        'independent_validation':False,'historical_exposure':release['historical_exposure'],
        'cross_task_adaptation':'Freeze global prompts, learned parameters and thresholds; no evaluation-feedback transfer.',
        'security':'Untrusted corpus content. Process runner is not a sandbox.'}
    save(data/'protocol.json',protocol)
    for name in ('tasks.json','release.json','protocol.json'):
        shutil.copy2(data/name,repo/'benchmark'/name)
    shutil.copy2(repo/'textinsightbench/output.schema.json',data/'output.schema.json')
    shutil.copytree(repo/'docs',data/'docs',dirs_exist_ok=True)
    shutil.copy2(repo/'docs/SOURCES.md',data/'SOURCES.md')
    header='''---
pretty_name: TextInsightBench
language:
- en
license: other
license_name: upstream-source-terms
license_link: https://huggingface.co/datasets/CodeSoulco/TextInsightBench/blob/main/SOURCES.md
size_categories:
- 1M<n<10M
task_categories:
- text-generation
tags:
- agent-evaluation
- data-mining
- evidence-grounding
- unsupervised-learning
configs:
'''
    for source in release['learning_by_source']:
        header += f'- config_name: {source}_learning\n  data_files:\n  - split: train\n    path: learning/{source}/*.parquet\n'
    header+='---\n\n'
    body='''# TextInsightBench

**English** | [简体中文](README.zh-CN.md)

An open natural-language data-mining challenge for agents: **50 tasks**, **435,000
task documents**, and **944,468 unlabeled learning documents**. Each task supplies
5,000 or 10,000 texts and a research objective. Agents select their conditions,
populations and comparisons, submit at most three discoveries, quantify their
findings and explain counterexamples and competing interpretations.

| Source | Tasks | Task texts | Learning texts |
|---|---:|---:|---:|
| Amazon Beauty | 13 | 130,000 | 330,885 |
| App Reviews | 13 | 65,000 | 1,660 |
| CFPB | 12 | 120,000 | 483,788 |
| NHTSA | 12 | 120,000 | 128,135 |

Files: tasks.json, corpora/*.jsonl.gz, learning/*/*.parquet, output.schema.json,
protocol.json, release.json, build_provenance.json and manifest.json. Learning
configurations are available with datasets.load_dataset; use the benchmark
runner for task corpora. The learning pool has no labels. Text is preserved;
metadata fields and missingness are described in [DATA.md](docs/DATA.md).

## Run and score

Use the [code and English/Chinese quick start](https://github.com/erwinmsmith/TextInsightBench).
The code's data.lock.json pins exact dataset commits; no numbered benchmark name
is used. Default tasks already use the full exploration challenge. The runner
provides a local corpus file for agent-controlled exploration.

All assignment partitions and arithmetic are verified. Semantic quality uses a
bounded model-reviewed document sample, not exhaustive semantic validation.
Scores emphasize useful discoveries, evidence, statistical validity, competing
explanations and calibrated limits. No independent validation phase is required.
The [evaluation assets](https://huggingface.co/datasets/CodeSoulco/TextInsightBench-Evaluation)
are public. Current redesigned tasks have zero fixed reference conclusions;
earlier references remain in history and are not answers to the new tasks.
Reference coverage is unavailable. See [scoring](docs/SCORING.md).

## Limitations and provenance

New task documents were drawn from a previously public curated learning pool:
they are not guaranteed unseen. Current task and learning IDs are disjoint and
inherit input text/template deduplication, but share entities and sources.
The 50 briefs are not statistically independent. Larger corpora and stronger
requirements do not establish empirical agent difficulty without actual results.

Data derives from Amazon Reviews'23 All Beauty, Android App Reviews, CFPB and
NHTSA complaints. Redistribution authorization was confirmed before publication;
upstream terms differ. [Source attribution and terms](SOURCES.md) apply; the
compilation does not grant new rights over third-party text. Narratives are
unverified author reports and may contain personal information.
'''
    (data/'README.md').write_text(header+body)
    (data/'README.zh-CN.md').write_text('''# TextInsightBench

[English](README.md) | **简体中文**

自然语言数据挖掘 Agent 挑战：50 道任务，435,000 篇任务文本，以及 944,468 篇无标签学习文本。
每题 5,000 或 10,000 篇，Agent 自行发现现象、选择分析范围与比较对象，最多提交 3 个有证据的发现，解释反例及其他可能原因。

任务包含 20 道群体差异、15 道时间变化、15 道复合关联。任务与剩余学习池文档不重叠；任务文本来自此前公开的学习池，不能称为未见数据。来源与实体可共享，题目并非统计独立。

本地检查完整标记与全量算术，模型评审采用语义抽样，不是全量语义确认，也不增加独立验证阶段。改题后没有把旧答案冒充成新 ground truth：当前固定参考结论为 0，旧结论保留在历史提交，参考覆盖率不可用。

[完整中文使用说明](https://github.com/erwinmsmith/TextInsightBench/blob/main/README.zh-CN.md) · [公开测评资源](https://huggingface.co/datasets/CodeSoulco/TextInsightBench-Evaluation) · [数据来源与条款](SOURCES.md)

仓库名称不另加数字版本，通过提交哈希固定快照。原始文本保持不变，正文与任务默认英文。
''')
    references={'benchmark_version':'textinsightbench','tasks_sha256':sha(data/'tasks.json'),
        'reference_policy':'No fixed conclusions for redesigned tasks. Historical references are not reused.',
        'tasks':[{'task_id':t['task_id'],'reference_id':None,'status':'no_fixed_reference'} for t in tasks]}
    save(evaluation/'references.json',references)
    save(evaluation/'release.json',{'version':'textinsightbench','benchmark_version':'textinsightbench',
        'tasks':50,'references':0,'references_sha256':sha(evaluation/'references.json'),
        'tasks_sha256':sha(data/'tasks.json'),'scoring_version':'finding-quality-discovery'})
    for name in ('SCORING.md','DIFFICULTY.md','ORGANIZER.md','SOURCES.md'):
        shutil.copy2(repo/'docs'/name,evaluation/name)
    (evaluation/'README.md').write_text('''---
pretty_name: TextInsightBench Evaluation Assets
language:
- en
license: other
license_name: upstream-source-terms
license_link: https://huggingface.co/datasets/CodeSoulco/TextInsightBench-Evaluation/blob/main/SOURCES.md
tags:
- agent-evaluation
- data-mining
---

# TextInsightBench — Evaluation Assets

**English** | [简体中文](README.zh-CN.md)

Public scoring protocol and reference-availability manifest for the current 50
open exploration tasks. **This snapshot has zero fixed reference conclusions.**
references.json has 50 task records with reference_id=null, bound to the current
tasks.json hash. These records are availability metadata, not annotated answers.

Earlier narrow-task reference conclusions remain in repository history. Their
definitions and populations do not transfer to the redesigned tasks, so they
are not relabeled as current ground truth. Scoring supported discoveries does
not require exact matching to a fixed answer; reference coverage is unavailable.

See [scoring](SCORING.md), [challenge](DIFFICULTY.md), [operations](ORGANIZER.md),
[participant data](https://huggingface.co/datasets/CodeSoulco/TextInsightBench),
and [code and quick start](https://github.com/erwinmsmith/TextInsightBench).
All repositories are public. Exact commit hashes identify snapshots.

Full arithmetic is verified, while semantic judgments use sampled documents and
are fallible. No independent validation set or complete semantic ground truth is
claimed. Report review model, budget, scored coverage and uncertainty. See
[source attribution and terms](SOURCES.md).
''')
    (evaluation/'README.zh-CN.md').write_text('''# TextInsightBench — 测评资源

[English](README.md) | **简体中文**

公开的评分协议与参考可用性清单，对应当前 50 道开放探索任务。
**当前固定参考结论为 0**；references.json 的 50 条记录均为 reference_id=null，表示可用性，不是 50 条标注答案。
旧结论针对旧题范围，仅在历史提交保留，不能直接当成新题的 ground truth。

新题按原文证据和评分规范评价，不要求匹配固定答案，参考覆盖率不可用。
算术全量检查，语义抽样评审；不增加独立验证阶段，不声称全量语义确认。

[完整使用说明](https://github.com/erwinmsmith/TextInsightBench/blob/main/README.zh-CN.md) · [参与者数据](https://huggingface.co/datasets/CodeSoulco/TextInsightBench) · [评分规范](SCORING.md)
''')
    for root in (data,evaluation):
        save(root/'manifest.json',{'files':{str(p.relative_to(root)):{'sha256':sha(p),'bytes':p.stat().st_size}
            for p in sorted(root.rglob('*')) if p.is_file() and p.name!='manifest.json' and '.cache' not in p.parts}})


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--data',type=Path,required=True)
    p.add_argument('--evaluation',type=Path,required=True)
    p.add_argument('--repo',type=Path,default=Path('.'))
    a=p.parse_args();package(a.data,a.evaluation,a.repo)
